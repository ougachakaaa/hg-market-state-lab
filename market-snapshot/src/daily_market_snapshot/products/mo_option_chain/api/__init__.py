"""FastAPI delivery adapter and composed market-snapshot runtime.

``create_app`` builds the isolated MO Option Chain contract application; the
exported runtime ``app`` additionally composes the independent MO Premium Plane
route. Both remain delivery surfaces and never reinterpret market semantics.
"""

from __future__ import annotations

from .app import app, create_app
from .endpoint import ROUTE_PATH

__all__ = ["ROUTE_PATH", "app", "create_app"]
