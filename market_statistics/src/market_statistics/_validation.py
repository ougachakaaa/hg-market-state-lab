"""Shared public-coordinate legality; no backend coercion or business meanings."""

from collections.abc import Sequence
from math import isfinite

from .failures import InvalidSample, InvalidStatisticalSpec

type ValidationError = type[InvalidSample] | type[InvalidStatisticalSpec]


def coordinates(value: object, error: ValidationError, minimum: int = 1) -> tuple[float, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise error("Expected an ordered one-dimensional numeric sequence")
    if len(value) < minimum:
        raise error(f"Expected at least {minimum} numeric coordinates")
    converted: list[float] = []
    for scalar in value:
        if type(scalar) not in (int, float):
            raise error("Coordinates must be built-in int or float, excluding bool")
        try:
            number = float(scalar)
        except (OverflowError, ValueError) as exc:
            raise error("Coordinate cannot be represented as binary64") from exc
        if not isfinite(number):
            raise error("Coordinates must be finite binary64 values")
        converted.append(number)
    return tuple(converted)


def unit(value: object, error: ValidationError) -> None:
    if not isinstance(value, str) or not value:
        raise error("Unit must be a non-empty opaque string")


def increasing(values: tuple[float, ...]) -> None:
    if any(left >= right for left, right in zip(values, values[1:], strict=False)):
        raise InvalidStatisticalSpec("Coordinates must be strictly increasing after conversion")
