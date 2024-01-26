from typing import Callable, Iterable, Type

from registry import Registry

from autodict.types import M


class _Meta:
    fn_construct: Callable[[Iterable], M] = None


class MappingFactory(Registry[_Meta]):
    """
    A factory to build mapping objects.

    This factory provides a unified interface to build mapping objects
    from a dict or/and an iterable of key-value pairs.
    """

    @staticmethod
    def build(mapping_cls: Type[M], data=None, **kwargs) -> M:
        """
        Build a mapping object.

        :param mapping_cls: The underlying mapping class.
        :param data: The data to be used to construct the mapping object.
            Can be a dict or/and an iterable of key-value pairs.
        :param kwargs: The data to be used to construct the mapping object.
        :return:
        """
        data = data or dict()

        if isinstance(data, dict):
            entries = (*data.items(), *kwargs.items())
        else:
            entries = (*data, *kwargs.items())

        constructor = MappingFactory.builder(mapping_cls)
        return constructor(entries)

    @staticmethod
    def builder(mapping_cls: Type[M]) -> Callable[[Iterable], M]:
        """
        Create a builder for building a mapping object.

        :param mapping_cls: The underlying mapping class.
            This class must either be registered in the factory or
            originally accepts a dict or/and an iterable of key-value pairs
            as its constructor argument.
        :return: A builder for building a mapping object.
        """
        try:
            meta = MappingFactory.meta_of(mapping_cls)
            constructor = meta.fn_construct
        except KeyError:
            constructor = mapping_cls

        return constructor


mapping_factory = MappingFactory.build

mapping_builder = MappingFactory.builder
