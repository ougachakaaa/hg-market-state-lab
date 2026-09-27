"""Hand-checkable Study core and Snapshot-contract checks."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import replace
from decimal import Decimal

import pytest

from market_research.studies.price_to_lagged_ma_distribution import (
    PriceToLaggedMARequest,
    PriceToLaggedMAStudyError,
    compute,
    derive_snapshot_request,
    run_key,
)
from market_research.studies.price_to_lagged_ma_distribution.study import (
    canonical_request,
    semantic_digest,
)
from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
    IndexDailyObservation,
)


def request(**changes: object) -> PriceToLaggedMARequest:
    values: dict[str, object] = {
        "instrument": "000852.SH",
        "reference_window": 2,
        "reference_method": "sma",
        "reference_method_parameters": {},
        "sample_start_trade_date": "2026-09-03",
        "sample_end_trade_date": "2026-09-04",
        "distribution_granularity": Decimal("0.01"),
        "percentile_probabilities": (Decimal("0.25"), Decimal("0.5")),
    }
    values.update(changes)
    return PriceToLaggedMARequest(**values)  # type: ignore[arg-type]


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
    result = compute(request(), snapshot())
    first, second = result.daily_observations
    assert [(row.trade_date, row.close, row.reference_ma) for row in result.daily_observations] == [
        ("2026-09-03", 120.0, 105.0),
        ("2026-09-04", 130.0, 115.0),
    ]
    assert first.instrument == second.instrument == "000852.SH"
    assert first.deviation == pytest.approx(120 / 105 - 1)
    assert second.deviation == pytest.approx(130 / 115 - 1)
    assert result.summary.sample_count == 2


def test_current_close_never_participates_in_its_own_reference() -> None:
    unusual = snapshot(
        sample=(
            IndexDailyObservation("2026-09-03", 1000.0, 2.0),
            IndexDailyObservation("2026-09-04", 130.0, 4.0),
        )
    )
    result = compute(request(), unusual)
    assert result.daily_observations[0].reference_ma == 105.0
    assert result.daily_observations[0].deviation == pytest.approx(1000 / 105 - 1)
    assert result.daily_observations[1].reference_ma == 555.0


def test_volume_weighted_uses_unequal_prior_volumes() -> None:
    result = compute(request(reference_method="volume_weighted"), snapshot())
    first, second = result.daily_observations
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
    with pytest.raises(PriceToLaggedMAStudyError):
        compute(request(reference_method="volume_weighted"), bad)


def test_zero_total_volume_fails_without_sma_fallback() -> None:
    baseline = snapshot()
    bad = replace(
        baseline,
        warmup_observations=tuple(replace(row, volume=0.0) for row in baseline.warmup_observations),
    )
    with pytest.raises(PriceToLaggedMAStudyError, match="positive total volume"):
        compute(request(reference_method="volume_weighted"), bad)


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
    with pytest.raises(PriceToLaggedMAStudyError):
        compute(request(), replace(snapshot(), **change))  # type: ignore[arg-type]


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
    with pytest.raises(PriceToLaggedMAStudyError):
        compute(request(), bad)


def test_shared_distribution_percentiles_summary_and_singleton() -> None:
    study_request = request(
        distribution_granularity="0.05", percentile_probabilities=("1", "0.5", "0")
    )
    result = compute(study_request, snapshot())
    values = [row.deviation for row in result.daily_observations]
    assert [row.probability for row in result.percentiles] == [0.0, 0.5, 1.0]
    assert [row.value for row in result.percentiles] == pytest.approx(
        [min(values), sum(values) / 2, max(values)]
    )
    assert result.summary.sample_count == 2
    assert result.summary.mean == pytest.approx(sum(values) / 2)
    assert result.summary.median == result.percentiles[1].value
    assert sum(bin_.count for bin_ in result.distribution_bins) == 2
    assert all(
        bin_.upper_bound - bin_.lower_bound == pytest.approx(0.05)
        for bin_ in result.distribution_bins
    )

    single = compute(request(), snapshot(sample=(snapshot().sample_observations[0],)))
    assert len(single.daily_observations) == 1
    assert single.summary.sample_count == 1
    assert single.summary.sample_standard_deviation is None
    assert all(row.value == single.daily_observations[0].deviation for row in single.percentiles)
    assert sum(bin_.count for bin_ in single.distribution_bins) == 1


def test_request_normalization_run_identity_and_snapshot_derivation() -> None:
    original = request()
    equivalent = request(
        distribution_granularity="0.0100",
        percentile_probabilities=(0.50, "0.2500"),
    )
    assert original == equivalent
    assert str(equivalent.distribution_granularity) == "0.01"
    assert tuple(map(str, equivalent.percentile_probabilities)) == ("0.25", "0.5")
    assert run_key(original) == run_key(equivalent)
    assert re.fullmatch(
        r"000852\.SH__sma2__20260903-20260904__g0\.01__[0-9a-f]{12}", run_key(original)
    )
    canonical = {
        "instrument": "000852.SH",
        "reference_window": 2,
        "reference_method": "sma",
        "reference_method_parameters": {},
        "sample_start_trade_date": "2026-09-03",
        "sample_end_trade_date": "2026-09-04",
        "distribution_granularity": "0.01",
        "percentile_probabilities": ["0.25", "0.5"],
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert canonical_request(original) == canonical
    assert semantic_digest(original) == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert len(semantic_digest(original)) == 64
    assert semantic_digest(original) == semantic_digest(equivalent)
    assert run_key(original).endswith(semantic_digest(original)[:12])
    assert derive_snapshot_request(original) == IndexDailyHistoryRequest(
        ts_code="000852.SH",
        start_trade_date="2026-09-03",
        end_trade_date="2026-09-04",
        pre_start_observation_count=2,
    )
    assert original.reference_method_parameters == {}
    assert original.percentile_probabilities == (Decimal("0.25"), Decimal("0.5"))


@pytest.mark.parametrize(
    "change",
    [
        {"instrument": "000001.SH"},
        {"reference_window": 3},
        {"reference_method": "volume_weighted"},
        {"sample_start_trade_date": "2026-09-02"},
        {"sample_end_trade_date": "2026-09-05"},
        {"distribution_granularity": "0.02"},
        {"percentile_probabilities": ("0.1", "0.5")},
    ],
)
def test_evidence_affecting_change_changes_run_key(change: dict[str, object]) -> None:
    assert run_key(request(**change)) != run_key(request())


def test_readable_prefix_changes_only_for_its_own_fields() -> None:
    baseline = request(
        reference_window=60,
        sample_start_trade_date="2025-01-01",
        sample_end_trade_date="2026-09-25",
        distribution_granularity="0.005",
    )
    prefix, suffix = run_key(baseline).rsplit("__", 1)
    assert prefix == "000852.SH__sma60__20250101-20260925__g0.005"
    assert re.fullmatch(r"[0-9a-f]{12}", suffix)
    assert run_key(baseline) == run_key(
        request(
            reference_window=60,
            sample_start_trade_date="2025-01-01",
            sample_end_trade_date="2026-09-25",
            distribution_granularity="0.0050",
            percentile_probabilities=("0.50", "0.250"),
        )
    )
    changed_percentiles = request(
        reference_window=60,
        sample_start_trade_date="2025-01-01",
        sample_end_trade_date="2026-09-25",
        distribution_granularity="0.005",
        percentile_probabilities=("0.1", "0.9"),
    )
    changed_prefix, changed_suffix = run_key(changed_percentiles).rsplit("__", 1)
    assert changed_prefix == prefix
    assert changed_suffix != suffix
    assert run_key(request(reference_method="volume_weighted")).startswith(
        "000852.SH__volume_weighted2__"
    )
    assert run_key(request(instrument="000001.SH")).startswith("000001.SH__sma2__")
    assert "__sma3__" in run_key(request(reference_window=3))
    assert "__20260902-20260904__" in run_key(
        request(sample_start_trade_date="2026-09-02")
    )
    assert "__20260903-20260905__" in run_key(
        request(sample_end_trade_date="2026-09-05")
    )
    assert "__g0.02__" in run_key(request(distribution_granularity="0.02"))


@pytest.mark.parametrize(
    "change",
    [
        {"instrument": " "},
        {"instrument": "../outside"},
        {"instrument": r"nested\path"},
        {"instrument": "CON"},
        {"instrument": "index:"},
        {"instrument": "index."},
        {"reference_window": 0},
        {"reference_window": True},
        {"reference_method": "decay_weighted"},
        {"reference_method_parameters": {"decay": 0.5}},
        {"sample_start_trade_date": "2026-09-31"},
        {"sample_start_trade_date": "2026-9-3"},
        {"sample_end_trade_date": "2026-09-02"},
        {"distribution_granularity": 0},
        {"distribution_granularity": math.inf},
        {"percentile_probabilities": ()},
        {"percentile_probabilities": ("0.5", "0.50")},
        {"percentile_probabilities": (-0.1,)},
        {"percentile_probabilities": (math.nan,)},
    ],
)
def test_invalid_request_fails(change: dict[str, object]) -> None:
    with pytest.raises(PriceToLaggedMAStudyError):
        request(**change)


def test_negative_zero_and_exponent_spelling_share_run_identity() -> None:
    assert run_key(request(percentile_probabilities=("-0", "1e0"))) == run_key(
        request(percentile_probabilities=("0.0", "1.00"))
    )
    assert run_key(request(distribution_granularity="1e-2")) == run_key(
        request(distribution_granularity="0.0100")
    )


def test_exact_positive_and_negative_deviation_boundaries_keep_canonical_bins() -> None:
    for close, expected in ((95.0, -0.05), (105.0, 0.05)):
        boundary_snapshot = replace(
            snapshot(),
            warmup_observations=(
                IndexDailyObservation("2026-09-01", 100.0, 1.0),
                IndexDailyObservation("2026-09-02", 100.0, 1.0),
            ),
            sample_observations=(IndexDailyObservation("2026-09-03", close, 1.0),),
        )
        result = compute(request(distribution_granularity="0.05"), boundary_snapshot)
        assert result.daily_observations[0].deviation == expected
        assert [(row.lower_bound, row.count) for row in result.distribution_bins] == [
            (expected, 1)
        ]
