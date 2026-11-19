from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import lab_config
from ui_http.app import create_app
from ui_http.auth import _http
from ui_http.auth._session import COOKIE, AuthConfig
from ui_http.products.mo_option_chain.app import create_app as create_chain_app

API = "http://127.0.0.1:8011"
WEB = "http://127.0.0.1:5173"
PEER = ("127.0.0.1", 54000)
CAPABILITIES = "/research/capabilities"


@pytest.fixture
def local_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FastAPI:
    monkeypatch.setattr(lab_config, "ENV_FILE", tmp_path / "missing.env")
    for key in (
        lab_config.LAB_AUTH_MODE_ENV,
        lab_config.LAB_AUTH_ORIGIN_ENV,
        lab_config.LAB_AUTH_JWT_SECRET_ENV,
    ):
        monkeypatch.delenv(key)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Local access constructed authenticated runtime state")

    monkeypatch.setattr(AuthConfig, "from_settings", forbidden)
    monkeypatch.setattr(_http, "create_service", forbidden)
    app = create_app()

    @app.post("/test-write")
    def write() -> int:
        app.state.writes += 1
        return app.state.writes

    app.state.writes = 0
    return app


def test_default_startup_allows_anonymous_business_without_auth_state(
    local_app: FastAPI, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(lab_config.LAB_AUTH_DB_PATH_ENV)
    with TestClient(local_app, base_url=API, client=PEER) as client:
        mode = client.get("/auth/mode", headers={"Cookie": f"{COOKIE}=old-session"})
        assert mode.status_code == 200
        assert mode.json() == "local"
        assert mode.headers["cache-control"] == "no-store"
        business = client.get(CAPABILITIES)
        assert business.status_code == 200
        assert isinstance(business.json(), list)
        assert client.get("/openapi.json").status_code == 200
        for method, name in (
            ("POST", "register"), ("POST", "login"), ("POST", "logout"), ("GET", "me")
        ):
            result = client.request(method, f"/auth/{name}", headers={"Origin": API})
            assert result.status_code == 404
            assert result.content == b""
            assert result.headers["cache-control"] == "no-store"
            assert "set-cookie" not in result.headers
        assert "set-cookie" not in mode.headers
        assert "set-cookie" not in business.headers
        assert not client.cookies
    assert not (tmp_path / "http-auth.sqlite3").exists()


def test_local_gate_uses_the_same_policy_on_the_product_factory(local_app: FastAPI) -> None:
    with TestClient(create_chain_app(), base_url=API, client=PEER) as client:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/openapi.json", headers={"Host": "external.example"}).status_code == 403


@pytest.mark.parametrize(
    ("listener", "peer", "headers"),
    [
        ("http://192.0.2.1:8011", PEER, {"Host": "127.0.0.1:5173"}),
        (API, ("192.0.2.5", 54000), {}),
        (API, PEER, {"Host": "external.example"}),
        (API, PEER, {"Host": "127.0.0.1:8111"}),
        (API, PEER, {"Host": "127.0.0.1:8011#"}),
        (API, PEER, [("Host", "127.0.0.1:8011"), ("Host", "127.0.0.1:8011")]),
        (API, PEER, {"Forwarded": "for=127.0.0.1"}),
        (API, PEER, {"X-Forwarded-Host": "127.0.0.1:5173"}),
        (API, PEER, {"X-Forwarded-For": "127.0.0.1"}),
        (API, PEER, {"Sec-Fetch-Site": "cross-site"}),
        (API, PEER, {"Origin": "https://external.example"}),
    ],
)
def test_local_rejects_unsafe_connections_and_cross_site_reads(
    local_app: FastAPI,
    listener: str,
    peer: tuple[str, int],
    headers: dict[str, str] | list[tuple[str, str]],
) -> None:
    client = TestClient(local_app, base_url=listener, client=peer)
    for path in ("/auth/mode", CAPABILITIES):
        response = client.get(path, headers=headers)
        assert response.status_code == 403
        assert response.json()["error"]["kind"] == "origin_forbidden"


def test_local_allows_same_origin_writes_and_rejects_others_before_routing(
    local_app: FastAPI,
) -> None:
    client = TestClient(local_app, base_url=API, client=PEER)
    frontend = {"Host": "127.0.0.1:5173"}
    for headers in (
        {},
        {"Origin": "null", "Referer": f"{WEB}/"},
        {"Origin": API},
        {"Origin": WEB, "Sec-Fetch-Site": "cross-site"},
        {"Referer": "https://external.example/page"},
    ):
        assert client.post("/test-write", headers={**frontend, **headers}).status_code == 403
    assert local_app.state.writes == 0
    for headers in (
        {"Origin": API},
        {**frontend, "Origin": WEB, "Sec-Fetch-Site": "same-origin"},
        {**frontend, "Referer": f"{WEB}/research/futures-basis"},
    ):
        response = client.post("/test-write", headers=headers)
        assert response.status_code == 200
        assert "set-cookie" not in response.headers
    assert local_app.state.writes == 3


@pytest.mark.parametrize(("mode", "origin"), [("loopback-http", WEB), ("production", "https://testserver")])
def test_authentication_mode_discovery_does_not_open_business_access(
    mode: str, origin: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(lab_config.LAB_AUTH_MODE_ENV, mode)
    monkeypatch.setenv(lab_config.LAB_AUTH_ORIGIN_ENV, origin)
    with TestClient(create_app(), base_url=API if mode == "loopback-http" else origin) as client:
        response = client.get("/auth/mode", headers={"Cookie": f"{COOKIE}=invalid"})
        assert response.status_code == 200
        assert response.json() == "authenticated"
        assert response.headers["cache-control"] == "no-store"
        assert "set-cookie" not in response.headers
        assert client.get(CAPABILITIES).status_code == 401
        assert client.get("/auth/me").status_code == 401
