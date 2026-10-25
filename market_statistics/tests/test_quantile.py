"""Frozen estimator, binary64 branches and public result fixtures."""

from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest

from market_statistics import (
    CalculationFailure,
    NumericSample,
    QuantileResult,
    QuantileSpec,
    compute,
)


@pytest.mark.parametrize(
    ("values", "points", "expected"),
    [
        ([3, 1, 1, 9], [0, 0.25, 0.5, 0.75, 1], [1, 1, 2, 4.5, 9]),
        ([7], [0, 0.5, 1], [7, 7, 7]),
        ([1, 3], [0.25], [1.5]),
        ([1, 1e16], [0.75], [7500000000000001.0]),
        ([-1e308, 1e308], [0, 1], [-1e308, 1e308]),
        ([-1e308, 1e308, 1e308], [0.5], [1e308]),
        ([5, 5, 5, 5], [0, 0.25, 0.5, 0.75, 1], [5, 5, 5, 5, 5]),
        ([1, 2, 3], [0, 0.5, 1], [1, 2, 3]),
        ([-9, -1, 2, 7], [0.125, 0.5, 0.875], [-6, 0.5, 5.125]),
    ],
)
def test_frozen_type7_examples(values: Any, points: Any, expected: Any) -> None:
    sample = NumericSample(values, " Points ")
    spec = QuantileSpec(points)
    before = sample.values
    result = compute(sample, spec)
    assert isinstance(result, QuantileResult)
    assert result.method == "quantile"
    assert result.estimator == "type7_linear_v1"
    assert result.points_and_values == tuple(zip(points, expected, strict=True))
    assert result.sample_count == len(values)
    assert result.unit == " Points "
    assert sample.values == before
    assert values == list(before)
    assert all(type(p) is float and type(v) is float for p, v in result.points_and_values)
    with pytest.raises(FrozenInstanceError):
        result.unit = "changed"  # type: ignore[misc]


def test_required_intermediate_overflow_fails() -> None:
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([-1e308, 1e308], "points"), QuantileSpec([0.5]))
    assert caught.value.method == "quantile"
    assert "difference" in caught.value.reason


def test_direct_branches_bypass_unnecessary_backend_arithmetic(monkeypatch: Any) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Direct-index branch must bypass backend interpolation")

    monkeypatch.setattr(np, "quantile", forbidden)
    fixtures: list[tuple[list[int | float], list[int | float]]] = [
        ([-1e308, 1e308], [0, 1]),
        ([-1e308, 1e308, 1e308], [0.5]),
        ([7], [0, 0.5, 1]),
    ]
    for values, points in fixtures:
        assert isinstance(compute(NumericSample(values, "u"), QuantileSpec(points)), QuantileResult)


def test_numpy_upper_half_branch_requires_exact_adaptation() -> None:
    backend = float(np.quantile([1, 1e16], [0.75], method="linear")[0])
    frozen = 7500000000000001.0
    assert backend == 7500000000000000.0
    result = compute(NumericSample([1, 1e16], "u"), QuantileSpec([0.75]))
    assert isinstance(result, QuantileResult)
    assert result.points_and_values == ((0.75, frozen),)


def test_public_numpy_interface_explicit_parameters_and_owned_arrays(monkeypatch: Any) -> None:
    original = np.quantile
    calls = []

    def backend(values: Any, points: Any, **kwargs: Any) -> Any:
        calls.append((values.copy(), list(points), kwargs))
        result = original(values, points, **kwargs)
        values[:] = 999  # backend sees a private copy, never caller storage
        return result

    monkeypatch.setattr(np, "quantile", backend)
    sample = NumericSample([9, 1, 3], "u")
    result = compute(sample, QuantileSpec([0, 0.25, 0.5, 0.75, 1]))
    assert isinstance(result, QuantileResult)
    assert result.points_and_values == ((0, 1), (0.25, 2), (0.5, 3), (0.75, 6), (1, 9))
    assert sample.values == (9, 1, 3)
    assert len(calls) == 1
    assert calls[0][1:] == ([0.25, 0.75], {"method": "linear"})
