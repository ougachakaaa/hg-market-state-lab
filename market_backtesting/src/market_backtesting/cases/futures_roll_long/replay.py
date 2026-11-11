"""W2 input adapter and projections over the single Core execution path."""

from datetime import date
from typing import cast

from ...core import (
    CloseAssumptions,
    CloseQuote,
    CoreError,
    DailyMarketSnapshot,
    InstrumentReference,
    Portfolio,
    ReplaySession,
    TargetPortfolio,
    replay,
)
from ...core.models import finite_number
from .failures import FuturesRollError
from .models import (
    DailyProjection,
    DecisionContext,
    Execution,
    ExecutionReason,
    FuturesRollInput,
    FuturesRollReplay,
    RollEvent,
    SelectionSlot,
    Slot,
)
from .policy import MechanicalRollPolicy
from .validation import _fail, _validate_inputs


def replay_futures_roll(inputs: FuturesRollInput) -> FuturesRollReplay:
    """No I/O, benchmark analyzer, full BacktestResult or partial-success return."""
    validated = _validate_inputs(inputs)
    if not isinstance(inputs.instrument_refs, tuple):
        _fail("invalid_contract_lifecycle", "invalid_instrument_references")
    references: dict[str, InstrumentReference] = {}
    for ref in inputs.instrument_refs:
        if not isinstance(ref, InstrumentReference):
            _fail("invalid_contract_lifecycle", "invalid_instrument_references")
        if ref.instrument_id in references:
            _fail(
                "invalid_contract_lifecycle",
                "duplicate_instrument_reference",
                contract_code=ref.instrument_id,
            )
        references[ref.instrument_id] = ref
    if references.keys() != validated.metadata.keys():
        _fail("invalid_contract_lifecycle", "instrument_reference_scope_mismatch")
    policy = MechanicalRollPolicy(validated.product_code, validated.strategy_profile)
    sessions = tuple(
        ReplaySession(
            day,
            DecisionContext(
                index == 0,
                index == len(validated.sessions) - 1,
                tuple(c for c in validated.metadata.values() if c.list_date <= day),
                tuple(
                    ref
                    for ref in inputs.instrument_refs
                    if validated.metadata[ref.instrument_id].list_date <= day
                ),
                validated.decision_evidence.get(day),
            ),
            DailyMarketSnapshot(
                day,
                tuple(CloseQuote(code, close) for code, close in validated.facts[day].items()),
                (
                    validated.decision_evidence[day].source_export_ref
                    if day in validated.decision_evidence
                    else f"synthetic-close:{day.isoformat()}"
                ),
            ),
        )
        for index, day in enumerate(validated.sessions)
    )
    try:
        # Resolve the initial target without prices to derive the W2 denominator;
        # Replay invokes Policy on every session and remains the only executor.
        entry = policy(sessions[0].trade_date, Portfolio(), sessions[0].decision_context)
        if entry.position is None:
            _fail("invalid_position_state", "missing_entry_target")
        initial_close = validated.index_closes[0].close
        capital = finite_number(
            initial_close * entry.position.instrument.multiplier, "initial_capital", positive=True
        )

        def decide(day: date, previous: Portfolio, context: DecisionContext) -> TargetPortfolio:
            # Reuse the price-free entry decision used for capital derivation.
            return entry if context.is_first else policy(day, previous, context)

        result = replay(
            sessions, decide, capital, CloseAssumptions("session_close", "session_close")
        )
    except CoreError as exc:
        raise FuturesRollError(
            exc.category,
            "missing_contract_row" if exc.reason == "missing_instrument_quote" else exc.reason,
            trade_date=exc.trade_date,
            contract_code=exc.instrument_id,
            detail=exc.detail,
        ) from exc
    if any(record.accounting.equity <= 0 for record in result.daily):
        _fail("accounting_failure", "non_positive_equity")
    daily: list[DailyProjection] = []
    executions: list[Execution] = []
    rolls: list[RollEvent] = []
    for record in result.daily:
        transition = record.transition
        held = transition.previous_portfolio.position
        next_position = transition.next_portfolio.position
        pnl_position = held if held is not None else next_position
        if pnl_position is None:
            _fail("invalid_position_state", "missing_daily_position", trade_date=record.trade_date)
        daily.append(
            DailyProjection(
                record.trade_date,
                pnl_position.instrument.instrument_id,
                next_position.instrument.instrument_id if next_position else None,
            )
        )
        evidence = record.target.evidence
        if evidence is None:
            _fail("invalid_position_state", "missing_decision_evidence")
        for event in transition.position_changes:
            is_open = event.kind == "open"
            position = event.after if is_open else event.before
            assert position is not None
            reason: ExecutionReason = (
                ("expiry_open" if is_open else "expiry_close")
                if evidence.reason == "expiry"
                else cast(ExecutionReason, evidence.reason)
            )
            executions.append(
                Execution(
                    record.trade_date,
                    "BUY" if is_open else "SELL",
                    position.instrument.instrument_id,
                    event.price,
                    reason,
                    cast(SelectionSlot, evidence.selection_role) if is_open else None,
                )
            )
        if evidence.reason == "expiry":
            close_event, open_event = transition.position_changes
            assert held is not None and next_position is not None
            rolls.append(
                RollEvent(
                    record.trade_date,
                    held.instrument.instrument_id,
                    cast(Slot, evidence.previous_role),
                    close_event.price,
                    next_position.instrument.instrument_id,
                    cast(SelectionSlot, evidence.selection_role),
                    open_event.price,
                    "expiry",
                )
            )
    if result.final_portfolio.position is not None:
        _fail("invalid_position_state", "final_state_not_flat")
    return FuturesRollReplay(
        validated.product_code,
        validated.strategy_profile,
        validated.sessions,
        tuple(daily),
        tuple(executions),
        tuple(rolls),
        result,
        next(iter(validated.metadata.values())).underlying_index_code,
        validated.index_closes,
    )
