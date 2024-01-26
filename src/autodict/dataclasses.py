# noinspection PyUnresolvedReferences,PyProtectedMember
from dataclasses import Field, MISSING, _FIELD, _FIELDS, _FIELD_INITVAR
from typing import Any, Tuple, Type, TypeVar

from autodict.types import is_generic_optional

T = TypeVar("T", bound=Any)


def instance_fields(cls: Type[T]) -> Tuple[Field, ...]:
    """
    Get the instance fields of a dataclass.

    :param cls: The dataclass
    :return: The instance fields of the dataclass
    """
    # noinspection PyProtectedMember
    return tuple(
        field
        for field in getattr(cls, _FIELDS).values()
        if field._field_type in (_FIELD, _FIELD_INITVAR)
    )


def default_value(field: Field) -> Any:
    """
    Get the default value of a dataclass field.

    :param field: The dataclass field
    :return: The default value of the field
    """
    if field.default != MISSING:
        return field.default

    if field.default_factory != MISSING:
        return field.default_factory()

    if is_generic_optional(field.type):
        return None

    raise RuntimeError(f"Default value not found for field: {field}")


def instantiate(cls: Type[T], init_values: dict, post_init_values: dict) -> T:
    """
    Instantiate a dataclass.

    :param cls: The dataclass.
    :param init_values: Initial values required by dataclass constructor.
    :param post_init_values: The values not required during dataclass construction.
    :return: The instantiated dataclass instance.
    """
    obj = cls(**init_values)
    obj.__dict__.update(**post_init_values)
    return obj
