"""Tests for the Data Service orchestration and the layer boundaries.

Authority: ``ARCHITECTURE.md`` section 2 (dependency direction),
``guides/data-services.md`` sections 5 and 6.

These tests keep the orchestration owned by the Data Service: the CLI only
resolves and reports, and the five Captures, their order and the Analysis
Preparation call are all reachable through the service module.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from daily_market_snapshot import artifacts, cli
from daily_market_snapshot.capture import common as capture_common
from daily_market_snapshot.capture import (
    csi1000_index_history,
    im_futures_basic,
    im_futures_daily,
    index_daily,
    mo_option_basic,
    mo_option_daily,
    stock_daily,
)
from daily_market_snapshot.preparation import csi1000_5d_analysis as preparation
from daily_market_snapshot.services import DataServiceError, catalog, csi1000_5d_analysis
from daily_market_snapshot.sources import tushare
from support.fake_source import CSI1000_TARGET_DATE, csi1000_5d_analysis_api

SERVICE_ID = "csi1000-5d-analysis"
TARGET_DATE = CSI1000_TARGET_DATE
RAW_DATASETS = (
    "index_daily_history",
    "mo_option_basic",
    "mo_option_daily",
    "im_futures_basic",
    "im_futures_daily",
)

CAPTURE_MODULES = (
    csi1000_index_history,
    im_futures_basic,
    im_futures_daily,
    mo_option_basic,
    mo_option_daily,
)
# Every Capture module of the package, including the two the first-version daily
# scenario owns and the shared Capture helpers.
ALL_CAPTURE_MODULES = (*CAPTURE_MODULES, index_daily, stock_daily, capture_common)


@pytest.fixture
def raw_root(tmp_path: Path) -> Path:
    return tmp_path / "raw"


@pytest.fixture
def output_root(tmp_path: Path) -> Path:
    return tmp_path / "output"


def output_path(output_root: Path) -> Path:
    return output_root / SERVICE_ID / TARGET_DATE / "snapshot.json"


# ---------------------------------------------------------------------------
# orchestration
# ---------------------------------------------------------------------------


def test_orchestration_returns_the_canonical_output_path(
    raw_root: Path, output_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The output contract is ``output/<service>/<date>/snapshot.json``."""
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    path = csi1000_5d_analysis.run_csi1000_5d_analysis(csi1000_5d_analysis_api(), TARGET_DATE)

    assert path == output_path(output_root)
    assert path.is_file()
    assert path.name == "snapshot.json"
    assert path.parent.name == TARGET_DATE
    assert path.parent.parent.name == SERVICE_ID
    assert path.parent.parent.parent == output_root


def test_orchestration_writes_every_raw_artifact_in_authority_order(
    raw_root: Path, output_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guide 5 order: CSI1000 history, MO basic, MO daily, IM basic, IM daily."""
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    csi1000_5d_analysis.run_csi1000_5d_analysis(csi1000_5d_analysis_api(), TARGET_DATE)

    dataset_dir = raw_root / artifacts.CSI1000_RAW_SUBDIR / TARGET_DATE
    assert sorted(path.name for path in dataset_dir.iterdir()) == [
        f"{dataset}.json" for dataset in sorted(RAW_DATASETS)
    ]


def test_a_failing_preparation_stage_is_reported_and_writes_no_output(
    raw_root: Path, output_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Analysis Preparation is a stage: an unusable Raw Artifact fails it.

    The five collection stages enforce enough completeness that the preparation
    normally succeeds, so the failure is injected into a collected Raw Artifact
    to reach the preparation error path of the service.
    """
    api = csi1000_5d_analysis_api()
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: api)
    monkeypatch.setattr(artifacts, "RAW_DIR", raw_root)
    monkeypatch.setattr(artifacts, "OUTPUT_DIR", output_root)

    write_raw = artifacts.write_raw_artifact

    def write_then_damage(
        records: list[artifacts.RawRecord], dataset_dir: Path, dataset: str
    ) -> Path:
        path = write_raw(records, dataset_dir, dataset)
        if dataset == "index_daily_history":
            # Fewer than the 120 trading rows the Definition needs.
            history = json.loads(path.read_text(encoding="utf-8"))
            path.write_text(json.dumps(history[:40]), encoding="utf-8")
        return path

    monkeypatch.setattr(artifacts, "write_raw_artifact", write_then_damage)

    with pytest.raises(DataServiceError, match="stage=snapshot_assembly"):
        csi1000_5d_analysis.orchestrate_csi1000_5d_analysis(
            api, TARGET_DATE, raw_root, output_root
        )

    assert not output_path(output_root).exists()


def test_the_catalog_entry_runs_this_service() -> None:
    entry = catalog.find_service(SERVICE_ID)

    assert entry is not None
    assert entry.run is csi1000_5d_analysis.run_csi1000_5d_analysis
    assert catalog.find_service("no-such-service") is None


# ---------------------------------------------------------------------------
# layer boundaries
# ---------------------------------------------------------------------------


def imported_modules(module: ModuleType) -> set[str]:
    """Return the top-level modules ``module``'s source imports."""
    import ast

    tree = ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_the_cli_does_not_orchestrate_captures_or_preparation() -> None:
    """The CLI resolves a Data Service; it never names a Capture or a formula."""
    import daily_market_snapshot.cli as cli_module

    source = Path(str(cli_module.__file__)).read_text(encoding="utf-8")

    for module in ALL_CAPTURE_MODULES:
        assert f"import {module.__name__}" not in source
    assert "import daily_market_snapshot.preparation" not in source
    # It reports through the catalog, not by reaching into a service stage.
    assert "catalog" in source


def test_the_data_service_owns_the_orchestration() -> None:
    """The five Captures and the Analysis Preparation call live in the service."""
    source = Path(str(csi1000_5d_analysis.__file__)).read_text(encoding="utf-8")

    for module in CAPTURE_MODULES:
        assert module.__name__.rsplit(".", 1)[-1] in source
    assert "build_snapshot" in source
    assert csi1000_5d_analysis.collect_csi1000_5d_analysis.__module__ == (
        "daily_market_snapshot.services.csi1000_5d_analysis"
    )


def test_preparation_does_not_access_the_source_or_the_captures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preparation reads local Raw Artifacts only (ARCHITECTURE.md 2 and 4)."""
    dataset_dir = tmp_path / "raw" / TARGET_DATE
    dataset_dir.mkdir(parents=True)
    for dataset in RAW_DATASETS:
        (dataset_dir / f"{dataset}.json").write_text("[]", encoding="utf-8")

    def unreachable(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Analysis Preparation must stay offline")

    monkeypatch.setattr(tushare, "create_tushare_api", unreachable)
    monkeypatch.setattr(tushare, "get_tushare_token", unreachable)

    # The preparation reads the Raw Artifacts it was pointed at; with empty Raw
    # Artifacts it fails on data, never by reaching for the Source.
    with pytest.raises(preparation.SnapshotError):
        preparation.build_snapshot(TARGET_DATE, dataset_dir)

    imported = imported_modules(preparation)
    assert "daily_market_snapshot" not in imported
    assert "tushare" not in imported
    source = Path(str(preparation.__file__)).read_text(encoding="utf-8")
    assert "create_tushare_api" not in source
    assert "TushareApi" not in source


def test_capture_does_not_depend_on_preparation() -> None:
    """Capture produces Raw Artifacts and knows nothing about the preparation."""
    for module in ALL_CAPTURE_MODULES:
        source = Path(str(module.__file__)).read_text(encoding="utf-8")
        assert "daily_market_snapshot.preparation" not in source
        assert "SnapshotError" not in source


def test_the_cli_shim_has_no_business_logic() -> None:
    """``scripts/dms.py`` only enters the package CLI."""
    shim = Path(__file__).resolve().parent.parent / "scripts" / "dms.py"
    source = shim.read_text(encoding="utf-8")

    assert "from daily_market_snapshot.cli import main" in source
    for module in ALL_CAPTURE_MODULES:
        assert f"import {module.__name__}" not in source
    assert "build_snapshot" not in source


def test_the_cli_reports_a_service_failure_without_knowing_the_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A service-level failure reaches the user as a reported error."""
    monkeypatch.setenv(tushare.TOKEN_ENV_VAR, "local-token")
    monkeypatch.setattr(tushare, "create_tushare_api", lambda token: object())

    def failing_service(api: object, target_trade_date: str) -> Path:
        raise DataServiceError("stage=example error=boom")

    failing_entry = catalog.DataService(
        service_id=SERVICE_ID, description="failing", run=failing_service
    )
    monkeypatch.setattr(catalog, "CATALOG", (failing_entry,))

    assert cli.main(["get", SERVICE_ID, "--date", TARGET_DATE]) == 1

    captured = capsys.readouterr()
    assert f"service={SERVICE_ID}" in captured.err
    assert "stage=example error=boom" in captured.err
    assert captured.out == ""


def test_the_catalog_is_explicit_and_never_discovered() -> None:
    """guides/data-services.md 2: no filesystem discovery, no dynamic registry."""
    source = Path(catalog.__file__).read_text(encoding="utf-8")

    assert "CATALOG: tuple[DataService, ...] = (" in source
    for discovery in ("iterdir", "glob", "walk", "pkgutil", "importlib"):
        assert discovery not in source
