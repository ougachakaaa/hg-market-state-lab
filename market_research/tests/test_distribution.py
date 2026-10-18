"""Focused checks for the shared empirical distribution authority."""

from __future__ import annotations

import math

import pytest

from market_research.shared.distribution import (
    DistributionInputError,
    descriptive_summary,
    fixed_width_distribution,
    linear_quantile,
)


def test_linear_quantile_endpoints_interpolation_and_singleton() -> None:
    sample = [10.0, 0.0, 20.0]
    assert linear_quantile(sample, 0) == 0.0
    assert linear_quantile(sample, 1) == 20.0
    assert linear_quantile(sample, 0.25) == 5.0
    assert linear_quantile(sample, 0.5) == 10.0
    assert linear_quantile([7.0], 0.25) == 7.0


@pytest.mark.parametrize("sample", [[], [math.nan], [math.inf], [-math.inf], ["bad"], [1.0, None]])
def test_invalid_samples_fail(sample: list[object]) -> None:
    with pytest.raises(DistributionInputError):
        linear_quantile(sample, 0.5)  # type: ignore[arg-type]
    with pytest.raises(DistributionInputError):
        fixed_width_distribution(sample, 1.0)  # type: ignore[arg-type]
    with pytest.raises(DistributionInputError):
        descriptive_summary(sample)  # type: ignore[arg-type]


@pytest.mark.parametrize("probability", [-0.1, 1.1, math.nan, math.inf, "bad"])
def test_invalid_probability_fails(probability: object) -> None:
    with pytest.raises(DistributionInputError):
        linear_quantile([1.0], probability)  # type: ignore[arg-type]


@pytest.mark.parametrize("granularity", [0.0, -1.0, math.nan, math.inf, "bad"])
def test_invalid_granularity_fails(granularity: object) -> None:
    with pytest.raises(DistributionInputError):
        fixed_width_distribution([1.0], granularity)  # type: ignore[arg-type]


def test_zero_anchored_bins_include_boundaries_and_empty_bins() -> None:
    bins = fixed_width_distribution([-2.0, -0.1, 0.0, 1.0, 3.0], 1.0)
    assert [(row.lower_bound, row.upper_bound, row.count) for row in bins] == [
        (-2.0, -1.0, 1),
        (-1.0, 0.0, 1),
        (0.0, 1.0, 1),
        (1.0, 2.0, 1),
        (2.0, 3.0, 0),
        (3.0, 4.0, 1),
    ]
    assert sum(row.count for row in bins) == 5
    assert sum(row.frequency for row in bins) == pytest.approx(1.0)
    assert bins[4].frequency == 0.0
    assert all(row.frequency == row.count / 5 for row in bins)


def test_decimal_boundary_is_assigned_to_bin_starting_at_boundary() -> None:
    bins = fixed_width_distribution([-0.3, 0.0, 0.3], 0.1)
    assert bins[0].lower_bound == -0.3
    assert bins[0].count == 1
    assert bins[3].lower_bound == 0.0
    assert bins[3].count == 1
    assert bins[6].lower_bound == 0.3
    assert bins[6].count == 1


def test_summary_median_matches_p50_and_singleton_std_is_none() -> None:
    singleton = descriptive_summary([7.0])
    assert singleton.sample_count == 1
    assert singleton.mean == singleton.median == singleton.min == singleton.max == 7.0
    assert singleton.sample_standard_deviation is None

    summary = descriptive_summary([1.0, 2.0, 3.0])
    assert summary.sample_count == 3
    assert summary.mean == 2.0
    assert summary.median == linear_quantile([1.0, 2.0, 3.0], 0.5)
    assert summary.sample_standard_deviation == 1.0
    assert summary.min == 1.0
    assert summary.max == 3.0


def test_finite_extreme_values_keep_finite_mean_and_median() -> None:
    assert linear_quantile([-1e308, 1e308], 0.5) == 0.0
    assert descriptive_summary([1e308, 1e308]).mean == 1e308
