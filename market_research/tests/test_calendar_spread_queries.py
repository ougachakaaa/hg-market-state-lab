"""WP4 synthetic public-service acceptance; no real market stores or network."""

import builtins
import os
import socket
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

from calendar_spread_fixtures import AFTER, DAY, Services, coverage, future
from data_lake import OperationError
from market_research.descriptive.cases import futures_calendar_spread as case
from market_research.descriptive.cases.futures_calendar_spread import queries, query_statistics
from market_research.descriptive.cases.futures_calendar_spread.observations import PAIRS
from market_statistics import (
    CalculationFailure,
    EmpiricalPercentileSpec,
    IntervalCountSpec,
    QuantileSpec,
    compute,
)

METRICS = (
    ("signed_spread", "index_points"),
    ("annualized_point_spread", "index_points_per_365_natural_days"),
    ("annualized_spread_ratio", "decimal_ratio"),
)


def daily(services, day=None):
    return case.query_daily_spreads(
        services.product, day or services.end, calendar_service=services, futures_service=services
    )


def historical(services, **kwargs):
    return case.query_historical_relative_value(
        services.product,
        services.start,
        services.end,
        calendar_service=services,
        futures_service=services,
        **kwargs,
    )


def rich_services(start=date(2024, 9, 2), end=date(2024, 10, 21), product="IM"):
    """Dynamic real identities on both sides of expiry, with all three stage bands."""
    services = Services(start, end, product)
    rows = []
    for session in services.calendar.records:
        if not session.is_open:
            continue
        day = session.cal_date
        if day <= date(2024, 9, 18):
            months = ("202409", "202410", "202412", "202503")
        elif day <= DAY:
            months = ("202410", "202411", "202412", "202503")
        else:
            months = ("202411", "202412", "202503", "202506")
        rows.extend(
            future(day, month, close, product)
            for month, close in zip(months, (110.0, 100.0, 120.0, 110.0), strict=True)
        )
    services.set_rows(rows)
    return services


def test_daily_full_contract_zero_and_source_resolution():
    services = Services()
    result = daily(services)
    assert isinstance(result, case.DailySpreadsResult)
    assert result.request == case.DailySpreadsRequest("IM", DAY)
    assert result.case == "futures_calendar_spread_v1"
    assert result.definition_version == "futures_calendar_spread_definition_v1"
    assert result.day.status == "open" and result.day.reason is None
    assert tuple((o.near_slot, o.far_slot) for o in result.day.observations) == PAIRS
    assert result.accounting == case.OutcomeAccounting(6, 6, 0, 0)
    assert result.day.observations[2].metrics.signed_spread.value == 0
    for o in result.day.observations:
        assert o.metrics is not None
        assert o.near in result.prepared_inputs.futures_export.records
        assert o.far in result.prepared_inputs.futures_export.records
        assert o.source_evidence.source_export_ref == "prepared_inputs.futures_export"
    assert [c[0] for c in services.calls] == ["calendar", "futures"]
    assert all(c[1].start_date == c[1].end_date == DAY for c in services.calls)
    assert result.source_context.provider == "tushare"
    assert "point" not in result.source_context.price_field
    assert any("historical trade date" in s for s in result.source_context.limitations)


@pytest.mark.parametrize("product", ["IF", "IH", "IC", "IM"])
@pytest.mark.parametrize(("metric", "unit"), METRICS)
def test_six_pairs_four_groups_population_and_all_metric_units(product, metric, unit):
    services = rich_services(product=product)
    result = historical(services, metric=metric)
    assert result.metric == result.request.metric == metric and result.unit == unit
    assert tuple((p.near_slot, p.far_slot) for p in result.pairs) == PAIRS
    assert result.current_day.trade_date == services.end
    assert len(services.calls) == 2
    assert result.historical_days[0].trade_date == services.start
    assert result.historical_days[-1].trade_date < services.end
    assert result.historical_accounting.valid_count == 6 * 35
    for pair in result.pairs:
        assert [d.stage for d in pair.distributions] == ["0_7", "8_21", "22_plus", "all_stages"]
        all_ = pair.distributions[-1]
        assert sum(d.sample_count for d in pair.distributions[:3]) == all_.sample_count
        assert all_.sample_count == 35 and all_.status == "available"
        assert all_.sample_dates[0] == services.start
        for dist in pair.distributions:
            assert dist.metric == metric and dist.unit == unit
            assert dist.accounting.valid_count == dist.sample_count
            assert dist.accounting.candidate_count == len(dist.candidate_dates)
            assert dist.histogram_status == "not_requested" and dist.histogram is None
            for point in dist.samples:
                o = point.observation
                assert o.product_code == product
                assert (o.near_slot, o.far_slot) == (pair.near_slot, pair.far_slot)
                assert services.start <= o.trade_date < services.end
                assert dist.stage == "all_stages" or o.expiry_stage == dist.stage
                assert point.metric is getattr(o.metrics, metric)
                assert point.metric.unit == unit
                assert o.near in result.prepared_inputs.futures_export.records
                assert o.far in result.prepared_inputs.futures_export.records
                assert o.source_evidence.source_export_ref == "prepared_inputs.futures_export"
            if dist.sample_count:
                assert dist.quantile.sample is dist.numeric_sample
                assert dist.quantile.spec.points == (0, 0.05, 0.25, 0.5, 0.75, 0.95, 1)
                assert dist.quantile.result.estimator == "type7_linear_v1"
                assert dist.quantile.result == compute(dist.numeric_sample, dist.quantile.spec)
                assert dist.numeric_sample.values == tuple(p.metric.value for p in dist.samples)
        for assessment in (pair.matching_stage, pair.all_stages):
            assert assessment.current is result.current_day.observations[result.pairs.index(pair)]
            assert assessment.percentile.sample is assessment.distribution.numeric_sample
            assert assessment.percentile.result == compute(
                assessment.percentile.sample, assessment.percentile.spec
            )
            assert assessment.percentile.spec.queries == (
                getattr(assessment.current.metrics, metric).value,
            )
            assert assessment.percentile.result.estimator == "midrank_v1"
        assert pair.matching_stage.distribution.stage == pair.matching_stage.current.expiry_stage
        assert pair.all_stages.distribution is all_
        assert all(
            any(point is p for p in all_.samples)
            for d in pair.distributions[:3]
            for point in d.samples
        )


def test_daily_and_historical_share_exact_current_observation():
    history = historical(Services(DAY, AFTER))
    current = daily(Services(AFTER, AFTER))
    assert history.current_day == current.day
    assert history.current_day.observations == current.day.observations
    assert current.accounting == case.OutcomeAccounting(6, 6, 0, 0)


def test_one_preparation_one_construction_and_public_statistics_dispatch(monkeypatch):
    services = Services(DAY, AFTER)
    prepared_calls, constructed_calls, statistical_calls = [], [], []
    prepare, construct = queries.prepare_inputs, queries.construct_observations

    def spy_prepare(*args, **kwargs):
        prepared = prepare(*args, **kwargs)
        prepared_calls.append((args, prepared))
        return prepared

    def spy_construct(prepared):
        collection = construct(prepared)
        constructed_calls.append((prepared, collection))
        return collection

    def spy_compute(sample, spec):
        result = compute(sample, spec)
        statistical_calls.append((sample, spec, result))
        return result

    monkeypatch.setattr(queries, "prepare_inputs", spy_prepare)
    monkeypatch.setattr(queries, "construct_observations", spy_construct)
    monkeypatch.setattr(query_statistics, "compute", spy_compute)
    result = historical(services, histogram_edges=[-20, 0, 20])
    assert len(prepared_calls) == len(constructed_calls) == 1
    assert prepared_calls[0][0] == ("IM", DAY, AFTER)
    assert constructed_calls[0][0] is prepared_calls[0][1]
    assert result.observation_set is constructed_calls[0][1]
    assert len(services.calls) == 2
    assert {type(spec) for _, spec, _ in statistical_calls} == {
        QuantileSpec,
        IntervalCountSpec,
        EmpiricalPercentileSpec,
    }
    for pair in result.pairs:
        for d in pair.distributions:
            if d.quantile:
                assert any(
                    r is d.quantile.result and s is d.quantile.sample
                    for s, _, r in statistical_calls
                )


def test_no_lookahead_extreme_evaluation_prices_do_not_pollute_reference():
    first = Services(DAY, AFTER)
    normal = historical(first, metric="signed_spread")
    second = Services(DAY, AFTER)
    second.set_rows(
        replace(row, close=1e100)
        if row.trade_date == AFTER and row.delivery_month == "202411"
        else row
        for row in second.futures.records
    )
    extreme = historical(second, metric="signed_spread")
    for old, new in zip(normal.pairs, extreme.pairs, strict=True):
        assert old.distributions == new.distributions
        for a, b in zip(
            (old.matching_stage, old.all_stages), (new.matching_stage, new.all_stages), strict=True
        ):
            assert a.distribution == b.distribution
            if a.percentile and b.percentile:
                assert a.percentile.sample == b.percentile.sample
                assert a.percentile.sample.sample_count == b.percentile.sample.sample_count == 1
    assert normal.pairs[0].all_stages.percentile.spec != extreme.pairs[0].all_stages.percentile.spec
    assert extreme.pairs[0].all_stages.percentile.result.query_results[0].percentile == 1
    assert normal.pairs[0].all_stages.percentile.sample.values == (10.0,)


@pytest.mark.parametrize("n", [0, 1, 29, 30])
def test_sufficiency_boundaries(n, monkeypatch):
    services = rich_services()
    dates = [
        r.cal_date for r in services.calendar.records if r.is_open and r.cal_date < services.end
    ][:n]
    services.set_rows(r for r in services.futures.records if r.trade_date in (*dates, services.end))
    calls = []
    original_sample = queries.NumericSample

    def sample(values, unit):
        assert values, "empty groups must never create NumericSample"
        calls.append(values)
        return original_sample(values, unit)

    monkeypatch.setattr(queries, "NumericSample", sample)
    result = historical(services, metric="signed_spread", histogram_edges=[-20, 20])
    status = "empty_sample" if n == 0 else "small_sample" if n < 30 else "available"
    for pair in result.pairs:
        dist = pair.distributions[-1]
        assert dist.status == pair.all_stages.status == status
        assert dist.sample_count == n
        assert dist.accounting.not_applicable_count == 35 - n
        assert dist.accounting.candidate_count == 35
        assert bool(dist.warnings) == (0 < n < 30)
        if n:
            assert dist.numeric_sample.sample_count == n
            assert dist.quantile is not None and dist.histogram is not None
            assert pair.all_stages.percentile is not None
        else:
            assert dist.reason == "no_valid_historical_observations"
            assert dist.numeric_sample is dist.quantile is dist.histogram is None
            assert dist.histogram_status == "empty_sample"
            assert pair.all_stages.percentile is None
    if n == 0:
        assert calls == []


def test_missing_matching_stage_does_not_fallback_and_duplicates_survive():
    services = rich_services()
    # Retain duplicate values across real contract changes, then isolate expiry-day history.
    result = historical(services, metric="signed_spread")
    all_ = result.pairs[0].distributions[-1]
    assert all_.numeric_sample.values == (10.0,) * 35
    assert len({p.observation.near.contract_code for p in all_.samples}) > 1
    assert len(set(all_.sample_dates)) == 35
    assert result.pairs[0].all_stages.percentile.result.query_results[0].equal_count == 35
    assert result.pairs[0].all_stages.percentile.result.query_results[0].percentile == 0.5
    services.set_rows(r for r in services.futures.records if r.trade_date >= DAY)
    filtered = historical(services, metric="signed_spread")
    pair = filtered.pairs[0]
    assert pair.matching_stage.status == "empty_sample"
    assert pair.matching_stage.distribution.stage == "22_plus"
    assert pair.matching_stage.percentile is None
    assert pair.all_stages.status == "small_sample" and pair.all_stages.percentile is not None


def test_closed_current_empty_current_excluded_current_and_zero():
    closed = historical(Services(DAY, date(2024, 10, 20)))
    assert closed.current_day.status == "closed"
    for p in closed.pairs:
        assert p.distributions[-1].sample_count == 1
        assert p.matching_stage.current is p.matching_stage.distribution is None
        assert p.matching_stage.reason == p.all_stages.reason == "non_trading_day"
        assert p.matching_stage.status == p.all_stages.status == "not_applicable"
        assert p.matching_stage.percentile is p.all_stages.percentile is None
    services = Services(DAY, AFTER)
    services.set_rows(r for r in services.futures.records if r.trade_date != AFTER)
    empty = historical(services)
    assert empty.current_day.status == "open"
    assert len(empty.current_day.observations) == 6
    assert all(p.all_stages.reason == "no_active_contract" for p in empty.pairs)
    assert all(p.all_stages.distribution.sample_count == 1 for p in empty.pairs)
    services = Services(DAY, AFTER)
    services.set_rows(
        replace(r, close=0.0) if r.trade_date == AFTER and r.delivery_month == "202411" else r
        for r in services.futures.records
    )
    excluded = historical(services)
    for p in excluded.pairs[:3]:
        assert p.matching_stage.reason == "nonpositive_close"
        assert p.matching_stage.status == "not_applicable"
        assert p.matching_stage.percentile is None
        assert p.matching_stage.current.metrics is None
        assert p.matching_stage.current.near.close == 0.0
    zero = excluded.pairs[-1].all_stages
    assert zero.current.metrics is not None
    assert zero.current.metrics.signed_spread.value is not None
    assert (
        historical(Services(DAY, AFTER), metric="signed_spread")
        .pairs[2]
        .all_stages.current.metrics.signed_spread.value
        == 0.0
    )


@pytest.mark.parametrize("mode", ["closed", "empty", "excluded"])
def test_daily_normal_availability_is_not_failure(mode):
    services = Services(date(2024, 10, 19), date(2024, 10, 19)) if mode == "closed" else Services()
    if mode == "empty":
        services.set_rows(())
    if mode == "excluded":
        services.set_rows(
            replace(r, close=0.0) if r.delivery_month == "202410" else r
            for r in services.futures.records
        )
    result = daily(services)
    if mode == "closed":
        assert result.day.reason == "non_trading_day" and result.day.observations == ()
        assert result.accounting.candidate_count == 0
    else:
        assert len(result.day.observations) == 6
        assert result.accounting.not_applicable_count == (6 if mode == "empty" else 0)
        assert result.accounting.excluded_count == (3 if mode == "excluded" else 0)


def test_histogram_explicit_edges_outside_counts_owned_request():
    edges = [-5, 0, 5]
    result = historical(Services(DAY, AFTER), metric="signed_spread", histogram_edges=edges)
    edges[0] = -100
    assert result.request.histogram_edges == (-5.0, 0.0, 5.0)
    for pair in result.pairs:
        for d in pair.distributions:
            if d.sample_count:
                assert d.histogram_status == "available"
                h = d.histogram
                assert h.sample is d.numeric_sample
                assert h.spec.edges == result.request.histogram_edges
                assert h.spec.unit == result.unit
                assert h.result.sample_count == d.sample_count
                assert (
                    sum(b.count for b in h.result.bins)
                    + h.result.underflow_count
                    + h.result.overflow_count
                    == d.sample_count
                )
    assert result.pairs[0].distributions[-1].histogram.result.overflow_count == 1
    assert result.pairs[1].distributions[-1].histogram.result.underflow_count == 1
    assert result.pairs[2].distributions[-1].histogram.result.bins[-1].count == 1


@pytest.mark.parametrize(
    "kwargs",
    [
        {"product_code": "im"},
        {"product_code": True},
        {"product_code": ["IM"]},
        {"history_start": DAY, "evaluation_date": DAY},
        {"history_start": AFTER, "evaluation_date": DAY},
        {"history_start": datetime(2024, 10, 18)},
        {"evaluation_date": datetime(2024, 10, 21)},
        {"evaluation_date": date(9999, 1, 1)},
        {"history_start": "2024-10-18"},
        {"metric": "Mean"},
        {"metric": None},
        {"metric": []},
        {"histogram_edges": []},
        {"histogram_edges": [0]},
        {"histogram_edges": [1, 0]},
        {"histogram_edges": [0, 0]},
        {"histogram_edges": [False, 1]},
        {"histogram_edges": [0, "1"]},
        {"histogram_edges": [0, Decimal(1)]},
        {"histogram_edges": [0, float("inf")]},
        {"histogram_edges": [0, float("nan")]},
        {"histogram_edges": [0, 10**400]},
    ],
)
def test_invalid_historical_request_before_io(kwargs, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid request reached preparation")

    monkeypatch.setattr(queries, "prepare_inputs", forbidden)
    parameters = {"product_code": "IM", "history_start": DAY, "evaluation_date": AFTER} | kwargs
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        case.query_historical_relative_value(**parameters)
    assert caught.value.category == "invalid_request"
    assert caught.value.stage == "query_validation" and caught.value.evidence == ()


@pytest.mark.parametrize(
    ("product", "day"),
    [
        ("IM ", DAY),
        ("XX", DAY),
        ("IM", datetime(2024, 10, 18)),
        ("IM", date(9999, 1, 1)),
        ("IM", None),
    ],
)
def test_invalid_daily_before_io(product, day, monkeypatch):
    monkeypatch.setattr(queries, "prepare_inputs", lambda *a, **k: pytest.fail("unexpected I/O"))
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        case.query_daily_spreads(product, day)
    assert caught.value.category == "invalid_request"


def test_shanghai_today_validation_at_utc_boundary(monkeypatch):
    from market_research.descriptive.cases.futures_calendar_spread import validation

    class Clock:
        @staticmethod
        def now(zone):
            assert str(zone) == "Asia/Shanghai"
            return datetime(2024, 10, 21, 0, 1, tzinfo=zone)

    monkeypatch.setattr(validation, "datetime", Clock)
    assert historical(Services(DAY, AFTER)).current_day.trade_date == AFTER
    services = Services(DAY, AFTER + timedelta(days=1))
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        historical(services)
    assert caught.value.category == "invalid_request" and services.calls == []


def test_missing_matching_stage_with_available_all_stages():
    services = rich_services()
    nearest = {}
    for r in services.futures.records:
        nearest[r.trade_date] = min(nearest.get(r.trade_date, r.delivery_month), r.delivery_month)
    services.set_rows(
        replace(
            r, delist_date=r.trade_date + timedelta(days=7 if r.trade_date == services.end else 22)
        )
        if r.delivery_month == nearest[r.trade_date]
        else r
        for r in services.futures.records
    )
    pair = historical(services).pairs[0]
    assert pair.matching_stage.current.expiry_stage == "0_7"
    assert pair.matching_stage.status == "empty_sample"
    assert pair.matching_stage.percentile is None
    assert pair.all_stages.status == "available"
    assert pair.all_stages.distribution.sample_count == 35
    assert pair.all_stages.percentile is not None


@pytest.mark.parametrize("query", ["daily", "historical"])
@pytest.mark.parametrize(
    "failure", ["incomplete", "unavailable", "malformed", "slot", "calculation"]
)
def test_classified_dependency_failures_retain_safe_context(query, failure):
    services = Services() if query == "daily" else Services(DAY, AFTER)
    expected = "incomplete_inputs"
    if failure == "incomplete":
        services.futures = replace(
            services.futures,
            records=(),
            coverage=coverage(services.futures.coverage.requested_units, 1),
        )
    if failure == "unavailable":
        services.errors["futures"] = OperationError("secret path /private/token=secret")
        expected = "upstream_unavailable"
    if failure == "malformed":
        services.futures = replace(services.futures, export_schema_version=999)
        expected = "input_contract_error"
    if failure == "slot":
        services.set_rows(r for r in services.futures.records if r.delivery_month != "202503")
        expected = "slot_resolution_error"
    if failure == "calculation":
        services.set_rows(
            replace(r, close=1e306) if r.delivery_month == "202410" else r
            for r in services.futures.records
        )
        expected = "calculation_failure"
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        (daily if query == "daily" else historical)(services)
    error = caught.value
    assert error.category == expected and error.dependency
    assert error.reason and "secret" not in error.reason and "/private" not in error.reason
    assert error.__cause__ is not None and error.evidence
    assert error.observation_set is None
    if failure in ("slot", "calculation"):
        assert error.prepared_inputs is not None and error.trade_date == DAY
    if failure == "calculation":
        assert error.method == "compute_calendar_spread"
        assert (error.near_slot, error.far_slot) == PAIRS[0]


@pytest.mark.parametrize("method", ["quantile", "interval_count", "empirical_percentile"])
def test_statistics_failure_is_never_empty(method, monkeypatch):
    def fail(sample, spec):
        if spec.method == method:
            raise CalculationFailure(method, "injected /private/secret")
        return compute(sample, spec)

    monkeypatch.setattr(query_statistics, "compute", fail)
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        historical(Services(DAY, AFTER), histogram_edges=[-1, 1])
    e = caught.value
    assert e.category == "statistical_failure" and e.stage == "statistics"
    assert e.method == method and (e.near_slot, e.far_slot) == PAIRS[0]
    assert e.observation_set.prepared_inputs is e.prepared_inputs
    assert e.evidence == e.prepared_inputs.evidence
    assert "secret" not in e.reason
    assert isinstance(e.__cause__, CalculationFailure)
    assert e.trade_date == (AFTER if method == "empirical_percentile" else None)


@pytest.mark.parametrize("method", ["quantile", "interval_count", "empirical_percentile"])
@pytest.mark.parametrize(
    "defect",
    ["variant", "method", "unit", "count", "shape", "numeric", "parameters", "estimator_or_counts"],
)
def test_result_association_rejects_mismatch(method, defect, monkeypatch):
    def bad(sample, spec):
        result = compute(sample, spec)
        if spec.method != method:
            return result
        if defect == "variant":
            return None
        if defect == "method":
            return replace(result, method="other")
        if defect == "unit":
            return replace(result, unit="OTHER")
        if defect == "count":
            return replace(result, sample_count=result.sample_count + 1)
        if method == "quantile":
            if defect == "shape":
                return replace(result, points_and_values=())
            if defect == "numeric":
                return replace(
                    result, points_and_values=((0.0, float("nan")), *result.points_and_values[1:])
                )
            if defect == "parameters":
                return replace(
                    result, points_and_values=((0.1, 1.0), *result.points_and_values[1:])
                )
            return replace(result, estimator="other")
        if method == "interval_count":
            if defect == "shape":
                return replace(result, bins=())
            if defect == "numeric":
                return replace(result, underflow_frequency=float("nan"))
            if defect == "parameters":
                return replace(result, edges=(-2.0, 2.0))
            return replace(result, underflow_count=-1)
        row = result.query_results[0]
        if defect == "shape":
            return replace(result, query_results=())
        if defect == "numeric":
            return replace(result, query_results=(replace(row, percentile=float("inf")),))
        if defect == "parameters":
            return replace(result, query_results=(replace(row, query=row.query + 1),))
        return replace(result, estimator="ecdf")

    monkeypatch.setattr(query_statistics, "compute", bad)
    with pytest.raises(case.CalendarSpreadQueryError) as caught:
        historical(Services(DAY, AFTER), histogram_edges=[-1, 1])
    assert caught.value.category == "statistical_failure"
    assert caught.value.stage == "result_association" and caught.value.method == method
    assert caught.value.observation_set is not None


@pytest.mark.parametrize("layer", ["service", "construction", "statistics"])
def test_programming_errors_propagate(layer, monkeypatch):
    services = Services(DAY, AFTER)
    bug = RuntimeError("programming defect")

    def fail(*args, **kwargs):
        raise bug

    if layer == "service":
        services.export = fail
    elif layer == "construction":
        monkeypatch.setattr(queries, "construct_observations", fail)
    else:
        monkeypatch.setattr(query_statistics, "compute", fail)
    with pytest.raises(RuntimeError) as caught:
        historical(services)
    assert caught.value is bug


def test_no_io_after_exports_no_ensure_and_immutable_result(monkeypatch):
    services = Services(DAY, AFTER)
    before = services.calendar, services.futures
    original = services.export

    def forbidden(*args, **kwargs):
        pytest.fail("query attempted extra I/O or acquisition")

    def export(request):
        result = original(request)
        if len(services.calls) == 2:
            monkeypatch.setattr(services, "export", forbidden)
            monkeypatch.setattr(builtins, "open", forbidden)
            monkeypatch.setattr(os, "open", forbidden)
            monkeypatch.setattr(socket, "socket", forbidden)
            monkeypatch.setattr(socket, "create_connection", forbidden)
        return result

    services.export = export
    services.ensure = forbidden
    services.coverage = forbidden
    result = historical(services)
    assert (services.calendar, services.futures) == before
    assert len(services.calls) == 2
    assert result.request.operation == "query_historical_relative_value"
    assert result.request.metric == "annualized_spread_ratio"
    assert result.request.histogram_edges is None
    with pytest.raises(FrozenInstanceError):
        result.pairs = ()
    with pytest.raises(FrozenInstanceError):
        result.request.metric = "signed_spread"
    with pytest.raises(FrozenInstanceError):
        result.pairs[0].distributions[-1].samples[0].metric.value = 1.0

    def visit(value: Any):
        if is_dataclass(value):
            assert value.__dataclass_params__.frozen
            for field in fields(value):
                visit(getattr(value, field.name))
        elif isinstance(value, tuple):
            for item in value:
                visit(item)
        else:
            assert type(value) in (str, int, float, bool, date, type(None))

    visit(result)


def test_public_facade_and_determinism():
    for name in (
        "query_daily_spreads",
        "query_historical_relative_value",
        "DailySpreadsRequest",
        "HistoricalRelativeValueRequest",
        "DailySpreadsResult",
        "HistoricalRelativeValueResult",
        "HistoricalSamplePoint",
        "HistoricalDistribution",
        "CurrentAssessment",
        "PairRelativeValueResult",
        "QuantileAnalysis",
        "HistogramAnalysis",
        "PercentileAnalysis",
        "SourceContext",
        "CalendarSpreadQueryError",
    ):
        assert getattr(case, name) is not None
    assert historical(Services(DAY, AFTER)) == historical(Services(DAY, AFTER))
    assert daily(Services()) == daily(Services())


def test_historical_exclusions_retain_stage_coverage_and_no_numeric_sample(monkeypatch):
    services = Services(DAY, AFTER)
    services.set_rows(
        replace(r, close=0.0) if r.trade_date == DAY and r.delivery_month == "202410" else r
        for r in services.futures.records
    )
    result = historical(services)
    assert result.historical_accounting == case.OutcomeAccounting(6, 3, 0, 3)
    for pair in result.pairs[:3]:
        all_ = pair.distributions[-1]
        own_stage = pair.distributions[0]
        for dist in (all_, own_stage):
            assert dist.accounting == case.OutcomeAccounting(1, 0, 0, 1)
            assert dist.candidate_dates == (DAY,)
            assert dist.samples == () and dist.quantile is dist.numeric_sample is None
            assert dist.status == "empty_sample"
        assert pair.all_stages.percentile is None
    excluded = result.historical_days[0].observations[0]
    assert excluded.outcome == "excluded" and excluded.near.close == 0.0
    assert excluded.near in result.prepared_inputs.futures_export.records

    closed = Services(date(2024, 10, 19), date(2024, 10, 20))

    def forbidden(*args, **kwargs):
        pytest.fail("closed history must never create numerical samples or call Statistics")

    monkeypatch.setattr(queries, "NumericSample", forbidden)
    monkeypatch.setattr(query_statistics, "compute", forbidden)
    empty = historical(closed)
    assert empty.historical_accounting == case.OutcomeAccounting(0, 0, 0, 0)
    assert all(d.histogram_status == "not_requested" for p in empty.pairs for d in p.distributions)
    assert all(p.all_stages.status == "not_applicable" for p in empty.pairs)
