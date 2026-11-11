"""Daily clock, state handoff and immutable in-memory recording."""

from collections.abc import Callable
from datetime import date

from .accounting import account
from .models import (
    AccountingState,
    CloseAssumptions,
    Context,
    CoreError,
    DailyMarketSnapshot,
    DailyRecord,
    InstrumentReference,
    Portfolio,
    ReplayResult,
    ReplaySession,
    TargetPortfolio,
    require_date,
)
from .transition import transition_portfolio


def replay(
    sessions: tuple[ReplaySession[Context], ...],
    policy: Callable[[date, Portfolio, Context], TargetPortfolio],
    initial_capital: float,
    assumptions: CloseAssumptions,
) -> ReplayResult:
    accounting = AccountingState.start(initial_capital)
    if not isinstance(assumptions, CloseAssumptions):
        raise CoreError("invalid_input", "assumptions_required")
    if not isinstance(sessions, tuple) or not sessions:
        raise CoreError("invalid_input", "nonempty_sessions_required")
    previous_day = None
    for session in sessions:
        if not isinstance(session, ReplaySession):
            raise CoreError("invalid_input", "replay_session_required")
        require_date(session.trade_date)
        if previous_day is not None and previous_day >= session.trade_date:
            raise CoreError("invalid_input", "sessions_not_increasing")
        if not isinstance(session.snapshot, DailyMarketSnapshot):
            raise CoreError("invalid_input", "snapshot_required")
        if session.snapshot.trade_date != session.trade_date:
            raise CoreError("invalid_input", "snapshot_date_mismatch")
        previous_day = session.trade_date
    portfolio = Portfolio()
    records: list[DailyRecord] = []
    quantity = None
    instruments: dict[str, InstrumentReference] = {}
    for session in sessions:
        target = policy(session.trade_date, portfolio, session.decision_context)
        if not isinstance(target, TargetPortfolio):
            raise CoreError(
                "invalid_target", "target_portfolio_required", trade_date=session.trade_date
            )
        if target.position is not None:
            position = target.position
            if quantity is None:
                quantity = position.quantity
            if quantity != position.quantity:
                raise CoreError(
                    "invalid_target", "quantity_change_unsupported", trade_date=session.trade_date
                )
            instrument = position.instrument
            known = instruments.setdefault(instrument.instrument_id, instrument)
            if known != instrument:
                raise CoreError(
                    "invalid_target", "instrument_reference_conflict", trade_date=session.trade_date
                )
        transition = transition_portfolio(portfolio, target, session.snapshot, assumptions)
        accounting = account(accounting, transition)
        records.append(DailyRecord(session.trade_date, transition, accounting))
        portfolio = transition.next_portfolio
    return ReplayResult(initial_capital, assumptions, tuple(records))
