"""Shared empirical distribution calculations for finite numeric samples.

Canonical authority: ARCHITECTURE.md (beside this file).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from numbers import Real
from statistics import stdev


class DistributionInputError(ValueError):
    """The numeric sample or distribution parameter is invalid."""


@dataclass(frozen=True)
class DistributionBin:
    lower_bound: float
    upper_bound: float
    count: int
    frequency: float


@dataclass(frozen=True)
class DescriptiveSummary:
    sample_count: int
    mean: float
    median: float
    sample_standard_deviation: float | None
    min: float
    max: float


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise DistributionInputError(f"{name} must be a finite numeric value.")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise DistributionInputError(f"{name} must be a finite numeric value.") from exc
    if not math.isfinite(number):
        raise DistributionInputError(f"{name} must be a finite numeric value.")
    return number


def _sample(values: Sequence[float]) -> tuple[float, ...]:
    if not values:
        raise DistributionInputError("an empirical distribution needs a non-empty sample.")
    return tuple(_finite_number(value, "observation") for value in values)


def linear_quantile(values: Sequence[float], probability: float) -> float:
    """Return the linearly interpolated empirical quantile."""
    sample = _sample(values)
    p = _finite_number(probability, "probability")
    if not 0 <= p <= 1:
        raise DistributionInputError("probability must be between 0 and 1.")
    ordered = sorted(sample)
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    difference = ordered[upper] - ordered[lower]
    if math.isfinite(difference):
        return ordered[lower] + difference * weight
    return (1 - weight) * ordered[lower] + weight * ordered[upper]


def fixed_width_distribution(
    values: Sequence[float], granularity: float
) -> tuple[DistributionBin, ...]:
    """Materialize every zero-anchored bin between the sample extremes."""
    sample = _sample(values)
    width = _finite_number(granularity, "granularity")
    if width <= 0:
        raise DistributionInputError("granularity must be greater than zero.")
    decimal_width = Decimal(str(width))

    def index(value: float) -> int:
        return int((Decimal(str(value)) / decimal_width).to_integral_value(rounding=ROUND_FLOOR))

    indices = [index(value) for value in sample]
    counts = Counter(indices)
    result: list[DistributionBin] = []
    for bin_index in range(min(indices), max(indices) + 1):
        lower = float(Decimal(bin_index) * decimal_width)
        upper = float(Decimal(bin_index + 1) * decimal_width)
        count = counts.get(bin_index, 0)
        result.append(DistributionBin(lower, upper, count, count / len(sample)))
    return tuple(result)


def descriptive_summary(values: Sequence[float]) -> DescriptiveSummary:
    """Return the narrow descriptive statistics of a complete sample."""
    sample = _sample(values)
    return DescriptiveSummary(
        sample_count=len(sample),
        mean=math.fsum(value / len(sample) for value in sample),
        median=linear_quantile(sample, 0.5),
        sample_standard_deviation=stdev(sample) if len(sample) >= 2 else None,
        min=min(sample),
        max=max(sample),
    )
