"""Public coordinate legality, immutable ownership and validation precedence."""

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from market_statistics import (
    IntervalCountSpec,
    InvalidSample,
    InvalidStatisticalSpec,
    NumericSample,
    QuantileSpec,
    StatisticalFailure,
    compute,
    validate_spec,
)


@pytest.mark.parametrize(
    "values",
    [
        [],
        True,
        1,
        1.0,
        "123",
        b"123",
        bytearray(b"123"),
        None,
        {1: 2},
        {1, 2},
        iter([1, 2]),
        [[1]],
        [(1,)],
        [True],
        [None],
        ["1"],
        [Decimal("1")],
        [Fraction(1, 2)],
        [1j],
        [np.int64(1)],
        [np.float64(1)],
        [float("nan")],
        [float("inf")],
        [float("-inf")],
        [10**400],
    ],
)
def test_illegal_samples(values: Any) -> None:
    with pytest.raises(InvalidSample):
        NumericSample(values, "unit")


@pytest.mark.parametrize("unit", ["", None, 1, True, b"points"])
def test_illegal_sample_units(unit: Any) -> None:
    with pytest.raises(InvalidSample):
        NumericSample([1], unit)


def test_owned_coordinates_conversion_and_no_business_metadata() -> None:
    source = [3, 1, 1, 2**53 + 1, -0.0]
    sample = NumericSample(source, " Points ")
    source[:] = [99]
    assert sample.values == (3.0, 1.0, 1.0, float(2**53), -0.0)
    assert all(type(value) is float for value in sample.values)
    assert sample.sample_count == 5
    assert sample.unit == " Points "
    assert {field.name for field in fields(sample)} == {"values", "unit"}
    with pytest.raises(FrozenInstanceError):
        sample.unit = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        sample.values[0] = 99  # type: ignore[index]


@pytest.mark.parametrize("values", [[7], (1, 2.5), range(3)])
def test_valid_ordered_samples(values: Any) -> None:
    sample = NumericSample(values, "points")
    assert sample.values == tuple(float(value) for value in values)
    assert sample.sample_count == len(values)


@pytest.mark.parametrize(
    "points",
    [
        [],
        [0.5, 0.5],
        [1, 0],
        [-0.1],
        [1.1],
        [True],
        ["0.5"],
        [None],
        [float("nan")],
        [float("inf")],
        [10**400],
        [[0.5]],
        "auto",
        {0, 1},
        {0: 1},
        [0.5, 0.5 + 1e-20],
        [Decimal("0.5")],
    ],
)
def test_illegal_quantile_specs(points: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        QuantileSpec(points)


@pytest.mark.parametrize(
    "edges",
    [
        [],
        [0],
        [0, 0],
        [2, 1],
        [False, 1],
        ["0", 1],
        [0, None],
        [0, float("nan")],
        [0, float("inf")],
        [0, float("-inf")],
        [0, 10**400],
        [[0], [1]],
        "auto",
        10,
        {0, 1},
        {0: 1},
        [2**53, 2**53 + 1],
        [Decimal("0"), 1],
    ],
)
def test_illegal_interval_specs(edges: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        IntervalCountSpec(edges, "points")


@pytest.mark.parametrize("unit", ["", None, 1, True])
def test_illegal_interval_units(unit: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        IntervalCountSpec([0, 1], unit)


def test_spec_preflight_is_sample_free_and_copies_inputs() -> None:
    points = [0, 0.5, 1]
    edges = [0, 1, 2]
    quantile = QuantileSpec(points)
    interval = IntervalCountSpec(edges, " Points ")
    points.clear()
    edges.clear()
    assert quantile.points == (0, 0.5, 1)
    assert interval.edges == (0, 1, 2)
    assert interval.unit == " Points "
    preflight: Any = validate_spec
    assert preflight(quantile) is None
    assert preflight(interval) is None
    with pytest.raises(FrozenInstanceError):
        quantile.points = (1,)  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        interval.unit = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("wrong", [None, {}, {"method": "unknown"}, [], "quantile", 1])
def test_wrong_public_variants_and_sample_precedence(wrong: Any) -> None:
    with pytest.raises(InvalidStatisticalSpec):
        validate_spec(wrong)
    with pytest.raises(InvalidSample):
        compute(wrong, wrong)
    with pytest.raises(InvalidStatisticalSpec):
        compute(NumericSample([1], "points"), wrong)


@pytest.mark.parametrize(
    "factory", [lambda: QuantileSpec([0.5]), lambda: IntervalCountSpec([0, 1], "points")]
)
def test_unknown_method_is_rejected_on_revalidation(factory: Any) -> None:
    spec = factory()
    object.__setattr__(spec, "method", "unknown")
    with pytest.raises(InvalidStatisticalSpec):
        validate_spec(spec)
    with pytest.raises(InvalidStatisticalSpec):
        compute(NumericSample([1], "points"), spec)


def test_compute_rechecks_stored_sample_and_spec_before_backend(monkeypatch: Any) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Backend called before validation finished")

    monkeypatch.setattr(np, "quantile", forbidden)
    sample = NumericSample([1, 3], "points")
    spec = QuantileSpec([0.25])
    object.__setattr__(sample, "values", (float("nan"),))
    object.__setattr__(spec, "points", ())
    with pytest.raises(InvalidSample):
        compute(sample, spec)
    with pytest.raises(InvalidStatisticalSpec):
        compute(NumericSample([1, 3], "points"), spec)


@pytest.mark.parametrize("values", [[1.0, 2.0], (2**53 + 1, 2**53 + 2)])
def test_revalidation_rejects_bypassed_sample_storage(values: Any) -> None:
    sample = NumericSample([1, 2], "u")
    object.__setattr__(sample, "values", values)
    with pytest.raises(InvalidSample):
        compute(sample, QuantileSpec([0, 1]))


@pytest.mark.parametrize("field", ["points", "edges"])
def test_revalidation_rejects_bypassed_spec_storage(field: str) -> None:
    spec = QuantileSpec([0, 1]) if field == "points" else IntervalCountSpec([0, 1], "u")
    object.__setattr__(spec, field, [0.0, 1.0])
    with pytest.raises(InvalidStatisticalSpec):
        validate_spec(spec)


@pytest.mark.parametrize("model", [NumericSample, QuantileSpec, IntervalCountSpec])
def test_incomplete_objects_use_public_categories(model: Any) -> None:
    incomplete = object.__new__(model)
    if model is NumericSample:
        with pytest.raises(InvalidSample):
            compute(incomplete, QuantileSpec([0.5]))
    else:
        with pytest.raises(InvalidStatisticalSpec):
            validate_spec(incomplete)


def test_unit_compatibility_is_exact_and_only_at_compute() -> None:
    spec = IntervalCountSpec([0, 1], "points")
    preflight: Any = validate_spec
    assert preflight(spec) is None
    for unit in ("Points", " points", "points "):
        with pytest.raises(InvalidStatisticalSpec):
            compute(NumericSample([0], unit), spec)
    assert compute(NumericSample([0], "points"), spec).unit == "points"
    assert issubclass(InvalidSample, StatisticalFailure)
    assert issubclass(InvalidStatisticalSpec, StatisticalFailure)
