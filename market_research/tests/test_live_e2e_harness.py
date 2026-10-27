"""Safety and oracle regression only: these tests never obtain live market facts."""

import sqlite3
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from data_lake.adapters.outbound.sqlite import Repository
from live_e2e_acceptance import (
    ROOT,
    WINDOW,
    IsolationError,
    check_statistics,
    isolated_storage,
    verify_job,
)
from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.cases.trailing_return import prepare_inputs
from market_research.descriptive.execution import execute_job
from market_research.descriptive.observation import ObservationJobSpec
from market_statistics import IntervalCountSpec, QuantileResult, QuantileSpec
from observation_fixtures import CalendarFake, IndexFake


def test_isolation_checks_every_factory_and_rejects_escape(tmp_path: Path) -> None:
    with isolated_storage(tmp_path) as audit:
        assert audit["established_before_source"]
        assert list(tmp_path.iterdir()) == []
        with pytest.raises(IsolationError, match="Repository escaped"):
            Repository(tmp_path.parent / "outside.sqlite3", "tushare_index_daily", "tushare")
        with pytest.raises(IsolationError, match="connection escaped"):
            sqlite3.connect(":memory:")
    assert audit["default_cache_metadata_unchanged"]
    assert audit["repository_bindings"] == {"tushare_trade_calendar": 2, "tushare_index_daily": 1}
    assert audit["sqlite_connections"] == {}


def test_isolation_refuses_source_tree_and_existing_state(tmp_path: Path) -> None:
    for unsafe in (ROOT, tmp_path):
        if unsafe == tmp_path:
            (tmp_path / "existing.sqlite3").touch()
        with (
            pytest.raises(IsolationError, match="Isolation not established"),
            isolated_storage(unsafe),
        ):
            pytest.fail("Unsafe isolation context was entered")


@pytest.mark.parametrize("missing", [False, True])
def test_oracle_checks_full_chain_and_detects_wrong_statistics(missing: bool) -> None:
    # Explicit synthetic metadata used only to exercise the oracle, never live evidence.
    sessions = tuple(date(2024, 1, d) for d in (8, 9, 10, 11, 12, 15, 16))
    closes = {day: 100.0 + i * 3 for i, day in enumerate(sessions)}
    if missing:
        del closes[sessions[2]]
    index = IndexFake(sessions, closes)
    index.transform = lambda view: replace(
        view,
        records=tuple(
            replace(row, index_code="000852.SH", symbol="000852", name="中证1000")
            for row in view.records
        ),
    )
    # The partial Ensure diagnostics must use the explicit synthetic subject as well.
    if missing:
        from data_lake import EnsureResult, UnitFailure

        index.ensure_value = EnsureResult(
            7,
            6,
            1,
            0,
            1,
            0,
            False,
            (UnitFailure(("000852.SH", sessions[2]), "synthetic absent fact"),),
        )
    fixed = ObservationJobSpec("000852.SH", "trailing_cumulative_return_v1", {}, 2, WINDOW)
    requests = (
        AnalysisRequest("q", QuantileSpec([0.1, 0.5, 0.9])),
        AnalysisRequest("i", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
    )
    with patch(
        "market_research.descriptive.execution.api.prepare_inputs",
        side_effect=lambda job: prepare_inputs(
            job, calendar_service=CalendarFake(sessions), index_service=index
        ),
    ):
        result = execute_job(fixed, requests)
    report = verify_job(result, requests)
    assert report["independent_checks"] == "passed"
    assert report["counts"] == {
        "candidate": 5,
        "eligible": 3 if missing else 5,
        "unavailable": 2 if missing else 0,
        "excluded": 0,
    }
    outcome = result.analysis_outcomes[0]
    raw = outcome.statistical_result
    assert isinstance(raw, QuantileResult)
    assert result.projection is not None
    corrupt = replace(raw, points_and_values=((0.1, 42.0), (0.5, 42.0), (0.9, 42.0)))
    with pytest.raises(AssertionError, match="Independent Type 7"):
        check_statistics(
            result.projection.numeric_sample.values, (replace(outcome, statistical_result=corrupt),)
        )
