import copy
import dataclasses
import enum
from typing import Type

from autodict.errors import UnableFromDict, UnableToDict
from autodict.types import T, strip_hidden_member_prefix


def default_to_dict(obj):
    return copy.copy(obj.__dict__)


def default_from_dict(cls: Type[T], dic: dict) -> T:
    # todo: support mixin style construction
    try:
        obj = cls()
        obj.__dict__.update(**dic)
    except TypeError:
        obj = cls(**{
            strip_hidden_member_prefix(cls, field): val
            for field, val in dic.items()
        })
    return obj


def enum_to_dict(obj: enum.Enum) -> dict:
    return dict(value=obj.value, name=obj.name)


def enum_from_dict(cls: Type[T], dic: dict) -> T:
    enum_name = dic['name']
    enum_value = dic['value']

    obj = cls(enum_value)
    assert obj.name == enum_name, \
        f'Inconsistent enum {cls} value {enum_value}: \n' \
        f'  expect name {obj.name}, but get name {enum_name}.'
    return obj


def dataclass_to_dict(obj) -> dict:
    return dict((f.name, getattr(obj, f.name)) for f in dataclasses.fields(obj))


def dataclass_from_dict(cls: Type[T], dic: dict) -> T:
    return cls(**dic)


def unable_to_dict(obj) -> dict:
    raise UnableToDict(type(obj))


def unable_from_dict(cls: Type[T], _dic: dict) -> T:
    raise UnableFromDict(cls)
