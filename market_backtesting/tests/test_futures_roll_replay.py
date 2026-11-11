"""WP1 business regressions migrated onto the W2/Core replay boundary."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import date

import pytest

import market_backtesting.cases.futures_roll_long.policy as policy_module
from futures_roll_fixtures import (
    APR20,
    EXPECTED_DAILY,
    EXPECTED_RESOLVER_CALLS,
    EXPECTED_ROLLS,
    FEB5,
    FEB20,
    JAN5,
    JAN20,
    JUN22,
    MAY6,
    SESSIONS,
    expiry_after_final_input,
    expiry_on_final_input,
    long_input,
    price,
    resolution_for,
    simple_input,
)
from market_backtesting.cases.futures_roll_long import (
    FuturesRollInput,
    FuturesRollReplay,
    replay_futures_roll,
)
from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailySlotResolution,
    DailyUniverseEvidence,
)

PROFILES = ("expiry_to_M1_v1", "expiry_to_Q1_v1")


def executions_on(timeline: FuturesRollReplay, day: date):
    return tuple(execution for execution in timeline.executions if execution.trade_date == day)


@pytest.mark.parametrize("profile", PROFILES)
def test_initial_entry_uses_first_session_m1(profile: str) -> None:
    timeline = replay_futures_roll(long_input(profile))
    entry = timeline.entry_execution

    assert entry.trade_date == JAN5
    assert entry.side == "BUY"
    assert entry.contract_code == "IM2602.CFX"
    assert entry.price == price(JAN5, "202602")
    assert entry.reason == "entry"
    assert entry.selection_slot == "M1"
    assert timeline.daily[0].trade_date == JAN5
    assert timeline.daily[0].pnl_contract_code == "IM2602.CFX"
    assert timeline.daily[0].position_contract_code == "IM2602.CFX"


@pytest.mark.parametrize("profile", PROFILES)
def test_ordinary_holding_session_has_no_execution(profile: str) -> None:
    timeline = replay_futures_roll(long_input(profile))

    assert executions_on(timeline, JAN20) == ()
    session_row = next(row for row in timeline.daily if row.trade_date == JAN20)
    assert session_row.pnl_contract_code == "IM2602.CFX"
    assert session_row.position_contract_code == "IM2602.CFX"


def test_m1_to_m0_role_change_does_not_trade() -> None:
    timeline = replay_futures_roll(long_input("expiry_to_M1_v1"))

    entry_resolution = resolution_for(JAN5)
    role_change_resolution = resolution_for(FEB5)
    assert entry_resolution.mappings[1].contract_code == "IM2602.CFX"
    assert entry_resolution.mappings[1].slot == "M1"
    assert role_change_resolution.mappings[0].contract_code == "IM2602.CFX"
    assert role_change_resolution.mappings[0].slot == "M0"

    assert executions_on(timeline, FEB5) == ()
    session_row = next(row for row in timeline.daily if row.trade_date == FEB5)
    assert session_row.pnl_contract_code == "IM2602.CFX"
    assert session_row.position_contract_code == "IM2602.CFX"


def test_q1_to_m1_role_change_does_not_trade() -> None:
    timeline = replay_futures_roll(long_input("expiry_to_Q1_v1"))

    assert resolution_for(FEB20).mappings[2].contract_code == "IM2606.CFX"
    assert resolution_for(MAY6).mappings[1].contract_code == "IM2606.CFX"
    assert executions_on(timeline, MAY6) == ()
    session_row = next(row for row in timeline.daily if row.trade_date == MAY6)
    assert session_row.pnl_contract_code == "IM2606.CFX"
    assert session_row.position_contract_code == "IM2606.CFX"


def test_expiry_roll_to_m1() -> None:
    timeline = replay_futures_roll(long_input("expiry_to_M1_v1"))
    roll = next(item for item in timeline.rolls if item.trade_date == FEB20)
    legs = executions_on(timeline, FEB20)

    assert (roll.old_contract_code, roll.old_slot) == ("IM2602.CFX", "M0")
    assert (roll.new_contract_code, roll.new_slot) == ("IM2603.CFX", "M1")
    assert roll.old_close == price(FEB20, "202602")
    assert roll.new_close == price(FEB20, "202603")
    assert [(leg.side, leg.reason, leg.contract_code) for leg in legs] == [
        ("SELL", "expiry_close", "IM2602.CFX"),
        ("BUY", "expiry_open", "IM2603.CFX"),
    ]
    assert legs[1].selection_slot == "M1"


def test_expiry_roll_to_q1() -> None:
    timeline = replay_futures_roll(long_input("expiry_to_Q1_v1"))
    roll = next(item for item in timeline.rolls if item.trade_date == FEB20)
    legs = executions_on(timeline, FEB20)

    assert (roll.old_contract_code, roll.old_slot) == ("IM2602.CFX", "M0")
    assert (roll.new_contract_code, roll.new_slot) == ("IM2606.CFX", "Q1")
    assert roll.old_close == price(FEB20, "202602")
    assert roll.new_close == price(FEB20, "202606")
    assert [(leg.side, leg.reason, leg.contract_code) for leg in legs] == [
        ("SELL", "expiry_close", "IM2602.CFX"),
        ("BUY", "expiry_open", "IM2606.CFX"),
    ]
    assert legs[1].selection_slot == "Q1"


@pytest.mark.parametrize("profile", PROFILES)
def test_roll_day_attribution_and_next_session(profile: str) -> None:
    timeline = replay_futures_roll(long_input(profile))
    daily = {row.trade_date: row for row in timeline.daily}

    for roll in timeline.rolls:
        roll_row = daily[roll.trade_date]
        assert roll_row.pnl_contract_code == roll.old_contract_code
        assert roll_row.position_contract_code == roll.new_contract_code
        next_index = SESSIONS.index(roll.trade_date) + 1
        next_row = daily[SESSIONS[next_index]]
        assert next_row.pnl_contract_code == roll.new_contract_code


def test_final_day_expiry_closes_only() -> None:
    timeline = replay_futures_roll(expiry_on_final_input())

    assert timeline.executions == (
        timeline.entry_execution,
        timeline.exit_execution,
    )
    assert timeline.exit_execution.side == "SELL"
    assert timeline.exit_execution.reason == "study_end_close"
    assert timeline.exit_execution.contract_code == "IM2602.CFX"
    assert timeline.rolls == ()
    assert timeline.daily[-1].trade_date == FEB20
    assert timeline.daily[-1].pnl_contract_code == "IM2602.CFX"
    assert timeline.daily[-1].position_contract_code is None
    assert executions_on(timeline, FEB20) == (timeline.exit_execution,)


def test_expiry_after_window_does_not_roll() -> None:
    timeline = replay_futures_roll(expiry_after_final_input())

    assert timeline.rolls == ()
    assert len(timeline.executions) == 2
    assert timeline.exit_execution.reason == "study_end_close"
    assert timeline.exit_execution.contract_code == "IM2602.CFX"
    assert timeline.daily[-1].position_contract_code is None


@pytest.mark.parametrize("profile", PROFILES)
def test_multi_month_daily_identities_and_roll_events(profile: str) -> None:
    timeline = replay_futures_roll(long_input(profile))

    actual_daily = tuple(
        (row.trade_date, row.pnl_contract_code, row.position_contract_code)
        for row in timeline.daily
    )
    assert actual_daily == EXPECTED_DAILY[profile]
    actual_rolls = tuple(
        (
            roll.trade_date,
            roll.old_contract_code,
            roll.new_contract_code,
            roll.old_slot,
            roll.new_slot,
        )
        for roll in timeline.rolls
    )
    assert actual_rolls == EXPECTED_ROLLS[profile]
    assert len(timeline.executions) == 2 + 2 * len(EXPECTED_ROLLS[profile])
    assert timeline.entry_execution.side == "BUY"
    assert timeline.exit_execution.side == "SELL"
    assert timeline.exit_execution.reason == "study_end_close"
    assert timeline.daily[-1].position_contract_code is None
    assert all(execution.trade_date <= JUN22 for execution in timeline.executions)


@pytest.mark.parametrize("profile", PROFILES)
def test_execution_order_explains_each_roll(profile: str) -> None:
    timeline = replay_futures_roll(long_input(profile))
    index_by_id = {id(execution): index for index, execution in enumerate(timeline.executions)}

    for roll in timeline.rolls:
        legs = executions_on(timeline, roll.trade_date)
        assert len(legs) == 2
        sell, buy = legs
        assert sell.side == "SELL"
        assert sell.reason == "expiry_close"
        assert buy.side == "BUY"
        assert buy.reason == "expiry_open"
        assert index_by_id[id(buy)] == index_by_id[id(sell)] + 1
        assert (sell.contract_code, buy.contract_code) == (
            roll.old_contract_code,
            roll.new_contract_code,
        )
        assert (sell.price, buy.price) == (roll.old_close, roll.new_close)


@pytest.mark.parametrize("profile", PROFILES)
def test_resolver_is_called_only_on_entry_and_actual_roll_days(
    profile: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[date] = []
    real_resolver = policy_module.resolve_daily_slots

    def wrapper(
        product_code: str,
        trade_date: date,
        contracts: tuple[ContractMetadata, ...],
        *,
        evidence: DailyUniverseEvidence,
    ) -> DailySlotResolution:
        calls.append(trade_date)
        return real_resolver(product_code, trade_date, contracts, evidence=evidence)

    monkeypatch.setattr(policy_module, "resolve_daily_slots", wrapper)
    replay_futures_roll(long_input(profile))
    assert tuple(calls) == EXPECTED_RESOLVER_CALLS[profile]


def test_determinism_same_input_same_timeline() -> None:
    inputs = long_input("expiry_to_Q1_v1")
    first = replay_futures_roll(inputs)
    second = replay_futures_roll(inputs)

    assert first == second
    assert hash(first) == hash(second)
    assert first.daily == second.daily
    assert first.executions == second.executions


def test_inputs_and_timeline_are_immutable() -> None:
    inputs = long_input("expiry_to_M1_v1")
    snapshot = deepcopy(inputs)
    timeline = replay_futures_roll(inputs)

    assert inputs == snapshot
    assert isinstance(inputs, FuturesRollInput)
    assert isinstance(timeline, FuturesRollReplay)
    with pytest.raises(FrozenInstanceError):
        inputs.sessions = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        timeline.daily = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        timeline.daily[0].position_contract_code = None  # type: ignore[misc]


@pytest.mark.parametrize("product", ("IF", "IH", "IC", "IM"))
def test_every_canonical_product_can_enter_and_exit(product: str) -> None:
    timeline = replay_futures_roll(simple_input(product))

    assert timeline.product_code == product
    assert timeline.entry_execution.contract_code == f"{product}2602.CFX"
    assert timeline.exit_execution.contract_code == f"{product}2602.CFX"
    assert timeline.daily[0].position_contract_code == f"{product}2602.CFX"
    assert timeline.daily[-1].position_contract_code is None


def test_final_exit_is_last_execution_and_final_position_is_flat() -> None:
    timeline = replay_futures_roll(long_input("expiry_to_M1_v1"))

    assert timeline.executions[-1].trade_date == JUN22
    assert timeline.executions[-1] is timeline.exit_execution
    assert timeline.daily[-1].trade_date == JUN22
    assert timeline.daily[-1].position_contract_code is None
    assert all(execution.trade_date <= JUN22 for execution in timeline.executions)
    assert APR20 in {roll.trade_date for roll in timeline.rolls}


@pytest.mark.parametrize("profile", PROFILES)
def test_case_core_pnl_is_independently_recomputable(profile: str) -> None:
    inputs = long_input(profile)
    result = replay_futures_roll(inputs)
    prices = {
        (row.trade_date, quote.contract_code): quote.close
        for row in inputs.session_facts
        for quote in row.closes
    }
    expected_total = 0.0
    for record in result.replay.daily:
        held = record.previous_portfolio.position
        expected = 0.0
        if held is not None:
            code = held.instrument.instrument_id
            expected = (prices[record.trade_date, code] - prices[held.valuation_date, code]) * 200
        assert record.transition.daily_pnl == expected
        expected_total += expected
        assert record.accounting.cumulative_pnl == expected_total
    assert result.replay.final_portfolio.position is None
