"""MO session-owned atomic checkpoints and cross-platform process exclusion."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, BinaryIO

from .service import OptionChainUnavailableError


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    """Publish a JSON manifest only after its complete bytes have been flushed."""
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("manifest must be an object")
    return payload


def verified_files(directory: Path, digests: object, names: tuple[str, ...]) -> bool:
    if not isinstance(digests, dict) or set(digests) != set(names):
        return False
    try:
        return all(digest_file(directory / f"{name}.json") == digests[name] for name in names)
    except OSError:
        return False


class SessionLock:
    """An OS advisory lock releases on process death; no stale PID cleanup needed."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.stream: BinaryIO | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stream = self.path.open("a+b")
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            stream.close()
            raise OptionChainUnavailableError(
                "an identical MO acquisition is already running"
            ) from None
        self.stream = stream

    def release(self) -> None:
        if self.stream is not None:
            if sys.platform == "win32":
                import msvcrt

                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
            self.stream.close()
            self.stream = None
