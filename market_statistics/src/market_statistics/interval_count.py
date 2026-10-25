"""Explicit-edge NumPy histogram and full-population accounting."""

from math import isfinite

import numpy as np

from .failures import CalculationFailure
from .models import IntervalBin, IntervalCountResult, IntervalCountSpec, NumericSample


def interval_count(sample: NumericSample, spec: IntervalCountSpec) -> IntervalCountResult:
    raw = np.histogram(
        np.array(sample.values, dtype=np.float64),
        bins=np.array(spec.edges, dtype=np.float64),
        density=False,
    )
    if not isinstance(raw, tuple) or len(raw) != 2:
        raise CalculationFailure(spec.method, "Expected histogram counts and edges")
    counts, edges = raw
    if (
        not isinstance(counts, np.ndarray)
        or counts.shape != (len(spec.edges) - 1,)
        or counts.dtype.kind not in "iu"
        or not isinstance(edges, np.ndarray)
        or edges.shape != (len(spec.edges),)
        or edges.dtype != np.dtype(np.float64)
        or not np.array_equal(edges, spec.edges)
    ):
        raise CalculationFailure(spec.method, "Malformed histogram counts or changed edges")
    exact_counts = tuple(int(count) for count in counts)
    underflow = sum(value < spec.edges[0] for value in sample.values)
    overflow = sum(value > spec.edges[-1] for value in sample.values)
    if (
        any(count < 0 for count in exact_counts)
        or sum(exact_counts) + underflow + overflow != sample.sample_count
    ):
        raise CalculationFailure(spec.method, "Histogram violates sample count conservation")
    bins = tuple(
        IntervalBin(
            left=spec.edges[index],
            right=spec.edges[index + 1],
            left_inclusive=True,
            right_inclusive=index == len(exact_counts) - 1,
            count=count,
            frequency=count / sample.sample_count,
        )
        for index, count in enumerate(exact_counts)
    )
    result = IntervalCountResult(
        edges=spec.edges,
        bins=bins,
        underflow_count=underflow,
        overflow_count=overflow,
        underflow_frequency=underflow / sample.sample_count,
        overflow_frequency=overflow / sample.sample_count,
        sample_count=sample.sample_count,
        unit=sample.unit,
    )
    if any(not isfinite(bin_.frequency) for bin_ in bins) or not all(
        isfinite(value) for value in (result.underflow_frequency, result.overflow_frequency)
    ):
        raise CalculationFailure(spec.method, "Non-finite empirical frequency")
    return result
