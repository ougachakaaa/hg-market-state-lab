"""Publication delivery through the actual app and public synthetic publisher."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from http_support.auth import authenticated_client
from market_research.publication import PublicationStore, publish, retain_source
from market_research.publication.visualization import validate_view
from ui_http.app import create_app

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "market_research" / "tests"))
from batch_execution_example import run  # noqa: E402


@pytest.fixture
def published(tmp_path: Path):
    batch = run("stop", inject_failure=True)
    source = retain_source(batch, "synthetic", tmp_path / "source.json")
    store = PublicationStore(tmp_path / "store")
    pid = publish(batch, source, "synthetic context", store)
    app = create_app()
    app.state.publication_store = store
    return authenticated_client(app), store, pid


def test_end_to_end(published):
    client, store, pid = published
    path = f"/research/publications/{pid}"
    listing = client.get("/research/publications")
    assert listing.status_code == 200, listing.text
    assert listing.json()["data"][0]["publication_id"] == pid
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert str(store.root) not in response.text and "source.json" not in response.text
    manifest = response.json()["data"]
    for item in manifest["analyses"]:
        analysis = client.get(f"{path}/analyses/{item['analysis_id']}")
        assert analysis.status_code == 200, analysis.text
        assert analysis.json()["data"]["outcome"] == item["status"]
        original = store.get_analysis(pid, item["analysis_id"])
        if item["status"] == "success":
            from ui_http.products.research_publication.endpoint import decode

            assert analysis.json()["data"]["result"] == decode(original["result"])
        for view in item["views"]:
            response = client.get(f"{path}/views/{view['view_id']}")
            assert response.status_code == 200, response.text
            result = response.json()["data"]
            assert result == store.get_chart_view(pid, view["view_id"])
            validate_view(result)
    assert client.get(path + "?unknown=1").status_code == 400
    assert client.get("/research/publications?limit=101").status_code == 400
    assert client.get("/research/publications/bad").status_code == 400
    assert client.get(path + "/analyses/" + "0" * 64).status_code == 404
    assert client.get(path + "/views/" + "0" * 64).status_code == 404
    assert "no-store" in listing.headers["cache-control"]


def test_access_and_openapi(published):
    client, store, pid = published
    anonymous = TestClient(client.app, base_url="https://testserver")
    assert anonymous.get(f"/research/publications/{pid}").status_code == 401
    schema = client.app.openapi()
    paths = [p for p in schema["paths"] if p.startswith("/research/publications")]
    assert len(paths) == 4
    parameters = schema["paths"]["/research/publications"]["get"]["parameters"]
    assert {item["name"] for item in parameters} == {"limit", "after"}
    routes = [
        route
        for entry in client.app.routes
        for route in getattr(getattr(entry, "original_router", None), "routes", [])
    ]
    for path in paths:
        assert sum(getattr(route, "path", None) == path for route in routes) == 1
    assert all(schema["paths"][path]["get"]["security"] for path in paths)
    assert all("422" not in schema["paths"][path]["get"]["responses"] for path in paths)


def test_access_never_invokes_reader(published, monkeypatch):
    from ui_http.auth import create_service

    client, store, pid = published
    paths = [
        "/research/publications",
        f"/research/publications/{pid}",
        f"/research/publications/{pid}/analyses/" + "0" * 64,
        f"/research/publications/{pid}/views/" + "0" * 64,
    ]

    def forbidden(*args, **kwargs):
        raise AssertionError("reader called before authentication")

    for method in (
        "list_publications",
        "get_publication_manifest",
        "get_analysis",
        "get_chart_view",
    ):
        monkeypatch.setattr(store, method, forbidden)
    anonymous = TestClient(client.app, base_url="https://testserver")
    for path in paths:
        assert anonymous.get(path).status_code == 401
        assert (
            anonymous.get(path, headers={"Cookie": "lab_access_token=invalid"}).status_code == 401
        )
    user_id = client.get("/auth/me").json()["id"]
    create_service().disable(user_id)
    for path in paths:
        assert client.get(path).status_code == 401


def test_failures_and_bounds(published, tmp_path, monkeypatch):
    from market_research.publication import (
        InconsistentPublication,
        PublicationCorrupt,
        PublicationUnavailable,
        UnsupportedPublicationVersion,
    )
    from ui_http.products.research_publication import endpoint

    client, store, pid = published
    path = f"/research/publications/{pid}"
    for exc, status, kind in [
        (PublicationCorrupt, 409, "corrupt"),
        (InconsistentPublication, 409, "inconsistent"),
        (UnsupportedPublicationVersion, 409, "unsupported_version"),
        (PublicationUnavailable, 503, "unavailable"),
        (RuntimeError, 500, "internal_error"),
    ]:

        def fail(*args, _exc=exc, **kwargs):
            raise _exc("secret /private/path")

        with monkeypatch.context() as patch:
            patch.setattr(store, "get_publication_manifest", fail)
            response = client.get(path)
            assert response.status_code == status
            assert response.json()["error"]["kind"] == kind
            assert "secret" not in response.text and "/private/path" not in response.text
    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "MAX_BYTES", 1)
        assert client.get(path).status_code == 413
    client.app.state.publication_store = PublicationStore(tmp_path / "empty")
    assert client.get("/research/publications").json() == {"data": [], "next_cursor": None}
    del client.app.state.publication_store
    monkeypatch.delenv("LAB_RESEARCH_PUBLICATION_ROOT", raising=False)
    assert client.get("/research/publications").status_code == 503


def test_corrupt_manifest_and_layer(published):
    import json

    client, store, pid = published
    commit = store.root / "publications" / f"{pid}.json"
    envelope = json.loads(commit.read_text())
    source_manifest = store.get_publication_manifest(pid)
    view = next(v for analysis in source_manifest["analyses"] for v in analysis["views"])
    layer = store.root / "bundles" / envelope["bundle"] / "layers" / f"{view['layer_id']}.json"
    layer.write_text("{}")
    response = client.get(f"/research/publications/{pid}/views/{view['view_id']}")
    assert response.status_code == 409 and response.json()["error"]["kind"] == "corrupt"
    commit.write_text("{}")
    response = client.get(f"/research/publications/{pid}")
    assert response.status_code == 409 and response.json()["error"]["kind"] == "corrupt"


def test_expired_cookie_rejected_before_read(published, monkeypatch):
    import jwt

    from ui_http.auth import _session
    from ui_http.auth._session import AUDIENCE, AuthConfig

    client, store, pid = published
    token = client.cookies["lab_access_token"]
    claims = jwt.decode(
        token,
        AuthConfig.from_environment().key,
        algorithms=["HS256"],
        audience=AUDIENCE,
        options={"verify_iat": False, "verify_exp": False},
    )
    monkeypatch.setattr(_session.time, "time", lambda: claims["exp"])

    def forbidden(*args, **kwargs):
        raise AssertionError("reader called for expired session")

    monkeypatch.setattr(store, "get_publication_manifest", forbidden)
    response = client.get(
        f"/research/publications/{pid}", headers={"Cookie": f"lab_access_token={token}"}
    )
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_cursor_and_strict_queries(published):
    client, store, pid = published
    response = client.get("/research/publications?limit=1")
    assert response.status_code == 200
    cursor = response.json()["next_cursor"]
    assert cursor and pid not in cursor
    assert client.get("/research/publications", params={"after": cursor}).json()["data"] == []
    for query in ("limit=1&limit=2", "after=bad", "limit=0", "other=value"):
        assert client.get(f"/research/publications?{query}").status_code == 400
    assert client.get("/research/publications/00000000000040008000000000000000").status_code == 404


def test_get_does_not_modify_store_or_invoke_execution(published, monkeypatch):
    import market_research.descriptive.execution as execution
    import market_research.publication as publication
    import market_statistics

    client, store, pid = published
    manifest = store.get_publication_manifest(pid)
    sample = next(a for a in manifest["analyses"] if a["views"])
    before = {
        p.relative_to(store.root): p.read_bytes() for p in store.root.rglob("*") if p.is_file()
    }

    def forbidden(*args, **kwargs):
        raise AssertionError("GET invoked a mutation or computation")

    monkeypatch.setattr(publication, "publish", forbidden)
    monkeypatch.setattr(publication, "retain_source", forbidden)
    monkeypatch.setattr(execution, "execute_batch", forbidden)
    monkeypatch.setattr(market_statistics, "compute", forbidden)
    path = f"/research/publications/{pid}"
    for url in (
        "/research/publications",
        path,
        f"{path}/analyses/{sample['analysis_id']}",
        f"{path}/views/{sample['views'][0]['view_id']}",
    ):
        assert client.get(url).status_code == 200
    after = {
        p.relative_to(store.root): p.read_bytes() for p in store.root.rglob("*") if p.is_file()
    }
    assert before == after
