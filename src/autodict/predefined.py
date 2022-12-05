import copy
import dataclasses
import enum
import inspect
from typing import Any, Type

import autodict.dataclasses as dataclasses_ext
from autodict.errors import UnableFromDict, UnableToDict
from autodict.types import O, T, strip_hidden_member_prefix


def default_to_dict(ins: Any) -> O:
    return copy.copy(ins.__dict__)


def default_from_dict(cls: Type[T], obj: O) -> T:
    fn_init = getattr(cls, '__init__', None)
    if fn_init:
        cand_param_values = {
            strip_hidden_member_prefix(cls, field_name):
                (field_name, field_value)
            for field_name, field_value in obj.items()
        }
        positional_param_values = list()
        keyword_param_values = dict()
        init_field_names = set()

        # capture param assignments
        sig = inspect.signature(fn_init)
        for param in sig.parameters.values():
            if param.name == 'self':
                continue

            if param.name in cand_param_values:
                field_name, field_value = cand_param_values[param.name]
                init_field_names.add(field_name)

                if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                    positional_param_values.append(field_value)
                elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    positional_param_values.append(field_value)
                elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                    positional_param_values.extend(field_value)
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    keyword_param_values[param.name] = field_value
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    keyword_param_values.update(field_value)

            else:
                keyword_param_values[param.name] = param.default

        # fields that not in __init__ parameter list
        post_init_values = {
            field_name: field_value
            for field_name, field_value in obj.items()
            if field_name not in init_field_names
        }
        ins = cls(*positional_param_values, **keyword_param_values)

    else:
        post_init_values = obj
        ins = cls()

    ins.__dict__.update(post_init_values)
    return ins


def enum_to_dict(ins: enum.Enum) -> O:
    return dict(value=ins.value, name=ins.name)


def enum_from_dict(cls: Type[T], obj: dict) -> T:
    enum_name = obj['name']
    enum_value = obj['value']

    obj = cls(enum_value)
    assert obj.name == enum_name, \
        f'Inconsistent enum {cls} value {enum_value}: \n' \
        f'  expect name {obj.name}, but get name {enum_name}.'
    return obj


def dataclass_to_dict(ins: Any) -> O:
    return dict((f.name, getattr(ins, f.name)) for f in dataclasses.fields(ins))


def dataclass_from_dict(cls: Type[T], obj: dict) -> T:
    init_values = {}
    post_init_values = {}

    for field in dataclasses_ext.instance_fields(cls):
        field_value = obj[field.name] if field.name in obj else \
            dataclasses_ext.default_value(field)

        if field.init:
            init_values[field.name] = field_value
        else:
            post_init_values[field.name] = field_value

    return dataclasses_ext.instantiate(cls, init_values, post_init_values)


def unable_to_dict(ins: Any):
    raise UnableToDict(type(ins))


def unable_from_dict(cls: Type[T], _obj: O) -> T:
    raise UnableFromDict(cls)
