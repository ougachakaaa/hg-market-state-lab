"""Offline schema and once-only process composition acceptance for W2."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

from http_support.auth import authenticated_client
from market_backtesting.cases.futures_roll_long import (
    create_futures_roll_online_application,
)
from ui_http.app import create_app
from ui_http.auth import _http
from ui_http.products.backtesting import runtime

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "market_backtesting/tests"))
from public_input_fixtures import fake_services  # noqa: E402

PREFIX = "/backtesting/futures-roll"
OPERATIONS = {
    ("post", PREFIX + "/preflight"): ("preflight_futures_roll_backtest", "200"),
    ("post", PREFIX + "/runs"): ("submit_futures_roll_backtest", "202"),
    ("get", PREFIX + "/runs/{run_id}"): ("get_futures_roll_backtest_run", "200"),
    ("get", PREFIX + "/runs/{run_id}/result"): ("get_futures_roll_backtest_result", "200"),
}


def test_offline_openapi_concrete_dtos_auth_and_no_store(monkeypatch):
    factory = Mock(side_effect=AssertionError("Offline initialized Store"))
    monkeypatch.setattr(runtime, "create_futures_roll_online_application", factory)
    monkeypatch.setattr(_http, "AuthRuntime", Mock(side_effect=AssertionError("Offline Auth")))
    schema = create_app().openapi()
    assert not factory.called and not runtime._runtime.initialized
    for (method, path), (identity, success) in OPERATIONS.items():
        operation = schema["paths"][path][method]
        assert operation["operationId"] == identity
        assert operation["security"] == [{"CookieSession": []}]
        statuses = operation["responses"]
        expected = {success, "400", "401", "403", "500"}
        if path.endswith("/preflight"):
            expected |= {"503"}
        elif method == "post":
            expected |= {"409", "503"}
        else:
            expected |= {"404", "409", "413", "503"}
        assert set(statuses) == expected
        assert "422" not in statuses
        for response in statuses.values():
            assert response["headers"]["Cache-Control"]["schema"]["const"] == "no-store"
        if method == "post":
            assert operation["requestBody"]["required"]
            assert set(operation["requestBody"]["content"]) == {"application/json"}
            assert operation["requestBody"]["content"]["application/json"]["schema"] == {
                "$ref": "#/components/schemas/FuturesRollRunRequest",
            }
    components = schema["components"]["schemas"]
    request = components["FuturesRollRunRequest"]
    assert set(request["required"]) == {
        "product_code",
        "start_date",
        "end_date",
        "strategy_profile",
    }
    assert request["additionalProperties"] is False
    assert request["properties"]["product_code"]["enum"] == ["IM", "IC", "IF", "IH"]
    assert request["properties"]["start_date"]["format"] == "date"
    assert set(components["FuturesRollResult"]["required"]) == {
        "profile",
        "case",
        "definition_version",
        "status",
        "request",
        "window",
        "benchmark",
        "initial_notional",
        "daily",
        "trades",
        "rolls",
        "summary",
        "evidence",
        "views",
    }
    assert components["FuturesRollResult"]["properties"]["profile"]["const"] == (
        "futures_roll_long_result_v1"
    )
    assert components["FuturesRollLine"]["properties"]["version"]["const"] == 2
    assert components["FuturesRollLine"]["properties"]["type"]["const"] == "line"
    assert components["FuturesRollNumberCoordinate"]["properties"]["unit"]["const"] == (
        "decimal_ratio"
    )
    # Every product-owned response graph uses concrete closed objects and resolves references.
    visited = set()

    def visit(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert "properties" in value
            ref = value.get("$ref")
            if ref and ref not in visited:
                visited.add(ref)
                visit(components[ref.rsplit("/", 1)[1]])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for name in ("FuturesRollResultResponse", "FuturesRollRun", "FuturesRollPreflight"):
        visit(components[name])
    assert len(visited) >= 25
    assert "owner_scope" not in json.dumps(
        [components[name] for name in components if name.startswith("FuturesRoll")]
    )


def test_runtime_single_factory_across_threads_and_apps(monkeypatch, tmp_path):
    real = create_futures_roll_online_application(root=tmp_path / "runs")
    factory = Mock(return_value=real)
    monkeypatch.setattr(runtime, "create_futures_roll_online_application", factory)
    apps = [create_app() for _ in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(runtime.application, apps)) == [real] * 4
    for app in apps:
        runtime.initialize(app)
        assert runtime.application(app) is real
    assert factory.call_count == 1


def test_runtime_failed_factory_not_retried_or_disabling_siblings(monkeypatch):
    factory = Mock(side_effect=RuntimeError("secret-token"))
    monkeypatch.setattr(runtime, "create_futures_roll_online_application", factory)
    app = create_app()
    client = authenticated_client(app)
    with client:
        for _ in range(2):
            response = client.post(
                PREFIX + "/preflight",
                json={
                    "product_code": "IM",
                    "start_date": "2025-02-17",
                    "end_date": "2025-03-25",
                    "strategy_profile": "expiry_to_M1_v1",
                },
            )
            assert response.status_code == 503
            assert response.json()["error"]["kind"] == "unavailable"
            assert "secret-token" not in response.text
        assert client.get("/research/capabilities").status_code == 200
    assert factory.call_count == 1


def test_real_failed_store_facade_retained_preflight_reads_only(monkeypatch, tmp_path):
    service = fake_services()[0]
    # Use an actual initialization failure rather than replacing the HTTP runtime result.
    (tmp_path / "file").write_text("not a directory")
    real = create_futures_roll_online_application(root=tmp_path / "file" / "runs", service=service)
    factory = Mock(return_value=real)
    monkeypatch.setattr(runtime, "create_futures_roll_online_application", factory)
    app = create_app()
    client = authenticated_client(app)
    response = client.post(
        PREFIX + "/preflight",
        json={
            "product_code": "IM",
            "start_date": "2025-02-17",
            "end_date": "2025-03-25",
            "strategy_profile": "expiry_to_M1_v1",
        },
    )
    assert response.status_code == 200 and response.json()["ready"]
    response = client.post(
        PREFIX + "/runs",
        json={
            "product_code": "IM",
            "start_date": "2025-02-17",
            "end_date": "2025-03-25",
            "strategy_profile": "expiry_to_M1_v1",
        },
    )
    assert response.status_code == 503 and factory.call_count == 1
    assert runtime.application(app) is real
