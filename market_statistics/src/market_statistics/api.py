"""Pure public dispatch and validation in the published precedence order."""

import warnings

import numpy as np

from .failures import CalculationFailure, InvalidSample, InvalidStatisticalSpec
from .interval_count import interval_count
from .models import NumericSample, QuantileSpec, StatisticalResult, StatisticalSpec
from .quantile import quantile
from .validation import validate_spec


def compute(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult:
    if type(sample) is not NumericSample:
        raise InvalidSample("Expected NumericSample")
    try:
        sample._validate()
    except AttributeError as exc:
        raise InvalidSample("Incomplete NumericSample") from exc
    validate_spec(spec)
    if not isinstance(spec, QuantileSpec) and sample.unit != spec.unit:
        raise InvalidStatisticalSpec("Sample and interval edge units must match exactly")

    try:
        # Local failure handling: no global warning/error policy is changed.
        with warnings.catch_warnings(), np.errstate(over="raise", invalid="raise", divide="raise"):
            warnings.simplefilter("error", RuntimeWarning)
            if isinstance(spec, QuantileSpec):
                return quantile(sample, spec)
            return interval_count(sample, spec)
    except CalculationFailure:
        raise
    except Exception as exc:
        raise CalculationFailure(spec.method, f"Numerical execution failed: {exc}") from exc
