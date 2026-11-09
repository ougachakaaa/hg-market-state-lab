"""Each HTTP test explicitly uses synthetic configuration and isolated storage."""

import base64
from pathlib import Path

import pytest

from ui_http.auth import _limiter


@pytest.fixture(autouse=True)
def http_auth_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAB_AUTH_DB_PATH", str(tmp_path / "http-auth.sqlite3"))
    monkeypatch.setenv("LAB_AUTH_JWT_SECRET", base64.urlsafe_b64encode(bytes(range(32))).decode())
    monkeypatch.setenv("LAB_AUTH_MODE", "production")
    monkeypatch.setenv("LAB_AUTH_ORIGIN", "https://testserver")
    monkeypatch.setattr(_limiter, "limiter", _limiter.RateLimiter())


@pytest.fixture(autouse=True)
def futures_basis_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ui_http.products.futures_basis_research import runtime

    monkeypatch.setenv("LAB_FUTURES_BASIS_RUN_ROOT", str(tmp_path / "futures-basis-runs"))
    monkeypatch.setattr(runtime, "_runtime", runtime.OnlineRuntime())
