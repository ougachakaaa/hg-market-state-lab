"""Independently executable public examples: pytest this file or either test node."""

from dataclasses import fields, is_dataclass
from typing import Any

import market_statistics as statistics


def test_quantile_example() -> None:
    sample = statistics.NumericSample(values=[3, 1, 1, 9], unit="points")
    spec = statistics.QuantileSpec(points=[0, 0.25, 0.5, 0.75, 1])
    result = statistics.compute(sample, spec)
    assert isinstance(result, statistics.QuantileResult)
    assert result.method == "quantile"
    assert result.estimator == "type7_linear_v1"
    assert result.points_and_values == ((0, 1), (0.25, 1), (0.5, 2), (0.75, 4.5), (1, 9))
    assert result.sample_count == 4
    assert result.unit == "points"


def test_interval_count_example() -> None:
    sample = statistics.NumericSample(values=[-1, 0, 1, 1, 2, 3], unit="points")
    spec = statistics.IntervalCountSpec(edges=[0, 1, 2], unit="points")
    result = statistics.compute(sample, spec)
    assert isinstance(result, statistics.IntervalCountResult)
    assert [bin_.count for bin_ in result.bins] == [1, 3]
    assert result.underflow_count == result.overflow_count == 1
    assert result.sample_count == 6
    assert (
        sum(bin_.count for bin_ in result.bins) + (result.underflow_count + result.overflow_count)
        == 6
    )
    assert [bin_.frequency for bin_ in result.bins] == [1 / 6, 3 / 6]
    assert result.underflow_frequency == result.overflow_frequency == 1 / 6


def test_complete_facade_exports() -> None:
    for name in (
        "NumericSample",
        "QuantileSpec",
        "IntervalCountSpec",
        "QuantileResult",
        "IntervalCountResult",
        "StatisticalSpec",
        "StatisticalResult",
        "StatisticalFailure",
        "InvalidSample",
        "InvalidStatisticalSpec",
        "CalculationFailure",
        "validate_spec",
        "compute",
    ):
        assert getattr(statistics, name) is not None
    assert not hasattr(statistics, "__all__")
    assert isinstance(statistics.QuantileSpec([0.5]), statistics.StatisticalSpec.__value__)
    assert isinstance(
        statistics.IntervalCountSpec([0, 1], "u"), statistics.StatisticalSpec.__value__
    )


def test_public_result_tree_contains_only_immutable_python_values() -> None:
    def visit(value: Any) -> None:
        if is_dataclass(value):
            for field in fields(value):
                visit(getattr(value, field.name))
        elif type(value) is tuple:
            for item in value:
                visit(item)
        else:
            assert type(value) in (str, int, float, bool)

    sample = statistics.NumericSample([1, 2, 3], "u")
    for spec in (
        statistics.QuantileSpec([0, 0.25, 0.75, 1]),
        statistics.IntervalCountSpec([0, 2, 4], "u"),
    ):
        result = statistics.compute(sample, spec)
        assert isinstance(result, statistics.StatisticalResult.__value__)
        visit(result)
