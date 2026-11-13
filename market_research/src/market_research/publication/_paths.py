"""Publication-owned portable path checks for operator-controlled local filesystems."""

import os
import stat
from ntpath import isreserved
from pathlib import Path

from .errors import InvalidPublicationInput, PublicationCorrupt


def path_value(value: str | Path) -> Path:
    raw = os.fspath(value)
    if not raw or "\x00" in raw or ".." in Path(raw).parts:
        raise InvalidPublicationInput("invalid publication path")
    path = Path(raw).absolute()
    if os.name == "nt" and any(isreserved(part) for part in path.parts[1:]):
        raise InvalidPublicationInput("reserved publication path")
    return path


def directories(path: Path, *, create: bool = False) -> bool:
    for part in (*reversed(path.parents), path):
        try:
            info = part.lstat()
        except FileNotFoundError:
            if not create:
                return False
            try:
                part.mkdir(mode=0o700)
            except FileExistsError:
                pass
            info = part.lstat()
        if (
            not stat.S_ISDIR(info.st_mode)
            or not info.st_ino
            or getattr(info, "st_file_attributes", 0) & 0x400
        ):
            raise PublicationCorrupt("unsafe publication directory")
    return True


def regular(path: Path) -> os.stat_result:
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or getattr(info, "st_file_attributes", 0) & 0x400
        or info.st_nlink != 1
        or not info.st_ino
    ):
        raise PublicationCorrupt("unsafe publication file")
    return info


def same(before: os.stat_result, after: os.stat_result) -> None:
    if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
        raise PublicationCorrupt("publication object changed")
