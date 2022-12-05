from typing import Callable, Iterable, Type

from registry import Registry

from autodict.types import M


class _Meta:
    fn_construct: Callable[[Iterable], M] = None


class MappingFactory(Registry[_Meta]):
    @staticmethod
    def build(mapping_cls: Type[M], data=None, **kwargs) -> M:
        data = data or dict()

        if isinstance(data, dict):
            entries = (*data.items(), *kwargs.items())
        else:
            entries = (*data, *kwargs.items())

        constructor = MappingFactory.builder(mapping_cls)
        return constructor(entries)

    @staticmethod
    def builder(mapping_cls: Type[M]) -> Callable[[Iterable], M]:
        try:
            meta = MappingFactory.meta_of(mapping_cls)
            constructor = meta.fn_construct
        except KeyError:
            constructor = mapping_cls

        return constructor


def mapping_factory(mapping_cls: Type[M], data=None, **kwargs) -> M:
    return MappingFactory.build(mapping_cls, data, **kwargs)


def mapping_builder(mapping_cls: Type[M]) -> Callable[[Iterable], M]:
    return MappingFactory.builder(mapping_cls)
