"""Fixed request validation, direct public entry and dependency execution boundaries."""

import ast
import importlib
from dataclasses import FrozenInstanceError
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from market_research.descriptive.cases.trailing_return import construct_observations
from market_research.descriptive.observation import (
    DateWindow,
    InvalidObservationRequest,
    ObservationJobSpec,
    observe,
)
from observation_fixtures import CODE, DAYS, CalendarFake, IndexFake, job, pure_fixture

SOURCE = Path(__file__).resolve().parents[1] / "src/market_research"


@pytest.mark.parametrize(
    "changes",
    [
        {"subject": "000001"},
        {"subject": "000001.sh"},
        {"subject": "000001.SH "},
        {"subject": "CSI1000"},
        {"subject": "000001.CFFEX"},
        {"subject": 1},
        {"subject": ""},
        {"metric": "trailing_cumulative_return_v2"},
        {"metric": ""},
        {"metric": 1},
        {"metric_parameters": {"unexpected": 1}},
        {"metric_parameters": []},
        {"metric_parameters": None},
        {"horizon": True},
        {"horizon": False},
        {"horizon": 0},
        {"horizon": -1},
        {"horizon": 2.0},
        {"horizon": "2"},
        {"historical_sample_window": (DAYS[2], DAYS[4])},
        {"historical_sample_window": DateWindow(date.max, date.max)},
    ],
)
def test_invalid_fixed_request_fails_before_even_creating_upstream_services(
    changes: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preparation = importlib.import_module(
        "market_research.descriptive.cases.trailing_return.preparation"
    )

    def forbidden() -> None:
        pytest.fail("Invalid request reached upstream factory")

    monkeypatch.setattr(preparation, "create_calendar_service", forbidden)
    monkeypatch.setattr(preparation, "create_index_service", forbidden)
    values: dict[str, Any] = dict(
        subject=CODE,
        metric="trailing_cumulative_return_v1",
        metric_parameters={},
        horizon=2,
        historical_sample_window=DateWindow(DAYS[2], DAYS[4]),
    )
    values.update(changes)
    with pytest.raises(InvalidObservationRequest):
        observe(ObservationJobSpec(**values))


@pytest.mark.parametrize(
    "start,end",
    [
        ("2024-01-10", DAYS[4]),
        (DAYS[2], "2024-01-12"),
        (datetime(2024, 1, 10), DAYS[4]),
        (DAYS[2], datetime(2024, 1, 12)),
        (DAYS[4], DAYS[2]),
        (None, DAYS[4]),
    ],
)
def test_dates_are_explicit_date_values_with_ordered_inclusive_bounds(start: Any, end: Any) -> None:
    with pytest.raises(InvalidObservationRequest):
        DateWindow(start, end)


def test_request_parameters_and_result_are_immutable() -> None:
    parameters: dict[str, object] = {}
    spec = ObservationJobSpec(
        CODE, "trailing_cumulative_return_v1", parameters, 2, DateWindow(DAYS[2], DAYS[4])
    )
    parameters["late_mutation"] = True
    assert not spec.metric_parameters
    original_parameters = spec.metric_parameters
    _, prepared = pure_fixture()
    result = construct_observations(spec, prepared)
    assert spec.metric_parameters is original_parameters
    with pytest.raises(FrozenInstanceError):
        result.candidate_anchors = ()  # type: ignore[misc]
    with pytest.raises(TypeError):
        spec.metric_parameters["x"] = 1  # type: ignore[index]


def test_public_observe_composes_actual_preparation_and_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preparation = importlib.import_module(
        "market_research.descriptive.cases.trailing_return.preparation"
    )
    calendar = CalendarFake(DAYS[:5])
    index = IndexFake(DAYS[:5], {DAYS[0]: 100.0, DAYS[1]: 110.0, DAYS[3]: 90.0, DAYS[4]: 120.0})
    monkeypatch.setattr(preparation, "create_calendar_service", lambda: calendar)
    monkeypatch.setattr(preparation, "create_index_service", lambda: index)
    result = observe(job())
    assert result.candidate_count == 3
    assert result.eligible_count == 1
    assert result.unavailable_count == 2
    assert len(result.provenance.input_fingerprint) == 64
    assert result.provenance.prepared_inputs.index_slice is not None
    assert calendar.calls and index.calls


def test_no_candidate_public_observe_does_not_create_an_index_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preparation = importlib.import_module(
        "market_research.descriptive.cases.trailing_return.preparation"
    )
    monkeypatch.setattr(preparation, "create_calendar_service", lambda: CalendarFake(()))
    monkeypatch.setattr(
        preparation,
        "create_index_service",
        lambda: pytest.fail("No-candidate request created Index service"),
    )
    assert observe(job()).candidate_count == 0


def test_l_pure_construction_does_not_call_upstream_factories_or_service_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec, prepared = pure_fixture()
    for module in (
        "data_lake.datasets.tushare_trade_calendar",
        "data_lake.datasets.tushare_index_daily",
    ):
        public = importlib.import_module(module)
        monkeypatch.setattr(
            public, "create_service", lambda: pytest.fail("Construction acquired facts")
        )
        service = getattr(public, "TradeCalendarService", None) or public.IndexDailyService
        for operation in ("coverage", "ensure", "export"):
            monkeypatch.setattr(
                service,
                operation,
                lambda *args: pytest.fail("Construction called a public service"),
            )
    assert construct_observations(spec, prepared).eligible_count == 3


def test_only_published_datalake_imports_and_no_forbidden_dependency_edges() -> None:
    public = {
        "data_lake",
        "data_lake.datasets.tushare_trade_calendar",
        "data_lake.datasets.tushare_index_daily",
        "data_lake.datasets.tushare_equity_index_futures",
    }
    forbidden = (
        "data_snapshot",
        "ui_cli",
        "ui_http",
        "ui_web",
        "tushare",
        "sqlite3",
        "requests",
        "httpx",
    )
    for path in SOURCE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in modules:
                if name == "market_statistics" or name.startswith("market_statistics."):
                    assert path.relative_to(SOURCE).as_posix() in {
                        "descriptive/capabilities.py",
                        "descriptive/cases/futures_basis/statistics.py",
                    } or {
                        "conversion",
                        "association",
                        "execution",
                        "publication",
                    } & set(path.relative_to(SOURCE).parts), (
                        path,
                        name,
                    )
                    assert name == "market_statistics", (path, name)
                assert not any(
                    name == prefix or name.startswith(prefix + ".") for prefix in forbidden
                ), (path, name)
                if name.startswith("data_lake"):
                    assert name in public, (path, name)
                    if name == "data_lake.datasets.tushare_equity_index_futures":
                        assert (
                            path.relative_to(SOURCE)
                            .as_posix()
                            .startswith("descriptive/cases/futures_basis/")
                        ), (path, name)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"export", "ensure", "coverage"}:
                    assert path.name == "preparation.py", path


def test_public_facades_export_attributes_directly_without_all() -> None:
    facade = importlib.import_module("market_research.descriptive.observation")
    case = importlib.import_module("market_research.descriptive.cases.trailing_return")
    assert facade.ObservationJobSpec is ObservationJobSpec
    assert facade.observe is observe
    assert case.construct_observations is construct_observations
    assert not hasattr(facade, "__all__")
    assert not hasattr(case, "__all__")
