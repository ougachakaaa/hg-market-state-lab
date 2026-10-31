"""Greedy PIP selection under the vertical-error-bounded V1 contract."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class PipResult:
    """Original indices and actual maximum reconstruction error."""

    indices: tuple[int, ...]
    max_reconstruction_error: float
    algorithm_id: str = "pip_vertical_error_bounded_v1"


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a real number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be finite binary64") from exc
    if not isfinite(number):
        raise ValueError(f"{name} must be finite binary64")
    return number


def _finite(value: float) -> float:
    if not isfinite(value):
        raise ArithmeticError("non-finite PIP intermediate calculation")
    return value


def find_pips(values: Sequence[float], *, epsilon: float) -> PipResult:
    """Select original indices until the actual vertical error is at most epsilon.

    Inputs are finite Python integers or floats convertible to binary64; booleans
    and text containers are rejected. Calculation uses Python binary64 floats.
    """
    if not isinstance(values, Sequence) or isinstance(values, str | bytes | bytearray):
        raise TypeError("values must be a sequence of numbers")
    if len(values) < 2:
        raise ValueError("values must contain at least two numbers")
    y = tuple(_number(value, "value") for value in values)
    threshold = _number(epsilon, "epsilon")
    if threshold <= 0.0:
        raise ValueError("epsilon must be positive")

    indices = [0, len(y) - 1]
    while True:
        maximum = 0.0
        candidate = None
        for a, b in zip(indices, indices[1:], strict=False):
            if b == a + 1:
                continue
            delta = _finite(y[b] - y[a])
            width = _finite(float(b - a))
            for i in range(a + 1, b):
                offset = _finite(float(i - a))
                product = _finite(delta * offset)
                fraction = _finite(product / width)
                reconstructed = _finite(y[a] + fraction)
                error = abs(_finite(y[i] - reconstructed))
                if candidate is None or error > maximum:
                    maximum, candidate = error, i
        if candidate is None or maximum <= threshold:
            result_indices = tuple(indices)
            if (
                result_indices[0] != 0
                or result_indices[-1] != len(y) - 1
                or any(a >= b for a, b in zip(result_indices, result_indices[1:], strict=False))
                or not isfinite(maximum)
                or maximum > threshold
            ):
                raise ArithmeticError("invalid PIP result")
            return PipResult(result_indices, maximum)
        indices.insert(next(j for j, index in enumerate(indices) if index > candidate), candidate)
