"""Repository-wide HTTP delivery runtime."""

from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .app import app as app
    from .app import create_app as create_app


class _HttpFacade(ModuleType):
    def __getattribute__(self, name: str) -> Any:
        # A submodule import sets package.app to that module. Preserve the historical
        # FastAPI object facade even when ui_http.app is imported before the facade.
        if name in {"app", "create_app"}:
            return getattr(import_module(".app", __name__), name)
        return super().__getattribute__(name)


sys.modules[__name__].__class__ = _HttpFacade
__all__ = ["app", "create_app"]
