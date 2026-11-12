"""Pure W2 performance analysis; Core remains the only strategy accounting owner."""

from ...core import CoreError
from ...core.models import finite_number
from .failures import FuturesRollError
from .models import (
    PRODUCT_CODES,
    STRATEGY_PROFILES,
    DailyPerformance,
    FuturesRollPerformance,
    FuturesRollReplay,
    PerformanceSummary,
)
from .validation import _fail, _validate_index_closes, _validate_sessions


def _number(value: float, name: str, *, positive: bool = False) -> float:
    try:
        return finite_number(value, name, positive=positive)
    except CoreError as exc:
        raise FuturesRollError("accounting_failure", exc.reason) from exc


def analyze_futures_roll(result: FuturesRollReplay) -> FuturesRollPerformance:
    """Project completed Core records and calculate only benchmark/excess/drawdown."""
    if not isinstance(result, FuturesRollReplay):
        _fail("invalid_case_input", "invalid_replay_result")
    sessions = _validate_sessions(result.sessions)
    index = _validate_index_closes(sessions, result.index_closes)
    records = result.replay.daily
    if (
        not isinstance(records, tuple)
        or tuple(row.trade_date for row in records) != sessions
        or tuple(row.trade_date for row in result.daily) != sessions
        or any(
            row.accounting.trade_date != row.trade_date
            or row.transition.trade_date != row.trade_date
            for row in records
        )
    ):
        _fail("invalid_case_input", "accounting_session_mismatch")
    if (
        result.product_code not in PRODUCT_CODES
        or result.strategy_profile not in STRATEGY_PROFILES
        or not isinstance(result.benchmark_index_code, str)
        or not result.benchmark_index_code.strip()
    ):
        _fail("invalid_case_input", "invalid_performance_identity")
    if result.replay.final_portfolio.position is not None:
        _fail("invalid_position_state", "final_state_not_flat")
    entry = records[0].target.position
    if entry is None or records[0].previous_portfolio.position is not None:
        _fail("invalid_position_state", "missing_entry_target")
    multiplier = _number(entry.instrument.multiplier, "entry_multiplier", positive=True)
    capital = _number(result.replay.initial_capital, "initial_capital", positive=True)
    first_close = index[0].close
    expected_capital = _number(first_close * multiplier, "initial_notional", positive=True)
    if capital != expected_capital:
        _fail("accounting_failure", "initial_capital_mismatch")
    strategy_peak = benchmark_peak = capital
    previous_close = first_close
    daily: list[DailyPerformance] = []
    for record, quote in zip(records, index, strict=True):
        accounting = record.accounting
        if _number(accounting.initial_capital, "initial_capital", positive=True) != capital:
            _fail("accounting_failure", "initial_capital_mismatch", trade_date=record.trade_date)
        for name, value in (
            ("daily_pnl", record.transition.daily_pnl),
            ("cumulative_pnl", accounting.cumulative_pnl),
            ("equity", accounting.equity),
            ("daily_return", accounting.daily_return),
            ("cumulative_return", accounting.cumulative_return),
        ):
            _number(value, name)
        benchmark_return = _number(quote.close / first_close - 1, "benchmark_cumulative_return")
        benchmark_daily = _number(quote.close / previous_close - 1, "benchmark_daily_return")
        benchmark_equity = _number(capital * (1 + benchmark_return), "benchmark_equity")
        if accounting.equity <= 0 or benchmark_equity <= 0:
            _fail("accounting_failure", "non_positive_equity", trade_date=record.trade_date)
        strategy_peak = max(strategy_peak, accounting.equity)
        benchmark_peak = max(benchmark_peak, benchmark_equity)
        daily.append(
            DailyPerformance(
                trade_date=record.trade_date,
                daily_pnl=record.transition.daily_pnl,
                cumulative_pnl=accounting.cumulative_pnl,
                equity=accounting.equity,
                daily_return=accounting.daily_return,
                cumulative_return=accounting.cumulative_return,
                benchmark_close=quote.close,
                benchmark_daily_return=benchmark_daily,
                benchmark_cumulative_return=benchmark_return,
                benchmark_equity=benchmark_equity,
                excess_cumulative_return=_number(
                    accounting.cumulative_return - benchmark_return, "excess_cumulative_return"
                ),
                drawdown=_number(accounting.equity / strategy_peak - 1, "drawdown"),
                benchmark_drawdown=_number(
                    benchmark_equity / benchmark_peak - 1, "benchmark_drawdown"
                ),
            )
        )
        previous_close = quote.close
    final = daily[-1]
    return FuturesRollPerformance(
        product_code=result.product_code,
        strategy_profile=result.strategy_profile,
        benchmark_index_code=result.benchmark_index_code,
        entry_multiplier=multiplier,
        daily=tuple(daily),
        summary=PerformanceSummary(
            initial_notional=capital,
            total_pnl=final.cumulative_pnl,
            gross_return=final.cumulative_return,
            benchmark_return=final.benchmark_cumulative_return,
            excess_return=final.excess_cumulative_return,
            strategy_max_drawdown=min(row.drawdown for row in daily),
            benchmark_max_drawdown=min(row.benchmark_drawdown for row in daily),
        ),
    )
