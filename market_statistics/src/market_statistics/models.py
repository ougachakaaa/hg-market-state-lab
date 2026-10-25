"""Immutable public numerical carriers, with owned binary64 coordinates."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from ._validation import coordinates, increasing, unit
from .failures import InvalidSample, InvalidStatisticalSpec


@dataclass(frozen=True, slots=True, init=False)
class NumericSample:
    values: tuple[float, ...]
    unit: str

    def __init__(self, values: Sequence[int | float], unit: str) -> None:
        object.__setattr__(self, "values", coordinates(values, InvalidSample))
        object.__setattr__(self, "unit", unit)
        self._validate()

    def _validate(self) -> None:
        coordinates(self.values, InvalidSample)
        if type(self.values) is not tuple or any(type(value) is not float for value in self.values):
            raise InvalidSample("NumericSample must retain its owned binary64 tuple")
        unit(self.unit, InvalidSample)

    @property
    def sample_count(self) -> int:
        return len(self.values)


@dataclass(frozen=True, slots=True, init=False)
class QuantileSpec:
    points: tuple[float, ...]
    method: Literal["quantile"] = "quantile"

    def __init__(self, points: Sequence[int | float]) -> None:
        object.__setattr__(self, "method", "quantile")
        object.__setattr__(self, "points", coordinates(points, InvalidStatisticalSpec))
        self._validate()

    def _validate(self) -> None:
        if type(self.method) is not str or self.method != "quantile":
            raise InvalidStatisticalSpec("Unknown Quantile method tag")
        points = coordinates(self.points, InvalidStatisticalSpec)
        if type(self.points) is not tuple or any(type(point) is not float for point in self.points):
            raise InvalidStatisticalSpec("QuantileSpec must retain its owned binary64 tuple")
        increasing(points)
        if any(point < 0 or point > 1 for point in points):
            raise InvalidStatisticalSpec("Quantile points must lie in [0, 1]")


@dataclass(frozen=True, slots=True, init=False)
class IntervalCountSpec:
    edges: tuple[float, ...]
    unit: str
    method: Literal["interval_count"] = "interval_count"

    def __init__(self, edges: Sequence[int | float], unit: str) -> None:
        object.__setattr__(self, "method", "interval_count")
        object.__setattr__(self, "edges", coordinates(edges, InvalidStatisticalSpec, 2))
        object.__setattr__(self, "unit", unit)
        self._validate()

    def _validate(self) -> None:
        if type(self.method) is not str or self.method != "interval_count":
            raise InvalidStatisticalSpec("Unknown IntervalCount method tag")
        increasing(coordinates(self.edges, InvalidStatisticalSpec, 2))
        if type(self.edges) is not tuple or any(type(edge) is not float for edge in self.edges):
            raise InvalidStatisticalSpec("IntervalCountSpec must retain its owned binary64 tuple")
        unit(self.unit, InvalidStatisticalSpec)


type StatisticalSpec = QuantileSpec | IntervalCountSpec


@dataclass(frozen=True, slots=True)
class QuantileResult:
    points_and_values: tuple[tuple[float, float], ...]
    sample_count: int
    unit: str
    method: Literal["quantile"] = "quantile"
    estimator: Literal["type7_linear_v1"] = "type7_linear_v1"


@dataclass(frozen=True, slots=True)
class IntervalBin:
    left: float
    right: float
    left_inclusive: bool
    right_inclusive: bool
    count: int
    frequency: float


@dataclass(frozen=True, slots=True)
class IntervalCountResult:
    edges: tuple[float, ...]
    bins: tuple[IntervalBin, ...]
    underflow_count: int
    overflow_count: int
    underflow_frequency: float
    overflow_frequency: float
    sample_count: int
    unit: str
    method: Literal["interval_count"] = "interval_count"


type StatisticalResult = QuantileResult | IntervalCountResult
