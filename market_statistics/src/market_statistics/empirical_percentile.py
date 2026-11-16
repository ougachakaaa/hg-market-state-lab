"""Midrank V1 using validated NumPy sorting and explicit insertion boundaries."""

from collections import Counter
from math import isfinite

import numpy as np

from .failures import CalculationFailure
from .models import (
    EmpiricalPercentileQueryResult,
    EmpiricalPercentileResult,
    EmpiricalPercentileSpec,
    NumericSample,
)


def empirical_percentile(
    sample: NumericSample, spec: EmpiricalPercentileSpec
) -> EmpiricalPercentileResult:
    n = sample.sample_count
    ordered = np.sort(np.array(sample.values, dtype=np.float64))
    if (
        not isinstance(ordered, np.ndarray)
        or ordered.shape != (n,)
        or ordered.dtype != np.dtype(np.float64)
        or not np.all(np.isfinite(ordered))
        or np.any(ordered[:-1] > ordered[1:])
        or Counter(ordered.tolist()) != Counter(sample.values)
    ):
        raise CalculationFailure(spec.method, "Malformed sorted sample or changed multiplicity")

    queries = np.array(spec.queries, dtype=np.float64)
    left = np.searchsorted(ordered, queries, side="left")
    right = np.searchsorted(ordered, queries, side="right")
    for indices in (left, right):
        if (
            not isinstance(indices, np.ndarray)
            or indices.shape != (len(spec.queries),)
            or indices.dtype.kind not in "iu"
        ):
            raise CalculationFailure(spec.method, "Malformed searchsorted insertion indices")

    results = []
    for query, raw_left, raw_right in zip(spec.queries, left, right, strict=True):
        lo, hi = int(raw_left), int(raw_right)
        if not 0 <= lo <= hi <= n:
            raise CalculationFailure(spec.method, "Insertion indices violate sample accounting")
        # Validate exact boundaries for this query, including empty tied groups.
        if (
            (lo > 0 and not ordered[lo - 1] < query)
            or (lo < n and not ordered[lo] >= query)
            or (hi > 0 and not ordered[hi - 1] <= query)
            or (hi < n and not ordered[hi] > query)
        ):
            raise CalculationFailure(
                spec.method, "Insertion indices do not match query order/value"
            )
        less, equal, greater = lo, hi - lo, n - hi
        percentile = (less + 0.5 * equal) / n
        if less + equal + greater != n or not isfinite(percentile) or not 0 <= percentile <= 1:
            raise CalculationFailure(spec.method, "Invalid midrank counts or percentile")
        results.append(EmpiricalPercentileQueryResult(query, less, equal, greater, percentile))
    return EmpiricalPercentileResult(tuple(results), n, sample.unit)
