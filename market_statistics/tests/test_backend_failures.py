"""Backend defects are calculation failures for valid public requests."""

import warnings
from typing import Any

import numpy as np
import pytest

from market_statistics import (
    CalculationFailure,
    IntervalCountSpec,
    NumericSample,
    QuantileSpec,
    StatisticalFailure,
    compute,
)


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [1.5],
        1.5,
        np.array(1.5),
        np.array([[1.5]]),
        np.array([]),
        np.array([1.5, 2]),
        np.array([np.nan]),
        np.array([np.inf]),
        np.array([-np.inf]),
        np.array(["1.5"]),
        np.array([True]),
        np.array([1]),
        np.array([1.5], dtype=object),
        np.array([1.5], dtype=np.float32),
        np.array([99.0]),
    ],
)
def test_malformed_quantile_outputs(payload: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(np, "quantile", lambda *args, **kwargs: payload)
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([1, 3], "u"), QuantileSpec([0.25]))
    assert caught.value.method == "quantile"
    assert caught.value.reason


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [np.array([1, 3]), np.array([0.0, 1.0, 2.0])],
        (),
        (np.array([1, 3]),),
        (np.array([1, 3]), np.array([0.0, 1.0, 2.0]), None),
        ([1, 3], np.array([0.0, 1.0, 2.0])),
        (np.array([1.0, 3.0]), np.array([0.0, 1.0, 2.0])),
        (np.array([True, True]), np.array([0.0, 1.0, 2.0])),
        (np.array([1, 3], dtype=object), np.array([0.0, 1.0, 2.0])),
        (np.array([np.nan, 3]), np.array([0.0, 1.0, 2.0])),
        (np.array([np.inf, 3]), np.array([0.0, 1.0, 2.0])),
        (np.array([1, 3]), [0.0, 1.0, 2.0]),
        (np.array([1, 3]), np.array([0, 1, 2])),
        (np.array([1, 3]), np.array([0.0, 1.0, np.inf])),
        (np.array([1, 3]), np.array([0.0, 1.1, 2.0])),
        (np.array([1, 3]), np.array([[0.0, 1.0, 2.0]])),
        (np.array([[1, 3]]), np.array([0.0, 1.0, 2.0])),
        (np.array([4]), np.array([0.0, 1.0, 2.0])),
        (np.array([-1, 5]), np.array([0.0, 1.0, 2.0])),
        (np.array([1, 4]), np.array([0.0, 1.0, 2.0])),
        (np.array([0, 0]), np.array([0.0, 1.0, 2.0])),
        (np.array([2**64 - 1, 5], dtype=np.uint64), np.array([0.0, 1.0, 2.0])),
    ],
)
def test_malformed_histogram_outputs(payload: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(np, "histogram", lambda *args, **kwargs: payload)
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([-1, 0, 1, 1, 2, 3], "u"), IntervalCountSpec([0, 1, 2], "u"))
    assert caught.value.method == "interval_count"
    assert caught.value.reason


@pytest.mark.parametrize("backend", ["quantile", "histogram"])
@pytest.mark.parametrize(
    "error",
    [
        ValueError("backend defect"),
        TypeError("backend defect"),
        FloatingPointError("overflow"),
        OverflowError("overflow"),
    ],
)
def test_execution_failures_retain_cause(backend: str, error: Exception, monkeypatch: Any) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise error

    monkeypatch.setattr(np, backend, fail)
    spec = QuantileSpec([0.25]) if backend == "quantile" else IntervalCountSpec([0, 2], "u")
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([1, 3], "u"), spec)
    assert caught.value.__cause__ is error
    assert caught.value.method == spec.method
    assert "backend defect" in caught.value.reason or "overflow" in caught.value.reason
    assert isinstance(caught.value, StatisticalFailure)


@pytest.mark.parametrize("backend", ["quantile", "histogram"])
def test_numerical_warning_cannot_yield_partial_success(backend: str, monkeypatch: Any) -> None:
    def warned(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("invalid numerical execution", RuntimeWarning, stacklevel=2)
        return np.array([1.5]) if backend == "quantile" else (np.array([1]), np.array([0.0, 2.0]))

    original_errors = np.geterr().copy()
    original_filters = warnings.filters[:]
    monkeypatch.setattr(np, backend, warned)
    spec = QuantileSpec([0.25]) if backend == "quantile" else IntervalCountSpec([0, 2], "u")
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([1, 3], "u"), spec)
    assert isinstance(caught.value.__cause__, RuntimeWarning)
    assert np.geterr() == original_errors
    assert warnings.filters == original_filters


def test_backend_nonfinite_arithmetic_cannot_hide_behind_finite_output(monkeypatch: Any) -> None:
    def invalid(*args: Any, **kwargs: Any) -> Any:
        np.subtract(np.float64(1e308), np.float64(-1e308))
        return np.array([1.5])

    monkeypatch.setattr(np, "quantile", invalid)
    with pytest.raises(CalculationFailure):
        compute(NumericSample([1, 3], "u"), QuantileSpec([0.25]))
