"""Public Midrank V1 fixtures, validation and malformed-backend rejection."""

import math
import warnings
from dataclasses import FrozenInstanceError
from decimal import Decimal
from typing import Any

import numpy as np
import pytest

from market_statistics import (
    CalculationFailure,
    EmpiricalPercentileQueryResult,
    EmpiricalPercentileResult,
    EmpiricalPercentileSpec,
    InvalidSample,
    InvalidStatisticalSpec,
    NumericSample,
    StatisticalResult,
    StatisticalSpec,
    compute,
    validate_spec,
)


def test_midrank_fixture() -> None:
    spec = EmpiricalPercentileSpec([0, 1, 2, 3, 9, 10], "points")
    assert validate_spec(spec) is None
    assert isinstance(spec, StatisticalSpec.__value__)
    result = compute(NumericSample([1, 1, 3, 9], "points"), spec)
    assert isinstance(result, EmpiricalPercentileResult)
    assert isinstance(result, StatisticalResult.__value__)
    assert result == EmpiricalPercentileResult(
        (
            EmpiricalPercentileQueryResult(0.0, 0, 0, 4, 0.0),
            EmpiricalPercentileQueryResult(1.0, 0, 2, 2, 0.25),
            EmpiricalPercentileQueryResult(2.0, 2, 0, 2, 0.5),
            EmpiricalPercentileQueryResult(3.0, 2, 1, 1, 0.625),
            EmpiricalPercentileQueryResult(9.0, 3, 1, 0, 0.875),
            EmpiricalPercentileQueryResult(10.0, 4, 0, 0, 1.0),
        ),
        4,
        "points",
    )
    assert result.method == "empirical_percentile"
    assert result.estimator == "midrank_v1"
    for row in result.query_results:
        assert type(row.query) is type(row.percentile) is float
        assert all(type(c) is int for c in (row.less_count, row.equal_count, row.greater_count))
        assert row.less_count + row.equal_count + row.greater_count == result.sample_count


@pytest.mark.parametrize(
    ("values", "queries", "expected"),
    [
        ([4, 4, 4], [4], [(0, 3, 0, 0.5)]),
        ([4], [3, 4, 5], [(0, 0, 1, 0), (0, 1, 0, 0.5), (1, 0, 0, 1)]),
        ([-9, -3, -3, -1], [-10, -3, 0], [(0, 0, 4, 0), (1, 2, 1, 0.5), (4, 0, 0, 1)]),
        ([-0.0, 0.0, -1, 1], [0.0, -0.0], [(1, 2, 1, 0.5)] * 2),
        (
            [1, 1, 3, 9],
            [9, 0, 9, 1],
            [(3, 1, 0, 0.875), (0, 0, 4, 0), (3, 1, 0, 0.875), (0, 2, 2, 0.25)],
        ),
        (
            [1.0, math.nextafter(1.0, 2.0)],
            [1.0, math.nextafter(1.0, 2.0)],
            [(0, 1, 1, 0.25), (1, 1, 0, 0.75)],
        ),
        ([0.1 + 0.2], [0.3, 0.1 + 0.2], [(0, 0, 1, 0), (0, 1, 0, 0.5)]),
        ([2**53, 2**53 + 1], [2**53 + 1], [(0, 2, 0, 0.5)]),
        (
            [-float.fromhex("0x1.fffffffffffffp+1023"), float.fromhex("0x1.fffffffffffffp+1023")],
            [0],
            [(1, 0, 1, 0.5)],
        ),
    ],
)
def test_edge_cases(values: Any, queries: Any, expected: Any) -> None:
    result = compute(NumericSample(values, "u"), EmpiricalPercentileSpec(queries, "u"))
    assert isinstance(result, EmpiricalPercentileResult)
    assert [r.query for r in result.query_results] == list(map(float, queries))
    assert [
        (r.less_count, r.equal_count, r.greater_count, r.percentile) for r in result.query_results
    ] == expected
    if queries == [0.0, -0.0]:
        assert math.copysign(1, result.query_results[0].query) == 1
        assert math.copysign(1, result.query_results[1].query) == -1


@pytest.mark.parametrize("unit", ["U", " u ", " "])
def test_units(unit: str) -> None:
    spec = EmpiricalPercentileSpec([1], unit)
    assert validate_spec(spec) is None
    result = compute(NumericSample([1], unit), spec)
    assert result.unit == unit
    with pytest.raises(InvalidStatisticalSpec):
        compute(NumericSample([1], unit + "x"), spec)


@pytest.mark.parametrize(
    "bad",
    [
        [],
        True,
        "1",
        {1},
        {"x": 1},
        [[1]],
        [True],
        ["1"],
        [Decimal("1")],
        [None],
        [complex(1)],
        [float("nan")],
        [float("inf")],
        [-float("inf")],
        [10**400],
    ],
)
def test_invalid_coordinates(bad: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        EmpiricalPercentileSpec(bad, "u")
    with pytest.raises(InvalidSample):
        compute(NumericSample(bad, "u"), EmpiricalPercentileSpec([1], "u"))


@pytest.mark.parametrize("bad", ["", None, 1, True])
def test_invalid_unit(bad: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        EmpiricalPercentileSpec([1], bad)


@pytest.mark.parametrize(
    ("field", "bad"),
    [("queries", ()), ("queries", [1.0]), ("queries", (True,)), ("unit", ""), ("method", "ecdf")],
)
def test_sample_first_and_compute_revalidation(field: str, bad: Any, monkeypatch: Any) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("backend called before input validation")

    monkeypatch.setattr(np, "sort", forbidden)
    spec = EmpiricalPercentileSpec([1], "u")
    object.__setattr__(spec, field, bad)
    with pytest.raises(InvalidStatisticalSpec):
        validate_spec(spec)
    with pytest.raises(InvalidStatisticalSpec):
        compute(NumericSample([1], "u"), spec)
    sample = NumericSample([1], "u")
    object.__setattr__(sample, "values", ())
    with pytest.raises(InvalidSample):
        compute(sample, spec)
    with pytest.raises(InvalidSample):
        compute(None, spec)


def test_immutability_and_determinism() -> None:
    values, queries = [9, 1, 3, 1], [9, 1, 9, 0]
    sample, spec = NumericSample(values, "u"), EmpiricalPercentileSpec(queries, "u")
    result = compute(sample, spec)
    assert compute(sample, spec) == result
    assert values == [9, 1, 3, 1] and queries == [9, 1, 9, 0]
    values[0], queries[0] = 100, 100
    assert sample.values == (9, 1, 3, 1) and spec.queries == (9, 1, 9, 0)
    assert compute(sample, spec) == result
    with pytest.raises(FrozenInstanceError):
        spec.unit = "changed"
    with pytest.raises(FrozenInstanceError):
        result.unit = "changed"
    with pytest.raises(FrozenInstanceError):
        result.query_results[0].percentile = 1


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [1.0, 1.0, 3.0, 9.0],
        np.array([1.0, 1.0, 3.0]),
        np.array([[1.0, 1.0, 3.0, 9.0]]),
        np.array([1, 1, 3, 9]),
        np.array([1.0, 1.0, 3.0, 9.0], dtype=np.float32),
        np.array([1.0, 1.0, 3.0, np.nan]),
        np.array([1.0, 1.0, 3.0, np.inf]),
        np.array([9.0, 1.0, 1.0, 3.0]),
        np.array([1.0, 3.0, 3.0, 9.0]),
        np.array([1.0, 1.0, 3.0, 10.0]),
    ],
)
def test_malformed_sort(payload: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr(np, "sort", lambda *a, **kw: payload)
    with pytest.raises(CalculationFailure, match="empirical_percentile"):
        compute(NumericSample([1, 1, 3, 9], "u"), EmpiricalPercentileSpec([1, 9], "u"))


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize(
    "payload",
    [
        None,
        [0, 3],
        np.array(0),
        np.array([[0, 3]]),
        np.array([0]),
        np.array([0, 3, 4]),
        np.array([0.0, 3.0]),
        np.array([True, False]),
        np.array([0, 3], dtype=object),
        np.array([np.nan, 3]),
        np.array([0, np.inf]),
        np.array([-1, 3]),
        np.array([0, 5]),
        np.array([2**64 - 1, 3], dtype=np.uint64),
        np.array([3, 0]),
        np.array([1, 3]),
        np.array([0, 4]),
    ],
)
def test_malformed_searchsorted(side: str, payload: Any, monkeypatch: Any) -> None:
    original = np.searchsorted

    def injected(a: Any, v: Any, *, side: str) -> Any:
        return payload if side == selected else original(a, v, side=side)

    selected = side
    monkeypatch.setattr(np, "searchsorted", injected)
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([1, 1, 3, 9], "u"), EmpiricalPercentileSpec([1, 9], "u"))
    assert caught.value.method == "empirical_percentile" and caught.value.reason


@pytest.mark.parametrize("backend", ["sort", "searchsorted"])
@pytest.mark.parametrize("mode", ["exception", "warning", "arithmetic"])
def test_backend_failure_boundary(backend: str, mode: str, monkeypatch: Any) -> None:
    original = getattr(np, backend)
    error = ValueError("backend defect")

    def fail(*args: Any, **kwargs: Any) -> Any:
        if mode == "exception":
            raise error
        if mode == "warning":
            warnings.warn("invalid numerical execution", RuntimeWarning, stacklevel=2)
        else:
            np.subtract(np.float64(1e308), np.float64(-1e308))
        return original(*args, **kwargs)

    filters, errors = warnings.filters[:], np.geterr().copy()
    monkeypatch.setattr(np, backend, fail)
    with pytest.raises(CalculationFailure) as caught:
        compute(NumericSample([1, 3], "u"), EmpiricalPercentileSpec([1], "u"))
    assert caught.value.method == "empirical_percentile"
    assert caught.value.__cause__ is not None
    if mode == "exception":
        assert caught.value.__cause__ is error
    assert warnings.filters == filters and np.geterr() == errors
