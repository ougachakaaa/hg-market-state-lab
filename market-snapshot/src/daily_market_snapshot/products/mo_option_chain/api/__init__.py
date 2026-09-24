"""FastAPI delivery adapter for the MO Option Chain product.

The exported application contains only the product-local HTTP contract. The
repository runtime composes product adapters from ``daily_market_snapshot.api``.
"""

from __future__ import annotations

from .app import app, create_app
from .endpoint import ROUTE_PATH

__all__ = ["ROUTE_PATH", "app", "create_app"]
