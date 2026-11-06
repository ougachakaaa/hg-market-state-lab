"""Mean numerical contract and backend failure conformance."""

import sys
from unittest.mock import patch

import numpy as np
import pytest

from market_statistics import (
    CalculationFailure,
    InvalidStatisticalSpec,
    MeanResult,
    MeanSpec,
    NumericSample,
    compute,
    validate_spec,
)


@pytest.mark.parametrize(
    ("values", "expected"), [([1, 3], 2), ([7], 7), ([1, 1, 4], 2), ([-3, 3], 0), ([0, 0], 0)]
)
def test_mean(values, expected):
    sample = NumericSample(values, " Opaque ")
    result = compute(sample, MeanSpec())
    assert result == MeanResult(expected, len(values), " Opaque ")
    assert sample.values == tuple(values)
    assert validate_spec(MeanSpec()) is None


def test_overflow_is_failure_even_for_finite_mathematical_mean():
    with pytest.raises(CalculationFailure, match="mean"):
        compute(NumericSample([sys.float_info.max] * 2, "u"), MeanSpec())


@pytest.mark.parametrize(
    "raw", [float("nan"), np.float64("inf"), np.array([1.0]), np.float64(20), 1.0]
)
def test_malformed_backend(raw):
    with patch("market_statistics.mean.np.mean", return_value=raw):
        with pytest.raises(CalculationFailure):
            compute(NumericSample([1, 3], "u"), MeanSpec())


def test_spec_revalidation():
    spec = MeanSpec()
    object.__setattr__(spec, "method", "other")
    with pytest.raises(InvalidStatisticalSpec):
        compute(NumericSample([1], "u"), spec)


def test_backend_warning_and_exception():
    import warnings

    def warning(*args, **kwargs):
        warnings.warn("overflow", RuntimeWarning, stacklevel=2)
        return np.float64(2)

    for backend in (warning, OverflowError("overflow")):
        with patch("market_statistics.mean.np.mean", side_effect=backend):
            with pytest.raises(CalculationFailure):
                compute(NumericSample([1, 3], "u"), MeanSpec())
