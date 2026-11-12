"""Independent acceptance of fixed-capital daily accounting, including invalid arithmetic."""

from dataclasses import FrozenInstanceError, replace
from datetime import date
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
    ReplayResult,
    ReplaySession,
    TargetPortfolio,
    TargetPosition,
    TransitionResult,
    account,
    replay,
    transition_portfolio,
)

ASSUMPTIONS = CloseAssumptions("session_close", "session_close")
A = InstrumentReference("A", 2, "independent-A")
B = InstrumentReference("B", 2, "independent-B")


def accounting_run() -> ReplayResult:
    days = tuple(date(2026, 1, day) for day in range(5, 11))
    desired = (None, A, A, B, B, None)
    quotes: tuple[dict[str, float], ...] = (
        {},
        {"A": 100},
        {"A": 110},
        {"A": 105, "B": 200},
        {"B": 200},
        {"B": 190},
    )
    sessions = tuple(
        ReplaySession(
            day,
            TargetPortfolio(TargetPosition(instrument, 1) if instrument else None),
            DailyMarketSnapshot(
                day, tuple(CloseQuote(code, price) for code, price in prices.items()), "oracle"
            ),
        )
        for day, instrument, prices in zip(days, desired, quotes, strict=True)
    )
    return replay(sessions, lambda _day, _previous, target: target, 1000, ASSUMPTIONS)


def flat_transition() -> TransitionResult:
    return transition_portfolio(
        Portfolio(),
        TargetPortfolio(),
        DailyMarketSnapshot(date(2026, 1, 5), (), "flat-oracle"),
        ASSUMPTIONS,
    )


def test_initial_state_and_immutable_daily_return() -> None:
    state = AccountingState.start(1000)
    assert state.daily_return == state.cumulative_return == state.cumulative_pnl == 0
    assert state.initial_capital == state.equity == 1000
    with pytest.raises(FrozenInstanceError):
        state.daily_return = 1  # type: ignore[misc]
    # Existing positional arguments keep their meaning.
    assert AccountingState(1000, 0, 1000, 0, None).daily_return == 0


def test_flat_entry_positive_roll_zero_and_negative_returns() -> None:
    result = accounting_run()
    assert [row.transition.daily_pnl for row in result.daily] == [0, 0, 20, -10, 0, -20]
    assert [row.accounting.daily_return for row in result.daily] == [0, 0, 0.02, -0.01, 0, -0.02]
    assert [row.accounting.cumulative_pnl for row in result.daily] == [0, 0, 20, 10, 10, -10]
    assert [row.accounting.equity for row in result.daily] == [1000, 1000, 1020, 1010, 1010, 990]
    assert sum(row.accounting.daily_return for row in result.daily) == pytest.approx(
        result.daily[-1].accounting.cumulative_return, rel=0, abs=1e-15
    )
    assert all(row.accounting.initial_capital == 1000 for row in result.daily)
    roll = result.daily[3]
    assert roll.next_portfolio.position is not None
    assert roll.next_portfolio.position.reference_price == 200
    assert roll.accounting.daily_return != roll.transition.daily_pnl / 1020
    assert result.final_portfolio.position is None


@pytest.mark.parametrize("value", (True, "1", None, nan, inf, -inf, 10**400))
def test_non_numeric_and_nonfinite_daily_pnl(value: Any) -> None:
    with pytest.raises(CoreError, match="daily_pnl"):
        account(AccountingState.start(1000), replace(flat_transition(), daily_pnl=value))


@pytest.mark.parametrize(
    "field", ("initial_capital", "cumulative_pnl", "equity", "daily_return", "cumulative_return")
)
@pytest.mark.parametrize("value", (nan, inf, -inf, True, "1"))
def test_invalid_previous_accounting(field: str, value: Any) -> None:
    with pytest.raises(CoreError, match=field):
        account(replace(AccountingState.start(1000), **{field: value}), flat_transition())


@pytest.mark.parametrize("capital", (0, -1, True, nan, inf, -inf, "1", 10**400))
def test_invalid_initial_capital(capital: Any) -> None:
    with pytest.raises(CoreError):
        AccountingState.start(capital)


def test_daily_return_overflow_is_rejected_even_when_cumulative_return_is_finite() -> None:
    capital = 1e-308
    previous = AccountingState(capital, -1, capital - 1, -1 / capital)
    with pytest.raises(CoreError, match="daily_return"):
        account(previous, replace(flat_transition(), daily_pnl=2))


def test_cumulative_and_equity_overflow_are_rejected() -> None:
    previous = AccountingState(1, 1e308, 1e308, 1e308)
    with pytest.raises(CoreError, match="cumulative_pnl"):
        account(previous, replace(flat_transition(), daily_pnl=1e308))
    with pytest.raises(CoreError, match="equity"):
        account(AccountingState.start(1e308), replace(flat_transition(), daily_pnl=1e308))
