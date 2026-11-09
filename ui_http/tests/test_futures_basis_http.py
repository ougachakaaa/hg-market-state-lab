"""R01-A transport acceptance using real Cookie auth and synthetic public services."""

import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from http_support.auth import ORIGIN, PASSWORD, authenticated_client
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisOnlineApplication,
    OnlineError,
    OnlineServices,
    compose_report,
    online,
)
from market_statistics import CalculationFailure
from ui_http.app import create_app
from ui_http.auth import create_service
from ui_http.products.futures_basis_research import endpoint, runtime
from ui_http.products.futures_basis_research.schemas import (
    FuturesBasisReportResponse,
    FuturesBasisRun,
    FuturesBasisRunAccepted,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "market_research" / "tests"))
from futures_basis_observation_fixtures import Services  # noqa: E402

PATH = "/research/futures-basis/runs"
BODY = {"product_code": "IM", "start_date": "2024-10-18", "end_date": "2024-10-21"}


@pytest.fixture
def product(tmp_path):
    services = Services()
    app = create_app()
    research = FuturesBasisOnlineApplication(
        root=tmp_path / "runs", services=OnlineServices(services, services, services)
    )
    app.state.futures_basis_application = research
    return app, research, services


def terminal(client, run_id):
    for _ in range(200):
        response = client.get(f"{PATH}/{run_id}")
        assert response.status_code == 200, response.text
        if response.json()["status"] in ("COMPLETED", "FAILED", "INTERRUPTED"):
            return response.json()
        time.sleep(0.01)
    pytest.fail("Synthetic run did not settle")


def assert_error(response, status, kind):
    assert response.status_code == status, response.text
    assert response.json()["error"]["kind"] == kind
    assert response.headers["cache-control"] == "no-store"
    assert not any(word in response.text for word in ("owner_scope", "/private", "Traceback"))


def test_anonymous_and_origin_gate_precede_product(product):
    app, research, services = product
    anonymous = TestClient(app, base_url=ORIGIN)
    research.submit = Mock(side_effect=AssertionError("Gate bypass"))
    for method, path in [("POST", PATH), ("GET", PATH + "/bad"), ("GET", PATH + "/bad/report")]:
        assert_error(
            anonymous.request(method, path, content=b"bad"), 401, "authentication_required"
        )
    client = authenticated_client(app)
    assert_error(
        client.post(PATH, content=b"bad", headers={"Origin": "https://foreign.test"}),
        403,
        "origin_forbidden",
    )
    assert research.submit.call_count == 0 and not services.calls


def test_completed_payload_dto_and_repeated_lightweight_status(product, monkeypatch):
    app, research, services = product
    client = authenticated_client(app)
    response = client.post(PATH, json=BODY)
    assert response.status_code == 202, response.text
    accepted = FuturesBasisRunAccepted.model_validate_json(response.content)
    assert accepted.status == "PENDING"
    run_id = accepted.run_id
    state = terminal(client, run_id)
    FuturesBasisRun.model_validate_json(json.dumps(state))
    assert state["status"] == "COMPLETED" and state["result_status"] == "complete"
    response = client.get(f"{PATH}/{run_id}/report")
    assert response.status_code == 200, response.text
    payload = response.json()
    FuturesBasisReportResponse.model_validate_json(response.content)
    assert payload["data"]["profile"] == "futures_basis_report_evidence_v1"
    metadata = json.loads((research.root / run_id / "request.json").read_bytes())
    identity = client.get("/auth/me").json()
    assert metadata["owner_scope"] == identity["id"]
    assert payload["data"] == research.get_report(run_id, identity["id"])
    assert {
        "request",
        "coverage",
        "fingerprint",
        "views",
        "distributions",
        "comparisons",
        "persistence",
        "limitations",
    } <= payload["data"].keys()
    assert response.headers["cache-control"] == "no-store"
    before = list(services.calls)
    research.observe = research.compose = Mock(side_effect=AssertionError("Read executed Research"))
    research._report = Mock(side_effect=AssertionError("Status parsed full report"))
    decode = online._decode

    def metadata_only(raw):
        assert len(raw) <= 8192
        return decode(raw)

    monkeypatch.setattr(online, "_decode", metadata_only)
    assert online._READ_PERMIT.acquire(blocking=False)
    try:
        for _ in range(4):
            assert client.get(f"{PATH}/{run_id}").json() == state
        assert_error(client.get(f"{PATH}/{run_id}/report"), 503, "read_busy")
    finally:
        online._READ_PERMIT.release()
    assert services.calls == before and research._report.call_count == 0


@pytest.mark.parametrize(
    "body",
    [
        {},
        [],
        {**BODY, "owner_scope": "foreign"},
        {**BODY, "analysis_profile": "custom"},
        {**BODY, "product_code": 1},
        {**BODY, "product_code": "im"},
        {**BODY, "start_date": "20241018"},
        {**BODY, "end_date": "2024-10-21T00:00:00"},
        {**BODY, "start_date": "2024-10-22"},
        {**BODY, "end_date": "2099-01-01"},
        {**BODY, "start_date": "2020-01-01"},
        {**BODY, "start_date": None},
    ],
)
def test_invalid_request_creates_no_run(product, body):
    app, research, services = product
    client = authenticated_client(app)
    assert_error(client.post(PATH, json=body), 400, "invalid_request")
    assert list(research.root.iterdir()) == [] and not services.calls


@pytest.mark.parametrize(
    "content,content_type,kind",
    [
        (b'{"product_code":"IM","product_code":"IF"}', "application/json", "invalid_request"),
        (b"{", "application/json", "invalid_request"),
        (b"[" * 1500 + b"]" * 1500, "application/json", "invalid_request"),
        (b"\xff", "application/json", "invalid_request"),
        (b"{}", "text/plain", "invalid_request"),
        (b" " * 4097, "application/json", "request_too_large"),
    ],
)
def test_strict_raw_body(product, content, content_type, kind):
    app, research, services = product
    client = authenticated_client(app)
    assert_error(
        client.post(PATH, content=content, headers={"Content-Type": content_type}), 400, kind
    )
    assert not list(research.root.iterdir()) and not services.calls


def test_request_stream_bound_and_exact_limit(product):
    app, research, _ = product
    client = authenticated_client(app)
    raw = json.dumps(BODY).encode()
    assert_error(
        client.post(
            PATH,
            content=iter([b" " * 3000, b" " * 1097]),
            headers={"Content-Type": "application/json"},
        ),
        400,
        "request_too_large",
    )
    response = client.post(
        PATH,
        content=raw + b" " * (4096 - len(raw)),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    assert response.status_code == 202, response.text
    terminal(client, response.json()["run_id"])


def test_busy_returns_without_waiting_for_worker(product):
    app, research, _ = product
    entered, release = threading.Event(), threading.Event()

    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        raise RuntimeError("/private provider token")

    research.observe = blocked
    client = authenticated_client(app)
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(client.post, PATH, json=BODY) for _ in range(3)]
            responses = [future.result(timeout=5) for future in futures]
        assert entered.wait(1)
        assert sorted(response.status_code for response in responses) == [202, 409, 409]
        run_id = next(
            response.json()["run_id"] for response in responses if response.status_code == 202
        )
        assert len(list(research.root.iterdir())) == 1
        assert_error(client.get(f"{PATH}/{run_id}/report"), 409, "result_not_ready")
    finally:
        release.set()
    assert terminal(client, run_id)["status"] == "FAILED"
    assert_error(client.get(f"{PATH}/{run_id}/report"), 409, "result_unavailable")


def test_foreign_unknown_malformed_are_indistinguishable(product):
    app, research, _ = product
    client = authenticated_client(app)
    run_id = client.post(PATH, json=BODY).json()["run_id"]
    terminal(client, run_id)
    service = create_service()
    service.register("second-user", PASSWORD)
    for user in service.list_pending():
        service.approve(user.id)
    foreign = TestClient(app, base_url=ORIGIN, headers={"Origin": ORIGIN})
    assert (
        foreign.post(
            "/auth/login", json={"username": "second-user", "password": PASSWORD}
        ).status_code
        == 200
    )
    for suffix in ("", "/report"):
        responses = [
            foreign.get(f"{PATH}/{value}{suffix}") for value in (run_id, "0" * 32, "BAD", "bad-id")
        ]
        for response in responses:
            assert_error(response, 404, "run_not_found")
        assert all(response.json() == responses[0].json() for response in responses)


@pytest.mark.parametrize("partial", [False, True])
def test_partial_science_and_interrupted_state(product, partial):
    app, research, _ = product
    if partial:

        def partial_compose(source, request):
            with patch(
                "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
                side_effect=CalculationFailure("mean", "synthetic failure"),
            ):
                return compose_report(source, request)

        research.compose = partial_compose
    client = authenticated_client(app)
    run_id = client.post(PATH, json=BODY).json()["run_id"]
    state = terminal(client, run_id)
    assert state["status"] == "COMPLETED"
    assert state["result_status"] == ("partial" if partial else "complete")
    response = client.get(f"{PATH}/{run_id}/report")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == state["result_status"]
    path = research.root / run_id / "state.json"
    state = json.loads(path.read_bytes())
    state.update(status="RUNNING", finished_at=None, result_status=None, result_digest=None)
    path.write_text(json.dumps(state))
    app.state.futures_basis_application = FuturesBasisOnlineApplication(root=research.root)
    assert terminal(client, run_id)["status"] == "INTERRUPTED"
    assert_error(client.get(f"{PATH}/{run_id}/report"), 409, "result_unavailable")


def test_corrupt_oversized_unknown_and_envelope_limit(product, monkeypatch):
    app, research, _ = product
    client = authenticated_client(app)
    run_id = client.post(PATH, json=BODY).json()["run_id"]
    terminal(client, run_id)
    report_path = research.root / run_id / "report.json"
    state_path = research.root / run_id / "state.json"
    payload = report_path.read_bytes()
    with monkeypatch.context() as context:
        context.setattr(endpoint, "MAX_REPORT_BYTES", len(payload))
        assert_error(client.get(f"{PATH}/{run_id}/report"), 413, "response_too_large")
    with monkeypatch.context() as context:
        context.setattr(online, "MAX_REPORT_BYTES", len(payload) - 1)
        assert_error(client.get(f"{PATH}/{run_id}/report"), 413, "response_too_large")
    report_path.write_bytes(payload + b" ")
    assert_error(client.get(f"{PATH}/{run_id}/report"), 409, "corrupt")
    reader = json.loads(payload)
    reader["profile"] = "unknown_v2"
    changed = json.dumps(reader).encode()
    report_path.write_bytes(changed)
    state = json.loads(state_path.read_bytes())
    state["result_digest"] = hashlib.sha256(changed).hexdigest()
    state_path.write_text(json.dumps(state))
    assert_error(client.get(f"{PATH}/{run_id}/report"), 409, "unsupported_version")
    with report_path.open("wb") as stream:
        stream.truncate(32 * 1024 * 1024 + 1)
    assert_error(client.get(f"{PATH}/{run_id}/report"), 413, "response_too_large")
    report_path.unlink()
    assert_error(client.get(f"{PATH}/{run_id}"), 409, "corrupt")
    state["version"] = 2
    state_path.write_text(json.dumps(state))
    for suffix in ("", "/report"):
        assert_error(client.get(f"{PATH}/{run_id}{suffix}"), 409, "unsupported_version")


@pytest.mark.parametrize("kind", ["unavailable", "internal_error"])
def test_safe_operational_errors(product, monkeypatch, kind):
    app, research, _ = product
    client = authenticated_client(app)
    exc = OnlineError("unavailable") if kind == "unavailable" else RuntimeError("/private/token")
    for method in ("submit", "get_run", "get_report"):
        monkeypatch.setattr(research, method, Mock(side_effect=exc))
    assert_error(client.post(PATH, json=BODY), 503 if kind == "unavailable" else 500, kind)
    for suffix in ("", "/report"):
        assert_error(
            client.get(f"{PATH}/{'0' * 32}{suffix}"), 503 if kind == "unavailable" else 500, kind
        )


def test_singleton_startup_offline_export_and_platform_isolation(tmp_path, monkeypatch):
    factory = Mock(side_effect=OnlineError("unavailable"))
    monkeypatch.setattr(runtime, "FuturesBasisOnlineApplication", factory)
    apps = [create_app(), create_app()]
    for app in apps:
        app.openapi()
    assert factory.call_count == 0
    clients = [authenticated_client(app) for app in apps]
    with clients[0]:
        assert factory.call_count == 1
        assert_error(clients[0].post(PATH, json=BODY), 503, "unavailable")
    assert_error(clients[1].post(PATH, json=BODY), 503, "unavailable")
    assert factory.call_count == 1
    assert clients[1].get("/research/capabilities").status_code == 200
    monkeypatch.setattr(runtime, "FuturesBasisOnlineApplication", FuturesBasisOnlineApplication)
    monkeypatch.setattr(runtime, "_runtime", runtime.OnlineRuntime())
    monkeypatch.setattr(online, "_supports_storage", lambda: False)
    with pytest.raises(OnlineError, match="unavailable"):
        FuturesBasisOnlineApplication(root=tmp_path / "unsupported")
    assert not (tmp_path / "unsupported").exists()
    client = authenticated_client(create_app())
    with client:
        assert_error(client.post(PATH, json=BODY), 503, "unavailable")
        assert client.get("/research/capabilities").status_code == 200
        assert client.get("/openapi.json").status_code == 200


def test_openapi_exact_operations_and_access(product):
    app, _, _ = product
    document = app.openapi()
    expected = [
        (PATH, "post", "submit_futures_basis_research_run", {"202", "400", "409", "503", "500"}),
        (
            PATH + "/{run_id}",
            "get",
            "get_futures_basis_research_run",
            {"200", "400", "404", "409", "503", "500"},
        ),
        (
            PATH + "/{run_id}/report",
            "get",
            "get_futures_basis_research_report",
            {"200", "400", "404", "409", "413", "503", "500"},
        ),
    ]
    assert {path for path in document["paths"] if path.startswith(PATH)} == {v[0] for v in expected}
    for path, method, operation_id, statuses in expected:
        operation = document["paths"][path][method]
        assert operation["operationId"] == operation_id
        assert set(operation["responses"]) == statuses | {"401", "403"}
        assert operation["security"] == [{"CookieSession": []}]
        assert (
            operation["responses"]["202" if method == "post" else "200"]["headers"][
                "Cache-Control"
            ]["schema"]["const"]
            == "no-store"
        )
    assert document["components"]["securitySchemes"]["CookieSession"]["in"] == "cookie"
    assert (
        document["components"]["schemas"]["FuturesBasisRunRequest"]["additionalProperties"] is False
    )


def test_successful_runtime_is_shared_across_concurrent_compositions(tmp_path, monkeypatch):
    services = Services()
    factory = Mock(
        side_effect=lambda: FuturesBasisOnlineApplication(
            root=tmp_path / "shared", services=OnlineServices(services, services, services)
        )
    )
    monkeypatch.setattr(runtime, "FuturesBasisOnlineApplication", factory)
    apps = [create_app() for _ in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        instances = list(pool.map(runtime.application, apps))
    assert factory.call_count == 1
    assert all(instance is instances[0] for instance in instances)
    clients = [authenticated_client(app) for app in apps[:2]]
    response = clients[0].post(PATH, json=BODY)
    assert response.status_code == 202, response.text
    run_id = response.json()["run_id"]
    assert terminal(clients[1], run_id)["status"] == "COMPLETED"
    with clients[0]:
        assert factory.call_count == 1
        assert clients[0].get(f"{PATH}/{run_id}/report").status_code == 200


def test_query_rejection_and_status_response_bound(product, monkeypatch):
    app, research, services = product
    client = authenticated_client(app)
    assert_error(client.post(PATH + "?owner=x", json=BODY), 400, "invalid_request")
    assert not list(research.root.iterdir()) and not services.calls
    for suffix in ("", "/report"):
        assert_error(client.get(f"{PATH}/bad{suffix}?owner=x"), 400, "invalid_request")
    run_id = client.post(PATH, json=BODY).json()["run_id"]
    terminal(client, run_id)
    monkeypatch.setattr(endpoint, "MAX_RUN_BYTES", 100)
    assert_error(client.get(f"{PATH}/{run_id}"), 500, "internal_error")


def test_http_report_contention_preserves_status_reads(product, monkeypatch):
    app, research, _ = product
    client = authenticated_client(app)
    run_id = client.post(PATH, json=BODY).json()["run_id"]
    terminal(client, run_id)
    entered, release = threading.Event(), threading.Event()
    original = research._report

    def blocked(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    monkeypatch.setattr(research, "_report", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(client.get, f"{PATH}/{run_id}/report")
        try:
            assert entered.wait(2)
            assert_error(client.get(f"{PATH}/{run_id}/report"), 503, "read_busy")
            assert client.get(f"{PATH}/{run_id}").status_code == 200
        finally:
            release.set()
        assert future.result().status_code == 200


def test_report_capacity_includes_serialization_and_releases_after_error(product, monkeypatch):
    app, _, _ = product
    client = authenticated_client(app)
    run_id = client.post(PATH, json=BODY).json()["run_id"]
    terminal(client, run_id)
    entered, release = threading.Event(), threading.Event()
    original = endpoint.serialize

    def blocked(model, *args, **kwargs):
        if model is FuturesBasisReportResponse:
            entered.set()
            assert release.wait(5)
            raise RuntimeError("/private serialization failure")
        return original(model, *args, **kwargs)

    monkeypatch.setattr(endpoint, "serialize", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(client.get, f"{PATH}/{run_id}/report")
        try:
            assert entered.wait(2)
            assert_error(client.get(f"{PATH}/{run_id}/report"), 503, "read_busy")
            assert client.get(f"{PATH}/{run_id}").status_code == 200
        finally:
            release.set()
        assert_error(future.result(), 500, "internal_error")
    monkeypatch.setattr(endpoint, "serialize", original)
    assert client.get(f"{PATH}/{run_id}/report").status_code == 200
