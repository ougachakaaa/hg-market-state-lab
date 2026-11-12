"""Independent five-session financial oracles and strict Analyzer boundary acceptance."""

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime
from math import inf, isfinite, nan
from typing import Any

import pytest

from futures_roll_fixtures import performance_oracle_input, set_contract_close, simple_input
from market_backtesting.cases.futures_roll_long import (
    FuturesRollError,
    FuturesRollReplay,
    IndexClose,
    analyze_futures_roll,
    replay_futures_roll,
)


@pytest.mark.parametrize(
    ("profile", "pnl", "cumulative", "equity", "gross", "excess", "strategy_mdd", "new_code"),
    (
        (
            "expiry_to_M1_v1",
            (0, 10000, 10000, 4000, -2000),
            (0, 10000, 20000, 24000, 22000),
            (1200000, 1210000, 1220000, 1224000, 1222000),
            22000 / 1200000,
            22000 / 1200000 - 0.0125,
            -2000 / 1224000,
            "IM2603.CFX",
        ),
        (
            "expiry_to_Q1_v1",
            (0, 10000, 10000, 1000, -2000),
            (0, 10000, 20000, 21000, 19000),
            (1200000, 1210000, 1220000, 1221000, 1219000),
            19000 / 1200000,
            19000 / 1200000 - 0.0125,
            -2000 / 1221000,
            "IM2606.CFX",
        ),
    ),
)
def test_independent_five_session_oracle(
    profile: str,
    pnl: tuple[int, ...],
    cumulative: tuple[int, ...],
    equity: tuple[int, ...],
    gross: float,
    excess: float,
    strategy_mdd: float,
    new_code: str,
) -> None:
    inputs = performance_oracle_input(profile)
    replay = replay_futures_roll(inputs)
    result = analyze_futures_roll(replay)
    assert replay.index_closes is inputs.index_closes
    assert result.product_code == "IM"
    assert result.strategy_profile == profile
    assert result.benchmark_index_code == "000852.SH"
    assert result.entry_multiplier == 200
    assert tuple(row.trade_date for row in result.daily) == inputs.sessions
    assert tuple(row.daily_pnl for row in result.daily) == pnl
    assert tuple(row.cumulative_pnl for row in result.daily) == cumulative
    assert tuple(row.equity for row in result.daily) == equity
    assert [row.daily_return for row in result.daily] == pytest.approx(
        [value / 1200000 for value in pnl], rel=0, abs=1e-15
    )
    assert [row.cumulative_return for row in result.daily] == pytest.approx(
        [value / 1200000 for value in cumulative], rel=0, abs=1e-15
    )
    assert [row.benchmark_close for row in result.daily] == [6000, 6060, 6030, 6090, 6075]
    assert [row.benchmark_cumulative_return for row in result.daily] == pytest.approx(
        [0, 0.01, 0.005, 0.015, 0.0125], rel=0, abs=1e-15
    )
    assert [row.benchmark_daily_return for row in result.daily] == pytest.approx(
        [0, 60 / 6000, -30 / 6060, 60 / 6030, -15 / 6090], rel=0, abs=1e-15
    )
    assert [row.benchmark_equity for row in result.daily] == pytest.approx(
        [1200000, 1212000, 1206000, 1218000, 1215000], rel=0, abs=1e-9
    )
    assert [row.drawdown for row in result.daily] == pytest.approx(
        [0, 0, 0, 0, strategy_mdd], rel=0, abs=1e-15
    )
    assert [row.benchmark_drawdown for row in result.daily] == pytest.approx(
        [0, 0, -6000 / 1212000, 0, -3000 / 1218000], rel=0, abs=1e-15
    )
    for row, core in zip(result.daily, replay.replay.daily, strict=True):
        assert row.daily_pnl == core.transition.daily_pnl
        for field in ("cumulative_pnl", "equity", "daily_return", "cumulative_return"):
            assert getattr(row, field) == getattr(core.accounting, field)
        assert (
            row.excess_cumulative_return == row.cumulative_return - row.benchmark_cumulative_return
        )
        assert all(
            isfinite(getattr(row, field.name))
            for field in fields(row)
            if field.name != "trade_date"
        )
    summary = result.summary
    assert summary.initial_notional == 1200000
    assert summary.total_pnl == cumulative[-1]
    assert summary.gross_return == pytest.approx(gross, rel=0, abs=1e-15)
    assert summary.benchmark_return == pytest.approx(0.0125, rel=0, abs=1e-15)
    assert summary.excess_return == pytest.approx(excess, rel=0, abs=1e-15)
    assert summary.strategy_max_drawdown == pytest.approx(strategy_mdd, rel=0, abs=1e-15)
    assert summary.benchmark_max_drawdown == pytest.approx(-6000 / 1212000, rel=0, abs=1e-15)
    assert sum(row.daily_return for row in result.daily) == pytest.approx(gross, rel=0, abs=1e-15)
    summed_benchmark = sum(row.benchmark_daily_return for row in result.daily)
    assert abs(summed_benchmark - summary.benchmark_return) > 1e-5
    summed_daily_excess = sum(row.daily_return - row.benchmark_daily_return for row in result.daily)
    assert abs(summed_daily_excess - summary.excess_return) > 1e-5
    assert result.daily[0].daily_pnl == result.daily[0].daily_return == 0
    assert (
        result.daily[0].benchmark_daily_return == result.daily[0].benchmark_cumulative_return == 0
    )
    roll = replay.replay.daily[2]
    assert roll.previous_portfolio.position is not None and roll.next_portfolio.position is not None
    assert roll.previous_portfolio.position.instrument.instrument_id == "IM2602.CFX"
    assert roll.next_portfolio.position.instrument.instrument_id == new_code
    assert roll.next_portfolio.position.reference_price == (
        6010 if new_code == "IM2603.CFX" else 6025
    )
    assert roll.transition.daily_pnl == 10000  # excludes 10/25 point cross-contract gap
    assert replay.replay.daily[-1].transition.daily_pnl == -2000
    assert replay.replay.final_portfolio.position is None
    assert len(replay.executions) == 4 and len(replay.rolls) == 1


def test_deterministic_immutable_result_and_inputs() -> None:
    inputs = performance_oracle_input()
    before = deepcopy(inputs)
    replay = replay_futures_roll(inputs)
    result = analyze_futures_roll(replay)
    assert result == analyze_futures_roll(replay_futures_roll(inputs))
    assert hash(result) == hash(analyze_futures_roll(replay))
    assert inputs == before
    with pytest.raises(FrozenInstanceError):
        inputs.index_closes[0].close = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.daily = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.daily[0].daily_return = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.summary.gross_return = 1  # type: ignore[misc]


@pytest.mark.parametrize("fault", ("missing", "duplicate", "reversed", "extra", "datetime", "list"))
def test_index_series_requires_exact_session_alignment(fault: str) -> None:
    inputs = performance_oracle_input()
    rows: Any = inputs.index_closes
    if fault == "missing":
        rows = rows[:-1]
    elif fault == "duplicate":
        rows = (rows[0], rows[0], *rows[2:])
    elif fault == "reversed":
        rows = rows[::-1]
    elif fault == "extra":
        rows += (IndexClose(date(2026, 2, 27), 6000),)
    elif fault == "datetime":
        rows = (IndexClose(datetime(2026, 1, 5), 6000), *rows[1:])
    elif fault == "list":
        rows = list(rows)
    with pytest.raises(FuturesRollError):
        replay_futures_roll(replace(inputs, index_closes=rows))
    replay = replay_futures_roll(inputs)
    with pytest.raises(FuturesRollError):
        analyze_futures_roll(replace(replay, index_closes=rows))


@pytest.mark.parametrize("value", (0, -1, nan, inf, -inf, True, "6000", None, 10**400))
@pytest.mark.parametrize("position", (0, 2, 4))
def test_every_index_close_must_be_finite_positive_numeric(value: Any, position: int) -> None:
    inputs = performance_oracle_input()
    rows = tuple(
        replace(row, close=value) if i == position else row
        for i, row in enumerate(inputs.index_closes)
    )
    with pytest.raises(FuturesRollError):
        replay_futures_roll(replace(inputs, index_closes=rows))
    with pytest.raises(FuturesRollError):
        analyze_futures_roll(replace(replay_futures_roll(inputs), index_closes=rows))


def test_single_first_close_controls_both_capital_and_benchmark() -> None:
    inputs = performance_oracle_input()
    inputs = replace(
        inputs, index_closes=(replace(inputs.index_closes[0], close=5000), *inputs.index_closes[1:])
    )
    result = analyze_futures_roll(replay_futures_roll(inputs))
    assert result.summary.initial_notional == 1000000
    assert result.summary.gross_return == 22000 / 1000000
    assert result.summary.benchmark_return == 6075 / 5000 - 1


def test_index_price_changes_cannot_change_policy_targets() -> None:
    inputs = performance_oracle_input()
    changed = replace(
        inputs,
        index_closes=tuple(
            replace(row, close=row.close * (2 + i)) for i, row in enumerate(inputs.index_closes)
        ),
    )
    first, second = replay_futures_roll(inputs), replay_futures_roll(changed)
    assert [row.target for row in first.replay.daily] == [row.target for row in second.replay.daily]


def test_initial_capital_participates_in_both_independent_peaks() -> None:
    inputs = simple_input()
    inputs = set_contract_close(inputs, inputs.sessions[0], "IM2602.CFX", 6000)
    inputs = set_contract_close(inputs, inputs.sessions[1], "IM2602.CFX", 5900)
    inputs = replace(
        inputs,
        index_closes=(IndexClose(inputs.sessions[0], 6000), IndexClose(inputs.sessions[1], 5900)),
    )
    result = analyze_futures_roll(replay_futures_roll(inputs))
    assert result.summary.strategy_max_drawdown == pytest.approx(-20000 / 1200000)
    assert result.summary.benchmark_max_drawdown == pytest.approx(-20000 / 1200000)


def replace_accounting(
    replay: FuturesRollReplay, position: int, **changes: Any
) -> FuturesRollReplay:
    records = tuple(
        replace(row, accounting=replace(row.accounting, **changes)) if i == position else row
        for i, row in enumerate(replay.replay.daily)
    )
    return replace(replay, replay=replace(replay.replay, daily=records))


@pytest.mark.parametrize("field", ("daily_return", "cumulative_return", "cumulative_pnl", "equity"))
@pytest.mark.parametrize("value", (nan, inf, -inf, True))
def test_nonfinite_or_invalid_core_accounting_fails(field: str, value: Any) -> None:
    replay = replay_futures_roll(performance_oracle_input())
    with pytest.raises(FuturesRollError):
        analyze_futures_roll(replace_accounting(replay, 2, **{field: value}))


@pytest.mark.parametrize("equity", (0, -1))
def test_strategy_equity_must_be_positive_on_every_session(equity: int) -> None:
    replay = replay_futures_roll(performance_oracle_input())
    with pytest.raises(FuturesRollError, match="non_positive_equity"):
        analyze_futures_roll(replace_accounting(replay, 2, equity=equity))


def test_consumes_core_daily_return_without_recomputing_it() -> None:
    replay = replay_futures_roll(performance_oracle_input())
    # Inject a finite sentinel to prove projection, rather than a second PnL/capital formula.
    result = analyze_futures_roll(replace_accounting(replay, 2, daily_return=0.12345))
    assert result.daily[2].daily_return == 0.12345


@pytest.mark.parametrize("fault", ("capital", "record_capital", "date", "missing", "flat"))
def test_inconsistent_replay_evidence_fails(fault: str) -> None:
    replay = replay_futures_roll(performance_oracle_input())
    if fault == "capital":
        replay = replace(replay, replay=replace(replay.replay, initial_capital=1))
    elif fault == "record_capital":
        replay = replace_accounting(replay, 1, initial_capital=1)
    elif fault == "date":
        replay = replace_accounting(replay, 1, trade_date=date(2026, 1, 1))
    elif fault == "missing":
        replay = replace(replay, replay=replace(replay.replay, daily=replay.replay.daily[:-1]))
    else:
        last = replay.replay.daily[-1]
        last = replace(
            last, transition=replace(last.transition, next_portfolio=last.previous_portfolio)
        )
        replay = replace(
            replay, replay=replace(replay.replay, daily=(*replay.replay.daily[:-1], last))
        )
    with pytest.raises(FuturesRollError):
        analyze_futures_roll(replay)


def test_benchmark_overflow_and_underflow_equity_fail_explicitly() -> None:
    replay = replay_futures_roll(performance_oracle_input())
    for close, reason in ((1e308, "benchmark_equity"), (1e-300, "non_positive_equity")):
        rows = tuple(
            replace(row, close=close) if i == 2 else row
            for i, row in enumerate(replay.index_closes)
        )
        with pytest.raises(FuturesRollError, match=reason):
            analyze_futures_roll(replace(replay, index_closes=rows))
