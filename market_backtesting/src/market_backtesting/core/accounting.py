"""Daily and cumulative accounting consume Daily PnL, never prices or targets."""

from .models import AccountingState, CoreError, TransitionResult, finite_number


def account(previous: AccountingState, transition: TransitionResult) -> AccountingState:
    capital = finite_number(previous.initial_capital, "initial_capital", positive=True)
    finite_number(previous.cumulative_pnl, "cumulative_pnl")
    finite_number(previous.equity, "equity")
    finite_number(previous.cumulative_return, "cumulative_return")
    finite_number(previous.daily_return, "daily_return")
    if (
        previous.equity != capital + previous.cumulative_pnl
        or previous.cumulative_return != previous.cumulative_pnl / capital
    ):
        raise CoreError("invalid_accounting", "inconsistent_previous_accounting")
    if previous.trade_date is not None and previous.trade_date >= transition.trade_date:
        raise CoreError("invalid_accounting", "session_already_accounted")
    pnl = finite_number(transition.daily_pnl, "daily_pnl")
    cumulative = finite_number(previous.cumulative_pnl + pnl, "cumulative_pnl")
    equity = finite_number(capital + cumulative, "equity")
    cumulative_return = finite_number(cumulative / capital, "cumulative_return")
    daily_return = finite_number(pnl / capital, "daily_return")
    return AccountingState(
        initial_capital=capital,
        cumulative_pnl=cumulative,
        equity=equity,
        cumulative_return=cumulative_return,
        trade_date=transition.trade_date,
        daily_return=daily_return,
    )
