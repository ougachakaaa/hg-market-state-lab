"""Composed HTTP acceptance: real Auth, synthetic public Research query inputs only."""

import asyncio
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from http_support.auth import ORIGIN, authenticated_client
from market_research.descriptive.cases import futures_calendar_spread as case
from ui_http.app import create_app
from ui_http.products.calendar_spread_relative_value.endpoint import (
    get_historical_query,
)
from ui_http.products.calendar_spread_relative_value.schemas import HistoricalResponse
from ui_http.products.futures_calendar_spread import transport
from ui_http.products.futures_calendar_spread.endpoint import get_daily_execution, get_daily_query
from ui_http.products.futures_calendar_spread.schemas import DailyResponse

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "market_research" / "tests"))
from calendar_spread_fixtures import AFTER, DAY, Services, future  # noqa: E402

DAILY = "/data/futures-calendar-spread"
EXECUTION = DAILY + "/query"
DAILY_BODY = {"product_code": "IM", "trade_date": DAY.isoformat()}
HISTORY = "/research/calendar-spread-relative-value/query"
BODY = {
    "product_code": "IM",
    "history_start": DAY.isoformat(),
    "evaluation_date": AFTER.isoformat(),
}
QUERY = "?product_code=IM&trade_date=" + DAY.isoformat()


def request_path(client, path):
    if path == DAILY:
        return client.get(DAILY + QUERY)
    return client.post(path, json=BODY if path == HISTORY else DAILY_BODY)


def historical(services, **kwargs):
    return case.query_historical_relative_value(
        services.product,
        services.start,
        services.end,
        calendar_service=services,
        futures_service=services,
        **kwargs,
    )


def daily(services):
    return case.query_daily_spreads(
        services.product,
        services.end,
        calendar_service=services,
        futures_service=services,
    )


@pytest.fixture
def product():
    app = create_app()
    dq = Mock(side_effect=lambda code, day: daily(Services(day, day, code)))
    hq = Mock(
        side_effect=lambda code, start, end, **kw: historical(
            Services(start, end, code),
            **kw,
        )
    )
    app.dependency_overrides[get_daily_query] = lambda: dq
    app.dependency_overrides[get_daily_execution] = lambda: dq
    app.dependency_overrides[get_historical_query] = lambda: hq
    return app, authenticated_client(app), dq, hq


def error(response, status, kind, param=None):
    assert response.status_code == status, response.text
    assert response.json()["error"]["kind"] == kind
    assert response.json()["error"]["param"] == param
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" not in response.headers
    assert all(x not in response.text for x in ("/private", "secret", "Traceback", "sqlite"))


def test_daily_six_pairs_metrics_identity_zero_and_cookie(product):
    _, client, query, _ = product
    response = client.get(DAILY + QUERY)
    assert response.status_code == 200, response.text
    result = DailyResponse.model_validate_json(response.content)
    assert response.headers["cache-control"] == "no-store"
    assert "set-cookie" in response.headers
    query.assert_called_once_with("IM", DAY)
    assert len(result.day.observations) == 6
    assert result.accounting.valid_count == 6
    first = result.day.observations[0]
    assert (first.near_slot, first.far_slot) == ("M0", "M1")
    assert first.near.contract_code == "IM2410.CFX"
    assert first.far.contract_code == "IM2411.CFX"
    assert first.near.delist_date == DAY
    assert first.near.close == 110 and first.far.close == 100
    metrics = first.metrics
    assert metrics.signed_spread.value == 10
    assert metrics.signed_spread.unit == "index_points"
    assert metrics.annualized_point_spread.unit == "index_points_per_365_natural_days"
    assert metrics.annualized_spread_ratio.unit == "decimal_ratio"
    assert result.day.observations[2].metrics.signed_spread.value == 0
    assert first.delta_days == 31 and first.near_dte_days == 0
    assert first.expiry_stage == "0_7"
    assert result.request.trade_date == DAY
    assert result.source_context.limitations
    assert not any(
        word in response.text
        for word in (
            "source_evidence",
            "futures_export",
            "source_export_ref",
            "observation_set",
            "resolution",
        )
    )


@pytest.mark.parametrize("mode", ["closed", "empty", "excluded"])
def test_daily_availability_is_200(product, mode):
    _, client, query, _ = product
    day = date(2024, 10, 19) if mode == "closed" else DAY
    services = Services(day, day)
    if mode == "empty":
        services.set_rows(())
    if mode == "excluded":
        services.set_rows(
            replace(row, close=0.0) if row.delivery_month == "202410" else row
            for row in services.futures.records
        )
    result = daily(services)
    query.side_effect = None
    query.return_value = result
    response = client.get(DAILY + "?product_code=IM&trade_date=" + day.isoformat())
    assert response.status_code == 200, response.text
    payload = response.json()
    if mode == "closed":
        assert payload["day"] == {
            "trade_date": day.isoformat(),
            "status": "closed",
            "reason": "non_trading_day",
            "observations": [],
        }
    else:
        assert len(payload["day"]["observations"]) == 6
        row = payload["day"]["observations"][0]
        assert row["metrics"] is None
        assert row["outcome"] == ("excluded" if mode == "excluded" else "not_applicable")
        if mode == "excluded":
            assert row["near"]["close"] == 0
        else:
            assert row["near"] is None


@pytest.mark.parametrize(
    "query,param",
    [
        ("", "product_code"),
        ("?product_code=IM", "trade_date"),
        ("?trade_date=2024-10-18", "product_code"),
        ("?product_code=im&trade_date=2024-10-18", "product_code"),
        ("?product_code=IM&trade_date=20241018", "trade_date"),
        ("?product_code=IM&trade_date=2024-10-18T00:00:00", "trade_date"),
        ("?product_code=IM&trade_date=2024-2-3", "trade_date"),
        ("?product_code=IM&trade_date=2024-02-30", "trade_date"),
        (QUERY + "&bad=1", None),
        (QUERY + "&product_code=IF", "product_code"),
        (QUERY + "&trade_date=2024-10-18", "trade_date"),
    ],
)
def test_daily_closed_query_parsing(product, query, param):
    _, client, dq, _ = product
    error(client.get(DAILY + query), 400, "invalid_request", param)
    dq.assert_not_called()


def test_get_body_and_chunked_request_bounds(product):
    _, client, dq, hq = product
    error(client.request("GET", DAILY + QUERY, content=b"{}"), 400, "invalid_request")
    error(
        client.post(
            HISTORY,
            content=iter([b" " * 8192] * 3),
            headers={"Content-Type": "application/json"},
        ),
        413,
        "request_too_large",
    )
    dq.assert_not_called()
    hq.assert_not_called()


@pytest.mark.parametrize(
    "change,param",
    [
        ({"product_code": 1}, "product_code"),
        ({"product_code": "xx"}, "product_code"),
        ({"history_start": "20241018"}, "history_start"),
        ({"evaluation_date": "2024-10-21T00:00:00Z"}, "evaluation_date"),
        ({"history_start": True}, "history_start"),
        ({"metric": None}, "metric"),
        ({"metric": "x"}, "metric"),
        ({"histogram_edges": None}, "histogram_edges"),
        ({"histogram_edges": [True, 1]}, "histogram_edges"),
        ({"histogram_edges": ["0", 1]}, "histogram_edges"),
        ({"histogram_edges": [0, float("inf")]}, None),
        ({"unknown": 1}, None),
    ],
)
def test_research_strict_wire(product, change, param):
    _, client, _, query = product
    # json.dumps deliberately exercises nonstandard Infinity on the wire.
    response = client.post(
        HISTORY,
        content=json.dumps(BODY | change),
        headers={"Content-Type": "application/json"},
    )
    error(response, 400, "invalid_request", param)
    query.assert_not_called()


@pytest.mark.parametrize(
    "raw,param",
    [
        (b"{", None),
        (b"[]", None),
        (b"null", None),
        (b'{"product_code":"IM","product_code":"IF"}', "product_code"),
        (b'{"extra": {"x":1,"x":2}}', None),
    ],
)
@pytest.mark.parametrize("path", [HISTORY, EXECUTION])
def test_research_duplicate_and_malformed_json(product, raw, param, path):
    _, client, dq, hq = product
    error(
        client.post(path, content=raw, headers={"Content-Type": "application/json"}),
        400,
        "invalid_request",
        param,
    )
    hq.assert_not_called()
    dq.assert_not_called()


@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Type": "text/plain"},
        {"Content-Type": "application/problem+json"},
        {"Content-Type": "application/json; charset=latin1"},
        {"Content-Type": "application/json; charset=utf-8; charset=utf-8"},
        {"Content-Type": "application/json", "Content-Encoding": "gzip"},
    ],
)
@pytest.mark.parametrize("path", [HISTORY, EXECUTION])
def test_research_media_type(product, headers, path):
    _, client, dq, query = product
    error(client.post(path, content=json.dumps(BODY), headers=headers), 400, "invalid_request")
    query.assert_not_called()
    dq.assert_not_called()


@pytest.mark.parametrize("query", ["?bad=1", "?metric=x&metric=y", "?product_code=IM"])
@pytest.mark.parametrize("path", [HISTORY, EXECUTION])
def test_research_rejects_all_query_parameters(product, query, path):
    _, client, dq, hq = product
    error(
        client.post(path + query, json=BODY if path == HISTORY else DAILY_BODY),
        400, "invalid_request",
    )
    hq.assert_not_called()
    dq.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"history_start": AFTER.isoformat()},
        {"history_start": "2024-10-22"},
        {"histogram_edges": []},
        {"histogram_edges": [0]},
        {"histogram_edges": [1, 0]},
        {"histogram_edges": [0, 0]},
        {"evaluation_date": "9999-01-01", "history_start": "9998-12-31"},
    ],
)
def test_public_business_validation(product, change):
    _, client, _, _ = product
    error(client.post(HISTORY, json=BODY | change), 400, "invalid_request")


def rich_services():
    services = Services(date(2024, 9, 2), AFTER)
    rows = []
    for session in services.calendar.records:
        if not session.is_open:
            continue
        day = session.cal_date
        months = (
            ("202409", "202410", "202412", "202503")
            if day <= date(2024, 9, 18)
            else ("202410", "202411", "202412", "202503")
            if day <= DAY
            else ("202411", "202412", "202503", "202506")
        )
        rows.extend(
            future(day, month, close)
            for month, close in zip(
                months,
                (110.0, 100.0, 120.0, 110.0),
                strict=True,
            )
        )
    services.set_rows(rows)
    return services


def test_research_complete_time_series_and_statistics(product):
    _, client, _, query = product
    services = rich_services()
    business = historical(services, histogram_edges=[-0.01, 0, 0.01])
    query.side_effect = None
    query.return_value = business
    request = BODY | {
        "history_start": services.start.isoformat(),
        "histogram_edges": [-0.01, 0, 0.01],
    }
    response = client.post(
        HISTORY,
        content=json.dumps(request),
        headers={"Content-Type": 'application/json; charset="UTF-8"'},
    )
    assert response.status_code == 200, response.text
    dto = HistoricalResponse.model_validate_json(response.content)
    assert response.headers["cache-control"] == "no-store" and "set-cookie" in response.headers
    assert len(dto.pairs) == 6
    assert len(dto.current_day.observations) == 6
    assert dto.request.metric == dto.metric == "annualized_spread_ratio"
    assert dto.unit == "decimal_ratio"
    assert dto.historical_accounting.valid_count == 210
    assert len(dto.historical_days) == (AFTER - services.start).days
    for wire, original in zip(dto.pairs, business.pairs, strict=True):
        points = original.distributions[-1].samples
        assert len(wire.samples) == 35
        assert [p.trade_date for p in wire.samples] == sorted(p.trade_date for p in points)
        if wire.near_slot == "M0":
            assert len({p.near.contract_code for p in wire.samples}) > 1
        for sample, point in zip(wire.samples, points, strict=True):
            assert sample.metric.value == point.metric.value
            assert sample.near.contract_code == point.observation.near.contract_code
            assert sample.far.delist_date == point.observation.far.delist_date
            assert sample.expiry_stage == point.observation.expiry_stage
        assert [d.stage for d in wire.distributions] == ["0_7", "8_21", "22_plus", "all_stages"]
        for dist, source in zip(wire.distributions, original.distributions, strict=True):
            assert dist.sample_dates == source.sample_dates
            assert dist.candidate_dates == source.candidate_dates
            assert dist.sample_count == source.sample_count
            if source.quantile:
                assert (
                    dist.quantile.result.points_and_values
                    == source.quantile.result.points_and_values
                )
                assert dist.quantile.spec.points == source.quantile.spec.points
                assert (
                    dist.histogram.result.underflow_count == source.histogram.result.underflow_count
                )
                assert (
                    dist.histogram.result.overflow_count == source.histogram.result.overflow_count
                )
                assert len(dist.histogram.result.bins) == 2
        for assessment, source in (
            (wire.matching_stage, original.matching_stage),
            (wire.all_stages, original.all_stages),
        ):
            assert assessment.distribution_stage == source.distribution.stage
            rank = assessment.percentile.result
            expected = source.percentile.result
            assert rank.estimator == "midrank_v1" and rank.sample_count == expected.sample_count
            for point, target in zip(rank.query_results, expected.query_results, strict=True):
                assert point.percentile == target.percentile
                assert 0 <= point.percentile <= 1
                assert (
                    point.less_count + point.equal_count + point.greater_count == rank.sample_count
                )
    assert not any(
        s in response.text
        for s in (
            "numeric_sample",
            "source_export_ref",
            "futures_export",
            "observation_set",
        )
    )


@pytest.mark.parametrize("mode", ["empty_history", "small", "closed", "empty_current", "excluded"])
def test_research_availability_and_nulls(product, mode):
    _, client, _, query = product
    end = date(2024, 10, 20) if mode == "closed" else AFTER
    services = Services(DAY, end)
    if mode in ("empty_history", "empty_current"):
        services.set_rows(
            row
            for row in services.futures.records
            if (row.trade_date == end if mode == "empty_history" else row.trade_date < end)
        )
    if mode == "excluded":
        services.set_rows(
            replace(row, close=0.0)
            if row.trade_date == end and row.delivery_month == "202411"
            else row
            for row in services.futures.records
        )
    query.side_effect = None
    query.return_value = historical(services, histogram_edges=[-1, 0, 1])
    response = client.post(
        HISTORY,
        json=BODY
        | {
            "evaluation_date": end.isoformat(),
            "histogram_edges": [-1, 0, 1],
        },
    )
    assert response.status_code == 200, response.text
    dto = HistoricalResponse.model_validate_json(response.content)
    assessment = dto.pairs[0].all_stages
    if mode == "empty_history":
        assert assessment.status == "empty_sample" and assessment.percentile is None
        assert dto.pairs[0].samples == ()
    elif mode == "small":
        assert assessment.status == "small_sample" and assessment.warnings
        assert assessment.percentile.result.sample_count == 1
        matching = dto.pairs[0].matching_stage
        assert matching.status == "empty_sample" and matching.percentile is None
        assert matching.distribution_stage == dto.current_day.observations[0].expiry_stage
        zero = dto.pairs[2].all_stages.percentile.result.query_results[0]
        assert zero.query == 0 and zero.percentile == 0.5
    else:
        assert assessment.status == "not_applicable" and assessment.percentile is None
        assert dto.pairs[0].samples
        assert (
            assessment.reason
            == {
                "closed": "non_trading_day",
                "empty_current": "no_active_contract",
                "excluded": "nonpositive_close",
            }[mode]
        )


@pytest.mark.parametrize("path", [DAILY, EXECUTION, HISTORY])
@pytest.mark.parametrize(
    "category,status",
    [
        ("invalid_request", 400),
        ("incomplete_inputs", 409),
        ("upstream_unavailable", 503),
        ("input_contract_error", 502),
        ("slot_resolution_error", 422),
        ("calculation_failure", 422),
        ("statistical_failure", 422),
    ],
)
def test_classified_errors_safe_and_no_renewal(product, path, category, status):
    _, client, dq, hq = product
    query = dq if path != HISTORY else hq
    query.side_effect = case.CalendarSpreadQueryError(
        category,
        "/private/db.sqlite",
        "secret",
        "/private/provider secret traceback",
    )
    response = request_path(client, path)
    error(response, status, category)
    assert "reason_code" not in response.json()["error"]


def test_auth_precedes_parsing_dependencies_and_same_origin(product):
    app, client, dq, hq = product
    deps = Mock(side_effect=AssertionError("Anonymous dependency"))
    app.dependency_overrides[get_daily_query] = deps
    app.dependency_overrides[get_historical_query] = deps
    app.dependency_overrides[get_daily_execution] = deps
    anonymous = TestClient(app, base_url=ORIGIN)
    error(anonymous.request("GET", DAILY + "?bad=1", content=b"{"), 401, "authentication_required")
    error(anonymous.post(HISTORY, content=b"{"), 401, "authentication_required")
    error(
        client.post(HISTORY, content=b"{", headers={"Origin": "https://evil"}),
        403,
        "origin_forbidden",
    )
    error(anonymous.post(EXECUTION, content=b"{"), 401, "authentication_required")
    error(
        client.post(EXECUTION, json=DAILY_BODY, headers={"Origin": "https://evil"}),
        403, "origin_forbidden",
    )
    deps.assert_not_called()
    dq.assert_not_called()
    hq.assert_not_called()


def test_typed_composed_openapi_business_422_and_other_operations(product):
    app, client, _, _ = product
    response = client.get("/openapi.json")
    assert response.status_code == 200
    doc = response.json()
    for path, method, op, schema in (
        (DAILY, "get", "query_futures_calendar_spread", "DailyResponse"),
        (EXECUTION, "post", "execute_futures_calendar_spread", "DailyResponse"),
        (HISTORY, "post", "query_calendar_spread_relative_value", "HistoricalResponse"),
    ):
        operation = doc["paths"][path][method]
        assert operation["operationId"] == op
        assert operation["security"] == [{"CookieSession": []}]
        assert set(map(str, [200, 400, 401, 403, 409, 413, 422, 500, 502, 503])) <= set(
            operation["responses"]
        )
        assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/" + schema,
        }
        assert (
            "ErrorResponse"
            in operation["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
        )
    assert doc["paths"][HISTORY]["post"]["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("/HistoricalRequest")
    params = doc["paths"][DAILY]["get"]["parameters"]
    assert {p["name"] for p in params} == {"product_code", "trade_date"}
    assert all(p["required"] for p in params)
    for path, methods in doc["paths"].items():
        if path not in (DAILY, EXECUTION, HISTORY):
            assert all("422" not in operation["responses"] for operation in methods.values())
    assert "HTTPValidationError" not in doc["components"]["schemas"]
    assert doc["components"]["securitySchemes"]["CookieSession"]["in"] == "cookie"


def test_limits_and_no_partial_200(product, monkeypatch):
    _, client, dq, hq = product
    error(
        client.post(HISTORY, json=BODY | {"history_start": "2000-01-01"}),
        413,
        "request_too_large",
        "history_start",
    )
    error(
        client.post(HISTORY, json=BODY | {"histogram_edges": list(range(129))}),
        413,
        "request_too_large",
        "histogram_edges",
    )
    hq.assert_not_called()
    monkeypatch.setattr(transport, "MAX_RESPONSE_BYTES", 100)
    error(client.get(DAILY + QUERY), 413, "response_too_large")
    assert dq.call_count == 1


@pytest.mark.parametrize("path", [DAILY, EXECUTION, HISTORY])
@pytest.mark.parametrize("nonfinite", [float("nan"), float("inf"), float("-inf")])
def test_unexpected_and_nonfinite_projection_is_atomic(product, path, nonfinite):
    _, client, dq, hq = product
    query = dq if path != HISTORY else hq
    query.side_effect = RuntimeError("/private/db.sqlite secret")

    def request():
        return request_path(client, path)

    error(request(), 500, "internal_error")
    query.side_effect = None
    services = Services() if path != HISTORY else Services(DAY, AFTER)
    original = daily(services) if path != HISTORY else historical(services)
    day = original.day if path != HISTORY else original.current_day
    observation = day.observations[0]
    metrics = replace(
        observation.metrics,
        signed_spread=replace(observation.metrics.signed_spread, value=nonfinite),
    )
    broken_day = replace(
        day, observations=(replace(observation, metrics=metrics), *day.observations[1:])
    )
    query.return_value = replace(
        original,
        observation_set=replace(
            original.observation_set,
            days=(*original.observation_set.days[:-1], broken_day),
        ),
    )
    error(request(), 500, "internal_error")


def test_workers_hold_capacity_through_serialization_and_free_after_failure(product, monkeypatch):
    app, client, _, hq = product
    entered = threading.Barrier(3)
    release = threading.Event()
    thread_ids = []
    business = historical(Services(DAY, AFTER))

    @app.get("/test-event-loop")
    async def event_loop():
        return {"thread": threading.get_ident()}

    def slow(*args, **kwargs):
        thread_ids.append(threading.get_ident())
        # There must be no running event loop in the business worker.
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()
        entered.wait(timeout=10)
        assert release.wait(timeout=10)
        return business

    hq.side_effect = slow
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = [pool.submit(client.post, HISTORY, json=BODY) for _ in range(2)]
        try:
            entered.wait(timeout=10)
            error(client.post(HISTORY, json=BODY), 503, "transport_busy")
            # Another application shares the same capacity.
            other = create_app()
            other.dependency_overrides[get_historical_query] = lambda: hq
            second_client = TestClient(other, base_url=ORIGIN, headers={"Origin": ORIGIN})
            second_client.cookies.update(client.cookies)
            error(second_client.post(HISTORY, json=BODY), 503, "transport_busy")
            assert client.get("/test-event-loop").json()["thread"] not in thread_ids
        finally:
            release.set()
        assert all(p.result(timeout=10).status_code == 200 for p in pending)
    hq.side_effect = RuntimeError("private")
    error(client.post(HISTORY, json=BODY), 500, "internal_error")
    hq.side_effect = None
    hq.return_value = business
    assert client.post(HISTORY, json=BODY).status_code == 200


@pytest.mark.parametrize("path", [DAILY, EXECUTION, HISTORY])
def test_lossless_finite_projection_and_only_auth_storage(product, path, tmp_path):
    app, client, dq, hq = product
    assert get_daily_query() is case.query_daily_spreads
    assert get_historical_query() is case.execute_historical_relative_value
    assert get_daily_execution() is case.execute_daily_spreads
    business = daily(Services()) if path != HISTORY else historical(Services(DAY, AFTER))
    original_day = business.day if path != HISTORY else business.current_day
    original = original_day.observations[0]
    values = (-0.0, 1.2345678901234567, 1.7976931348623157e308)
    metrics = replace(
        original.metrics,
        signed_spread=replace(original.metrics.signed_spread, value=values[0]),
        annualized_point_spread=replace(original.metrics.annualized_point_spread, value=values[1]),
        annualized_spread_ratio=replace(original.metrics.annualized_spread_ratio, value=values[2]),
    )
    day = replace(
        original_day,
        observations=(replace(original, metrics=metrics), *original_day.observations[1:]),
    )
    business = replace(
        business,
        observation_set=replace(
            business.observation_set,
            days=(*business.observation_set.days[:-1], day),
        ),
    )
    query = dq if path != HISTORY else hq
    query.side_effect = None
    query.return_value = business
    # DI returns a completed public Result: no service construction, acquisition,
    # observation construction or numerical call is necessary in the adapter.
    from market_research.descriptive.cases.futures_calendar_spread import queries
    from market_statistics import api

    with pytest.MonkeyPatch.context() as patch:

        def forbidden(*args, **kwargs):
            pytest.fail("HTTP attempted business computation or source access")

        patch.setattr(queries, "prepare_inputs", forbidden)
        patch.setattr(queries, "construct_observations", forbidden)
        patch.setattr(api, "compute", forbidden)
        response = request_path(client, path)
    assert response.status_code == 200, response.text
    result_day = response.json()["day" if path != HISTORY else "current_day"]
    projected = result_day["observations"][0]["metrics"]
    actual = tuple(
        projected[name]["value"]
        for name in (
            "signed_spread",
            "annualized_point_spread",
            "annualized_spread_ratio",
        )
    )
    assert actual == values
    assert "-0.0" in response.text
    # Conftest configures isolated auth, Basis and Backtesting roots under tmp_path.
    # These read-only requests create only the actual Auth DB, no Run/persistence.
    assert {p.name for p in tmp_path.iterdir()} == {"http-auth.sqlite3"}


def test_capacity_includes_projection_encoding(product, monkeypatch):
    _, client, dq, _ = product
    entered = threading.Event()
    release = threading.Event()
    original_dump = DailyResponse.model_dump
    monkeypatch.setattr(transport, "_CAPACITY", threading.BoundedSemaphore(1))

    def slow_dump(self, *args, **kwargs):
        entered.set()
        assert release.wait(timeout=10)
        return original_dump(self, *args, **kwargs)

    monkeypatch.setattr(DailyResponse, "model_dump", slow_dump)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(client.get, DAILY + QUERY)
        try:
            assert entered.wait(timeout=10)
            error(client.get(DAILY + QUERY), 503, "transport_busy")
            assert dq.call_count == 1
        finally:
            release.set()
        assert pending.result(timeout=10).status_code == 200


@pytest.mark.parametrize("path", [DAILY, EXECUTION, HISTORY])
def test_incomplete_business_projection_cannot_return_200(product, path):
    _, client, dq, hq = product
    business = daily(Services()) if path != HISTORY else historical(Services(DAY, AFTER))
    day = business.day if path != HISTORY else business.current_day
    broken = replace(
        business,
        observation_set=replace(
            business.observation_set,
            days=(
                *business.observation_set.days[:-1],
                replace(day, observations=day.observations[:-1]),
            ),
        ),
    )
    query = dq if path != HISTORY else hq
    query.side_effect = None
    query.return_value = broken
    response = request_path(client, path)
    error(response, 500, "internal_error")


@pytest.mark.parametrize("path", [DAILY, EXECUTION, HISTORY])
@pytest.mark.parametrize("reason,kind,status", [
    ("cache_incomplete", "incomplete_inputs", 409),
    ("final_export_incomplete", "incomplete_inputs", 409),
    ("credential_missing", "upstream_unavailable", 503),
    ("cache_incompatible", "upstream_unavailable", 503),
    ("operation_unavailable", "upstream_unavailable", 503),
    ("malformed_export", "input_contract_error", 502),
    ("malformed_ensure_result", "input_contract_error", 502),
    ("upstream_request_rejected", "input_contract_error", 502),
])
def test_reason_projection(product, path, reason, kind, status):
    _, client, dq, hq = product
    query = hq if path == HISTORY else dq
    query.side_effect = case.CalendarSpreadQueryError(
        kind, "input_preparation", "secret", "/private/db.sqlite secret", reason_code=reason,
    )
    response = request_path(client, path)
    error(response, status, kind)
    assert response.json()["error"]["reason_code"] == reason
    assert response.json()["error"]["detail"] != "/private/db.sqlite secret"


@pytest.mark.parametrize("kind,reason", [
    ("incomplete_inputs", "credential_missing"), ("upstream_unavailable", "unknown"),
    ("transport_busy", None), ("unknown", None), ("invalid_request", "malformed_export"),
])
def test_unknown_failure_contract_is_internal(product, kind, reason):
    _, client, dq, _ = product
    dq.side_effect = case.CalendarSpreadQueryError(
        kind, "secret", "secret", "/private/db.sqlite secret", reason_code=reason,
    )
    response = client.post(EXECUTION, json=DAILY_BODY)
    error(response, 500, "internal_error")
    assert "reason_code" not in response.json()["error"]


@pytest.mark.parametrize("body", [
    {}, {"product_code": "IM"}, DAILY_BODY | {"extra": 1},
    DAILY_BODY | {"product_code": True}, DAILY_BODY | {"product_code": "im"},
    DAILY_BODY | {"trade_date": None}, DAILY_BODY | {"trade_date": 20241018},
    DAILY_BODY | {"trade_date": "20241018"}, DAILY_BODY | {"trade_date": "2024-02-30"},
    DAILY_BODY | {"trade_date": "2024-10-18T00:00:00"},
])
def test_daily_execution_strict_body(product, body):
    _, client, dq, _ = product
    response = client.post(EXECUTION, json=body)
    assert response.status_code == 400
    dq.assert_not_called()


def test_daily_read_and_execution_dependencies_are_independent(product):
    app, client, dq, _ = product
    result = case.execute_daily_spreads(
        "IM", DAY, calendar_service=Services(), futures_service=Services(),
    )
    execution = Mock(return_value=result)
    app.dependency_overrides[get_daily_execution] = lambda: execution
    response = client.post(EXECUTION, json=DAILY_BODY)
    assert response.status_code == 200, response.text
    assert response.json() == DailyResponse.model_validate(result).model_dump(mode="json")
    assert response.json()["request"]["operation"] == "query_daily_spreads"
    execution.assert_called_once_with("IM", DAY)
    dq.assert_not_called()
    assert client.get(DAILY + QUERY).status_code == 200
    dq.assert_called_once_with("IM", DAY)


def test_cancelled_requests_hold_shared_capacity(product):
    import httpx

    app, client, dq, hq = product
    entered = threading.Barrier(3)
    release = threading.Event()
    completed = threading.Event()
    business = daily(Services())
    count = 0
    lock = threading.Lock()

    def slow(*args):
        nonlocal count
        entered.wait(timeout=10)
        assert release.wait(timeout=10)
        with lock:
            count += 1
            if count == 2:
                completed.set()
        return business

    dq.side_effect = slow

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=ORIGIN,
            headers={"Origin": ORIGIN}, cookies=client.cookies,
        ) as caller:
            tasks = [
                asyncio.create_task(caller.get(DAILY + QUERY)),
                asyncio.create_task(caller.post(EXECUTION, json=DAILY_BODY)),
            ]
            try:
                await asyncio.to_thread(entered.wait, 10)
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                error(await caller.post(HISTORY, json=BODY), 503, "transport_busy")
                error(await caller.post(EXECUTION, json=DAILY_BODY), 503, "transport_busy")
                hq.assert_not_called()
            finally:
                release.set()
                assert await asyncio.to_thread(completed.wait, 10)
            # Capacity includes projection/encoding after the fake business call returns.
            for _ in range(1000):
                if transport._CAPACITY._value == 2:
                    break
                await asyncio.sleep(0.01)
            assert transport._CAPACITY._value == 2
            assert (await caller.post(HISTORY, json=BODY)).status_code == 200

    asyncio.run(scenario())


def test_historical_execution_preserves_complete_result_and_analysis_identity(product):
    _, client, _, hq = product
    services = Services(DAY, AFTER)
    result = case.execute_historical_relative_value(
        "IM", DAY, AFTER, calendar_service=services, futures_service=services,
    )
    from ui_http.products.calendar_spread_relative_value.projection import historical_response

    hq.side_effect = None
    hq.return_value = result
    response = client.post(HISTORY, json=BODY)
    assert response.status_code == 200, response.text
    assert response.json() == historical_response(result).model_dump(mode="json")
    assert response.json()["request"]["operation"] == "query_historical_relative_value"
    hq.assert_called_once_with(
        "IM", DAY, AFTER, metric="annualized_spread_ratio", histogram_edges=None,
    )


def test_daily_execution_streamed_body_and_response_bounds(product, monkeypatch):
    _, client, dq, _ = product
    error(client.post(
        EXECUTION, content=iter([b" " * 8192] * 3),
        headers={"Content-Type": "application/json"},
    ), 413, "request_too_large")
    dq.assert_not_called()
    monkeypatch.setattr(transport, "MAX_RESPONSE_BYTES", 100)
    error(client.post(EXECUTION, json=DAILY_BODY), 413, "response_too_large")
    dq.assert_called_once_with("IM", DAY)


@pytest.mark.parametrize("path", [DAILY, EXECUTION])
@pytest.mark.parametrize("availability,reason,category,close", [
    ("available", None, None, 0.0),
    ("not_applicable", "non_trading_day", None, None),
    ("unavailable", "cache_incomplete", None, None),
    ("error", "final_export_incomplete", "incomplete_inputs", None),
    ("error", "credential_missing", "upstream_unavailable", None),
    ("error", "cache_incompatible", "upstream_unavailable", None),
    ("error", "operation_unavailable", "upstream_unavailable", None),
    ("error", "malformed_export", "input_contract_error", None),
    ("error", "malformed_ensure_result", "input_contract_error", None),
    ("error", "upstream_request_rejected", "input_contract_error", None),
])
def test_daily_reference_projection_all_states(
    product, path, availability, reason, category, close,
):
    _, client, query, _ = product
    original = daily(Services())
    reference = case.DailyUnderlyingIndexReference(
        "000852.SH", DAY, close, availability, reason, category,
    )
    query.side_effect = None
    from market_research.descriptive.cases.futures_calendar_spread.daily_spot import (
        construct_daily_spot_comparisons,
    )

    query.return_value = replace(original, underlying_index=reference,
        futures_spot_comparisons=construct_daily_spot_comparisons(
            original.day, original.prepared_inputs, reference, original.underlying_index_evidence))
    response = request_path(client, path)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["underlying_index"] == {
        "index_code": "000852.SH", "trade_date": DAY.isoformat(), "close": close,
        "availability": availability, "reason_code": reason, "failure_category": category,
    }
    assert len(payload["day"]["observations"]) == 6
    assert payload["day"] == DailyResponse.model_validate(original).model_dump(mode="json")["day"]
    assert not any(
        word in response.text for word in ('"attempts":', '"ensure_result":', '"exception":')
    )


def test_daily_reference_optional_but_non_null_and_complete():
    from pydantic import ValidationError

    payload = DailyResponse.model_validate(daily(Services())).model_dump(mode="json")
    reference = payload.pop("underlying_index")
    payload.pop("futures_spot_comparisons")
    legacy = DailyResponse.model_validate_json(json.dumps(payload))
    assert "underlying_index" not in legacy.model_dump()
    assert "underlying_index" not in json.loads(legacy.model_dump_json())
    DailyResponse.model_validate_json(json.dumps({**payload, "underlying_index": reference}))
    for bad in (None, {}, {"index_code": "000852.SH"}):
        with pytest.raises(ValidationError):
            DailyResponse.model_validate_json(json.dumps({**payload, "underlying_index": bad}))
    for field in reference:
        incomplete = {k: v for k, v in reference.items() if k != field}
        with pytest.raises(ValidationError):
            DailyResponse.model_validate_json(
                json.dumps({**payload, "underlying_index": incomplete})
            )


@pytest.mark.parametrize("field,value", [
    ("index_code", "000300.SH"), ("trade_date", AFTER.isoformat()),
    ("availability", "missing"), ("reason_code", "cache_incomplete"),
    ("failure_category", "upstream_unavailable"), ("close", 0.0), ("extra", "forbidden"),
])
def test_daily_reference_rejects_bad_association_and_states(field, value):
    from pydantic import ValidationError

    result = daily(Services())  # proven SSE closure requires null Close
    payload = DailyResponse.model_validate(result).model_dump(mode="json")
    payload["underlying_index"][field] = value
    with pytest.raises(ValidationError):
        DailyResponse.model_validate_json(json.dumps(payload))


@pytest.mark.parametrize("path", [DAILY, EXECUTION])
@pytest.mark.parametrize("defect", ["null", "missing", "wrong_identity", "wrong_date"])
def test_online_reference_defects_cannot_be_200(product, path, defect):
    from types import SimpleNamespace

    _, client, query, _ = product
    result = daily(Services())
    if defect == "null":
        result = replace(result, underlying_index=None)
    elif defect == "missing":
        result = SimpleNamespace(**{key: getattr(result, key) for key in (
            "case", "definition_version", "request", "day", "accounting", "source_context",
        )})
    else:
        changes = (
            {"index_code": "000300.SH"} if defect == "wrong_identity" else {"trade_date": AFTER}
        )
        result = replace(result, underlying_index=replace(result.underlying_index, **changes))
    query.side_effect = None
    query.return_value = result
    error(request_path(client, path), 500, "internal_error")


def test_daily_reference_openapi_omission_non_null_and_historical_unchanged():
    schemas = create_app().openapi()["components"]["schemas"]
    daily_schema = next(v for v in schemas.values() if v.get("title") == "DailyResponse")
    assert "underlying_index" not in daily_schema["required"]
    field = daily_schema["properties"]["underlying_index"]
    assert "$ref" in field and "anyOf" not in field and "default" not in field
    reference = schemas[field["$ref"].rsplit("/", 1)[1]]
    assert reference["additionalProperties"] is False
    assert set(reference["required"]) == {
        "index_code", "trade_date", "close", "availability", "reason_code", "failure_category",
    }
    for schema in schemas.values():
        if schema.get("title") in {"HistoricalResponse", "Day", "DaySummary"}:
            assert "underlying_index" not in schema["properties"]


@pytest.mark.parametrize("path", [DAILY, EXECUTION])
def test_formal_reference_acquisition_permissions(product, path):
    from test_calendar_spread_daily_index import ReferenceServices

    _, client, query, _ = product
    fake = ReferenceServices(cold=("sse", "index"))
    query.side_effect = lambda code, day: fake.run(execution=path == EXECUTION)
    response = request_path(client, path)
    assert response.status_code == 200, response.text
    reference = response.json()["underlying_index"]
    if path == DAILY:
        assert reference["availability"] == "unavailable"
        assert fake.events[-1] == ("sse", "export")
    else:
        assert reference["availability"] == "available"
        assert fake.events.count(("sse", "ensure")) == 1
        assert fake.events.count(("index", "ensure")) == 1


@pytest.mark.parametrize("path", [DAILY, EXECUTION])
def test_daily_spot_online_projection_and_internal_evidence_boundary(product, path):
    from test_calendar_spread_daily_index import ReferenceServices

    _, client, query, _ = product
    result = ReferenceServices().run()
    query.side_effect = None
    query.return_value = result
    response = request_path(client, path)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert [i["slot"] for i in payload["futures_spot_comparisons"]] == ["M0", "M1", "Q1", "Q2"]
    assert len(payload["day"]["observations"]) == 6
    first = payload["futures_spot_comparisons"][0]
    assert first["signed_spread"] == 110 - 3500.123456789
    assert first["annualized_point_spread"] is None
    assert first["remaining_days"] == 0 and first["reason"] == "expiry_day"
    assert first["underlying_index"] == payload["underlying_index"]
    assert not any(word in response.text for word in (
        '"source_evidence":', '"reference_evidence":', '"calculation_exception":',
    ))


@pytest.mark.parametrize(
    "defect", ["null", "missing_reference", "order", "contract", "date", "expiry", "category"],
)
def test_daily_spot_rejects_invalid_wire_associations(defect):
    from pydantic import ValidationError

    from test_calendar_spread_daily_index import ReferenceServices
    from ui_http.products.futures_calendar_spread.endpoint import project_daily

    payload = project_daily(ReferenceServices().run()).model_dump(mode="json")
    item = payload["futures_spot_comparisons"][0]
    if defect == "null":
        payload["futures_spot_comparisons"] = None
    elif defect == "missing_reference":
        payload.pop("underlying_index")
    elif defect == "order":
        payload["futures_spot_comparisons"].reverse()
    elif defect == "contract":
        item["futures"]["contract_code"] = "invented"
    elif defect == "date":
        item["trade_date"] = AFTER.isoformat()
    elif defect == "expiry":
        item["annualized_spread_ratio"] = 0
    else:
        item["failure_category"] = "calculation_failure"
    with pytest.raises(ValidationError):
        DailyResponse.model_validate_json(json.dumps(payload))


def test_daily_spot_omission_preserved_for_both_generations_of_legacy_bundle():
    payload = DailyResponse.model_validate(daily(Services())).model_dump(mode="json")
    payload.pop("futures_spot_comparisons")
    for with_reference in (True, False):
        if not with_reference:
            payload.pop("underlying_index")
        legacy = DailyResponse.model_validate_json(json.dumps(payload))
        assert "futures_spot_comparisons" not in legacy.model_dump()
        assert json.loads(legacy.model_dump_json()) == payload
