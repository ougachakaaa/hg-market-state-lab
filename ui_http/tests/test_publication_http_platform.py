"""Publication unavailability is isolated from HTTP app composition."""

from __future__ import annotations

from pathlib import Path

import pytest

from http_support.auth import authenticated_client
from market_research.publication import PublicationStore
from ui_http.app import create_app


def test_publication_routes_report_unavailable_with_unsafe_storage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "store"
    root.write_text("unsafe root")
    application = create_app()
    application.state.publication_store = PublicationStore(root)
    client = authenticated_client(application)

    response = client.get("/research/publications")

    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "kind": "corrupt",
            "detail": "Publication artifact is corrupt.",
            "param": None,
        }
    }
    assert root.read_text() == "unsafe root"
    assert client.get("/openapi.json").status_code == 200
