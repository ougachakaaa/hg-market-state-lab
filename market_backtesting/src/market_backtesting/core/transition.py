"""The single implementation of close-to-close position transition and Daily PnL."""

from dataclasses import replace

from .models import (
    CloseAssumptions,
    CoreError,
    DailyMarketSnapshot,
    Portfolio,
    Position,
    PricingEvidence,
    StateEvent,
    TargetPortfolio,
    TransitionResult,
    finite_number,
)


def transition_portfolio(
    previous: Portfolio,
    target: TargetPortfolio,
    snapshot: DailyMarketSnapshot,
    assumptions: CloseAssumptions,
) -> TransitionResult:
    if not isinstance(previous, Portfolio) or not isinstance(target, TargetPortfolio):
        raise CoreError("invalid_input", "portfolio_required")
    if not isinstance(snapshot, DailyMarketSnapshot) or not isinstance(
        assumptions, CloseAssumptions
    ):
        raise CoreError("invalid_input", "snapshot_and_assumptions_required")
    held, desired = previous.position, target.position
    day = snapshot.trade_date
    if held is not None and held.valuation_date >= day:
        raise CoreError("invalid_input", "valuation_date_not_before_session", trade_date=day)
    if held is not None and desired is not None:
        if held.quantity != desired.quantity:
            raise CoreError("invalid_target", "quantity_change_unsupported", trade_date=day)
        if (
            held.instrument.instrument_id == desired.instrument.instrument_id
            and held.instrument != desired.instrument
        ):
            raise CoreError("invalid_target", "instrument_reference_conflict", trade_date=day)
    # Validate all required prices before producing a transition.
    old_close = snapshot.close_for(held.instrument.instrument_id) if held else None
    new_close = snapshot.close_for(desired.instrument.instrument_id) if desired else None
    events: list[StateEvent] = []
    pricing = None
    daily_pnl = 0.0
    current = held
    if held is not None and old_close is not None:
        pricing = PricingEvidence(held.instrument, held.quantity, held.reference_price, old_close)
        daily_pnl = finite_number(
            (old_close - held.reference_price) * held.quantity * held.instrument.multiplier,
            "daily_pnl",
        )
        current = replace(held, reference_price=old_close, valuation_date=day)
        events.append(StateEvent("mark", held, current, old_close))
    same = held is not None and desired is not None and held.instrument == desired.instrument
    if not same:
        if current is not None and old_close is not None:
            events.append(StateEvent("close", current, None, old_close))
            current = None
        if desired is not None and new_close is not None:
            current = Position(desired.instrument, desired.quantity, new_close, day)
            events.append(StateEvent("open", None, current, new_close))
    return TransitionResult(
        day,
        previous,
        target,
        snapshot,
        assumptions,
        daily_pnl,
        pricing,
        tuple(events),
        Portfolio(current),
    )
