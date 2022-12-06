import dataclasses


@dataclasses.dataclass
class Options:
    # A boolean value indicating if transforming recursively or not.
    recursively: bool = True

    # A boolean value indicating if raise exceptions or not when there is
    # non-builtin object is un-dictable.
    strict: bool = True

    # A boolean value indicating if embedding class name into the final pure
    # python object or not.
    with_cls: bool = True
