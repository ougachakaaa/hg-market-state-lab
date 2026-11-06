"""Arithmetic float64 mean; overflow never triggers a substitute algorithm."""

import numpy as np

from .failures import CalculationFailure
from .models import MeanResult, MeanSpec, NumericSample


def mean(sample: NumericSample, spec: MeanSpec) -> MeanResult:
    raw = np.mean(np.array(sample.values, dtype=np.float64), dtype=np.float64)
    if not isinstance(raw, np.float64) or not np.isfinite(raw):
        raise CalculationFailure(spec.method, "Malformed or non-finite NumPy mean result")
    value = float(raw)
    if not min(sample.values) <= value <= max(sample.values):
        raise CalculationFailure(spec.method, "Mean lies outside the sample range")
    return MeanResult(value, sample.sample_count, sample.unit)
