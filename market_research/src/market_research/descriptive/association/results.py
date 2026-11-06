"""Request linkage and bounded result shape/accounting, never computation verification."""

from math import isfinite

from market_statistics import (
    IntervalBin,
    IntervalCountResult,
    IntervalCountSpec,
    NumericSample,
    QuantileResult,
    QuantileSpec,
    StatisticalResult,
    StatisticalSpec,
)

from .source import require


def _float(value: float) -> bool:
    return type(value) is float and isfinite(value)


def _coordinates(actual: tuple[float, ...], expected: tuple[float, ...]) -> bool:
    return (
        type(actual) is tuple
        and len(actual) == len(expected)
        and all(
            _float(value) and value.hex() == wanted.hex()
            for value, wanted in zip(actual, expected, strict=True)
        )
    )


def _account(count: int, frequency: float, size: int) -> None:
    require(type(count) is int and 0 <= count <= size, "Invalid result count")
    require(
        _float(frequency) and 0 <= frequency <= 1 and frequency == count / size,
        "Result frequency must equal retained count/sample_count",
    )


def validate_result(
    sample: NumericSample,
    spec: StatisticalSpec,
    result: StatisticalResult,
) -> None:
    require(
        isinstance(spec, QuantileSpec | IntervalCountSpec), "Unsupported scalar association method"
    )
    require(type(result) in (QuantileResult, IntervalCountResult), "Wrong public result variant")
    require(
        type(result.sample_count) is int and result.sample_count == sample.sample_count,
        "Result/sample count mismatch",
    )
    require(
        isinstance(result.unit, str) and bool(result.unit) and result.unit == sample.unit,
        "Result/sample unit mismatch",
    )
    if isinstance(spec, QuantileSpec):
        require(type(result) is QuantileResult, "Quantile request requires QuantileResult")
        assert isinstance(result, QuantileResult)
        require(result.method == "quantile", "Wrong Quantile method tag")
        require(result.estimator == "type7_linear_v1", "Wrong Quantile estimator")
        pairs = result.points_and_values
        require(type(pairs) is tuple, "Quantile payload must be immutable")
        require(
            all(
                type(pair) is tuple and len(pair) == 2 and _float(pair[0]) and _float(pair[1])
                for pair in pairs
            ),
            "Malformed Quantile point/value pairs",
        )
        require(
            _coordinates(tuple(pair[0] for pair in pairs), spec.points),
            "Result Quantile points differ from the exact requested sequence",
        )
        return
    require(type(result) is IntervalCountResult, "Interval request requires IntervalCountResult")
    assert isinstance(result, IntervalCountResult)
    require(result.method == "interval_count", "Wrong IntervalCount method tag")
    assert isinstance(spec, IntervalCountSpec)
    require(spec.unit == sample.unit, "Interval spec/sample unit mismatch")
    require(
        _coordinates(result.edges, spec.edges), "Result edges differ from exact requested edges"
    )
    require(
        type(result.bins) is tuple and len(result.bins) == len(spec.edges) - 1,
        "Wrong IntervalCount bin shape",
    )
    for index, bin in enumerate(result.bins):
        require(type(bin) is IntervalBin, "Expected typed IntervalBin")
        require(
            _coordinates((bin.left, bin.right), spec.edges[index : index + 2])
            and bin.left_inclusive is True
            and bin.right_inclusive is (index == len(result.bins) - 1),
            "Interval bin geometry/closure differs from requested partition",
        )
        _account(bin.count, bin.frequency, sample.sample_count)
    _account(result.underflow_count, result.underflow_frequency, sample.sample_count)
    _account(result.overflow_count, result.overflow_frequency, sample.sample_count)
    require(
        sum(bin.count for bin in result.bins) + result.underflow_count + result.overflow_count
        == sample.sample_count,
        "Interval counts do not conserve sample_count",
    )
