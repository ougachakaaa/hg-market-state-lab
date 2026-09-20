"""Tests for the HTTP adapter launcher shim ``scripts/api.py``.

Authority: ``README.md`` (the documented local HTTP API address) over
``guides/mo-option-chain-http-contract.md`` (the endpoint contract, which leaves
the bind address to deployment).

These tests lock the documented startup behaviour of the thin executable shim:
running it with no arguments serves the adapter on ``127.0.0.1:8011``, and the
bind address stays overridable. They never start a server: ``uvicorn.run`` is
replaced by a recorder.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

from daily_market_snapshot.api import app as adapter_app

SHIM_PATH = Path(__file__).resolve().parent.parent / "scripts" / "api.py"

# The local address the README documents for the HTTP API.
DOCUMENTED_HOST = "127.0.0.1"
DOCUMENTED_PORT = 8011


def load_shim() -> Any:
    """Load ``scripts/api.py`` without executing its ``__main__`` block."""
    spec = importlib.util.spec_from_file_location("dms_api_shim", SHIM_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def serve(module: Any, monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> dict[str, Any]:
    """Run the shim with ``argv`` and record what it asked uvicorn to do."""
    calls: dict[str, Any] = {}

    def fake_run(application: Any, **kwargs: Any) -> None:
        calls["app"] = application
        calls.update(kwargs)

    monkeypatch.setattr(module.uvicorn, "run", fake_run)
    module.main(argv)
    return calls


def test_the_shim_serves_the_delivery_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_shim()

    calls = serve(module, monkeypatch, [])

    assert calls["app"] is adapter_app


def test_the_default_bind_address_is_the_documented_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_shim()

    calls = serve(module, monkeypatch, [])

    assert calls["host"] == DOCUMENTED_HOST
    assert calls["port"] == DOCUMENTED_PORT


def test_the_bind_address_stays_overridable(monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_shim()

    calls = serve(module, monkeypatch, ["--host", "0.0.0.0", "--port", "9000"])

    assert calls["host"] == "0.0.0.0"
    assert calls["port"] == 9000
