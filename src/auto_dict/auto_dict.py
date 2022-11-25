import copy
import enum
import importlib
import inspect
from collections import OrderedDict
from typing import Type, TypeVar, ForwardRef

from registry import Registry, SubclassRegistry

T = TypeVar('T')


def dictable(Cls: T = None, name=None, to_dict=None, from_dict=None) -> T:
    """
    Mark [Cls] as dictable.

    The default transformation behavior can be overwritten by providing custom
    implementations.

    :param Cls: The class want to be dictable.
    :param name: The annotation name that may be embedded into dict.
    :param to_dict: A custom function to transform an instance of class `Cls` to
      a dictionary, where the fields can be still objects. None for using
      `default_to_dict`.
    :param from_dict: A custom function to transform a dictionary to an instance
      of class `Cls`, where the fields are already transformed.
    :return: the original type.
    """
    if issubclass(Cls, enum.Enum):
        to_dict = to_dict or enum_to_dict
        from_dict = from_dict or enum_from_dict
    else:
        to_dict = to_dict or default_to_dict
        from_dict = from_dict or default_from_dict

    def inner(cls):
        name_ = name or cls.__name__
        AutoDict.register(name=name_, to_dict=to_dict, from_dict=from_dict)(cls)
        return cls

    return inner(Cls) if Cls else inner


class Dictable(SubclassRegistry):
    """
    Base class for these classes that want to be dictable.

    Any classes that derive this class will be automatically marked as dictable.
    The transformation behavior can be overwritten.
    """
    @classmethod
    def _from_dict(cls: Type[T], dic: dict) -> T:
        """
        Transform a dictionary to an instance of this class.

        The items/fields of the input dictionary should have already been
        transformed.

        :param dic: The dictionary.
        :return: An instance of this class.
        """
        return default_from_dict(cls, dic)

    def _to_dict(self) -> dict:
        """
        Transform self into a dictionary.

        The fields of this instance can be preserved as objects instead of
        dictionaries.

        :return: The transformed dictionary.
        """
        return default_to_dict(self)

    @classmethod
    def from_dict(cls: Type[T], dic: dict) -> T:
        return AutoDict.from_dict(dic, cls=cls, module=cls.__module__)

    def to_dict(self, with_cls: bool = True) -> dict:
        return AutoDict.to_dict(self, with_cls=with_cls)


class AutoDict(Registry):
    CLS_ANNO_KEY = '@'

    @staticmethod
    def to_dict(obj, with_cls=True, recursively=True):
        """
        Transform `obj` to a dictionary if its class is registered.

        :param obj: The object going to be transformed.
        :param with_cls: A boolean value indicating if embedding class path into
          the final dict or not.
        :param recursively: A boolean value indicating if
        :return: the transformed dictionary if the class of obj is registered;
          otherwise, just the original object.
        """
        cls = type(obj)

        if obj and isinstance(obj, Dictable):
            # noinspection PyProtectedMember
            dic = obj._to_dict()
        elif AutoDict.registered(cls):
            dic = AutoDict.meta_of(cls)['to_dict'](obj)
        else:
            dic = obj

        if recursively:
            dic = AutoDict._to_dict_for_items(dic, with_cls)

        AutoDict._embed_class(cls, dic, with_cls)
        return dic

    @staticmethod
    def from_dict(dic: dict or T, cls: Type[T] = None, module=None,
                  recursively=True) -> T:
        """
        Instantiate an object from a dictionary.

        :param dic: The dictionary which contains necessary information for
          instantiation.
        :param cls: The class that is going to be instantiated against. If
          providing `None`, the real class will be inferred from the dictionary.
        :param module: The module path of the current class. This is used to
          provide module information for these local annotation type strings.
        :param recursively: A boolean value indicating if transforms
          items/fields or not.
        :return:
        """
        embedded_cls = AutoDict._extract_class(dic)
        cls = cls or embedded_cls

        if recursively:
            dic = AutoDict._from_dict_for_items(dic, cls, module)

        if inspect.isclass(cls) and issubclass(cls, Dictable):
            obj = cls._from_dict(dic)
        elif AutoDict.registered(cls):
            obj = AutoDict.meta_of(cls)['from_dict'](cls, dic)
        else:
            obj = dic

        return obj

    @staticmethod
    def infer_type(dic):
        """
        Infer type from the given dictionary.

        Normally, the type information was embedded into the dictionary under
        the key of `AutoDict.CLS_ANNO_KEY`
        """
        if not isinstance(dic, dict):
            return None
        try:
            return AutoDict.query(name=dic[AutoDict.CLS_ANNO_KEY])
        except ValueError or KeyError:
            return None

    @staticmethod
    def _to_dict_for_items(obj, with_cls):
        obj = _map(obj, lambda v, _: AutoDict.to_dict(v, with_cls))
        return obj

    @staticmethod
    def _from_dict_for_items(dic, cls, module):
        from_dict = AutoDict.from_dict

        if hasattr(cls, '__annotations__'):
            module = module or cls.__module__

            # infer field type from class annotations
            def _infer_ty(field: str):
                anno_cls = cls.__annotations__.get(field)
                return _resolve_cls(anno_cls, module)

            dic = _map(dic, lambda v, k: from_dict(v, _infer_ty(k), module))

        elif hasattr(cls, '__origin__'):
            # infer item type from template args of typing._GenericAlias
            container_cls = cls.__origin__
            item_cls = cls.__args__[0] \
                if not issubclass(container_cls, dict) else cls.__args__[1]
            item_cls = _resolve_cls(item_cls, module)

            dic = _map(dic, lambda v, _: from_dict(v, item_cls, module))

        else:
            dic = _map(dic, lambda v, _: from_dict(v, module=module))

        return dic

    @staticmethod
    def _embed_class(typ: type, dic: dict, with_cls: bool):
        if with_cls and isinstance(dic, dict):
            dic[AutoDict.CLS_ANNO_KEY] = typ.__name__

    @staticmethod
    def _extract_class(dic):
        if not isinstance(dic, dict) or AutoDict.CLS_ANNO_KEY not in dic:
            return None

        cls_name = dic[AutoDict.CLS_ANNO_KEY]
        del dic[AutoDict.CLS_ANNO_KEY]
        return AutoDict.query(name=cls_name)


def default_to_dict(obj):
    return copy.copy(obj.__dict__)


def default_from_dict(cls: Type[T], dic: dict) -> T:
    try:
        obj = cls()
        obj.__dict__.update(dic)
    except TypeError:
        obj = cls(**dic)
    return obj


def enum_to_dict(enum_obj: enum.Enum) -> dict:
    return dict(value=enum_obj.value, name=enum_obj.name)


def enum_from_dict(cls: Type[T], enum_dic: dict) -> T:
    enum_name = enum_dic['name']
    enum_value = enum_dic['value']

    obj = cls(enum_value)
    assert obj.name == enum_name, \
        f'Inconsistent enum {cls} value {enum_value}: \n' \
        f'  expect name {obj.name}, but get name {enum_name}.'
    return obj


def _is_collection(cls):
    return issubclass(cls, (list, set, tuple, dict, OrderedDict))


def _map(obj, mapper):
    """
    Transform each item of `obj` with `mapper`.

    :param obj: A collection like object
    :param mapper: A transform function.
    """
    typ = type(obj)

    if typ is list:
        return list(mapper(item, None) for item in obj)

    if typ is set:
        return set(mapper(item, None) for item in obj)

    if typ is tuple:
        return tuple(mapper(item, None) for item in obj)

    if typ is dict:
        return dict({key: mapper(item, key) for key, item in obj.items()})

    if typ is OrderedDict:
        return OrderedDict({key: mapper(val, key) for key, val in obj.items()})

    return obj


def _resolve_cls(cls_ref: type or str or ForwardRef, ctx_module: str = None):
    """
    Resolve class by a class reference.

    :param cls_ref: A reference to a class, either directly be a class type, or
      be a full class path, or be an inner module path, or be a `ForwardRef`.
    :param ctx_module: Module path. This is used only when `cls_ref` is an inner
      module path.
    :return: the resolved class.
    """
    if not cls_ref:
        return

    if isinstance(cls_ref, ForwardRef):
        cls_ref = cls_ref.__forward_arg__

    if isinstance(cls_ref, str):
        try:
            module_name, cls_name = cls_ref.rsplit('.', maxsplit=1)
            module = importlib.import_module(module_name)
            inner_module_ref = cls_name

        except ModuleNotFoundError:
            module = importlib.import_module(ctx_module)
            inner_module_ref = cls_ref

        cls = module
        for cls_name in inner_module_ref.split('.'):
            cls = getattr(cls, cls_name)
        return cls

    return cls_ref
