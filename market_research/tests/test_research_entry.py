"""Read-only publication and preview preserve the existing execution authority."""

from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.capabilities import (
    CapabilityNotFound,
    get_capability,
    list_capabilities,
)
from market_research.descriptive.execution import InvalidPlan, ResearchPlan, preview_plan
from market_research.descriptive.observation import DateWindow
from market_statistics import QuantileSpec


def plan() -> ResearchPlan:
    return ResearchPlan(
        "trailing_cumulative_return_v1",
        {},
        ["000852.SH", "000300.SH"],
        [2, 5],
        [
            DateWindow(date(2024, 1, 10), date(2024, 1, 16)),
            DateWindow(date(2024, 1, 11), date(2024, 1, 16)),
        ],
        [AnalysisRequest(" exact ID ", QuantileSpec([0.1, 0.5, 0.9]))],
        "continue",
    )


def test_single_immutable_declaration_and_unknown_id(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden() -> None:
        pytest.fail("read-only capability created upstream service")

    monkeypatch.setattr(
        "market_research.descriptive.cases.trailing_return.preparation.create_calendar_service",
        forbidden,
    )
    monkeypatch.setattr(
        "market_research.descriptive.cases.trailing_return.preparation.create_index_service",
        forbidden,
    )
    (descriptor,) = list_capabilities()
    assert descriptor is get_capability("trailing_cumulative_return_v1")
    assert descriptor.unit == "decimal_ratio"
    assert descriptor.subject.verified_example == "000852.SH"
    assert descriptor.live_readiness == "not_probed"
    assert [m.method for m in descriptor.analysis_methods] == ["quantile", "interval_count"]
    with pytest.raises(FrozenInstanceError):
        descriptor.name = "changed"  # type: ignore[misc]
    with pytest.raises(CapabilityNotFound):
        get_capability("stock_return")


def test_preview_reuses_complete_expansion_and_is_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object) -> None:
        pytest.fail("preview attempted a Job or upstream creation")

    monkeypatch.setattr("market_research.descriptive.execution.batch.execute_job", forbidden)
    monkeypatch.setattr(
        "market_research.descriptive.cases.trailing_return.preparation.create_calendar_service",
        forbidden,
    )
    original = plan()
    preview = preview_plan(original)
    assert preview.plan is original
    assert preview.planned_count == 8 and preview.analysis_attempt_count == 8
    assert [
        (
            j.fixed_job_spec.subject,
            j.fixed_job_spec.horizon,
            j.fixed_job_spec.historical_sample_window.start_date,
        )
        for j in preview.jobs
    ] == [
        (s, h, d)
        for s in original.subjects
        for h in original.horizons
        for d in (date(2024, 1, 10), date(2024, 1, 11))
    ]
    with pytest.raises(FrozenInstanceError):
        preview.jobs = ()  # type: ignore[misc]
    object.__setattr__(original, "subjects", ("000852.SH", "invalid"))
    with pytest.raises(InvalidPlan):
        preview_plan(original)
