"""G2 acceptance: real SQLite, Argon2, JWT, HTTP Security and deterministic clocks."""

import base64
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from uuid import uuid4

import jwt
import pytest
from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.testclient import TestClient

from http_support.auth import ORIGIN, PASSWORD
from ui_cli.cli import main as cli_main
from ui_http.app import create_app
from ui_http.auth import (
    _http,
    _limiter,
    _session,
    create_service,
)
from ui_http.auth._http_models import AuthHttpError
from ui_http.auth._session import AUDIENCE, COOKIE, ISSUER, AuthConfig
from ui_http.products.mo_option_chain.app import create_app as chain_app
from ui_http.products.mo_option_premium.app import create_app as premium_app


@pytest.fixture
def application() -> FastAPI:
    app = create_app()

    @app.get("/future")
    def future() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/business-failure")
    def failure() -> None:
        raise AuthHttpError("invalid_request")

    return app


@pytest.fixture
def client(application: FastAPI) -> TestClient:
    return TestClient(application, base_url=ORIGIN, headers={"Origin": ORIGIN})


def active_user() -> str:
    service = create_service()
    service.register("alice", PASSWORD)
    user = next(user for user in service.list_pending() if user.username == "alice")
    return service.approve(user.id).id


def login(client: TestClient) -> Any:
    return client.post("/auth/login", json={"username": " ALICE ", "password": PASSWORD})


def assert_error(response: Any, status: int, kind: str) -> None:
    assert response.status_code == status, response.text
    assert response.json()["error"]["kind"] == kind
    assert response.json()["error"]["param"] is None
    assert "set-cookie" not in response.headers
    assert response.headers["cache-control"] == "no-store"
    assert PASSWORD not in response.text


def test_register_cli_approval_login_me_logout(client: TestClient) -> None:
    response = client.post("/auth/register", json={"username": "Alice", "password": PASSWORD})
    assert response.status_code == 202
    assert response.json() == {"message": "Registration request accepted."}
    assert "set-cookie" not in response.headers
    assert_error(login(client), 401, "invalid_credentials")
    (pending,) = create_service().list_pending()
    assert pending.status == "pending"
    assert cli_main(["auth", "approve", pending.id]) == 0
    response = login(client)
    assert response.status_code == 200
    assert response.json() == {"id": pending.id, "username": "alice", "status": "active"}
    header = response.headers["set-cookie"]
    for value in ("HttpOnly", "Secure", "SameSite=strict", "Path=/", "Max-Age=3600", "expires="):
        assert value in header
    assert "Domain=" not in header
    assert COOKIE not in response.text
    assert client.get("/auth/me").json() == response.json()
    logout = client.post("/auth/logout")
    assert logout.status_code == 204 and logout.content == b""
    assert "Max-Age=0" in logout.headers["set-cookie"]
    assert COOKIE not in client.cookies
    assert_error(client.get("/auth/me"), 401, "authentication_required")


@pytest.mark.parametrize("state", ["unknown", "pending", "rejected", "disabled", "wrong"])
def test_uniform_credentials_failure(client: TestClient, state: str) -> None:
    service = create_service()
    if state != "unknown":
        service.register("alice", PASSWORD if state != "wrong" else "another-test-password")
        (pending,) = service.list_pending()
        if state in {"disabled", "wrong"}:
            service.approve(pending.id)
        if state == "disabled":
            service.disable(pending.id)
        if state == "rejected":
            service.reject(pending.id)
    response = login(client)
    assert_error(response, 401, "invalid_credentials")
    assert response.json() == {
        "error": {
            "kind": "invalid_credentials",
            "detail": "Invalid username or password.",
            "param": None,
        }
    }


def test_unknown_user_verifies_dummy_hash(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []
    verify = PasswordHasher.verify

    def tracked(self: PasswordHasher, hash: str, password: str) -> bool:
        calls.append(hash)
        return verify(self, hash, password)

    monkeypatch.setattr(PasswordHasher, "verify", tracked)
    assert_error(login(client), 401, "invalid_credentials")
    assert len(calls) == 1 and calls[0].startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_disable_and_restart_do_not_use_cached_status_or_token_sessions(client: TestClient) -> None:
    user_id = active_user()
    assert login(client).status_code == 200
    second = TestClient(create_app(), base_url=ORIGIN, cookies=client.cookies)
    assert second.get("/auth/me").status_code == 200
    create_service().disable(user_id)
    assert_error(second.get("/auth/me"), 401, "authentication_required")
    assert_error(client.get("/auth/me"), 401, "authentication_required")


def test_sliding_uses_final_status_and_response_time(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [2_000_000_000]
    monkeypatch.setattr(_session.time, "time", lambda: clock[0])
    active_user()
    assert login(client).status_code == 200
    original = client.cookies[COOKIE]
    config = AuthConfig.from_environment()

    def claims(token: str) -> Any:
        return jwt.decode(
            token,
            config.key,
            algorithms=["HS256"],
            audience=AUDIENCE,
            options={"verify_iat": False, "verify_exp": False},
        )

    assert claims(original)["exp"] - claims(original)["iat"] == 3600
    clock[0] += 15
    response = client.get("/future")
    assert response.status_code == 200
    assert claims(client.cookies[COOKIE])["exp"] == clock[0] + 3600
    latest = client.cookies[COOKIE]
    clock[0] += 10
    for path in ("/business-failure", "/absent", "/mo-option-chain"):
        response = client.get(path)
        assert response.status_code >= 400 and "set-cookie" not in response.headers
        assert client.cookies[COOKIE] == latest
    clock[0] = claims(latest)["exp"]
    # httpx may discard an expired cookie; send the token explicitly to test the server boundary.
    response = client.get("/future", headers={"Cookie": f"{COOKIE}={latest}"})
    assert_error(response, 401, "authentication_required")
    assert original != latest


def test_response_time_renewal(
    client: TestClient, application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = [2_000_000_000]
    monkeypatch.setattr(_session.time, "time", lambda: clock[0])
    active_user()
    login(client)

    @application.get("/slow")
    def slow() -> dict[str, str]:
        clock[0] += 4000
        return {"status": "partial"}

    assert client.get("/slow").status_code == 200
    assert AuthConfig.from_environment().subject(client.cookies[COOKIE])


def test_me_and_real_product_success_renew_session(
    client: TestClient, application: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    from http_support.fake_chain_service import FakeChainReadProvider
    from ui_http.products.mo_option_chain.endpoint import get_chain_read_provider

    clock = [2_000_000_000]
    monkeypatch.setattr(_session.time, "time", lambda: clock[0])
    application.dependency_overrides[get_chain_read_provider] = lambda: FakeChainReadProvider()
    active_user()
    assert login(client).status_code == 200
    for path in (
        "/auth/me",
        "/mo-option-chain?target_trade_date=2026-09-17&option_product=MO",
    ):
        clock[0] += 10
        response = client.get(path)
        assert response.status_code == 200
        token = client.cookies[COOKIE]
        claims = jwt.decode(
            token, AuthConfig.from_environment().key, algorithms=["HS256"], audience=AUDIENCE,
            options={"verify_iat": False, "verify_exp": False},
        )
        assert claims["iat"] == clock[0] and claims["exp"] == clock[0] + 3600
        assert "set-cookie" in response.headers


@pytest.mark.parametrize(
    "mutation",
    [
        {"iat": True},
        {"iat": "2000000000"},
        {"iat": 2_000_000_001},
        {"exp": 2_000_000_000},
        {"exp": 2_000_003_601},
        {"exp": 2_000_003_600.0},
        {"iss": "other"},
        {"aud": "other"},
        {"aud": [AUDIENCE]},
        {"sub": "not-uuid"},
        *[{claim: None} for claim in ("iat", "exp", "iss", "aud", "sub")],
    ],
)
def test_invalid_jwt_claims(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, mutation: dict[str, Any]
) -> None:
    monkeypatch.setattr(_session.time, "time", lambda: 2_000_000_000)
    user = active_user()
    claims = {
        "sub": user,
        "iat": 2_000_000_000,
        "exp": 2_000_003_600,
        "iss": ISSUER,
        "aud": AUDIENCE,
    }
    claims.update(mutation)
    claims = {key: value for key, value in claims.items() if value is not None}
    token = jwt.encode(claims, AuthConfig.from_environment().key, algorithm="HS256")
    assert_error(
        client.get("/future", headers={"Cookie": f"{COOKIE}={token}"}),
        401,
        "authentication_required",
    )


@pytest.mark.parametrize(
    "algorithm,key", [("HS384", bytes(range(48))), ("HS256", b"x" * 32), ("none", None)]
)
def test_wrong_signature_and_algorithms(client: TestClient, algorithm: str, key: Any) -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "iat": 1, "exp": 3601, "iss": ISSUER, "aud": AUDIENCE},
        key,
        algorithm=algorithm,
    )
    assert_error(
        client.get("/future", headers={"Cookie": f"{COOKIE}={token}"}),
        401,
        "authentication_required",
    )


@pytest.mark.parametrize("factory", [create_app, chain_app, premium_app])
@pytest.mark.parametrize(
    "path",
    [
        "/docs",
        "/openapi.json",
        "/redoc",
        "/docs/oauth2-redirect",
        "/mo-option-chain",
        "/mo-option-premium-plane",
        "/research/capabilities",
        "/auth/me",
        "/future",
    ],
)
def test_every_app_surface_is_default_deny(factory: Any, path: str) -> None:
    client = TestClient(factory(), base_url=ORIGIN)
    assert_error(client.get(path), 401, "authentication_required")
    assert_error(
        client.get(path, headers={"Authorization": "Bearer ignored"}),
        401,
        "authentication_required",
    )


def test_authentication_precedes_body_parsing_and_research_guard(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Anonymous request entered Research execution")

    monkeypatch.setattr("ui_http.products.research.endpoint.execute_batch", forbidden)
    assert_error(client.post("/research/execute", content=b"{"), 401, "authentication_required")
    assert_error(client.post("/research/preview", content=b"{"), 401, "authentication_required")


@pytest.mark.parametrize(
    "headers,success",
    [
        ({"Origin": ORIGIN}, True),
        ({"Origin": "https://TESTSERVER:443"}, True),
        ({"Referer": ORIGIN + "/login?foo=1"}, True),
        ({}, False),
        ({"Origin": "null"}, False),
        ({"Origin": ""}, False),
        ({"Origin": "https://testserver.evil"}, False),
        ({"Origin": "https://testserver:444"}, False),
        ({"Origin": "http://testserver"}, False),
        ({"Origin": ORIGIN + "/"}, False),
        ({"Origin": ORIGIN + ", " + ORIGIN}, False),
        ({"Origin": "https://evil", "Referer": ORIGIN}, False),
        ({"Referer": "https://evil/path"}, False),
        ({"Origin": "https://testserver@evil"}, False),
        ({"Forwarded": "host=testserver;proto=https", "X-Forwarded-Host": "testserver"}, False),
    ],
)
def test_same_origin_rules(application: FastAPI, headers: dict[str, str], success: bool) -> None:
    client = TestClient(application, base_url=ORIGIN)
    response = client.post("/auth/logout", headers=headers)
    if success:
        assert response.status_code == 204
    else:
        assert_error(response, 403, "origin_forbidden")


@pytest.mark.parametrize(
    "payload",
    [
        b"{",
        b"null",
        b"[]",
        b"{}",
        b'{"username":1,"password":"synthetic-test-password"}',
        b'{"username":"alice","password":"synthetic-test-password","extra":1}',
        b'{"username":"alice","username":"bobby","password":"synthetic-test-password"}',
        b'{"username":"alice","password":"short"}',
        json.dumps({"username": "a" * 65, "password": PASSWORD}).encode(),
        json.dumps({"username": "alice", "password": "a" * 129}).encode(),
        json.dumps({"username": "alice", "password": "test-password\ud800"}).encode(),
        json.dumps({"username": "\talice", "password": PASSWORD}).encode(),
        b" " * 4097,
    ],
)
@pytest.mark.parametrize("path", ["/auth/register", "/auth/login"])
def test_strict_auth_body(client: TestClient, payload: bytes, path: str) -> None:
    response = client.post(path, content=payload, headers={"Content-Type": "application/json"})
    assert_error(response, 400, "invalid_request")


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Type": "text/plain"},
        {"Content-Type": "application/json", "Content-Encoding": "gzip"},
    ],
)
def test_auth_media_type_and_compression(client: TestClient, headers: dict[str, str]) -> None:
    assert_error(client.post("/auth/login", content=b"{}", headers=headers), 400, "invalid_request")


@pytest.mark.parametrize(
    "path,method",
    [
        ("/auth/login?bad=1", "post"),
        ("/auth/register?bad=1", "post"),
        ("/auth/logout?bad=1", "post"),
        ("/auth/me?bad=1", "get"),
    ],
)
def test_auth_rejects_query(client: TestClient, path: str, method: str) -> None:
    active_user()
    login(client)
    assert_error(getattr(client, method)(path), 400, "invalid_request")


def test_me_logout_reject_body(client: TestClient) -> None:
    active_user()
    login(client)
    assert_error(client.request("GET", "/auth/me", content=b"{}"), 400, "invalid_request")
    assert_error(client.post("/auth/logout", content=b"{}"), 400, "invalid_request")


def test_limiter_precedes_body_hash_and_origin_and_ignores_forwarded_ip(
    application: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    monkeypatch.setattr(_limiter.time, "monotonic", lambda: clock[0])
    client = TestClient(application, base_url=ORIGIN)
    for number in range(5):
        assert_error(
            client.post(
                "/auth/login", content=b"{", headers={"X-Forwarded-For": f"192.0.2.{number}"}
            ),
            403,
            "origin_forbidden",
        )
    limited = client.post("/auth/login", content=b"{")
    assert_error(limited, 429, "rate_limited")
    assert limited.headers["retry-after"] == "60"
    clock[0] = 60
    assert_error(client.post("/auth/login"), 403, "origin_forbidden")
    assert_error(client.post("/auth/register"), 403, "origin_forbidden")
    limited = client.post("/auth/register")
    assert_error(limited, 429, "rate_limited")
    assert limited.headers["retry-after"] == "300"
    clock[0] = 360
    assert_error(client.post("/auth/register"), 403, "origin_forbidden")


def test_failed_credentials_count_and_limits_are_shared_across_apps(client: TestClient) -> None:
    for _ in range(5):
        assert_error(login(client), 401, "invalid_credentials")
    other = TestClient(create_app(), base_url=ORIGIN, headers={"Origin": ORIGIN})
    assert_error(login(other), 429, "rate_limited")


def test_atomic_limiter_and_bounded_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_limiter.time, "monotonic", lambda: 10.0)
    limiter = _limiter.RateLimiter(capacity=2)
    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(lambda _: limiter.reserve("login", "proxy-peer"), range(50)))
    assert results.count(None) == 5
    assert set(results) == {None, 60}
    assert limiter.reserve("register", "proxy-peer") is None
    assert limiter.reserve("login", "new-peer") is not None
    assert limiter.reserve("login", "proxy-peer") == 60
    monkeypatch.setattr(_limiter.time, "monotonic", lambda: 310.0)
    assert limiter.reserve("login", "new-peer") is None
    assert len(limiter._buckets) == 1


@pytest.mark.parametrize(
    "setting,value",
    [
        ("LAB_AUTH_JWT_SECRET", None),
        ("LAB_AUTH_JWT_SECRET", "not-base64!"),
        ("LAB_AUTH_JWT_SECRET", base64.urlsafe_b64encode(b"short").decode()),
        ("LAB_AUTH_MODE", "unknown"),
        ("LAB_AUTH_ORIGIN", None),
        ("LAB_AUTH_ORIGIN", "http://testserver"),
        ("LAB_AUTH_ORIGIN", "https://testserver/path"),
        ("LAB_AUTH_ORIGIN", "https://testserver?x=1"),
    ],
)
def test_invalid_serving_config_is_closed_but_offline_schema_works(
    monkeypatch: pytest.MonkeyPatch,
    setting: str,
    value: str | None,
) -> None:
    if value is None:
        monkeypatch.delenv(setting)
    else:
        monkeypatch.setenv(setting, value)
    app = create_app()
    assert "paths" in app.openapi()
    with pytest.raises(RuntimeError, match="configuration"):
        with TestClient(app, base_url=ORIGIN):
            pass
    assert_error(TestClient(app, base_url=ORIGIN).get("/docs"), 500, "internal_error")


def test_loopback_origin_listener_and_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LAB_AUTH_MODE", "loopback-http")
    monkeypatch.setenv("LAB_AUTH_ORIGIN", "http://127.0.0.1:5173")
    config = AuthConfig.from_environment()
    for host in ("0.0.0.0", "192.0.2.1", "::"):
        with pytest.raises(RuntimeError, match="listener"):
            config.validate_listener(host)
    config.validate_listener("127.0.0.1")
    config.validate_listener("::1")
    active_user()
    client = TestClient(
        create_app(), base_url="http://127.0.0.1:8011", headers={"Origin": "http://127.0.0.1:5173"}
    )
    response = login(client)
    assert response.status_code == 200
    assert "Secure" not in response.headers["set-cookie"]
    assert client.get("/auth/me").status_code == 200
    # Alternate factory served with nonlocal listener still refuses even without launcher.
    remote = TestClient(create_app(), base_url="http://192.0.2.1:8011")
    assert_error(remote.get("/docs"), 500, "internal_error")
    monkeypatch.setenv("LAB_AUTH_ORIGIN", "http://192.0.2.1:5173")
    with pytest.raises(RuntimeError):
        AuthConfig.from_environment()


def test_database_failure_is_operational_not_bad_password(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    active_user()
    assert login(client).status_code == 200
    path = Path(str(__import__("os").environ["LAB_AUTH_DB_PATH"]))
    path.write_bytes(b"corrupt database")
    assert_error(client.get("/auth/me"), 500, "internal_error")
    assert_error(login(client), 500, "internal_error")


def test_signing_failure_never_commits_cookie(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    active_user()
    assert login(client).status_code == 200

    def broken(*args: Any) -> Any:
        raise ValueError("synthetic signing failure")

    monkeypatch.setattr(AuthConfig, "issue", broken)
    assert_error(client.get("/auth/me"), 500, "internal_error")
    assert_error(login(client), 500, "internal_error")


def test_offline_schema_publishes_auth_and_security_without_secrets_or_storage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("LAB_AUTH_JWT_SECRET")
    monkeypatch.delenv("LAB_AUTH_ORIGIN")
    for factory in (create_app, chain_app, premium_app):
        doc = factory().openapi()
        scheme = doc["components"]["securitySchemes"]["CookieSession"]
        assert scheme == {"type": "apiKey", "in": "cookie", "name": COOKIE}
        assert "AuthErrorResponse" in doc["components"]["schemas"]
        for path, methods in doc["paths"].items():
            for method, operation in methods.items():
                public = (method.upper(), path) in _http.PUBLIC
                assert operation["security"] == ([] if public else [{"CookieSession": []}])
                assert "422" not in operation["responses"]
    assert not (tmp_path / "http-auth.sqlite3").exists()


def test_chunked_body_bound_is_enforced_before_hashing(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Oversize body reached password hashing")

    monkeypatch.setattr(PasswordHasher, "hash", forbidden)
    assert_error(
        client.post(
            "/auth/register",
            content=iter([b" " * 2048] * 3),
            headers={"Content-Type": "application/json"},
        ),
        400,
        "invalid_request",
    )


def test_duplicate_origin_headers_are_forbidden(client: TestClient) -> None:
    assert_error(
        client.post("/auth/logout", headers=[("Origin", ORIGIN), ("Origin", ORIGIN)]),
        403,
        "origin_forbidden",
    )


def test_public_cookie_precedence_and_failed_login_keep_existing_cookie(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active_user()
    login(client)
    token = client.cookies[COOKIE]
    assert_error(
        client.post("/auth/login", json={"username": "alice", "password": "wrong-password"}),
        401,
        "invalid_credentials",
    )
    assert client.cookies[COOKIE] == token
    register = client.post(
        "/auth/register", json={"username": "alice", "password": "other-password"}
    )
    assert register.status_code == 202 and "set-cookie" not in register.headers
    assert client.cookies[COOKIE] == token
    assert login(client).status_code == 200
    logout = client.post("/auth/logout", headers={"Cookie": f"{COOKIE}=invalid"})
    assert logout.status_code == 204
    assert "Max-Age=0" in logout.headers["set-cookie"]
    assert "Max-Age=3600" not in logout.headers["set-cookie"]


def test_anonymous_valid_queries_never_resolve_product_services(
    client: TestClient,
    application: FastAPI,
) -> None:
    from ui_http.products.mo_option_chain.endpoint import get_chain_read_provider
    from ui_http.products.mo_option_premium.endpoint import get_premium_plane_provider

    def forbidden() -> None:
        raise AssertionError("Anonymous request resolved market service")

    application.dependency_overrides[get_chain_read_provider] = forbidden
    application.dependency_overrides[get_premium_plane_provider] = forbidden
    assert_error(
        client.get("/mo-option-chain?target_trade_date=2026-09-17&option_product=MO"),
        401,
        "authentication_required",
    )
    assert_error(
        client.get("/mo-option-premium-plane?as_of=2026-09-17&option_product=MO"),
        401,
        "authentication_required",
    )


def test_unhandled_runtime_failure_does_not_renew_or_cache(application: FastAPI) -> None:
    @application.get("/unexpected-failure")
    def failure() -> None:
        raise RuntimeError("Synthetic business failure")

    active_user()
    client = TestClient(
        application, base_url=ORIGIN, headers={"Origin": ORIGIN}, raise_server_exceptions=False
    )
    login(client)
    response = client.get("/unexpected-failure")
    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
