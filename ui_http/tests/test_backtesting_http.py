"""W2 ASGI acceptance: real Cookie auth, worker, public pipeline and temporary store."""

import asyncio
import json
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from http_support.auth import ORIGIN, PASSWORD, authenticated_client
from market_backtesting.cases.futures_roll_long import (
    FuturesRollApplicationError,
    FuturesRollOnlineError,
    create_futures_roll_online_application,
    online,
    online_sqlite_store,
)
from ui_http.app import create_app
from ui_http.auth import _session, create_service
from ui_http.auth._session import COOKIE, AuthConfig
from ui_http.products.backtesting import endpoint

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "market_backtesting/tests"))
from public_input_fixtures import DAYS, fake_services, request  # noqa: E402

BASE = "/backtesting/futures-roll"
RUNS = BASE + "/runs"
BODY = {
    "product_code": "IM",
    "start_date": "2025-02-17",
    "end_date": "2025-03-25",
    "strategy_profile": "expiry_to_M1_v1",
}
PATHS = [
    ("POST", BASE + "/preflight"),
    ("POST", RUNS),
    ("GET", RUNS + "/bad"),
    ("GET", RUNS + "/bad/result"),
]


@pytest.fixture
def product(tmp_path):
    service, calendar, futures, index = fake_services()
    app = create_app()
    root = tmp_path / "runs"
    online_app = create_futures_roll_online_application(root=root, service=service)
    app.state.backtesting_application = online_app
    client = authenticated_client(app)
    return app, online_app, client, root, (calendar, futures, index)


def run_count(root):
    with sqlite3.connect(root / "runs.sqlite3") as connection:
        return connection.execute("SELECT count(*) FROM runs").fetchone()[0]


def assert_error(response, status, kind):
    assert response.status_code == status, response.text
    assert response.json()["error"]["kind"] == kind
    assert response.json()["error"]["param"] is None
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    for word in ("owner_scope", "Traceback", "/private", "secret-token", PASSWORD):
        assert word not in response.text


def terminal(client, run_id):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        response = client.get(f"{RUNS}/{run_id}")
        assert response.status_code == 200, response.text
        state = response.json()
        if state["status"] in {"COMPLETED", "FAILED", "INTERRUPTED"}:
            # Terminal persistence precedes release of the admission guard.
            with online._PROCESS_LOCK:
                if online._ACTIVE is None:
                    return state
        time.sleep(0.005)
    pytest.fail("Worker did not settle")


def complete(client, body=None):
    response = client.post(RUNS, json=BODY if body is None else body)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "PENDING"
    assert set(response.json()) == {"run_id", "status", "request", "created_at"}
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" in response.headers
    run_id = response.json()["run_id"]
    assert terminal(client, run_id)["status"] == "COMPLETED"
    return run_id


@pytest.mark.parametrize(
    "profile,pnl,target",
    [
        ("expiry_to_M1_v1", 22000, "IM2504.CFX"),
        ("expiry_to_Q1_v1", 19000, "IM2506.CFX"),
    ],
)
def test_complete_result_is_exact_producer_projection(product, profile, pnl, target):
    app, application, client, root, services = product
    run_id = complete(client, {**BODY, "strategy_profile": profile})
    state = client.get(f"{RUNS}/{run_id}").json()
    assert set(state) == {
        "run_id",
        "request",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "failure",
        "result_available",
    }
    assert state["result_available"] and state["failure"] is None
    identity = client.get("/auth/me").json()["id"]
    with sqlite3.connect(root / "runs.sqlite3") as connection:
        metadata = connection.execute(
            "SELECT metadata FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()[0]
    assert json.loads(metadata)["owner_scope"] == identity
    response = client.get(f"{RUNS}/{run_id}/result")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    expected = json.loads(
        json.dumps(asdict(application.get_result(run_id, identity)), default=endpoint.json_date)
    )
    assert data == expected
    assert response.json()["request"] == data["request"] == state["request"]
    assert response.json()["run_id"] == run_id
    assert data["summary"]["total_pnl"] == pnl
    assert data["initial_notional"]["value"] == 1200000
    assert data["rolls"][0]["new_contract_code"] == target
    assert data["daily"][2]["pnl_contract_code"] == "IM2503.CFX"
    assert data["daily"][-1]["position_contract_code"] is None
    assert [row["trade_date"] for row in data["daily"]] == [day.isoformat() for day in DAYS]
    assert data["summary"]["gross_return"] == data["daily"][-1]["cumulative_return"]
    assert data["summary"]["gross_return"] < 0.02
    assert data["summary"]["execution_count"] == len(data["trades"]) == 4
    assert data["summary"]["roll_count"] == len(data["rolls"]) == 1
    for name, field in [("returns", "cumulative_return"), ("drawdown", "drawdown")]:
        view = data["views"][name]
        assert view["version"] == 2
        assert view["layers"][0]["layer"]["y"]["unit"] == "decimal_ratio"
        assert [mark["y"] for mark in view["layers"][0]["layer"]["data"]] == [
            row[field] for row in data["daily"]
        ]
    assert data["evidence"]["input_fingerprint"] == expected["evidence"]["input_fingerprint"]
    assert "set-cookie" in response.headers and response.headers["cache-control"] == "no-store"
    assert "etag" not in response.headers
    before = [list(service.calls) for service in services]
    application._service.run = Mock(side_effect=AssertionError("Read executed backtest"))
    assert client.get(f"{RUNS}/{run_id}/result").json()["data"] == data
    assert [service.calls for service in services] == before
    assert "owner_scope" not in response.text and str(root) not in response.text


@pytest.mark.parametrize("path", [BASE + "/preflight", RUNS])
@pytest.mark.parametrize(
    "changes",
    [
        {"product_code": "im"},
        {"product_code": "XX"},
        {"product_code": 1},
        {"strategy_profile": "custom"},
        {"strategy_profile": None},
        {"start_date": "20250217"},
        {"start_date": "2025-02-30"},
        {"start_date": "2025-02-17T00:00:00"},
        {"end_date": "2099-01-01"},
        {"start_date": "2020-01-01"},
        {"start_date": "2025-04-01"},
        {"start_date": False},
        {"end_date": ["2025-03-25"]},
        {"owner_scope": "foreign"},
        {"case": "override"},
        {"benchmark": "override"},
        {"multiplier": 200},
        {"trading_fee": 1},
    ],
)
def test_invalid_input_before_runtime_or_io(product, monkeypatch, path, changes):
    app, application, client, root, services = product
    obtain = Mock(side_effect=AssertionError("Invalid input obtained application"))
    monkeypatch.setattr(endpoint, "application", obtain)
    assert_error(client.post(path, json={**BODY, **changes}), 400, "invalid_request")
    assert not obtain.called and run_count(root) == 0
    assert not any(service.calls for service in services)


@pytest.mark.parametrize("path", [BASE + "/preflight", RUNS])
@pytest.mark.parametrize(
    "content,headers,kind",
    [
        (b"{}", {}, "invalid_request"),
        (b"[]", {}, "invalid_request"),
        (b'{"product_code":"IM","product_code":"IF"}', {}, "invalid_request"),
        (b"{", {}, "invalid_request"),
        (b"\xff", {}, "invalid_request"),
        (b"[" * 1500 + b"]" * 1500, {}, "invalid_request"),
        (b"{}", {"Content-Type": "text/plain"}, "invalid_request"),
        (b"{}", {"Content-Encoding": "gzip"}, "invalid_request"),
        (b"{}", {"Content-Encoding": "br"}, "invalid_request"),
        (b" " * 4097, {}, "request_too_large"),
    ],
)
def test_malformed_body(product, path, content, headers, kind):
    client = product[2]
    assert_error(
        client.post(path, content=content, headers={"Content-Type": "application/json", **headers}),
        400,
        kind,
    )
    assert run_count(product[3]) == 0


@pytest.mark.parametrize("field", list(BODY))
def test_every_field_required(product, field):
    body = {key: value for key, value in BODY.items() if key != field}
    for path in (BASE + "/preflight", RUNS):
        assert_error(product[2].post(path, json=body), 400, "invalid_request")


@pytest.mark.parametrize("product_code", ["IM", "IC", "IF", "IH"])
@pytest.mark.parametrize("profile", ["expiry_to_M1_v1", "expiry_to_Q1_v1"])
def test_canonical_enums_preflight(product, product_code, profile):
    response = product[2].post(
        BASE + "/preflight",
        json={
            **BODY,
            "product_code": product_code,
            "strategy_profile": profile,
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["request"]["product_code"] == product_code
    assert response.json()["request"]["strategy_profile"] == profile
    assert run_count(product[3]) == 0


@pytest.mark.parametrize("method,path", PATHS)
def test_query_and_auth_order(product, method, path, monkeypatch):
    app, application, client, root, services = product
    parse = Mock(side_effect=AssertionError("Gate bypass"))
    monkeypatch.setattr(endpoint, "parse_request", parse)
    anonymous = TestClient(app, base_url=ORIGIN)
    assert_error(anonymous.request(method, path, content=b"bad"), 401, "authentication_required")
    assert_error(
        client.request(method, path + "?forbidden=1", content=b"bad"), 400, "invalid_request"
    )
    if method == "POST":
        assert_error(
            client.post(path, content=b"bad", headers={"Origin": "https://foreign.test"}),
            403,
            "origin_forbidden",
        )
    assert not parse.called and not any(service.calls for service in services)


@pytest.mark.parametrize("cookie", ["invalid", "expired", "disabled"])
def test_invalid_session_all_routes(product, cookie, monkeypatch):
    app, application, client, root, services = product
    if cookie == "invalid":
        token = "invalid-cookie"
    else:
        identity = client.get("/auth/me").json()["id"]
        if cookie == "expired":
            with monkeypatch.context() as clock:
                clock.setattr(_session.time, "time", lambda: 1_000_000_000)
                token, _ = AuthConfig.from_environment().issue(identity)
        else:
            token = client.cookies[COOKIE]
            create_service().disable(identity)
    client.cookies.clear()
    client.cookies.set(COOKIE, token)
    for method, path in PATHS:
        assert_error(client.request(method, path, content=b"bad"), 401, "authentication_required")
    assert run_count(root) == 0


def test_stream_limit_does_not_trust_content_length(product):
    app, application, client, root, services = product

    async def stream():
        for _ in range(5):
            yield b" " * 1024

    async def exercise():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=ORIGIN, cookies=client.cookies
        ) as caller:
            for path in (BASE + "/preflight", RUNS):
                result = await caller.post(
                    path,
                    content=stream(),
                    headers={
                        "Origin": ORIGIN,
                        "Content-Type": "application/json",
                        "Content-Length": "1",
                    },
                )
                assert_error(result, 400, "request_too_large")

    asyncio.run(exercise())
    assert run_count(root) == 0 and not any(service.calls for service in services)


def test_exact_body_limit_charset_and_identity_encoding(product):
    raw = json.dumps(BODY).encode()
    response = product[2].post(
        BASE + "/preflight",
        content=raw + b" " * (4096 - len(raw)),
        headers={"Content-Type": "application/json; charset=utf-8", "Content-Encoding": "identity"},
    )
    assert response.status_code == 200, response.text


def test_preflight_readonly_and_store_unavailable(product, monkeypatch):
    app, application, client, root, services = product
    application._unavailable = "unavailable"
    application.submit = Mock(side_effect=AssertionError("Preflight submitted"))
    application._service.run = Mock(side_effect=AssertionError("Preflight computed"))
    for service in services:
        service.ensure = Mock(side_effect=AssertionError("Preflight ensured"))
    response = client.post(BASE + "/preflight", json=BODY)
    assert response.status_code == 200, response.text
    assert response.json()["ready"]
    assert set(response.json()) == {"request", "ready", "calendar_cffex", "futures", "index"}
    assert run_count(root) == 0
    assert client.get("/research/capabilities").status_code == 200
    assert_error(client.get(RUNS + "/" + "a" * 32), 503, "unavailable")


def test_incomplete_preflight_does_not_block_submission(product):
    app, application, client, root, services = product
    calendar = services[0]
    original = calendar.exports[0]
    calendar.exports.insert(
        0,
        replace(
            original,
            coverage=replace(
                original.coverage,
                successful_units=0,
                missing_units=original.coverage.requested_units,
                complete=False,
            ),
            records=(),
        ),
    )
    result = client.post(BASE + "/preflight", json=BODY)
    assert result.status_code == 200, result.text
    data = result.json()
    assert not data["ready"] and data["calendar_cffex"]["state"] == "incomplete"
    assert data["futures"]["state"] == data["index"]["state"] == "unknown"
    complete(client)


class ControlledService:
    def __init__(self, error=None):
        self.delegate = fake_services()[0]
        self.entered = threading.Event()
        self.release = threading.Event()
        self.calls = 0
        self.error = error

    def run(self, req):
        self.calls += 1
        self.entered.set()
        assert self.release.wait(5)
        if self.error:
            raise self.error
        return self.delegate.run(req)

    def preflight(self, req):
        return self.delegate.preflight(req)


def test_running_busy_and_failed_safe_classification(product):
    app, application, client, root, services = product
    service = ControlledService(
        FuturesRollApplicationError(
            "upstream_operation",
            "operation_unavailable",
            stage="ensure",
            dependency="futures",
        )
    )
    application._service = service
    accepted = client.post(RUNS, json=BODY)
    assert accepted.status_code == 202 and accepted.json()["status"] == "PENDING"
    run_id = accepted.json()["run_id"]
    try:
        assert service.entered.wait(2)
        state = client.get(f"{RUNS}/{run_id}").json()
        assert state["status"] == "RUNNING" and not state["result_available"]
        assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "result_not_ready")
        assert_error(client.post(RUNS, json=BODY), 409, "run_busy")
        assert len(list(root.iterdir())) == 1 and service.calls == 1
    finally:
        service.release.set()
        state = terminal(client, run_id)
    assert state["status"] == "FAILED" and not state["result_available"]
    assert state["failure"] == {
        "stage": "ensure",
        "category": "upstream_operation",
        "dependency": "futures",
        "reason": "operation_unavailable",
    }
    assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "result_not_ready")


def test_thread_start_failure_preserves_admission_snapshot(product, monkeypatch):
    app, application, client, root, services = product
    start = online.threading.Thread.start

    def start_worker(thread):
        if thread.name == "w2-backtest-worker":
            raise RuntimeError("secret-token")
        return start(thread)

    with monkeypatch.context() as patch:
        patch.setattr(online.threading.Thread, "start", start_worker)
        response = client.post(RUNS, json=BODY)
    assert response.status_code == 202 and response.json()["status"] == "PENDING"
    run_id = response.json()["run_id"]
    state = terminal(client, run_id)
    assert state["status"] == "FAILED"
    assert state["failure"]["category"] == "internal_failure"
    assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "result_not_ready")


def test_recovered_interrupted_and_pending_transport(product):
    app, application, client, root, services = product
    owner = client.get("/auth/me").json()["id"]
    store = online_sqlite_store.FuturesRollSQLiteRunStore(root)
    accepted = store.create(request(), owner)
    # Inject the public immutable carrier to observe PENDING without worker timing races.
    original = application.get_status
    application.get_status = lambda run_id, scope: accepted
    state = client.get(f"{RUNS}/{accepted.run_id}").json()
    assert state["status"] == "PENDING" and not state["result_available"]
    assert_error(client.get(f"{RUNS}/{accepted.run_id}/result"), 409, "result_not_ready")
    application.get_status = original
    app.state.backtesting_application = create_futures_roll_online_application(
        root=root,
        service=fake_services()[0],
    )
    state = client.get(f"{RUNS}/{accepted.run_id}").json()
    assert state["status"] == "INTERRUPTED" and not state["result_available"]
    assert state["failure"] == {
        "stage": "execution",
        "category": "interrupted",
        "dependency": None,
        "reason": "interrupted",
    }
    assert_error(client.get(f"{RUNS}/{accepted.run_id}/result"), 409, "result_not_ready")


def foreign_client(app):
    service = create_service()
    service.register("foreign", PASSWORD)
    pending = next(user for user in service.list_pending() if user.username == "foreign")
    service.approve(pending.id)
    client = TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN})
    response = client.post("/auth/login", json={"username": "foreign", "password": PASSWORD})
    assert response.status_code == 200
    return client


def test_foreign_unknown_malformed_and_busy_privacy(product):
    app, application, client, root, services = product
    run_id = complete(client)
    foreign = foreign_client(app)
    assert endpoint._RESULT_DELIVERY_PERMIT.acquire(blocking=False)
    try:
        for suffix in ("", "/result"):
            hidden = foreign.get(f"{RUNS}/{run_id}{suffix}")
            missing = foreign.get(f"{RUNS}/{'b' * 32}{suffix}")
            malformed = foreign.get(f"{RUNS}/bad{suffix}")
            for response in (hidden, missing, malformed):
                assert_error(response, 404, "run_not_found")
            assert hidden.content == missing.content == malformed.content
    finally:
        endpoint._RESULT_DELIVERY_PERMIT.release()


@pytest.mark.parametrize("permit", ["http", "store"])
def test_full_reader_contention_status_independent(product, permit, monkeypatch):
    app, application, client, root, services = product
    run_id = complete(client)
    guard = endpoint._RESULT_DELIVERY_PERMIT if permit == "http" else online._READ_PERMIT
    assert guard.acquire(blocking=False)
    try:
        assert client.get(f"{RUNS}/{run_id}").json()["result_available"]
        assert_error(client.get(f"{RUNS}/{run_id}/result"), 503, "read_busy")
    finally:
        guard.release()
    assert client.get(f"{RUNS}/{run_id}/result").status_code == 200
    monkeypatch.setattr(online, "decode_result", Mock(side_effect=AssertionError("Status decoded")))
    assert client.get(f"{RUNS}/{run_id}").json()["result_available"]


def test_delivery_permit_covers_serialization_and_releases_after_failure(product, monkeypatch):
    app, application, client, root, services = product
    run_id = complete(client)
    entered, release = threading.Event(), threading.Event()
    original = endpoint.serialize

    def blocked(model, value, limit, status=200):
        if model is endpoint.FuturesRollResultResponse:
            entered.set()
            assert release.wait(5)
        return original(model, value, limit, status)

    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "serialize", blocked)
        with ThreadPoolExecutor() as pool:
            first = pool.submit(client.get, f"{RUNS}/{run_id}/result")
            try:
                assert entered.wait(2)
                assert_error(client.get(f"{RUNS}/{run_id}/result"), 503, "read_busy")
                assert client.get(f"{RUNS}/{run_id}").status_code == 200
            finally:
                release.set()
            assert first.result().status_code == 200
    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "serialize", Mock(side_effect=RuntimeError("secret-token")))
        assert_error(client.get(f"{RUNS}/{run_id}/result"), 500, "internal_error")
    assert client.get(f"{RUNS}/{run_id}/result").status_code == 200


def test_corrupt_result_and_metadata(product):
    app, application, client, root, services = product
    run_id = complete(client)
    with sqlite3.connect(root / "runs.sqlite3") as connection:
        size = connection.execute(
            "SELECT result_length FROM runs WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        connection.execute("UPDATE results SET payload=? WHERE run_id=?", (b"x" * size, run_id))
    # Presence/size is sufficient for status; full digest validation belongs to result read.
    assert client.get(f"{RUNS}/{run_id}").json()["result_available"]
    assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "corrupt")
    with sqlite3.connect(root / "runs.sqlite3") as connection:
        connection.execute("UPDATE runs SET state=? WHERE run_id=?", (b"corrupt", run_id))
    assert_error(client.get(f"{RUNS}/{run_id}"), 409, "corrupt")
    assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "corrupt")


def test_delivery_bounds_and_association(product, monkeypatch):
    app, application, client, root, services = product
    run_id = complete(client)
    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "MAX_RESULT_BYTES", 100)
        assert_error(client.get(f"{RUNS}/{run_id}/result"), 413, "response_too_large")
    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "MAX_STATUS_BYTES", 100)
        assert_error(client.get(f"{RUNS}/{run_id}"), 500, "internal_error")
    original = application.get_result
    with monkeypatch.context() as patch:
        patch.setattr(
            application,
            "get_result",
            lambda run_id, owner: replace(
                original(run_id, owner),
                request=request("expiry_to_Q1_v1"),
            ),
        )
        assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "corrupt")
    assert client.get(f"{RUNS}/{run_id}/result").status_code == 200


def test_real_result_delivery_size_bound(product):
    app, application, client, root, services = product
    run_id = complete(client)
    # Actual BLOB size is checked before payload allocation.
    with sqlite3.connect(root / "runs.sqlite3") as connection:
        connection.execute("UPDATE results SET payload=zeroblob(?)", (32 * 1024 * 1024 + 1,))
    assert_error(client.get(f"{RUNS}/{run_id}/result"), 409, "corrupt")


@pytest.mark.parametrize(
    "kind,status",
    [
        ("unavailable", 503),
        ("corrupt", 409),
        ("result_too_large", 413),
        ("read_busy", 503),
        ("unexpected_category", 500),
    ],
)
def test_safe_operation_error_mapping(product, monkeypatch, kind, status):
    app, application, client, root, services = product
    monkeypatch.setattr(application, "get_status", Mock(side_effect=FuturesRollOnlineError(kind)))
    assert_error(
        client.get(f"{RUNS}/{'c' * 32}"),
        status,
        kind if kind in endpoint.ERRORS else "internal_error",
    )


@pytest.mark.parametrize("state", ["pending", "rejected"])
def test_nonactive_signed_identity_cannot_reach_product(product, state):
    app, application, client, root, services = product
    service = create_service()
    service.register("notactive", PASSWORD)
    user = next(user for user in service.list_pending() if user.username == "notactive")
    if state == "rejected":
        service.reject(user.id)
    token, _ = AuthConfig.from_environment().issue(user.id)
    client.cookies.clear()
    client.cookies.set(COOKIE, token)
    for method, path in PATHS:
        assert_error(client.request(method, path, content=b"bad"), 401, "authentication_required")
    assert not any(service.calls for service in services)


def test_unavailable_readiness_does_not_expose_provider_details(product):
    from data_lake import OperationError

    app, application, client, root, services = product
    services[0].error = OperationError("secret-token /private/provider")
    response = client.post(BASE + "/preflight", json=BODY)
    assert response.status_code == 200, response.text
    data = response.json()
    assert not data["ready"]
    assert data["calendar_cffex"]["state"] == "unavailable"
    assert data["calendar_cffex"]["reason"] == "public_export_unavailable"
    assert data["calendar_cffex"]["coverage"] is None
    assert data["futures"]["state"] == data["index"]["state"] == "unknown"
    assert "secret-token" not in response.text and "/private" not in response.text
    assert not services[1].calls and not services[2].calls


def test_full_envelope_real_32_mib_bound_and_exact_boundary(product, monkeypatch):
    app, application, client, root, services = product
    run_id = complete(client)
    url = f"{RUNS}/{run_id}/result"
    original = application.get_result
    length = len(client.get(url).content)
    with monkeypatch.context() as patch:
        patch.setattr(endpoint, "MAX_RESULT_BYTES", length)
        assert client.get(url).status_code == 200
        patch.setattr(endpoint, "MAX_RESULT_BYTES", length - 1)
        assert_error(client.get(url), 413, "response_too_large")
    with monkeypatch.context() as patch:

        def oversized(run_id, owner):
            result = original(run_id, owner)
            return replace(
                result,
                evidence=replace(
                    result.evidence,
                    limitations=("x" * (32 * 1024 * 1024),),
                ),
            )

        patch.setattr(application, "get_result", oversized)
        assert_error(client.get(url), 413, "response_too_large")
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("path", [BASE + "/preflight", RUNS])
def test_duplicate_keys_in_otherwise_valid_body_and_ambiguous_headers(product, path):
    client = product[2]
    raw = json.dumps(BODY)
    duplicate = raw[:-1] + ',"product_code":"IM"}'
    assert_error(
        client.post(path, content=duplicate, headers={"Content-Type": "application/json"}),
        400,
        "invalid_request",
    )
    assert_error(client.post(path, content=raw), 400, "invalid_request")
    for headers in [
        [("Content-Type", "application/json"), ("Content-Type", "application/json")],
        [
            ("Content-Type", "application/json"),
            ("Content-Encoding", "identity"),
            ("Content-Encoding", "gzip"),
        ],
    ]:
        assert_error(client.post(path, content=raw, headers=headers), 400, "invalid_request")
    assert run_count(product[3]) == 0
