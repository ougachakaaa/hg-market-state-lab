"""FastAPI delivery adapter for the MO Option Chain product.

The exported application contains only the product-local HTTP contract. The
repository runtime composes product adapters from ``ui_http.app``.
"""

from __future__ import annotations

from .app import app as app
from .app import create_app as create_app
from .endpoint import ROUTE_PATH as ROUTE_PATH
