"""Independent synthetic acceptance for the position-driven Core."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime
from math import inf, nan
from typing import Any

import pytest

from market_backtesting.core import (
    AccountingState,
    CloseAssumptions,
    CloseQuote,
    CoreError,
    DailyMarketSnapshot,
    InstrumentReference,
    Portfolio,
    Position,
    ReplaySession,
    TargetPortfolio,
    TargetPosition,
    account,
    replay,
    transition_portfolio,
)

ASSUMPTIONS = CloseAssumptions("session_close", "session_close")
DAYS = tuple(date(2026, 1, day) for day in (5, 6, 7, 8))
A = InstrumentReference("A", 200, "artificial-contract-A")
B = InstrumentReference("B", 200, "artificial-contract-B")


def target(instrument: InstrumentReference | None, quantity: float = 1) -> TargetPortfolio:
    return TargetPortfolio(TargetPosition(instrument, quantity) if instrument else None)


def snapshot(day: date, **quotes: float) -> DailyMarketSnapshot:
    return DailyMarketSnapshot(
        day, tuple(CloseQuote(code, close) for code, close in quotes.items()), "artificial-prices"
    )


def oracle_sessions() -> tuple[ReplaySession[TargetPortfolio], ...]:
    return (
        ReplaySession(DAYS[0], target(A), snapshot(DAYS[0], A=6000)),
        ReplaySession(DAYS[1], target(A), snapshot(DAYS[1], A=6100)),
        ReplaySession(DAYS[2], target(B), snapshot(DAYS[2], A=6120, B=6080)),
        ReplaySession(DAYS[3], target(B), snapshot(DAYS[3], B=6090)),
    )


def choose(_day: date, _previous: Portfolio, desired: TargetPortfolio) -> TargetPortfolio:
    return desired


def test_four_session_independent_oracle() -> None:
    sessions = oracle_sessions()
    result = replay(sessions, choose, 1_200_000, ASSUMPTIONS)
    assert [r.transition.daily_pnl for r in result.daily] == [0, 20_000, 4_000, 2_000]
    assert [r.accounting.cumulative_pnl for r in result.daily] == [0, 20_000, 24_000, 26_000]
    assert [r.accounting.equity for r in result.daily] == [
        1_200_000,
        1_220_000,
        1_224_000,
        1_226_000,
    ]
    roll = result.daily[2].transition
    assert [event.kind for event in roll.events] == ["mark", "close", "open"]
    assert [event.price for event in roll.position_changes] == [6120, 6080]
    assert roll.next_portfolio.position == Position(B, 1, 6080, DAYS[2])
    assert result.final_portfolio.position == Position(B, 1, 6090, DAYS[3])
    assert sum(r.transition.daily_pnl for r in result.daily) == 26_000
    for record in result.daily:
        assert record.accounting.equity == 1_200_000 + record.accounting.cumulative_pnl
        assert record.accounting.cumulative_return == record.accounting.cumulative_pnl / 1_200_000
    assert result == replay(sessions, choose, 1_200_000, ASSUMPTIONS)
    assert hash(result) == hash(replay(sessions, choose, 1_200_000, ASSUMPTIONS))


def test_previous_state_and_all_events_reconstruct_next_and_independent_pnl() -> None:
    result = replay(oracle_sessions(), choose, 1_200_000, ASSUMPTIONS)
    for record in result.daily:
        state = record.previous_portfolio
        for event in record.transition.events:
            assert state.position == event.before
            state = Portfolio(event.after)
        assert state == record.next_portfolio
        p = record.transition.pricing
        expected = (
            0
            if p is None
            else (p.current_close - p.previous_reference) * p.quantity * p.instrument.multiplier
        )
        assert record.transition.daily_pnl == expected
    # No-trade sessions still mark and update the date/reference.
    hold = result.daily[1].transition
    assert hold.position_changes == ()
    assert [e.kind for e in hold.events] == ["mark"]
    assert hold.next_portfolio.position == Position(A, 1, 6100, DAYS[1])


def test_flat_open_and_separate_final_close() -> None:
    opened = transition_portfolio(Portfolio(), target(A), snapshot(DAYS[0], A=6000), ASSUMPTIONS)
    assert opened.daily_pnl == 0
    assert [e.kind for e in opened.position_changes] == ["open"]
    closed = transition_portfolio(
        opened.next_portfolio, target(None), snapshot(DAYS[1], A=6100), ASSUMPTIONS
    )
    assert closed.daily_pnl == 20_000
    assert [e.kind for e in closed.position_changes] == ["close"]
    assert closed.next_portfolio == Portfolio()
    assert opened.next_portfolio.position == Position(A, 1, 6000, DAYS[0])
    with pytest.raises(FrozenInstanceError):
        opened.next_portfolio.position = None  # type: ignore[misc]
    assert opened.next_portfolio.position is not None
    with pytest.raises(FrozenInstanceError):
        opened.next_portfolio.position.reference_price = 0  # type: ignore[misc]


def test_flat_to_flat_and_non_one_lot_core() -> None:
    flat = transition_portfolio(Portfolio(), target(None), snapshot(DAYS[0]), ASSUMPTIONS)
    assert flat.events == () and flat.daily_pnl == 0 and flat.next_portfolio == Portfolio()
    previous = Portfolio(Position(A, 3, 6000, DAYS[0]))
    held = transition_portfolio(previous, target(A, 3), snapshot(DAYS[1], A=6100), ASSUMPTIONS)
    assert held.daily_pnl == 60_000
    assert previous.position == Position(A, 3, 6000, DAYS[0])
    assert held.next_portfolio.position is not previous.position


@pytest.mark.parametrize("bad", (nan, inf, -inf, 0, -1, True, "6000", None, 10**1000))
def test_invalid_quotes_capital_multipliers_quantities_and_reference(bad: Any) -> None:
    for action in (
        lambda: CloseQuote("A", bad),
        lambda: InstrumentReference("A", bad, "source"),
        lambda: TargetPosition(A, bad),
        lambda: Position(A, 1, bad, DAYS[0]),
        lambda: AccountingState.start(bad),
    ):
        with pytest.raises(CoreError):
            action()


def test_missing_old_or_new_price_and_duplicate_quote_fail() -> None:
    previous = Portfolio(Position(A, 1, 6000, DAYS[0]))
    for quotes in ({"B": 6080}, {"A": 6120}):
        with pytest.raises(CoreError, match="missing_instrument_quote"):
            transition_portfolio(previous, target(B), snapshot(DAYS[1], **quotes), ASSUMPTIONS)
    with pytest.raises(CoreError, match="duplicate_quote"):
        DailyMarketSnapshot(DAYS[0], (CloseQuote("A", 1), CloseQuote("A", 2)), "source")


def test_invalid_shapes_assumptions_and_dates() -> None:
    with pytest.raises(CoreError, match="immutable_quotes_required"):
        DailyMarketSnapshot(DAYS[0], [], "source")  # type: ignore[arg-type]
    with pytest.raises(CoreError, match="single_position_required"):
        Portfolio((Position(A, 1, 6000, DAYS[0]),))  # type: ignore[arg-type]
    with pytest.raises(CoreError, match="single_target_required"):
        TargetPortfolio((TargetPosition(A, 1),))  # type: ignore[arg-type]
    with pytest.raises(CoreError, match="unsupported_price_model"):
        CloseAssumptions("open", "close")  # type: ignore[arg-type]
    with pytest.raises(CoreError, match="date_only_required"):
        snapshot(datetime(2026, 1, 5), A=1)
    with pytest.raises(CoreError, match="valuation_date_not_before_session"):
        transition_portfolio(
            Portfolio(Position(A, 1, 1, DAYS[0])), target(A), snapshot(DAYS[0], A=2), ASSUMPTIONS
        )


def test_replay_session_shape_order_and_no_partial_success() -> None:
    sessions = oracle_sessions()
    for invalid in ((), tuple(reversed(sessions)), (sessions[0], sessions[0])):
        with pytest.raises(CoreError):
            replay(invalid, choose, 1_200_000, ASSUMPTIONS)
    with pytest.raises(CoreError, match="snapshot_date_mismatch"):
        replay((replace(sessions[0], trade_date=DAYS[1]),), choose, 1_200_000, ASSUMPTIONS)
    calls = []

    def fails(day: date, previous: Portfolio, context: TargetPortfolio) -> TargetPortfolio:
        calls.append(day)
        if day == DAYS[2]:
            raise ValueError("policy failed")
        return choose(day, previous, context)

    with pytest.raises(ValueError, match="policy failed"):
        replay(sessions, fails, 1_200_000, ASSUMPTIONS)
    assert calls == list(DAYS[:3])


def test_resize_and_reference_conflict_including_reentry_are_rejected() -> None:
    previous = Portfolio(Position(A, 1, 6000, DAYS[0]))
    for desired in (target(A, 2), target(B, 2), target(replace(A, multiplier=100))):
        with pytest.raises(CoreError):
            transition_portfolio(previous, desired, snapshot(DAYS[1], A=6120, B=6080), ASSUMPTIONS)
    sessions = oracle_sessions()
    for desired in (target(A, 2), target(replace(A, source_ref="changed"))):
        with pytest.raises(CoreError):
            replay(
                (
                    sessions[0],
                    replace(sessions[1], decision_context=target(None)),
                    replace(sessions[2], decision_context=desired),
                ),
                choose,
                1_200_000,
                ASSUMPTIONS,
            )


def test_accounting_consumes_pnl_once_and_rejects_nonfinite_results() -> None:
    transition = transition_portfolio(Portfolio(), target(None), snapshot(DAYS[0]), ASSUMPTIONS)
    # Deliberately supplied PnL proves Accounting does not re-fetch/recompute prices.
    supplied = replace(transition, daily_pnl=-10)
    state = account(AccountingState.start(5), supplied)
    assert state.cumulative_pnl == -10 and state.equity == -5 and state.cumulative_return == -2
    with pytest.raises(CoreError, match="session_already_accounted"):
        account(state, supplied)
    for bad in (nan, inf):
        with pytest.raises(CoreError):
            account(AccountingState.start(1), replace(transition, daily_pnl=bad))
    with pytest.raises(CoreError):
        account(AccountingState.start(1e308), replace(transition, daily_pnl=1e308))
    previous = Portfolio(Position(InstrumentReference("A", 1e308, "source"), 2, 1, DAYS[0]))
    with pytest.raises(CoreError, match="daily_pnl"):
        transition_portfolio(previous, target(None), snapshot(DAYS[1], A=1e308), ASSUMPTIONS)
