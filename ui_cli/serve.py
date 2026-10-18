"""Delegate development servers to their owning launchers."""

from __future__ import annotations

import sys

from . import ROOT
from .process import resolve_executable, run_foreground, run_python

BACKEND_API = ROOT / "ui_http"
FRONTEND = ROOT / "ui_web"


def backend() -> int:
    if not (ROOT / "pyproject.toml").is_file() or not (ROOT / "poetry.lock").is_file():
        print("backend prerequisites missing: root pyproject.toml or poetry.lock", file=sys.stderr)
        return 1
    if not (BACKEND_API / "scripts" / "api.py").is_file():
        print("backend launcher missing: ui_http/scripts/api.py", file=sys.stderr)
        return 1
    return run_python(["ui_http/scripts/api.py"], ROOT)


def frontend() -> int:
    if not (FRONTEND / "package.json").is_file():
        print("frontend not initialized: ui_web/package.json not found", file=sys.stderr)
        return 1
    npm = resolve_executable("npm")
    if npm is None:
        print("frontend prerequisite missing: npm", file=sys.stderr)
        return 1
    return run_foreground([npm, "run", "dev"], FRONTEND)
