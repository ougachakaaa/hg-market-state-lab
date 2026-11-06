"""Publication unavailability is isolated from HTTP app composition."""

from __future__ import annotations

from pathlib import Path

import pytest

from http_support.auth import authenticated_client
from market_research.publication import PublicationStore, _platform
from ui_http.app import create_app


def test_publication_routes_report_unavailable_without_posix_storage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(_platform, "supports_descriptor_relative_io", lambda: False)
    root = tmp_path / "store"
    application = create_app()
    application.state.publication_store = PublicationStore(root)
    client = authenticated_client(application)

    response = client.get("/research/publications")

    assert response.status_code == 503, response.text
    assert response.json() == {
        "error": {
            "kind": "unavailable",
            "detail": "Publication storage is unavailable.",
            "param": None,
        }
    }
    assert not root.exists()
    assert client.get("/openapi.json").status_code == 200
