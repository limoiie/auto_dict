import pathlib as _plib

from .autodict import dictable, to_dictable, from_dictable, AutoDict, Dictable

__all__ = ['dictable', 'to_dictable', 'from_dictable', 'AutoDict', 'Dictable']


def _path_to_dict(path: _plib.Path):
    return str(path)


def _path_from_dict(cls: type, path: str) -> _plib.Path:
    cls = cls or _plib.Path
    return cls(path)


dictable(_plib.Path, to_dict=_path_to_dict, from_dict=_path_from_dict)
dictable(_plib.PosixPath, to_dict=_path_to_dict, from_dict=_path_from_dict)
dictable(_plib.WindowsPath, to_dict=_path_to_dict, from_dict=_path_from_dict)

# autodict(bson.ObjectId)
