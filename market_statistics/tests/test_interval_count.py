"""Partition, closure, multiplicity, immutable outputs and population accounting."""

from dataclasses import FrozenInstanceError
from math import copysign, nextafter
from typing import Any

import numpy as np
import pytest

from market_statistics import IntervalCountResult, IntervalCountSpec, NumericSample, compute


@pytest.mark.parametrize(
    ("values", "edges", "counts", "underflow", "overflow"),
    [
        ([-1, 0, 1, 1, 2, 3], [0, 1, 2], [1, 3], 1, 1),
        ([0, 1, 2], [0, 2], [3], 0, 0),
        ([-2, -1, 3, 4], [0, 1, 2], [0, 0], 2, 2),
        ([0, 0, 1, 1, 2, 2, 3, 3], [0, 1, 2, 3], [2, 2, 4], 0, 0),
        ([1], [0, 1, 2], [0, 1], 0, 0),
        ([2], [0, 1, 2], [0, 1], 0, 0),
        ([-0.0, 0.0], [-0.0, 1], [2], 0, 0),
        ([-1e308, 0, 1e308], [-1e308, 1e308], [3], 0, 0),
        ([nextafter(0, -1), 0, nextafter(1, 0), 1, nextafter(1, 2)], [0, 1], [3], 1, 1),
    ],
)
def test_partition_fixtures(
    values: Any, edges: Any, counts: Any, underflow: int, overflow: int
) -> None:
    sample = NumericSample(values, "Points")
    spec = IntervalCountSpec(edges, "Points")
    result = compute(sample, spec)
    assert isinstance(result, IntervalCountResult)
    assert result.method == "interval_count"
    assert result.edges == tuple(edges)
    assert result.sample_count == len(values)
    assert result.unit == "Points"
    assert [bin_.count for bin_ in result.bins] == counts
    assert result.underflow_count == underflow
    assert result.overflow_count == overflow
    assert sum(bin_.count for bin_ in result.bins) + underflow + overflow == len(values)
    for i, bin_ in enumerate(result.bins):
        assert (bin_.left, bin_.right) == (edges[i], edges[i + 1])
        assert bin_.left_inclusive is True
        assert bin_.right_inclusive is (i == len(counts) - 1)
        assert type(bin_.count) is int
        assert type(bin_.frequency) is float
        assert bin_.frequency == counts[i] / len(values)
    assert result.underflow_frequency == underflow / len(values)
    assert result.overflow_frequency == overflow / len(values)
    assert sum(bin_.frequency for bin_ in result.bins) + result.underflow_frequency + (
        result.overflow_frequency
    ) == pytest.approx(1)
    assert sample.values == tuple(values)
    assert spec.edges == tuple(edges)
    with pytest.raises(FrozenInstanceError):
        result.bins[0].count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.edges = ()  # type: ignore[misc]


def test_signed_zero_boundary_is_retained() -> None:
    result = compute(NumericSample([0], "u"), IntervalCountSpec([-0.0, 1], "u"))
    assert isinstance(result, IntervalCountResult)
    assert copysign(1, result.edges[0]) == -1
    assert copysign(1, result.bins[0].left) == -1


def test_histogram_uses_explicit_edges_and_count_mode(monkeypatch: Any) -> None:
    original = np.histogram
    retained: list[Any] = []

    def backend(values: Any, **kwargs: Any) -> Any:
        assert kwargs.keys() == {"bins", "density"}
        assert kwargs["density"] is False
        assert tuple(kwargs["bins"]) == (0, 1, 2)
        raw = original(values, **kwargs)
        retained.append(raw)
        return raw

    monkeypatch.setattr(np, "histogram", backend)
    result = compute(NumericSample([-1, 0, 1, 1, 2, 3], "u"), IntervalCountSpec([0, 1, 2], "u"))
    assert isinstance(result, IntervalCountResult)
    retained[0][0][:] = 99
    retained[0][1][:] = 99
    assert result.edges == (0, 1, 2)
    assert tuple(bin_.count for bin_ in result.bins) == (1, 3)
