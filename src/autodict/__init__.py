__all__ = ['dictable', 'to_dictable', 'from_dictable', 'AutoDict', 'Dictable']

try:
    import importlib.metadata as _importlib_metadata
except ModuleNotFoundError:
    # noinspection PyUnresolvedReferences
    import importlib_metadata as _importlib_metadata

try:
    __version__ = _importlib_metadata.version("autodict")
except _importlib_metadata.PackageNotFoundError:
    __version__ = "unknown version"

import pathlib as _plib

from .autodict import AutoDict, Dictable, dictable, from_dictable, to_dictable


def _path_to_dict(path: _plib.Path):
    return str(path)


def _path_from_dict(cls: type, path: str) -> _plib.Path:
    cls = cls or _plib.Path
    return cls(path)


dictable(_plib.Path, to_dict=_path_to_dict, from_dict=_path_from_dict)
dictable(_plib.PosixPath, to_dict=_path_to_dict, from_dict=_path_from_dict)
dictable(_plib.WindowsPath, to_dict=_path_to_dict, from_dict=_path_from_dict)

# autodict(bson.ObjectId)
