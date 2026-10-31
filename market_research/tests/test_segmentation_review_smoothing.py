"""Review merging preserves the canonical partition and endpoint facts."""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from segmentation_review_smoothing import Profile, smooth


def base(prices: list[float], indices: list[int]) -> tuple:
    origin = date(2024, 1, 1)
    return tuple(
        SimpleNamespace(
            start_index=a,
            end_index=b,
            start_date=origin + timedelta(days=a),
            end_date=origin + timedelta(days=b),
            start_close=x,
            end_close=y,
        )
        for a, b, x, y in zip(indices[:-1], indices[1:], prices[:-1], prices[1:], strict=True)
    )


def test_sandwich_priority_and_traceability() -> None:
    source = base([100, 110, 109, 120, 100], [0, 3, 4, 8, 12])
    before = tuple(vars(s).copy() for s in source)
    result = smooth(source, Profile(1, 0))
    assert result == smooth(source, Profile(1, 0))
    assert [s.base_segments for s in result] == [(0, 1, 2), (3,)]
    assert tuple(i for s in result for i in s.base_segments) == tuple(range(len(source)))
    assert result[0].start_index == 0 and result[-1].end_index == 12
    assert all(a.end_index == b.start_index for a, b in zip(result, result[1:], strict=False))
    assert all(s.duration_sessions == s.end_index - s.start_index > 0 for s in result)
    assert all(s.amplitude_ratio == s.end_close / s.start_close - 1 for s in result)
    assert tuple(vars(s).copy() for s in source) == before


def test_tiny_amplitude_and_final_segment_merge() -> None:
    source = base([100, 110, 110.5], [0, 5, 9])
    result = smooth(source, Profile(0, 0.01))
    assert len(result) == 1 and result[0].base_segments == (0, 1)
    assert smooth(source, Profile(0, 0)) == smooth(source, Profile(0, 0))
    assert len(smooth(source, Profile(0, 0))) == 2


def test_invalid_threshold_and_discontinuity() -> None:
    with pytest.raises(ValueError):
        Profile(0, float("nan"))
    source = base([100, 110, 105], [0, 2, 4])
    source[1].start_index = 3
    with pytest.raises(ValueError, match="continuous"):
        smooth(source, Profile(1, 0))
