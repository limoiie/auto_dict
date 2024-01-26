import copy
import dataclasses
import enum
import inspect
from typing import Any, Type

import autodict.dataclasses as dataclasses_ext
from autodict.errors import UnableFromDict, UnableToDict
from autodict.options import Options
from autodict.types import O, T, strip_hidden_member_prefix

__all__ = [
    "default_to_dict",
    "default_from_dict",
    "enum_to_dict",
    "enum_from_dict",
    "dataclass_to_dict",
    "dataclass_from_dict",
    "unable_to_dict",
    "unable_from_dict",
]


def default_to_dict(ins: Any, _option: Options) -> O:
    """
    Default to_dict implementation.

    This method transforms any instance to a dict by copying its __dict__.
    NOTE: this method do NOT transform in a recursive manner.

    :param ins: The instance to be transformed.
    :param _option: The transform options.
    :return: The dict representation of the instance.
    """
    return copy.copy(ins.__dict__)


def default_from_dict(cls: Type[T], obj: O, _option: Options) -> T:
    """
    Default from_dict implementation.

    This method transforms a dict to an instance of the given class.
    The instantiation follows the following rules:
    - if the class has __init__ method, the dict is used to initialize the instance;
        concretely, any keys in the dict that are also in the __init__ parameter list
        are used to initialize the instance,
        and the rest are used to update the instance's __dict__;
    _ otherwise, the instance is created without parameters and
        the dict is used to update the instance's __dict__.
    NOTE: this method do NOT transform in a recursive manner.

    :param cls: The class of the instance to be transformed.
    :param obj: The dict to be transformed.
    :param _option: The transform options.
    :return: The instance of the given class.
    """
    fn_init = getattr(cls, "__init__", None)
    if fn_init:
        # candidate parameter name-value pairs by processing the given dict
        cand_param_values = {
            strip_hidden_member_prefix(cls, field_name): (field_name, field_value)
            for field_name, field_value in obj.items()
        }
        positional_param_values = list()
        keyword_param_values = dict()
        init_field_names = set()

        # capture param assignments
        sig = inspect.signature(fn_init)
        for param in sig.parameters.values():
            if param.name == "self":
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


def enum_to_dict(ins: enum.Enum, _options: Options) -> O:
    """
    Transform an enum instance to a dict.

    NOTE: this method do NOT transform in a recursive manner.
    """
    return dict(value=ins.value, name=ins.name)


def enum_from_dict(cls: Type[T], obj: dict, _options: Options) -> T:
    """
    Transform a dict to an enum instance.

    NOTE: this method do NOT transform in a recursive manner.
    """
    enum_name = obj["name"]
    enum_value = obj["value"]

    obj = cls(enum_value)
    assert obj.name == enum_name, (
        f"Inconsistent enum {cls} value {enum_value}: \n"
        f"  expect name {obj.name}, but get name {enum_name}."
    )
    return obj


def dataclass_to_dict(ins: Any, _options: Options) -> O:
    """
    Transform a dataclass to a dict.

    This method respects the dataclass field definition.
    NOTE: this method do NOT transform in a recursive manner.

    This method is preferred rather than `dataclasses.asdict` because:
    - it transforms the dataclass fields with no respect to autodict;
    - here we just want to transform the dataclass fields in a non-recursive manner.

    :param ins: A dataclass instance
    :param _options: The options for the transform.
    :return: The dict representation of the dataclass instance.
    """
    return dict((f.name, getattr(ins, f.name)) for f in dataclasses.fields(ins))


def dataclass_from_dict(cls: Type[T], obj: dict, _options: Options) -> T:
    """
    Transform a dict to a dataclass instance.

    This method respects the dataclass field definition.
    NOTE: this method do NOT transform in a recursive manner.

    :param cls: The dataclass class.
    :param obj: The dict to be transformed.
    :param _options: The options for the transform.
    :return: The dataclass instance.
    """
    init_values = {}
    post_init_values = {}

    for field in dataclasses_ext.instance_fields(cls):
        field_value = (
            obj[field.name]
            if field.name in obj
            else dataclasses_ext.default_value(field)
        )

        if field.init:
            init_values[field.name] = field_value
        else:
            post_init_values[field.name] = field_value

    return dataclasses_ext.instantiate(cls, init_values, post_init_values)


def unable_to_dict(ins: Any, _options: Options):
    raise UnableToDict(type(ins))


def unable_from_dict(cls: Type[T], _obj: O, _options: Options) -> T:
    raise UnableFromDict(cls)
