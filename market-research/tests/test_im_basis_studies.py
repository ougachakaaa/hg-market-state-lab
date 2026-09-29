"""Shared semantics, retained studies, and full fake-Source vertical slice."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from typing import cast

import pandas as pd
import pytest

from market_research.shared.distribution import linear_quantile
from market_research.shared.im_basis import daily_im_basis
from market_research.studies.im_basis_baseline import study as baseline
from market_research.studies.im_basis_forward_return_association import study as association
from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryRequest,
    CSI1000IMBasisHistoryService,
)
from market_snapshot.sources import tushare

CONTRACTS = (
    ("IM2601.CFE", "20250101", "20260130", 102.0),
    ("IM2602.CFE", "20250201", "20260227", 104.0),
    ("IM2603.CFE", "20250301", "20260327", 106.0),
    ("IM2606.CFE", "20250601", "20260626", 108.0),
)


class FakeTushareApi:
    """Small Source fake containing only the three endpoints in this slice."""

    def __init__(
        self,
        index_frame: pd.DataFrame,
        basic_frame: pd.DataFrame,
        daily_frames: dict[str, pd.DataFrame],
    ) -> None:
        self.index_frame = index_frame
        self.basic_frame = basic_frame
        self.daily_frames = daily_frames

    @staticmethod
    def _range(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
        values = frame["trade_date"].astype(str)
        return frame[(values >= start) & (values <= end)].copy()

    def index_daily(
        self,
        *,
        ts_code: str,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        assert ts_code == "000852.SH"
        if trade_date is not None:
            return self._range(self.index_frame, trade_date, trade_date)
        assert start_date is not None and end_date is not None
        return self._range(self.index_frame, start_date, end_date)

    def fut_basic(
        self,
        *,
        exchange: str,
        fut_type: str | None = None,
        fut_code: str | None = None,
        fields: str | None = None,
    ) -> pd.DataFrame:
        assert exchange == "CFFEX" and fut_type == "1" and fut_code == "IM"
        return self.basic_frame.copy()

    def fut_daily(
        self,
        *,
        ts_code: str | None = None,
        trade_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        assert ts_code is not None
        frame = self.daily_frames[ts_code]
        if trade_date is not None:
            return self._range(frame, trade_date, trade_date)
        assert start_date is not None and end_date is not None
        return self._range(frame, start_date, end_date)


def weekdays(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    result: list[str] = []
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    return result


def full_service(count: int = 30) -> tuple[CSI1000IMBasisHistoryService, list[str]]:
    dates = weekdays("2025-12-01", count)
    index_frame = pd.DataFrame(
        {
            "ts_code": ["000852.SH"] * count,
            "trade_date": dates,
            "close": [100.0 + index for index in range(count)],
        }
    )
    basic_frame = pd.DataFrame(
        [
            {
                "ts_code": code,
                "symbol": code.split(".")[0],
                "exchange": "CFFEX",
                "fut_code": "IM",
                "list_date": listed,
                "delist_date": delisted,
            }
            for code, listed, delisted, _ in CONTRACTS
        ]
    )
    daily_frames = {
        code: pd.DataFrame(
            {
                "ts_code": [code] * count,
                "trade_date": dates,
                "close": [close + index for index in range(count)],
            }
        )
        for code, _, _, close in CONTRACTS
    }
    api = FakeTushareApi(
        index_frame=index_frame,
        basic_frame=basic_frame,
        daily_frames=daily_frames,
    )
    return CSI1000IMBasisHistoryService(cast(tushare.TushareApi, api)), dates


def request(dates: list[str]) -> CSI1000IMBasisHistoryRequest:
    return CSI1000IMBasisHistoryRequest(
        start_trade_date=date.fromisoformat(
            f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}"
        ).isoformat(),
        end_trade_date=date.fromisoformat(
            f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}"
        ).isoformat(),
    )


def test_shared_predictor_excludes_m0_and_quantile_is_linear() -> None:
    service, dates = full_service(2)
    daily = daily_im_basis(service.run(request(dates)))

    first = daily[0]
    assert first.non_front_mean_basis == pytest.approx(
        sum(first.annualized_basis_by_slot[slot] for slot in ("M1", "Q1", "Q2")) / 3
    )
    assert linear_quantile([0.0, 10.0], 0.25) == 2.5


def test_baseline_statistics_use_sample_std_and_median_equals_p50() -> None:
    service, dates = full_service(3)
    result = baseline.compute(service.run(request(dates)))

    assert set(result.statistics) == {"M0", "M1", "Q1", "Q2", "non_front_mean_basis"}
    for stats in result.statistics.values():
        assert stats.count == 3
        assert stats.median == stats.percentiles["P50"]
        assert stats.standard_deviation > 0


def test_baseline_rejects_an_insufficient_sample() -> None:
    service, dates = full_service(1)
    with pytest.raises(baseline.BaselineStudyError, match="at least two"):
        baseline.compute(service.run(request(dates)))


def test_association_uses_one_common_sample_and_all_canonical_horizons() -> None:
    service, dates = full_service(30)
    result = association.compute(service.run(request(dates)))

    assert result.common_sample_count == 10
    assert result.source_observation_count == 30
    assert result.future_support_only_count == 20
    assert result.effective_predictor_start_trade_date == date.fromisoformat(dates[0]).isoformat()
    assert result.effective_predictor_end_trade_date == date.fromisoformat(dates[9]).isoformat()
    assert result.horizons == (1, 3, 5, 10, 15, 20)
    assert {row.sample_count for row in result.association} == {10}
    assert len(result.quintiles) == 5 * 6
    assert {row.sample_count for row in result.quintiles if row.horizon == 20} == {2}
    for horizon in result.horizons:
        rows = [row for row in result.quintiles if row.horizon == horizon]
        assert sum(row.sample_count for row in rows) == result.common_sample_count
        assert {row.basis_quintile for row in rows} == {"Q1", "Q2", "Q3", "Q4", "Q5"}

    daily = daily_im_basis(service.run(request(dates)))
    first_bucket = next(
        row for row in result.quintiles if row.horizon == 1 and row.basis_quintile == "Q1"
    )
    p20 = result.quintile_breakpoints["P20"]
    assert p20 == pytest.approx(
        linear_quantile([row.non_front_mean_basis for row in daily[:10]], 0.2)
    )
    expected = [
        (daily[index + 1].underlying_close / daily[index].underlying_close - 1) * 100
        for index in range(result.common_sample_count)
        if daily[index].non_front_mean_basis <= p20
    ]
    assert first_bucket.mean_forward_return_pct == pytest.approx(sum(expected) / len(expected))


def test_zero_outcome_variance_fails_the_whole_association_run() -> None:
    service, dates = full_service(30)
    snapshot = service.run(request(dates))
    flat = tuple(replace(row, underlying_close=100.0) for row in snapshot.observations)
    with pytest.raises(association.AssociationStudyError, match="zero variance"):
        association.compute(replace(snapshot, observations=flat))


def test_non_finite_forward_return_fails_the_whole_association_run() -> None:
    service, dates = full_service(30)
    snapshot = service.run(request(dates))
    first_date = snapshot.observations[0].trade_date
    flat = tuple(
        replace(row, underlying_close=1e-308) if row.trade_date == first_date else row
        for row in snapshot.observations
    )
    with pytest.raises(association.AssociationStudyError, match="non-finite forward return"):
        association.compute(replace(snapshot, observations=flat))


def test_overflowing_finite_predictor_fails_as_study_error() -> None:
    service, dates = full_service(30)
    snapshot = service.run(request(dates))
    flat = tuple(replace(row, annualized_basis_pct=1e308) for row in snapshot.observations)
    with pytest.raises(association.AssociationStudyError, match="basis predictor"):
        association.compute(replace(snapshot, observations=flat))


def test_association_rejects_unordered_snapshot_public_result() -> None:
    service, dates = full_service(30)
    snapshot = service.run(request(dates))
    observations = list(snapshot.observations)
    observations[0], observations[1] = observations[1], observations[0]
    with pytest.raises(association.AssociationStudyError, match="canonically ordered"):
        association.compute(replace(snapshot, observations=tuple(observations)))


def test_association_rejects_insufficient_sample_and_empty_tied_quintiles() -> None:
    short_service, short_dates = full_service(24)
    with pytest.raises(association.AssociationStudyError, match="at least 25"):
        association.compute(short_service.run(request(short_dates)))

    service, dates = full_service(30)
    snapshot = service.run(request(dates))
    tied = tuple(replace(row, annualized_basis_pct=1.0) for row in snapshot.observations)
    with pytest.raises(association.AssociationStudyError, match="empty bucket"):
        association.compute(replace(snapshot, observations=tied))


def test_end_to_end_fake_source_retains_machine_human_and_static_outputs(
    tmp_path: Path,
) -> None:
    service, dates = full_service(30)
    study_request = request(dates)

    snapshot = service.run(study_request)
    baseline_result = baseline.run_and_retain(snapshot, tmp_path / "baseline")
    association_result = association.run_and_retain(
        snapshot, tmp_path / "association"
    )

    assert baseline_result.statistics["M0"].count == 30
    assert association_result.common_sample_count == 10
    association_dir = tmp_path / "association"
    machine = json.loads((association_dir / "result.json").read_text(encoding="utf-8"))
    assert machine["source_observation_count"] == 30
    assert machine["future_support_only_count"] == 20
    assert (
        machine["common_sample_count"] + machine["future_support_only_count"]
        == machine["source_observation_count"]
    )
    assert set(machine["quintile_breakpoints"]) == {"P20", "P40", "P60", "P80"}
    assert len(machine["association"]) == 6
    assert len(machine["quintiles"]) == 30
    report = (association_dir / "report.md").read_text(encoding="utf-8")
    for required in (
        "Effective predictor dates",
        "future support only: 20 observations",
        "annualized percentage points",
        "trading observations",
        "OLS beta",
        "| P20 |",
        "| Q5 | 20 |",
        "historical empirical conditional rate",
    ):
        assert required in report
    for directory, plot in (
        (tmp_path / "baseline", "baseline.png"),
        (tmp_path / "association", "correlation_by_horizon.png"),
    ):
        assert json.loads((directory / "result.json").read_text(encoding="utf-8"))
        assert (directory / "report.md").read_text(encoding="utf-8").startswith("# IM")
        assert (directory / plot).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_research_imports_only_snapshot_public_product_boundary() -> None:
    research_root = Path(__file__).resolve().parents[1] / "src" / "market_research"
    source = "\n".join(path.read_text(encoding="utf-8") for path in research_root.rglob("*.py"))
    for forbidden in (
        "market_snapshot.sources",
        "market_snapshot.capture",
        "market_snapshot.preparation",
        "market_snapshot.artifacts",
        "backend_api",
    ):
        assert forbidden not in source


def test_study_computation_does_not_depend_on_research_ui() -> None:
    studies_root = Path(__file__).resolve().parents[1] / "src" / "market_research" / "studies"
    source = "\n".join(path.read_text(encoding="utf-8") for path in studies_root.rglob("study.py"))
    assert "market_research.ui" not in source
    assert "...ui" not in source
