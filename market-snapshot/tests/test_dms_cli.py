"""Tests for the Data Service CLI (``scripts/dms.py`` -> ``cli.main``).

Authority: ``services/ARCHITECTURE.md``.

The CLI resolves a Data Service from the explicit catalog, validates its own
input and reports the result; the orchestration it triggers belongs to
``services/csi1000_5d_analysis.py``.

Everything runs against a fake Source and temporary Raw / output directories: no
test touches the network, the repository's real ``data/raw`` or its real
``output/``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from market_snapshot import artifacts, cli
from market_snapshot.services import catalog
from market_snapshot.sources import tushare
from support.fake_source import (
    CSI1000_INDEX_CODE,
    CSI1000_MO_CODES,
    CSI1000_TARGET_DATE,
    FakeTushareApi,
    csi1000_5d_analysis_api,
)

SERVICE_ID = "csi1000-5d-analysis"
TARGET_DATE = CSI1000_TARGET_DATE
RAW_DATASETS = (
    "index_daily_history",
    "mo_option_basic",
    "mo_option_daily",
    "im_futures_basic",
    "im_futures_daily",
)


def patch_source(monkeypatch: pytest.MonkeyPatch, api: FakeTushareApi) -> None:
    """Serve every Source request from the fake Source instead of Tushare."""
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)


@pytest.fixture
def raw_root(tmp_path: Path) -> Path:
    """The temporary Raw root the CLI is pointed at."""
    return tmp_path / "raw"


@pytest.fixture
def output_root(tmp_path: Path) -> Path:
    """The temporary canonical output root the CLI is pointed at."""
    return tmp_path / "output"


def dataset_dir(raw_root: Path) -> Path:
    return raw_root / artifacts.CSI1000_RAW_SUBDIR / TARGET_DATE


def output_path(output_root: Path) -> Path:
    """The canonical Data Service artifact of the request."""
    return output_root / artifacts.CSI1000_RAW_SUBDIR / TARGET_DATE / "snapshot.json"


def read_records(directory: Path, dataset: str) -> list[dict[str, Any]]:
    payload: Any = json.loads((directory / f"{dataset}.json").read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    return payload


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_list_prints_the_catalog_entry_and_returns_success(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli.main(["list"]) == 0

    lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
    assert len(lines) == len(catalog.CATALOG)
    service_id, description = lines[0].split("\t")
    assert service_id == SERVICE_ID
    assert description.strip()


def test_list_order_is_stable(capsys: pytest.CaptureFixture[str]) -> None:
    """The catalog is explicit and static, not discovered by scanning."""
    cli.main(["list"])
    first = capsys.readouterr().out

    cli.main(["list"])
    second = capsys.readouterr().out

    assert first == second
    assert [line.split("\t")[0] for line in first.splitlines()] == [
        service.service_id for service in catalog.CATALOG
    ]


def test_catalog_holds_exactly_the_authority_locked_service() -> None:
    assert [service.service_id for service in catalog.CATALOG] == [SERVICE_ID]


# ---------------------------------------------------------------------------
# argument validation
# ---------------------------------------------------------------------------


def test_unknown_service_fails_without_touching_the_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def unreachable(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("an unknown service must fail before any Source call")

    monkeypatch.setattr(tushare, "get_tushare_token", unreachable)
    monkeypatch.setattr(tushare, "create_tushare_api", unreachable)

    assert cli.main(["get", "no-such-service", "--date", TARGET_DATE]) != 0

    captured = capsys.readouterr()
    assert "no-such-service" in captured.err
    assert SERVICE_ID in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "value",
    ["20260917", "2026-9-17", "2026-13-45", "2026-02-30", "today", "latest", ""],
)
def test_invalid_date_fails_without_touching_the_source(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], value: str
) -> None:
    def unreachable(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("an invalid date must fail before any Source call")

    monkeypatch.setattr(tushare, "get_tushare_token", unreachable)
    monkeypatch.setattr(tushare, "create_tushare_api", unreachable)

    assert cli.main(["get", SERVICE_ID, "--date", value]) != 0

    captured = capsys.readouterr()
    assert "invalid date" in captured.err
    assert captured.out == ""


def test_missing_date_argument_is_rejected() -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["get", SERVICE_ID])

    assert excinfo.value.code != 0


# ---------------------------------------------------------------------------
# successful get
# ---------------------------------------------------------------------------


def test_get_runs_the_whole_orchestration_and_writes_the_canonical_artifact(
    raw_root: Path,
    output_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = csi1000_5d_analysis_api()
    patch_source(monkeypatch, api)
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    assert cli.main(["get", SERVICE_ID, "--date", TARGET_DATE]) == 0

    # All five Raw Artifacts were collected for the requested target date.
    written = dataset_dir(raw_root)
    assert sorted(path.name for path in written.iterdir()) == [
        f"{dataset}.json" for dataset in sorted(RAW_DATASETS)
    ]
    for dataset in RAW_DATASETS:
        assert read_records(written, dataset)

    # The collected Source facts are the ones the fake Source holds.
    history = read_records(written, "index_daily_history")
    assert {str(record["ts_code"]) for record in history} == {CSI1000_INDEX_CODE}
    assert TARGET_DATE in {str(record["trade_date"]) for record in history}
    assert {str(record["ts_code"]) for record in read_records(written, "mo_option_daily")} == set(
        CSI1000_MO_CODES
    )

    # The Analysis Preparation ran on exactly those Raw Artifacts.
    snapshot: dict[str, Any] = json.loads(output_path(output_root).read_text(encoding="utf-8"))
    assert snapshot["target_trade_date"] == TARGET_DATE
    assert len(snapshot["underlying"]["history"]) == 120
    assert snapshot["im_futures"]["target_date_curve"]

    # The CLI reports where the final artifact is.
    report: dict[str, str] = json.loads(capsys.readouterr().out)
    assert report["service"] == SERVICE_ID
    assert report["target_trade_date"] == TARGET_DATE
    assert Path(report["output_path"]) == output_path(output_root)


def test_get_prints_an_output_path_that_exists(
    raw_root: Path,
    output_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    patch_source(monkeypatch, csi1000_5d_analysis_api())
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    cli.main(["get", SERVICE_ID, "--date", TARGET_DATE])

    report: dict[str, str] = json.loads(capsys.readouterr().out)
    assert Path(report["output_path"]) == output_path(output_root)
    assert Path(report["output_path"]).is_file()


# ---------------------------------------------------------------------------
# stage failure
# ---------------------------------------------------------------------------


def test_a_failing_collection_stage_stops_the_chain_and_writes_no_output(
    raw_root: Path,
    output_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed Capture stage is never skipped and never yields a partial artifact."""
    # The Source holds no MO contract, so the second stage cannot succeed.
    api = csi1000_5d_analysis_api()
    api.option_basic = api.option_basic.iloc[0:0]
    patch_source(monkeypatch, api)
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    assert cli.main(["get", SERVICE_ID, "--date", TARGET_DATE]) != 0

    captured = capsys.readouterr()
    assert f"service={SERVICE_ID}" in captured.err
    assert f"date={TARGET_DATE}" in captured.err
    assert "stage=mo_option_basic" in captured.err
    assert captured.out == ""

    # The chain stopped: no later Capture ran, nothing was prepared.
    written = dataset_dir(raw_root)
    assert sorted(path.name for path in written.iterdir()) == ["index_daily_history.json"]
    assert not output_path(output_root).exists()


def test_a_failing_daily_stage_reports_itself_and_stops_the_chain(
    raw_root: Path,
    output_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    api = csi1000_5d_analysis_api()
    # One active MO contract without a daily fact: the daily stage cannot map the
    # whole active universe.
    api.option_daily = api.option_daily.iloc[0:1]
    patch_source(monkeypatch, api)
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    assert cli.main(["get", SERVICE_ID, "--date", TARGET_DATE]) != 0

    captured = capsys.readouterr()
    assert "stage=mo_option_daily" in captured.err
    written = dataset_dir(raw_root)
    assert sorted(path.name for path in written.iterdir()) == [
        "index_daily_history.json",
        "mo_option_basic.json",
    ]
    assert not output_path(output_root).exists()
