"""Daily-only futures–spot formula, evidence and isolation acceptance."""

from dataclasses import FrozenInstanceError, replace
from datetime import timedelta
from math import log

import pytest

from calendar_spread_fixtures import DAY, coverage
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRecord
from market_research.descriptive.cases import futures_calendar_spread as case
from market_research.descriptive.cases.futures_calendar_spread.daily_spot import (
    construct_daily_spot_comparisons,
)
from test_calendar_spread_daily_index import ReferenceServices


def test_four_spot_results_reuse_rows_reference_and_do_not_change_pairs():
    services = ReferenceServices()
    result = services.run()
    original = case.construct_observations(result.prepared_inputs)
    assert result.observation_set == original
    assert len(result.day.observations) == 6
    assert [item.slot for item in result.futures_spot_comparisons] == ["M0", "M1", "Q1", "Q2"]
    for item in result.futures_spot_comparisons:
        assert item.futures is next(
            row
            for row in result.prepared_inputs.futures_export.records
            if row.contract_code == item.futures.contract_code
        )
        assert item.underlying_index is result.underlying_index
        assert item.reference_evidence is result.underlying_index_evidence
        assert item.source_evidence is result.day.resolution.evidence
        f, s = item.futures.close, result.underlying_index.close
        assert item.signed_spread == f - s
        d = (item.futures.delist_date - DAY).days
        assert item.remaining_days == d
        if d:
            assert item.annualized_point_spread == (f - s) * 365 / d
            assert item.annualized_spread_ratio == 365 * log(f / s) / d
        else:
            assert item.outcome == "not_applicable" and item.reason == "expiry_day"
            assert item.annualized_point_spread is item.annualized_spread_ratio is None
    assert services.events.count(("index", "export")) == 1
    with pytest.raises(FrozenInstanceError):
        result.futures_spot_comparisons[0].remaining_days = 1


@pytest.mark.parametrize("spot", [100.0, 110.0, 120.0, 0.0, -1.0])
def test_sign_zero_nonpositive_and_expiry(spot):
    services = ReferenceServices()
    services.index = replace(
        services.index, records=(replace(services.index.records[0], close=spot),)
    )
    result = services.run()
    front = result.futures_spot_comparisons[0]
    if spot <= 0:
        assert all(
            i.outcome == "excluded" and i.reason == "nonpositive_close" and i.signed_spread is None
            for i in result.futures_spot_comparisons
        )
    else:
        assert front.signed_spread == 110.0 - spot
        assert front.annualized_point_spread is front.annualized_spread_ratio is None
        assert (
            result.futures_spot_comparisons[1].annualized_spread_ratio == 365 * log(100 / spot) / 31
        )


def test_unavailable_index_keeps_all_original_pairs():
    services = ReferenceServices(cold=("index",))
    result = services.run()
    assert result.day == case.construct_observations(result.prepared_inputs).days[0]
    assert all(
        i.reason == "index_reference_unavailable" and i.signed_spread is None
        for i in result.futures_spot_comparisons
    )
    assert result.underlying_index.reason_code == "cache_incomplete"


def test_independent_calendar_closure_and_empty_contracts():
    sse_closed = ReferenceServices(closed=True)
    assert all(
        i.reason == "index_reference_unavailable" for i in sse_closed.run().futures_spot_comparisons
    )
    cffex_closed = ReferenceServices()
    cffex_closed.calendar = replace(
        cffex_closed.calendar, records=(TradeCalendarRecord("CFFEX", DAY, 0, None),)
    )
    cffex_closed.futures = replace(cffex_closed.futures, records=(), coverage=coverage(0))
    result = cffex_closed.run()
    assert result.futures_spot_comparisons == ()
    assert result.underlying_index.availability == "available"
    assert ("index", "export") in cffex_closed.events
    empty = ReferenceServices()
    empty.set_rows(())
    assert all(
        i.reason == "no_active_contract" and i.futures is None
        for i in empty.run().futures_spot_comparisons
    )


def test_nonpositive_futures_retains_quote_and_original_pair_outcomes():
    services = ReferenceServices()
    services.set_rows(
        (replace(services.futures.records[0], close=0.0), *services.futures.records[1:])
    )
    result = services.run()
    item = result.futures_spot_comparisons[0]
    assert item.outcome == "excluded" and item.futures.close == 0
    assert item.signed_spread is None
    assert result.day == case.construct_observations(result.prepared_inputs).days[0]


@pytest.mark.parametrize("spot", [1e308, 5e-324])
def test_spot_overflow_and_ratio_failure_are_isolated(spot):
    services = ReferenceServices()
    services.index = replace(
        services.index, records=(replace(services.index.records[0], close=spot),)
    )
    result = services.run()
    assert all(o.outcome == "valid" for o in result.day.observations)
    # D=0 never executes annualization or price division.
    assert result.futures_spot_comparisons[0].reason == "expiry_day"
    for item in result.futures_spot_comparisons[1:]:
        assert item.outcome == "error" and item.reason == "calculation_failure"
        assert item.failure_category == "calculation_failure"
        assert (
            item.signed_spread
            is item.annualized_point_spread
            is item.annualized_spread_ratio
            is None
        )
        assert item.calculation_exception is not None


@pytest.mark.parametrize("value", [float("inf"), float("nan"), True])
def test_nonfinite_or_boolean_input_is_not_a_success(value):
    result = ReferenceServices().run()
    reference = replace(result.underlying_index, close=value)
    with pytest.raises(ValueError):
        construct_daily_spot_comparisons(
            result.day, result.prepared_inputs, reference, result.underlying_index_evidence
        )


@pytest.mark.parametrize("days,stage", [(7, "0_7"), (8, "8_21"), (21, "8_21"), (22, "22_plus")])
def test_spot_stage_boundaries(days, stage):
    result = ReferenceServices().run()
    # This pure capability consumes the resolved row identity, never resolves again.
    rows = tuple(
        replace(row, delist_date=DAY + timedelta(days=days))
        for row in result.prepared_inputs.futures_export.records
    )
    prepared = replace(
        result.prepared_inputs,
        futures_export=replace(result.prepared_inputs.futures_export, records=rows),
    )
    items = construct_daily_spot_comparisons(
        result.day, prepared, result.underlying_index, result.underlying_index_evidence
    )
    assert all(i.remaining_days == days and i.expiry_stage == stage for i in items)


@pytest.mark.parametrize("f,s", [(5e-324, 2.0), (1e300, 1e-30)])
def test_finite_price_ratio_underflow_or_overflow_retains_other_business_results(f, s):
    services = ReferenceServices()
    services.set_rows(tuple(replace(row, close=f) for row in services.futures.records))
    services.index = replace(
        services.index, records=(replace(services.index.records[0], close=s),)
    )
    result = services.run()
    assert all(o.outcome == "valid" for o in result.day.observations)
    assert result.futures_spot_comparisons[0].reason == "expiry_day"
    assert all(i.reason == "calculation_failure" for i in result.futures_spot_comparisons[1:])
