import dataclasses
from typing import Any, Optional, Tuple


def is_namedtuple(obj: Any):
    """
    Check if an object is a namedtuple.
    """
    cls = obj if isinstance(obj, type) else type(obj)
    return issubclass(cls, tuple) and hasattr(cls, "_fields")


@dataclasses.dataclass
class NamedtupleField:
    name: str
    default: Optional[Tuple[Any]]

    def get_default(self):
        return self.default[0] if self.default else None


def instance_fields(cls: tuple) -> Tuple[NamedtupleField, ...]:
    """
    Get the instance fields of a namedtuple.
    """
    fields = getattr(cls, "_fields")
    defaults = getattr(cls, "_field_defaults")
    return tuple(
        NamedtupleField(
            field,
            default=defaults[field] if field in defaults else None,
        )
        for field in fields
    )
