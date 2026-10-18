"""Shared lagged-reference observations and Snapshot contract checks."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from data_snapshot.products.index_daily_history import (
    IndexDailyHistoryResult,
    IndexDailyObservation,
)
from market_research.shared.price_to_lagged_reference import (
    LaggedReferenceError,
    PriceToLaggedMAObservation,
    compute_daily_observations,
)


def observations(
    method: str, result: IndexDailyHistoryResult
) -> tuple[PriceToLaggedMAObservation, ...]:
    return compute_daily_observations(
        "000852.SH", "2026-09-03", "2026-09-04", 2, method, result
    )


def snapshot(
    *, sample: tuple[IndexDailyObservation, ...] | None = None
) -> IndexDailyHistoryResult:
    return IndexDailyHistoryResult(
        ts_code="000852.SH",
        requested_start_trade_date="2026-09-03",
        requested_end_trade_date="2026-09-04",
        requested_pre_start_observation_count=2,
        warmup_observations=(
            IndexDailyObservation("2026-09-01", 100.0, 1.0),
            IndexDailyObservation("2026-09-02", 110.0, 3.0),
        ),
        sample_observations=sample
        if sample is not None
        else (
            IndexDailyObservation("2026-09-03", 120.0, 2.0),
            IndexDailyObservation("2026-09-04", 130.0, 4.0),
        ),
    )


def test_sma_uses_prior_actual_rows_and_preserves_first_sample() -> None:
    result = observations("sma", snapshot())
    first, second = result
    assert [(row.trade_date, row.close, row.reference_ma) for row in result] == [
        ("2026-09-03", 120.0, 105.0),
        ("2026-09-04", 130.0, 115.0),
    ]
    assert first.instrument == second.instrument == "000852.SH"
    assert first.deviation == pytest.approx(120 / 105 - 1)
    assert second.deviation == pytest.approx(130 / 115 - 1)


def test_current_close_never_participates_in_its_own_reference() -> None:
    unusual = snapshot(
        sample=(
            IndexDailyObservation("2026-09-03", 1000.0, 2.0),
            IndexDailyObservation("2026-09-04", 130.0, 4.0),
        )
    )
    result = observations("sma", unusual)
    assert result[0].reference_ma == 105.0
    assert result[0].deviation == pytest.approx(1000 / 105 - 1)
    assert result[1].reference_ma == 555.0


def test_volume_weighted_uses_unequal_prior_volumes() -> None:
    result = observations("volume_weighted", snapshot())
    first, second = result
    assert first.reference_ma == 107.5  # (100*1 + 110*3) / 4
    assert first.deviation == pytest.approx(120 / 107.5 - 1)
    assert second.reference_ma == pytest.approx(114.0)  # (110*3 + 120*2) / 5
    assert second.deviation == pytest.approx(130 / 114 - 1)


@pytest.mark.parametrize("bad_volume", [None, -1.0, math.nan, math.inf])
def test_missing_or_invalid_required_volume_fails(bad_volume: float | None) -> None:
    baseline = snapshot()
    bad = replace(
        baseline,
        warmup_observations=(
            replace(baseline.warmup_observations[0], volume=bad_volume),
            baseline.warmup_observations[1],
        ),
    )
    with pytest.raises(LaggedReferenceError):
        observations("volume_weighted", bad)


def test_zero_total_volume_fails_without_sma_fallback() -> None:
    baseline = snapshot()
    bad = replace(
        baseline,
        warmup_observations=tuple(replace(row, volume=0.0) for row in baseline.warmup_observations),
    )
    with pytest.raises(LaggedReferenceError, match="positive total volume"):
        observations("volume_weighted", bad)


@pytest.mark.parametrize(
    "change",
    [
        {"ts_code": "000001.SH"},
        {"requested_start_trade_date": "2026-09-02"},
        {"requested_end_trade_date": "2026-09-05"},
        {"requested_pre_start_observation_count": 3},
        {"warmup_observations": (IndexDailyObservation("2026-09-02", 110.0, 3.0),)},
        {"sample_observations": ()},
        {"sample_observations": (
            IndexDailyObservation("2026-09-04", 130.0, 4.0),
            IndexDailyObservation("2026-09-03", 120.0, 2.0),
        )},
        {"sample_observations": (IndexDailyObservation("2026-09-05", 120.0, 2.0),)},
        {"warmup_observations": (
            IndexDailyObservation("2026-09-01", 100.0, 1.0),
            IndexDailyObservation("2026-09-03", 110.0, 3.0),
        )},
    ],
)
def test_snapshot_contract_mismatch_fails(change: dict[str, object]) -> None:
    with pytest.raises(LaggedReferenceError):
        observations("sma", replace(snapshot(), **change))  # type: ignore[arg-type]


@pytest.mark.parametrize("bad_close", [None, 0.0, -1.0, math.nan, math.inf])
def test_invalid_snapshot_close_fails_entire_run(bad_close: float | None) -> None:
    baseline = snapshot()
    bad = replace(
        baseline,
        sample_observations=(
            baseline.sample_observations[0],
            replace(baseline.sample_observations[1], close=bad_close),  # type: ignore[arg-type]
        ),
    )
    with pytest.raises(LaggedReferenceError):
        observations("sma", bad)
