"""Auth export is a narrow offline projection, with no runtime configuration."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_auth_export_is_offline_and_complete(monkeypatch, tmp_path):
    for name in ("LAB_AUTH_JWT_SECRET", "LAB_AUTH_MODE", "LAB_AUTH_ORIGIN"):
        monkeypatch.delenv(name, raising=False)
    database = tmp_path / "must-not-exist.sqlite3"
    monkeypatch.setenv("LAB_AUTH_DB_PATH", str(database))
    exporter = runpy.run_path(str(ROOT / "ui_web/scripts/export_contracts.py"))
    document = exporter["create_auth_app"]().openapi()
    assert not database.exists()
    assert set(document["paths"]) == {
        "/auth/register", "/auth/login", "/auth/me", "/auth/logout",
    }
    assert set(document["components"]["schemas"]) == {
        "Accepted", "ActiveIdentity", "AuthErrorBody", "AuthErrorResponse", "Credentials",
    }
    assert document["components"]["securitySchemes"]["CookieSession"] == {
        "type": "apiKey", "in": "cookie", "name": "lab_access_token",
    }
    assert document["paths"]["/auth/me"]["get"]["security"] == [{"CookieSession": []}]
    for path in ("/auth/register", "/auth/login", "/auth/logout"):
        assert document["paths"][path]["post"]["security"] == []
    assert "429" in document["paths"]["/auth/login"]["post"]["responses"]
