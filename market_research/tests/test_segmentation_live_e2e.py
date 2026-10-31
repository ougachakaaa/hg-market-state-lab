"""Offline oracle regression; no live Source or default cache access."""

from dataclasses import replace
from datetime import date

import pytest

from market_research.descriptive.cases.price_segmentation import (
    SegmentationRequest,
    observe_price_segments,
)
from observation_fixtures import CalendarFake, IndexFake
from segmentation_live_e2e import verify


def test_oracle_checks_facts_and_rejects_changed_segment() -> None:
    days = tuple(date(2024, 1, d) for d in (8, 9, 10))
    cal = CalendarFake(days)
    idx = IndexFake(days, dict(zip(days, (100.0, 150.0, 110.0), strict=True)))
    idx.transform = lambda view: replace(
        view,
        records=tuple(
            replace(row, index_code="000852.SH", symbol="000852", name="中证1000")
            for row in view.records
        ),
    )
    req = SegmentationRequest("000852.SH", days[0], days[-1], 0.01)
    result = observe_price_segments(req, calendar_service=cal, index_service=idx)
    assert verify(result)["independent_checks"] == "passed"
    bad_segment = replace(result.segments[0], amplitude_ratio=42.0)
    with pytest.raises(AssertionError, match="Simple return"):
        verify(replace(result, segments=(bad_segment, *result.segments[1:])))
