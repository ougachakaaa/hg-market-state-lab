"""W2 target causality and case accounting constraints, with no market I/O."""

from dataclasses import fields, replace
from datetime import date
from typing import Any

import pytest

from futures_roll_fixtures import FEB20, JAN5, JAN20, long_input, set_contract_close, simple_input
from market_backtesting.cases.futures_roll_long import (
    DecisionContext,
    FuturesRollError,
    FuturesRollInput,
    IndexClose,
    MechanicalRollPolicy,
    replay_futures_roll,
)
from market_backtesting.core import InstrumentReference, Portfolio, Position


def context(inputs: FuturesRollInput, day: date) -> DecisionContext:
    return DecisionContext(
        day == inputs.sessions[0],
        day == inputs.sessions[-1],
        inputs.contracts,
        inputs.instrument_refs,
        next((row.evidence for row in inputs.decision_slots if row.trade_date == day), None),
    )


@pytest.mark.parametrize("profile", ("expiry_to_M1_v1", "expiry_to_Q1_v1"))
def test_current_and_future_close_changes_never_change_mechanical_targets(profile: str) -> None:
    inputs = long_input(profile)
    baseline = replay_futures_roll(inputs)
    changed = set_contract_close(inputs, JAN5, "IM2602.CFX", 9999)
    changed = set_contract_close(changed, FEB20, "IM2602.CFX", 8000)
    changed = set_contract_close(changed, FEB20, "IM2603.CFX", 9000)
    changed = set_contract_close(changed, inputs.sessions[-1], "IM2606.CFX", 10000)
    perturbed = replay_futures_roll(changed)
    assert [record.target for record in baseline.replay.daily] == [
        record.target for record in perturbed.replay.daily
    ]
    assert [record.transition.daily_pnl for record in baseline.replay.daily] != [
        record.transition.daily_pnl for record in perturbed.replay.daily
    ]
    policy = MechanicalRollPolicy("IM", profile)  # type: ignore[arg-type]
    # Published interfaces contain configuration/current metadata, no snapshot accessor.
    assert {field.name for field in fields(policy)} == {"product_code", "strategy_profile"}
    assert {field.name for field in fields(context(inputs, JAN5))} == {
        "is_first",
        "is_final",
        "contracts",
        "instrument_refs",
        "evidence",
    }
    assert not hasattr(context(inputs, JAN5), "snapshot")
    assert not hasattr(context(inputs, JAN5), "sessions")
    assert policy(JAN5, Portfolio(), context(inputs, JAN5)) == baseline.replay.daily[0].target
    # A previous close is necessarily in actual Portfolio; it is not a selection input.
    previous = baseline.replay.daily[1].next_portfolio
    assert previous.position is not None
    altered_previous = Portfolio(replace(previous.position, reference_price=1))
    assert policy(FEB20, previous, context(inputs, FEB20)) == policy(
        FEB20, altered_previous, context(inputs, FEB20)
    )


@pytest.mark.parametrize("index_close", (0, -1, float("nan"), float("inf"), True))
def test_index_close_fails_explicitly(index_close: Any) -> None:
    with pytest.raises(FuturesRollError, match="non_.*close"):
        inputs = simple_input()
        replay_futures_roll(
            replace(
                inputs, index_closes=tuple(IndexClose(day, index_close) for day in inputs.sessions)
            )
        )


def test_multiplier_mismatch_on_used_contract_and_reference_scope() -> None:
    inputs = long_input()
    refs = tuple(
        replace(ref, multiplier=300) if ref.instrument_id == "IM2603.CFX" else ref
        for ref in inputs.instrument_refs
    )
    with pytest.raises(FuturesRollError, match="multiplier_mismatch"):
        replay_futures_roll(replace(inputs, instrument_refs=refs))
    for refs in (
        inputs.instrument_refs[:-1],
        inputs.instrument_refs + (inputs.instrument_refs[0],),
    ):
        with pytest.raises(FuturesRollError):
            replay_futures_roll(replace(inputs, instrument_refs=refs))


def test_w2_initial_capital_uses_index_and_nonpositive_equity_fails() -> None:
    inputs = simple_input()
    result = replay_futures_roll(inputs)
    assert result.replay.initial_capital == 6000 * 200
    assert result.replay.initial_capital != result.entry_execution.price * 200
    inputs = replace(inputs, index_closes=tuple(IndexClose(day, 1) for day in inputs.sessions))
    inputs = set_contract_close(inputs, JAN20, "IM2602.CFX", 1)
    with pytest.raises(FuturesRollError, match="non_positive_equity"):
        replay_futures_roll(inputs)


def test_policy_unexpected_flat_and_held_lifecycle_fail_explicitly() -> None:
    inputs = long_input()
    policy = MechanicalRollPolicy("IM", "expiry_to_M1_v1")
    with pytest.raises(FuturesRollError, match="unexpected_flat_state"):
        policy(JAN20, Portfolio(), context(inputs, JAN20))
    with pytest.raises(FuturesRollError, match="no_position_on_final_session"):
        policy(inputs.sessions[-1], Portfolio(), context(inputs, inputs.sessions[-1]))
    ref = next(ref for ref in inputs.instrument_refs if ref.instrument_id == "IM2602.CFX")
    altered = replace(ref, source_ref="conflicting")
    with pytest.raises(FuturesRollError, match="held_instrument_conflict"):
        policy(JAN20, Portfolio(Position(altered, 1, 5000, JAN5)), context(inputs, JAN20))
    assert isinstance(ref, InstrumentReference)
