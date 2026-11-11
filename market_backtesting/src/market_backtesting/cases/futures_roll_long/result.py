"""Formal result projection; no replay, analyzer invocation or market lookup."""

from dataclasses import asdict

from .application_models import FuturesRollExecution
from .result_models import (
    DEFINITION_VERSION,
    LIMITATIONS,
    RESULT_PROFILE,
    BacktestResult,
    Benchmark,
    CoverageEvidence,
    EvidenceSummary,
    InitialNotional,
    ObservedWindow,
    ResultDaily,
    ResultSummary,
    ResultViews,
    SourceIdentity,
    Trade,
)
from .visualization import build_view

SLOT_AUTHORITY = "market_research/descriptive/cases/futures_basis/SLOT_RESOLUTION.md"


def _project_result(execution: FuturesRollExecution) -> BacktestResult:
    replay, performance, inputs = execution.replay, execution.performance, execution.inputs
    daily = []
    trades = []
    for record, identities, measures in zip(
        replay.replay.daily, replay.daily, performance.daily, strict=True
    ):
        transition = record.transition
        pricing = transition.pricing
        daily.append(
            ResultDaily(
                **asdict(measures),
                position_contract_code=identities.position_contract_code,
                pnl_contract_code=identities.pnl_contract_code,
                previous_close=pricing.previous_reference if pricing else None,
                close=pricing.current_close if pricing else transition.position_changes[0].price,
            )
        )
    legs = tuple(
        (record.trade_date, event)
        for record in replay.replay.daily
        for event in record.transition.position_changes
    )
    for (day, event), execution_leg in zip(legs, replay.executions, strict=True):
        position = event.after if event.kind == "open" else event.before
        if position is None:
            from .failures import FuturesRollError

            raise FuturesRollError("invalid_result", "missing_execution_position")
        trades.append(
            Trade(
                day,
                execution_leg.side,
                position.instrument.instrument_id,
                event.price,
                position.instrument.multiplier,
                execution_leg.reason,
                execution_leg.selection_slot,
            )
        )
    exports = tuple(getattr(inputs.exports, key) for key in ("calendar_cffex", "futures", "index"))
    evidence = EvidenceSummary(
        inputs.fingerprint_profile,
        inputs.input_fingerprint,
        inputs.public_requests,
        tuple(
            CoverageEvidence(key, **asdict(export.coverage))
            for key, export in zip(("calendar_cffex", "futures", "index"), exports, strict=True)
        ),
        tuple(
            SourceIdentity(export.dataset, export.view, export.export_schema_version)
            for export in exports
        ),
        SLOT_AUTHORITY,
        DEFINITION_VERSION,
        RESULT_PROFILE,
        LIMITATIONS,
    )
    return BacktestResult(
        RESULT_PROFILE,
        "futures_roll_long_v1",
        DEFINITION_VERSION,
        "complete",
        execution.request,
        ObservedWindow(replay.sessions[0], replay.sessions[-1], len(replay.sessions)),
        Benchmark(
            replay.benchmark_index_code,
            inputs.exports.index.records[0].name,
            performance.daily[0].benchmark_close,
            performance.daily[-1].benchmark_close,
        ),
        InitialNotional(
            performance.daily[0].benchmark_close,
            performance.entry_multiplier,
            "CNY",
            performance.summary.initial_notional,
        ),
        tuple(daily),
        tuple(trades),
        replay.rolls,
        ResultSummary(
            **asdict(performance.summary), execution_count=len(trades), roll_count=len(replay.rolls)
        ),
        evidence,
        ResultViews(
            build_view(performance.daily, replay, drawdown=False),
            build_view(performance.daily, replay, drawdown=True),
        ),
    )


def build_backtest_result(execution: FuturesRollExecution) -> BacktestResult:
    from .result_validation import validate_backtest_result, validate_execution

    validate_execution(execution)
    result = _project_result(execution)
    validate_backtest_result(result, execution)
    return result
