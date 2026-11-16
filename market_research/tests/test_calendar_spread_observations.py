"""WP2 deterministic pure Pair-day construction through the published capabilities."""

import builtins
import os
import socket
from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from calendar_spread_fixtures import AFTER, DAY, Services, coverage, future
from market_research.descriptive.cases.futures_basis import SlotResolutionError
from market_research.descriptive.cases.futures_calendar_spread import (
    CalendarSpreadObservationSet,
    ObservationConstructionError,
    compute_calendar_spread,
    construct_observations,
    construction,
    preparation,
    validation,
)

PAIR_ORDER = (("M0", "M1"), ("M0", "Q1"), ("M0", "Q2"), ("M1", "Q1"), ("M1", "Q2"), ("Q1", "Q2"))


def assert_accounting(result):
    counts = result.accounting
    assert counts.candidate_count == 6 * len(result.prepared_inputs.candidate_dates)
    assert (
        counts.candidate_count
        == counts.valid_count + counts.not_applicable_count + counts.excluded_count
    )
    assert len(result.observations) == counts.candidate_count
    assert counts.valid_count == sum(p.outcome == "valid" for p in result.observations)
    assert counts.not_applicable_count == sum(
        p.outcome == "not_applicable" for p in result.observations
    )
    assert counts.excluded_count == sum(p.outcome == "excluded" for p in result.observations)
    keys = [(p.trade_date, p.near_slot, p.far_slot) for p in result.observations]
    assert len(set(keys)) == len(keys)
    for day in result.days:
        if day.status == "open":
            assert tuple((p.near_slot, p.far_slot) for p in day.observations) == PAIR_ORDER
        else:
            assert day.observations == ()
            assert day.reason == "non_trading_day"


def test_single_day_six_pairs_signs_units_full_rows_and_evidence():
    prepared = Services().prepare()
    result = construct_observations(prepared)
    assert isinstance(result, CalendarSpreadObservationSet)
    assert result.prepared_inputs is prepared
    assert_accounting(result)
    assert result.accounting.valid_count == 6
    signs = [p.metrics.signed_spread.value for p in result.observations]
    assert signs[:3] == [10.0, -10.0, 0.0]
    assert result.case == "futures_calendar_spread_v1"
    assert result.definition_version == "futures_calendar_spread_definition_v1"
    for p in result.observations:
        assert p.product_code == "IM" and p.trade_date == DAY
        assert p.case == result.case and p.definition_version == result.definition_version
        assert p.near in prepared.futures_export.records
        assert p.far in prepared.futures_export.records
        assert p.metrics.definition_version == p.definition_version
        assert p.delta_days == (p.far.delist_date - p.near.delist_date).days
        assert p.near_dte_days == (p.near.delist_date - DAY).days
        assert p.source_evidence is result.days[0].resolution.evidence
        assert p.source_evidence.source_export_ref == "prepared_inputs.futures_export"
        assert set(p.source_evidence.active_contract_codes) == {
            row.contract_code for row in prepared.futures_export.records
        }
        assert p.metrics == compute_calendar_spread(
            p.near.close, p.far.close, p.near.delist_date, p.far.delist_date
        )
    assert result == construct_observations(prepared)
    with pytest.raises(FrozenInstanceError):
        result.days = ()
    with pytest.raises(FrozenInstanceError):
        result.observations[0].near = None
    with pytest.raises(FrozenInstanceError):
        result.accounting.valid_count = 100


def test_multi_day_order_expiry_inclusion_and_next_open_transition():
    services = Services(DAY, AFTER)
    result = construct_observations(services.prepare())
    assert_accounting(result)
    assert [day.trade_date for day in result.days] == [DAY + timedelta(days=i) for i in range(4)]
    assert result.accounting.valid_count == 12
    before, after = result.days[0], result.days[-1]
    assert before.observations[0].near.contract_code == "IM2410.CFX"
    assert before.observations[0].near_dte_days == 0
    assert after.observations[0].near.contract_code == "IM2411.CFX"
    assert before.observations[0].far.contract_code == after.observations[0].near.contract_code
    assert result.days[1].status == result.days[2].status == "closed"
    assert all(p.trade_date == DAY for p in result.observations[:6])
    assert all(p.trade_date == AFTER for p in result.observations[6:])


@pytest.mark.parametrize(
    "dte, stage", [(0, "0_7"), (7, "0_7"), (8, "8_21"), (21, "8_21"), (22, "22_plus")]
)
def test_dte_stage_boundaries(dte, stage):
    # Use arbitrary proven calendar openings; do not infer sessions from weekdays.
    services = Services()
    rows = tuple(
        replace(row, delist_date=DAY + timedelta(days=dte))
        if row.delivery_month == "202410"
        else row
        for row in services.futures.records
    )
    services.set_rows(rows)
    result = construct_observations(services.prepare())
    pair = result.observations[0]
    assert pair.near_dte_days == dte
    assert pair.expiry_stage == stage
    assert_accounting(result)


@pytest.mark.parametrize(
    "day, months",
    [
        (date(2024, 3, 18), ("202403", "202404", "202406", "202409")),
        (date(2023, 12, 15), ("202312", "202401", "202403", "202406")),
        (date(2024, 1, 15), ("202401", "202402", "202403", "202406")),
    ],
)
def test_month_quarter_and_cross_year_mapping(day, months):
    services = Services(day, day)
    services.set_rows(future(day, month) for month in months)
    result = construct_observations(services.prepare())
    assert tuple(m.contract.delivery_month for m in result.days[0].resolution.mappings) == months
    assert_accounting(result)


def test_cross_year_multi_day_transition():
    first, last = date(2023, 12, 29), date(2024, 1, 2)
    services = Services(first, last)
    rows = []
    for row in services.calendar.records:
        if not row.is_open:
            continue
        months = (
            ("202312", "202401", "202403", "202406")
            if row.cal_date == first
            else ("202401", "202402", "202403", "202406")
        )
        for month in months:
            item = future(row.cal_date, month)
            if month == "202312":
                item = replace(item, delist_date=first)
            rows.append(item)
    services.set_rows(rows)
    result = construct_observations(services.prepare())
    assert result.days[0].observations[0].near.contract_code == "IM2312.CFX"
    assert result.days[-1].observations[0].near.contract_code == "IM2401.CFX"
    assert_accounting(result)


@pytest.mark.parametrize(
    "start, end",
    [(date(2024, 10, 19), date(2024, 10, 19)), (date(2024, 10, 19), date(2024, 10, 20))],
)
def test_closed_date_and_all_closed_window(start, end):
    services = Services(start, end)
    result = construct_observations(services.prepare())
    assert result.observations == ()
    assert all(day.reason == "non_trading_day" for day in result.days)
    assert all(day.resolution is None for day in result.days)
    assert_accounting(result)
    assert len(services.calls) == 2
    assert services.futures.coverage.requested_units == 0


def test_complete_empty_open_day_is_six_not_applicable_pairs():
    services = Services()
    services.set_rows(())
    prepared = services.prepare()
    assert prepared.futures_export.coverage.successful_units == 1
    result = construct_observations(prepared)
    assert result.days[0].status == "open"
    assert result.days[0].reason is None
    assert result.accounting.not_applicable_count == 6
    assert_accounting(result)
    for p in result.observations:
        assert p.outcome == "not_applicable" and p.reason == "no_active_contract"
        assert (
            p.near
            is p.far
            is p.metrics
            is p.delta_days
            is p.near_dte_days
            is p.expiry_stage
            is None
        )
        assert p.source_evidence.complete is True
        assert p.source_evidence.active_contract_codes == ()


def test_mixed_valid_empty_and_closed_days_accounting():
    services = Services(DAY, AFTER)
    services.set_rows(row for row in services.futures.records if row.trade_date == DAY)
    result = construct_observations(services.prepare())
    assert result.accounting.valid_count == 6
    assert result.accounting.not_applicable_count == 6
    assert_accounting(result)


@pytest.mark.parametrize("close", [0.0, -1.0, -0.0])
def test_nonpositive_close_excludes_affected_pairs_without_fabricated_metrics(close):
    services = Services()
    services.set_rows(
        replace(row, close=close) if row.delivery_month == "202410" else row
        for row in services.futures.records
    )
    result = construct_observations(services.prepare())
    assert result.accounting.valid_count == 3
    assert result.accounting.excluded_count == 3
    assert_accounting(result)
    for p in result.observations[:3]:
        assert p.outcome == "excluded" and p.reason == "nonpositive_close"
        assert p.near.close == close
        assert p.metrics is None
        assert p.delta_days > 0 and p.near_dte_days == 0 and p.expiry_stage == "0_7"


@pytest.mark.parametrize(
    "mode",
    [
        "equal-expiry",
        "reversed-expiry",
        "missing-contract",
        "illegal-month-structure",
        "overflow",
        "ratio-underflow",
    ],
)
def test_construction_failures_never_downgraded(mode):
    services = Services()
    rows = list(services.futures.records)
    expected = "input_contract_error"
    if mode == "equal-expiry":
        rows[0] = replace(rows[0], delist_date=rows[1].delist_date, close=0.0)
    if mode == "reversed-expiry":
        rows[0] = replace(rows[0], delist_date=date(2025, 1, 1))
    if mode == "missing-contract":
        rows.pop()
        expected = "slot_resolution_error"
    if mode == "illegal-month-structure":
        rows[-1] = future(DAY, "202506")
        expected = "slot_resolution_error"
    if mode == "overflow":
        rows[0] = replace(rows[0], close=1e306)
        expected = "calculation_failure"
    if mode == "ratio-underflow":
        rows[0] = replace(rows[0], close=5e-324)
        rows[1] = replace(rows[1], close=1e305)
        expected = "calculation_failure"
    services.set_rows(rows)
    prepared = services.prepare()
    with pytest.raises(ObservationConstructionError) as error:
        construct_observations(prepared)
    assert error.value.category == expected
    assert error.value.trade_date == DAY
    assert error.value.prepared_inputs is prepared
    if expected != "slot_resolution_error":
        assert (error.value.near_slot, error.value.far_slot) == PAIR_ORDER[0]
    assert len(services.calls) == 2


@pytest.mark.parametrize(
    "kind",
    [
        "candidates",
        "request",
        "version",
        "calendar-association",
        "futures-association",
        "coverage",
        "malformed-row",
        "mutable",
    ],
)
def test_revalidate_prepared_association_and_integrity(kind):
    prepared = Services().prepare()
    if kind == "candidates":
        prepared = replace(prepared, candidate_dates=())
    if kind == "request":
        prepared = replace(prepared, request=replace(prepared.request, product_code="IF"))
    if kind == "version":
        prepared = replace(prepared, definition_version="wrong")
    if kind == "calendar-association":
        prepared = replace(
            prepared, calendar_request=replace(prepared.calendar_request, exchange="SSE")
        )
    if kind == "futures-association":
        prepared = replace(
            prepared, futures_request=replace(prepared.futures_request, product_codes=("IF",))
        )
    if kind == "coverage":
        prepared = replace(
            prepared,
            futures_export=replace(prepared.futures_export, coverage=coverage(1, 1), records=()),
        )
    if kind == "malformed-row":
        prepared = replace(
            prepared, futures_export=replace(prepared.futures_export, records=(SimpleNamespace(),))
        )
    if kind == "mutable":
        prepared = replace(
            prepared,
            futures_export=replace(
                prepared.futures_export, records=list(prepared.futures_export.records)
            ),
        )
    with pytest.raises(ObservationConstructionError) as error:
        construct_observations(prepared)
    assert error.value.category == "input_contract_error"


def test_delegates_to_public_resolver_and_wp1_exactly_per_day_pair(monkeypatch):
    prepared = Services(DAY, AFTER).prepare()
    financial_calls, slot_calls = [], []
    original_resolver = construction.resolve_daily_slots

    def finance(*args):
        result = compute_calendar_spread(*args)
        financial_calls.append((args, result))
        return result

    def slots(*args, **kwargs):
        slot_calls.append((args, kwargs))
        return original_resolver(*args, **kwargs)

    monkeypatch.setattr(construction, "compute_calendar_spread", finance)
    monkeypatch.setattr(construction, "resolve_daily_slots", slots)
    result = construct_observations(prepared)
    assert len(financial_calls) == 12 and len(slot_calls) == 2
    for p, (args, metrics) in zip(result.observations, financial_calls, strict=True):
        assert args == (p.near.close, p.far.close, p.near.delist_date, p.far.delist_date)
        assert p.metrics is metrics
    assert tuple(call[0][1] for call in slot_calls) == prepared.candidate_dates


def test_public_slot_failure_context_and_programming_errors_propagate(monkeypatch):
    prepared = Services().prepare()
    failure = SlotResolutionError("invalid_month_structure", "IM", DAY, "synthetic", (), None)

    def reject(*args, **kwargs):
        raise failure

    monkeypatch.setattr(construction, "resolve_daily_slots", reject)
    with pytest.raises(ObservationConstructionError) as error:
        construct_observations(prepared)
    assert error.value.category == "slot_resolution_error"
    assert error.value.__cause__ is failure

    def bug(*args, **kwargs):
        raise RuntimeError("programming bug")

    monkeypatch.setattr(construction, "resolve_daily_slots", bug)
    with pytest.raises(RuntimeError):
        construct_observations(prepared)


def test_construction_no_network_files_services_or_clock(monkeypatch):
    services = Services()
    prepared = services.prepare()
    before = prepared
    expected = construct_observations(prepared)

    def forbidden(*args, **kwargs):
        pytest.fail("pure construction performed I/O, service or clock access")

    class NoClock:
        now = forbidden

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(os, "open", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(services, "export", forbidden)
    monkeypatch.setattr(preparation, "create_calendar_service", forbidden)
    monkeypatch.setattr(preparation, "create_futures_service", forbidden)
    monkeypatch.setattr(validation, "datetime", NoClock)
    result = construct_observations(prepared)
    assert result == expected
    assert prepared == before
    assert len(services.calls) == 2
