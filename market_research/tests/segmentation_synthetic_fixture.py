"""Synthetic public-export evidence for offline review regressions."""

import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

from data_lake import CoverageResult, EnsureResult
from market_research.descriptive.cases.price_segmentation import (
    SegmentationRequest,
    observe_price_segments,
)
from observation_fixtures import CalendarFake, IndexFake
from segmentation_live_e2e import verify


def write_evidence(path: Path) -> Path:
    start, end = date(2024, 1, 8), date(2024, 2, 29)
    days = tuple(start + timedelta(days=i * 3) for i in range(12))
    prices = (100.0, 103.0, 101.0, 105.0, 104.0, 109.0,
              102.0, 104.0, 101.0, 108.0, 105.0, 110.0)
    calendar = CalendarFake(days)
    index = IndexFake(days, dict(zip(days, prices, strict=True)))
    index.transform = lambda view: replace(
        view,
        records=tuple(replace(row, index_code="000852.SH", symbol="000852", name="中证1000")
                      for row in view.records),
    )
    for service, count in ((calendar, (end - start).days + 1), (index, len(days))):
        original = service.transform
        service.transform = lambda view, original=original: replace(
            original(view), records=(),
            coverage=CoverageResult(view.coverage.requested_units, 0,
                                    view.coverage.requested_units, 0, 0, False),
        )
        service.after_ensure = original
        service.ensure_value = EnsureResult(count, 0, count, count, 0, count, True, ())
    result = observe_price_segments(
        SegmentationRequest("000852.SH", start, end, 0.01),
        calendar_service=calendar, index_service=index,
    )
    scenario = verify(result)
    report = {"executed_at_utc": "synthetic", "tested_sha": "synthetic", "scenarios": [scenario]}
    path.write_text(json.dumps(report), encoding="utf-8")
    return path
