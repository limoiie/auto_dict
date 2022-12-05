import copy
import dataclasses
import enum
from typing import Type

import autodict.dataclasses as dataclasses_ext
from autodict.errors import UnableFromDict, UnableToDict
from autodict.types import T, strip_hidden_member_prefix


def default_to_dict(obj):
    return copy.copy(obj.__dict__)


def default_from_dict(cls: Type[T], obj: dict) -> T:
    # todo: support mixin style construction
    try:
        obj = cls()
        obj.__dict__.update(**obj)
    except TypeError:
        obj = cls(**{
            strip_hidden_member_prefix(cls, field): val
            for field, val in obj.items()
        })
    return obj


def enum_to_dict(ins: enum.Enum) -> dict:
    return dict(value=ins.value, name=ins.name)


def enum_from_dict(cls: Type[T], obj: dict) -> T:
    enum_name = obj['name']
    enum_value = obj['value']

    obj = cls(enum_value)
    assert obj.name == enum_name, \
        f'Inconsistent enum {cls} value {enum_value}: \n' \
        f'  expect name {obj.name}, but get name {enum_name}.'
    return obj


def dataclass_to_dict(ins) -> dict:
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


def unable_to_dict(ins) -> dict:
    raise UnableToDict(type(ins))


def unable_from_dict(cls: Type[T], _obj: dict) -> T:
    raise UnableFromDict(cls)
