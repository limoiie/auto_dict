import dataclasses
import enum
import inspect

# noinspection PyUnresolvedReferences,PyProtectedMember
from typing import (
    Any,
    Callable,
    ForwardRef,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    _GenericAlias,
    get_type_hints,
)

try:
    from typing import final

except ImportError:
    from typing_extensions import final

from registry import Registry

from autodict.errors import UnableFromDict, UnableToDict
from autodict.mapping_factory import mapping_builder
from autodict.options import Options
from autodict import predefined
from autodict.types import (
    O,
    T,
    inspect_generic_origin,
    inspect_generic_templ_args,
    is_annotated_class,
    is_builtin,
    is_generic,
    is_generic_collection,
    is_generic_literal,
    is_generic_union,
    stable_map,
)


@dataclasses.dataclass
class Meta:
    name: str
    to_dict: Optional[Callable[[Any, Options], dict]] = None
    from_dict: Optional[Callable[[Type[T], dict, Options], T]] = None


def dictable(
    cls: T = None, name=None, to_dict=None, from_dict=None
) -> Union[T, Callable[[T], T]]:
    """
    Annotate [Cls] as dictable.

    The default transformation behavior can be overwritten by providing custom
    implementations.

    :param cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param to_dict: A custom function to transform an instance of class `Cls` to
      a dictionary, where the fields can be still objects. None for
      using :py:func:`default_to_dict`.
    :param from_dict: A custom function to transform a dictionary to an instance
      of class `Cls`, where the fields are already transformed.
    :return: the original type.
    """

    def inner(_cls):
        if dataclasses.is_dataclass(_cls):
            to_dict_ = to_dict or predefined.dataclass_to_dict
            from_dict_ = from_dict or predefined.dataclass_from_dict
        elif issubclass(_cls, enum.Enum):
            to_dict_ = to_dict or predefined.enum_to_dict
            from_dict_ = from_dict or predefined.enum_from_dict
        else:
            to_dict_ = to_dict or predefined.default_to_dict
            from_dict_ = from_dict or predefined.default_from_dict

        name_ = name or _cls.__name__
        AutoDict.register(name=name_, to_dict=to_dict_, from_dict=from_dict_)(_cls)
        return _cls

    return inner(cls) if cls else inner


def to_dictable(cls: T = None, name=None, to_dict=None) -> Union[T, Callable[[T], T]]:
    """
    Annotate [cls] as to_dictable.

    :param cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param to_dict: A custom function to transform an instance of class `Cls` to
      a dictionary, where the fields can be still objects. None for
      using :py:func:`default_to_dict`.
    :return: the original type.
    """
    try:
        meta = AutoDict.meta_of(cls)
        from_dict = meta.from_dict or predefined.unable_from_dict
    except KeyError:
        from_dict = predefined.unable_from_dict
    return dictable(cls, name=name, to_dict=to_dict, from_dict=from_dict)


def from_dictable(
    cls: T = None, name=None, from_dict=None
) -> Union[T, Callable[[T], T]]:
    """
    Annotate [cls] as from_dictable.

    :param cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param from_dict: A custom function to transform a dictionary to an instance
      of class `Cls`, where the fields are already transformed.
    :return: the original type.
    """
    try:
        meta = AutoDict.meta_of(cls)
        to_dict = meta.to_dict or predefined.unable_to_dict
    except KeyError:
        to_dict = predefined.unable_to_dict
    return dictable(cls, name=name, to_dict=to_dict, from_dict=from_dict)


class Dictable:
    """
    Base class for these classes that want to be dictable.

    Any classes that derive this class will be automatically marked as dictable.
    The transformation behavior can be overwritten.
    """

    def __init_subclass__(cls, name=None, to_dict=None, from_dict=None):
        dictable(cls, name=name, to_dict=to_dict, from_dict=from_dict)

    def _to_dict(self, options: Options) -> dict:
        """
        Transform self into a dictionary.

        The fields of this instance can be preserved as objects instead of
        dictionaries.

        :return: The transformed dictionary.
        """
        return predefined.default_to_dict(self, options)

    @classmethod
    def _from_dict(cls: Type[T], obj: O, options: Options) -> T:
        """
        Transform a dictionary to an instance of this class.

        The items/fields of the input dictionary should have already been
        transformed.

        :param obj: The dictionary.
        :return: An instance of this class.
        """
        return predefined.default_from_dict(cls, obj, options)

    @final
    def to_dict(self, options: Optional[Options] = None) -> dict:
        """
        Transform self to a dictionary if its class is registered.

        :param options: Options that controls the transform behaviors.
        :return: the transformed dictionary if the class of obj is registered;
          otherwise, just the original object.
        :raises UnToDictable: if there is non-builtin object is not to_dictable
        """
        return AutoDict.to_dict(self, options)

    @classmethod
    @final
    def from_dict(cls: Type[T], obj: O, options: Optional[Options] = None) -> T:
        """
        Instantiate an object from a dictionary.

        :param obj: The dictionary which contains necessary information for
          instantiation.
        :param cls: The class that is going to be instantiated against. If
          providing `None`, the real class will be inferred from the dictionary.
        :param options: Options that controls the transform behaviors.
        :return: the instantiated object of the given class.
        :raises UnFromDictable: if there is non-builtin object is not
          from_dictable.
        """
        return AutoDict.from_dict(obj, cls, options)


class AutoDict(Registry[Meta]):
    CLS_ANNO_KEY = "@"

    @staticmethod
    def to_dict(ins: Any, options: Optional[Options] = None):
        """
        Transform `obj` to a dictionary if its class is registered.

        :param ins: The object going to be transformed.
        :param options: Options that controls the transform behaviors.
        :return: the transformed dictionary if the class of obj is registered;
          otherwise, just the original object.
        :raises UnToDictable: if there is non-builtin object is not to_dictable
        """
        cls = type(ins)
        options = options or Options()

        if issubclass(cls, Dictable):
            # noinspection PyProtectedMember
            obj = ins._to_dict(options)
        elif AutoDict.registered(cls):
            obj = AutoDict.meta_of(cls).to_dict(ins, options)
        elif dataclasses.is_dataclass(ins):
            obj = predefined.dataclass_to_dict(ins, options)
        elif isinstance(ins, enum.Enum):
            obj = predefined.enum_to_dict(ins, options)
        elif is_builtin(cls) or not options.strict:
            obj = ins
        else:
            raise UnableToDict(cls)

        if options.recursively:
            obj = _items_to_dict(obj, options)

        obj = embed_class(cls, obj, options)
        return obj

    @staticmethod
    def from_dict(obj: O, cls: Type[T] = None, options: Optional[Options] = None) -> T:
        """
        Instantiate an object from a dictionary.

        :param obj: The dictionary which contains necessary information for
          instantiation.
        :param cls: The class that is going to be instantiated against. If
          providing `None`, the real class will be inferred from the dictionary.
        :param options: Options that controls the transform behaviors.
        :return: the instantiated object of the given class.
        :raises UnFromDictable: if there is non-builtin object is not
          from_dictable.
        """
        options = options or Options()
        cls = strip_class(obj, cls, options)

        if options.recursively:
            obj = _items_from_dict(obj, cls, options)

        if inspect.isclass(cls) and issubclass(cls, Dictable):
            ins = cls._from_dict(obj, options)
        elif AutoDict.registered(cls):
            ins = AutoDict.meta_of(cls).from_dict(cls, obj, options)
        elif dataclasses.is_dataclass(cls):
            ins = predefined.dataclass_from_dict(cls, obj, options)
        elif inspect.isclass(cls) and issubclass(cls, enum.Enum):
            ins = predefined.enum_from_dict(cls, obj, options)
        elif cls is None or is_builtin(cls) or not options.strict:
            ins = obj
        else:
            raise UnableFromDict(cls)

        return ins


def embed_class(cls: Type[T], obj: O, options: Options) -> O:
    """
    Embed class name into the dictionary if it is not builtin.

    :param cls: The class to be embedded.
    :param obj: The dictionary.
    :param options: Options that controls the transform behaviors.
    :return: The dictionary with class name embedded if it is not builtin;
        otherwise, just the original dictionary.
    """
    if options.with_cls:
        if not is_builtin(cls) and isinstance(obj, dict):
            # if registered, use the registered name
            if AutoDict.registered(cls):
                obj[AutoDict.CLS_ANNO_KEY] = AutoDict.meta_of(cls).name
            # if the cls is native supported (dataclass or enum), use the class name
            elif dataclasses.is_dataclass(cls) or issubclass(cls, enum.Enum):
                obj[AutoDict.CLS_ANNO_KEY] = cls.__name__
            # otherwise, raise the error
            else:
                raise UnableToDict(cls)
    return obj


def strip_class(
    obj: O, cand_cls: Optional[Type[T]], options: Options
) -> Optional[Type[T]]:
    """
    Strip class name from the dictionary if it is embedded,
    and return the class bound to that name if it is registered.

    :param obj: The dictionary.
    :param cand_cls: The candidate class that is going to be instantiated
        against. If providing `None`, the real class will be inferred from the
        dictionary.
    :param options: Options that controls the transform behaviors.
    :return: The class bound to the class name if it is registered; otherwise,
        just the original class.
    """
    if not isinstance(obj, dict) or AutoDict.CLS_ANNO_KEY not in obj:
        return cand_cls

    cls_name = obj[AutoDict.CLS_ANNO_KEY]
    cls = AutoDict.query(name=cls_name)

    if cls is None:
        if not cand_cls and options.strict:
            raise UnableFromDict(cls_name)
    else:
        del obj[AutoDict.CLS_ANNO_KEY]

    return cls or cand_cls


def _items_to_dict(obj: O, options: Options):
    return stable_map(obj, lambda v, _: AutoDict.to_dict(v, options))


def _items_from_dict(obj: O, cls: Optional[type], options: Options):
    if dataclasses.is_dataclass(cls):
        return _items_from_dict_dataclass(obj, cls, options)

    if is_annotated_class(cls):
        return _items_from_dict_annotated_class(obj, cls, options)

    if is_generic_collection(cls):  # List, Set, Dict, Tuple, Mapping, etc
        return _items_from_dict_generic_collection(obj, cls, options)

    if is_generic(cls):  # Union including Optional,
        return _items_from_dict_generic_non_collection(obj, cls, options)

    return stable_map(obj, lambda v, _: AutoDict.from_dict(v, None, options))


def _items_from_dict_dataclass(obj: O, cls: type, opts: Options):
    annotations = get_type_hints(cls)

    def transform_field(field_dic, field_name):
        field_cls = annotations.get(field_name)
        if inspect.isclass(field_cls) and issubclass(field_cls, dataclasses.InitVar):
            field_cls = field_cls.type

        return AutoDict.from_dict(field_dic, field_cls, opts)

    return stable_map(obj, transform_field)


def _items_from_dict_annotated_class(obj: O, cls: type, opts: Options):
    annotations = get_type_hints(cls)

    def transform_field(field_dic, field_name):
        return AutoDict.from_dict(field_dic, annotations.get(field_name), opts)

    return stable_map(obj, transform_field)


def _items_from_dict_generic_non_collection(obj: O, cls: type, opts: Options):
    if is_generic_union(cls):
        cand_classes = inspect_generic_templ_args(cls, defaults=(Any,))
        cand_objects = dict()
        for cand_cls in cand_classes:
            # builtin-as dict should be an instance of the original builtin
            cand_orig_cls = inspect_generic_origin(cand_cls) or cand_cls
            if is_builtin(cand_orig_cls) and not isinstance(obj, cand_orig_cls):
                continue

            # noinspection PyBroadException
            try:
                obj = AutoDict.from_dict(obj, cand_cls, opts)
                cand_objects[cand_cls] = obj
            except Exception:
                continue

        if len(cand_objects) > 1:
            raise ValueError(f"Multiple union type matched: {cand_objects}")

        return cand_objects.popitem()[-1]

    if is_generic_literal(cls):
        cand_literals = inspect_generic_templ_args(cls)
        assert obj in cand_literals
        return obj

    return obj


def _items_from_dict_generic_collection(obj: O, cls: type, opts: Options):
    # infer item type from template args of typing._GenericAlias
    data_cls = inspect_generic_origin(cls)

    if issubclass(data_cls, Mapping):
        key_cls, val_cls = inspect_generic_templ_args(cls, defaults=(Any, Any))
        data_cls = mapping_builder(data_cls)
        return data_cls(
            (
                AutoDict.from_dict(key, key_cls, opts),
                AutoDict.from_dict(val, val_cls, opts),
            )
            for key, val in obj.items()
        )

    if issubclass(data_cls, tuple):
        item_classes = inspect_generic_templ_args(cls, defaults=(Any, ...))
        if len(item_classes) == 2 and item_classes[-1] is ...:
            item_classes = (item_classes[0],) * len(obj)
        return data_cls(
            AutoDict.from_dict(item, item_cls, opts)
            for item, item_cls in zip(obj, item_classes)
        )

    if issubclass(data_cls, (list, set, frozenset)):
        (item_cls,) = inspect_generic_templ_args(cls, defaults=(Any,))
        return data_cls(AutoDict.from_dict(item, item_cls, opts) for item in obj)

    raise ValueError(f"Unhandled generic collection type: {data_cls}")
