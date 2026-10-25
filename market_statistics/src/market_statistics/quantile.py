"""Type 7 NumPy adapter preserving the frozen binary64 branches."""

from math import floor, isfinite

import numpy as np

from .failures import CalculationFailure
from .models import NumericSample, QuantileResult, QuantileSpec


def quantile(sample: NumericSample, spec: QuantileSpec) -> QuantileResult:
    values = sorted(sample.values)
    answers: dict[float, float] = {}
    interpolations: list[tuple[float, int, float, float]] = []
    for point in spec.points:
        h = (sample.sample_count - 1) * point
        j = floor(h)
        g = h - j
        if point == 0 or sample.sample_count == 1:
            answers[point] = values[0]
        elif point == 1:
            answers[point] = values[-1]
        elif g == 0:
            answers[point] = values[j]
        else:
            difference = values[j + 1] - values[j]
            if not isfinite(difference):
                raise CalculationFailure(spec.method, "Type 7 interpolation difference overflowed")
            interpolations.append((point, j, g, difference))

    if interpolations:
        raw = np.quantile(
            np.array(values, dtype=np.float64),
            [item[0] for item in interpolations],
            method="linear",
        )
        if (
            not isinstance(raw, np.ndarray)
            or raw.shape != (len(interpolations),)
            or raw.dtype != np.dtype(np.float64)
            or not np.all(np.isfinite(raw))
        ):
            raise CalculationFailure(spec.method, "Malformed or non-finite NumPy quantile result")
        for (point, j, g, difference), backend_value in zip(interpolations, raw, strict=True):
            value = float(backend_value)
            if not values[j] <= value <= values[j + 1]:
                raise CalculationFailure(spec.method, "Quantile lies outside its order statistics")
            # NumPy's upper-half lerp subtracts from the right endpoint. Only this
            # branch needs the published left + g * difference operation order.
            if g >= 0.5:
                scaled = g * difference
                value = values[j] + scaled
                if not isfinite(scaled) or not isfinite(value):
                    raise CalculationFailure(spec.method, "Type 7 interpolation overflowed")
            answers[point] = value

    payload = tuple((point, answers[point]) for point in spec.points)
    if len(payload) != len(spec.points) or any(not isfinite(value) for _, value in payload):
        raise CalculationFailure(spec.method, "Invalid Quantile result")
    return QuantileResult(payload, sample.sample_count, sample.unit)
