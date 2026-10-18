"""Shared foreground process mechanics for repository commands."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def resolve_executable(name: str) -> str | None:
    return shutil.which(name)


def run_foreground(command: Sequence[str], cwd: Path) -> int:
    try:
        child = subprocess.Popen(command, cwd=cwd)
    except OSError as error:
        print(f"unable to start {command[0]}: {error}", file=sys.stderr)
        return 1
    try:
        return child.wait()
    except KeyboardInterrupt:
        # Both processes receive Ctrl+C in the same foreground console. Give the
        # native launcher a chance to exit, then ensure it is not left running.
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            child.terminate()
            child.wait()
        return 130


def run_python(arguments: Sequence[str], cwd: Path) -> int:
    return run_foreground([sys.executable, *arguments], cwd)
