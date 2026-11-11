"""Cross-field checks over recorded evidence, never a second calculation engine."""

from dataclasses import fields, is_dataclass
from datetime import date
from math import isfinite
from typing import Any, NoReturn, cast

from .application_models import FuturesRollExecution, validate_futures_roll_request
from .failures import FuturesRollError
from .fingerprint import input_fingerprint
from .input_validation import validate_calendar, validate_futures, validate_index
from .public_inputs import build_replay_input
from .result_models import DEFINITION_VERSION, BacktestResult
from .visualization import validate_view_v2


def fail(reason: str) -> NoReturn:
    raise FuturesRollError("invalid_result", reason)


def require(condition: bool, reason: str) -> None:
    if not condition:
        fail(reason)


def immutable_finite(value: Any) -> None:
    """Reject mutable descendants, bool numeric substitution and nonfinite numbers."""
    if is_dataclass(value) and not isinstance(value, type):
        require(cast(Any, value).__dataclass_params__.frozen, "immutable_evidence_required")
        for f in fields(value):
            item = getattr(value, f.name)
            if f.type in (float, float | None, "float", "float | None") and item is not None:
                require(type(item) in (int, float), "invalid_numeric_type")
            immutable_finite(item)
    elif isinstance(value, tuple):
        for item in value:
            immutable_finite(item)
    elif type(value) in (float, int):
        try:
            require(isfinite(value), "nonfinite_output")
        except OverflowError:
            fail("nonfinite_output")
    elif value is not None and type(value) not in (str, int, bool, date):
        fail("immutable_evidence_required")


def validate_execution(execution: FuturesRollExecution) -> None:
    require(isinstance(execution, FuturesRollExecution), "invalid_execution")
    # Acquisition diagnostics may carry raw Source errors and are deliberately excluded.
    inputs, replay, performance = execution.inputs, execution.replay, execution.performance
    for value in (
        inputs.exports,
        inputs.index_calendar_export,
        inputs.replay_input,
        replay,
        performance,
    ):
        immutable_finite(value)
    validate_futures_roll_request(execution.request)
    require(inputs.request == execution.request, "request_mismatch")
    require(inputs.definition_version == DEFINITION_VERSION, "definition_version_mismatch")
    require(inputs.fingerprint_profile == "futures_roll_long_inputs_v1", "input_profile_mismatch")
    sessions = validate_calendar(inputs.exports.calendar_cffex, execution.request)
    sse = validate_calendar(inputs.index_calendar_export, execution.request, exchange="SSE")
    require(len(sessions) >= 2, "insufficient_sessions")
    underlying = validate_futures(inputs.exports.futures, execution.request, sessions)
    require(underlying is not None, "missing_underlying")
    assert underlying is not None
    validate_index(inputs.exports.index, execution.request, sessions, underlying, sse)
    for export in (
        inputs.exports.calendar_cffex,
        inputs.exports.futures,
        inputs.exports.index,
        inputs.index_calendar_export,
    ):
        require(export.coverage.complete, "incomplete_input")
    fingerprint = input_fingerprint(inputs.exports)
    require(fingerprint == inputs.input_fingerprint, "fingerprint_mismatch")
    require(
        inputs.replay_input == build_replay_input(execution.request, inputs.exports, fingerprint),
        "replay_input_mismatch",
    )
    request = execution.request
    for public, identity_field, expected_identity in (
        (inputs.public_requests.calendar_cffex, "exchange", "CFFEX"),
        (inputs.public_requests.futures, "product_codes", (request.product_code,)),
        (inputs.public_requests.index, "index_codes", (underlying,)),
        (inputs.index_calendar_request, "exchange", "SSE"),
    ):
        require(
            getattr(public, identity_field) == expected_identity
            and (public.start_date, public.end_date) == (request.start_date, request.end_date),
            "public_request_mismatch",
        )
    require(
        replay.sessions == sessions
        and (execution.observed_start_date, execution.observed_end_date)
        == (sessions[0], sessions[-1]),
        "observed_window_mismatch",
    )
    require(
        replay.product_code == performance.product_code == request.product_code
        and replay.strategy_profile == performance.strategy_profile == request.strategy_profile
        and replay.benchmark_index_code == performance.benchmark_index_code == underlying,
        "execution_identity_mismatch",
    )
    require(replay.index_closes == inputs.replay_input.index_closes, "index_association_mismatch")
    records = replay.replay.daily
    require(
        all(
            tuple(row.trade_date for row in rows) == sessions
            for rows in (records, replay.daily, performance.daily)
        ),
        "daily_session_mismatch",
    )
    require(records[-1].next_portfolio.position is None, "final_state_not_flat")
    previous = None
    legs = []
    rolls = []
    for i, (record, identity, day) in enumerate(
        zip(records, replay.daily, performance.daily, strict=True)
    ):
        t, a = record.transition, record.accounting
        facts = inputs.replay_input.session_facts[i]
        source = inputs.replay_input.decision_slots[i].evidence.source_export_ref
        require(
            t.snapshot.trade_date == record.trade_date
            and tuple((q.instrument_id, q.close) for q in t.snapshot.quotes)
            == tuple((q.contract_code, q.close) for q in facts.closes)
            and t.snapshot.source_ref == source,
            "snapshot_association_mismatch",
        )
        require(
            t.target.evidence is not None
            and t.target.evidence.source_ref
            == (
                t.previous_portfolio.position.instrument.source_ref
                if t.previous_portfolio.position is not None
                and t.target.evidence.reason in ("hold", "study_end_close")
                else source
            ),
            "policy_source_mismatch",
        )
        require(
            t.assumptions == replay.replay.assumptions
            and t.assumptions.execution == t.assumptions.valuation == "session_close",
            "assumptions_mismatch",
        )
        for position in (t.previous_portfolio.position, t.next_portfolio.position):
            if position is not None:
                require(
                    position.instrument in inputs.replay_input.instrument_refs,
                    "instrument_reference_mismatch",
                )
        require(t.trade_date == a.trade_date == record.trade_date, "record_date_mismatch")
        require(t.previous_portfolio.position == previous, "portfolio_chain_mismatch")
        current = previous
        expected_kinds = [] if previous is None else ["mark"]
        target = t.target.position
        changing = previous is not None and (
            target is None or target.instrument.instrument_id != previous.instrument.instrument_id
        )
        if changing:
            expected_kinds.append("close")
        if target is not None and (previous is None or changing):
            expected_kinds.append("open")
        require([e.kind for e in t.events] == expected_kinds, "state_event_order_mismatch")
        for event in t.events:
            require(event.before == current, "state_event_before_mismatch")
            position = event.after if event.kind != "close" else event.before
            require(position is not None, "missing_event_position")
            assert position is not None
            require(
                event.price == t.snapshot.close_for(position.instrument.instrument_id),
                "event_price_mismatch",
            )
            if event.kind != "close":
                require(
                    position.reference_price == event.price
                    and position.valuation_date == record.trade_date,
                    "event_reference_mismatch",
                )
            if event.kind == "mark":
                require(
                    event.before is not None
                    and event.after is not None
                    and event.before.instrument == event.after.instrument
                    and event.before.quantity == event.after.quantity,
                    "mark_identity_mismatch",
                )
            elif event.kind == "close":
                require(event.after is None, "close_state_mismatch")
            else:
                require(
                    event.before is None
                    and target is not None
                    and position.instrument == target.instrument
                    and position.quantity == target.quantity,
                    "open_target_mismatch",
                )
            current = event.after
        require(current == t.next_portfolio.position, "state_reconstruction_mismatch")
        require(
            (target is None and current is None)
            or (
                target is not None
                and current is not None
                and target.instrument == current.instrument
                and target.quantity == current.quantity == 1
            ),
            "target_state_mismatch",
        )
        pnl_position = previous if previous is not None else current
        require(pnl_position is not None, "missing_pnl_position")
        assert pnl_position is not None
        require(
            identity.pnl_contract_code == pnl_position.instrument.instrument_id
            and identity.position_contract_code
            == (current.instrument.instrument_id if current else None),
            "contract_attribution_mismatch",
        )
        if previous is None:
            require(i == 0 and t.pricing is None and t.daily_pnl == 0, "entry_row_mismatch")
        else:
            p = t.pricing
            require(p is not None, "missing_pricing")
            assert p is not None
            require(
                p.instrument == previous.instrument
                and p.quantity == previous.quantity
                and p.previous_reference == previous.reference_price
                and p.current_close == t.events[0].price,
                "pricing_association_mismatch",
            )
        for name in ("cumulative_pnl", "equity", "daily_return", "cumulative_return"):
            require(
                type(getattr(a, name)) in (int, float) and getattr(day, name) == getattr(a, name),
                "accounting_projection_mismatch",
            )
        require(
            type(t.daily_pnl) in (int, float) and day.daily_pnl == t.daily_pnl,
            "pnl_projection_mismatch",
        )
        require(
            a.initial_capital
            == replay.replay.initial_capital
            == performance.summary.initial_notional,
            "capital_mismatch",
        )
        require(a.equity > 0 and day.benchmark_equity > 0, "non_positive_equity")
        require(
            day.benchmark_close == replay.index_closes[i].close
            and day.drawdown <= 0
            and day.benchmark_drawdown <= 0,
            "performance_association_mismatch",
        )
        evidence = t.target.evidence
        require(evidence is not None, "missing_decision")
        assert evidence is not None
        reason = (
            "entry"
            if i == 0
            else "study_end_close"
            if i == len(records) - 1
            else ("expiry" if changing and target else "hold")
        )
        require(evidence.reason == reason, "decision_reason_mismatch")
        for event in t.position_changes:
            position = event.after if event.kind == "open" else event.before
            assert position is not None
            leg_reason = (
                ("expiry_open" if event.kind == "open" else "expiry_close")
                if reason == "expiry"
                else reason
            )
            legs.append(
                (
                    record.trade_date,
                    "BUY" if event.kind == "open" else "SELL",
                    position.instrument.instrument_id,
                    event.price,
                    leg_reason,
                    evidence.selection_role if event.kind == "open" else None,
                )
            )
        if reason == "expiry":
            require(
                evidence.previous_role == "M0"
                and evidence.selection_role
                == ("M1" if request.strategy_profile == "expiry_to_M1_v1" else "Q1"),
                "roll_slot_mismatch",
            )
            assert previous is not None and current is not None
            old = next(
                row
                for row in inputs.exports.futures.records
                if row.trade_date == record.trade_date
                and row.contract_code == previous.instrument.instrument_id
            )
            require(old.delist_date == record.trade_date, "roll_expiry_mismatch")
            rolls.append(
                (
                    record.trade_date,
                    previous.instrument.instrument_id,
                    "M0",
                    t.position_changes[0].price,
                    current.instrument.instrument_id,
                    evidence.selection_role,
                    t.position_changes[1].price,
                    "expiry",
                )
            )
        if i == 0:
            require(
                evidence.selection_role == "M1"
                and day.cumulative_pnl
                == day.daily_return
                == day.cumulative_return
                == day.benchmark_daily_return
                == day.benchmark_cumulative_return
                == day.excess_cumulative_return
                == 0,
                "entry_values_mismatch",
            )
        previous = current
    require(
        legs == [tuple(getattr(e, f.name) for f in fields(e)) for e in replay.executions],
        "execution_projection_mismatch",
    )
    require(
        rolls == [tuple(getattr(e, f.name) for f in fields(e)) for e in replay.rolls],
        "roll_projection_mismatch",
    )
    require(len(legs) == 2 + 2 * len(rolls), "execution_count_mismatch")
    s, final = performance.summary, performance.daily[-1]
    # RESULT.md Σ uses Core's chronological binary64 order. Python 3.13 sum()
    # compensates floating additions and can differ from the recorded accumulation.
    ordered_pnl_sum = 0.0
    for record in records:
        ordered_pnl_sum += record.transition.daily_pnl
    require(
        s.total_pnl == final.cumulative_pnl == ordered_pnl_sum,
        "total_pnl_mismatch",
    )
    require(
        (s.gross_return, s.benchmark_return, s.excess_return)
        == (
            final.cumulative_return,
            final.benchmark_cumulative_return,
            final.excess_cumulative_return,
        ),
        "summary_return_mismatch",
    )
    require(
        s.strategy_max_drawdown == min(d.drawdown for d in performance.daily)
        and s.benchmark_max_drawdown == min(d.benchmark_drawdown for d in performance.daily),
        "summary_drawdown_mismatch",
    )
    entry = records[0].next_portfolio.position
    assert entry is not None
    require(
        performance.entry_multiplier == entry.instrument.multiplier, "entry_multiplier_mismatch"
    )


def validate_backtest_result(result: BacktestResult, execution: FuturesRollExecution) -> None:
    from .result import _project_result

    validate_execution(execution)
    require(isinstance(result, BacktestResult), "invalid_result_type")
    immutable_finite(result)
    validate_view_v2(result.views.returns)
    validate_view_v2(result.views.drawdown)
    # Compare all fields with a direct evidence projection, not financial recomputation.
    require(result == _project_result(execution), "result_projection_mismatch")
