"""Minimal HTTP delivery adapter of ``market-snapshot`` (FastAPI).

The adapter exposes the MO Option Chain HTTP contract
(``market-snapshot/guides/mo-option-chain/http-contract.md``) and nothing else. It is a delivery
surface, not a business layer: it reads the chain through the Data Service
application boundary and never reinterprets market semantics.
"""

from __future__ import annotations

from .app import app, create_app
from .endpoint import ROUTE_PATH

__all__ = ["ROUTE_PATH", "app", "create_app"]
