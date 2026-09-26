"""CLI-level coverage of both retained Research vertical slices."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from market_research.ui import catalog, cli, configuration
from market_research.ui.catalog import StudyEntry
from market_research.ui.execution import (
    ResearchOutputError,
    canonical_run_directory,
    execute_run,
)
from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryError,
    CSI1000IMBasisHistoryRequest,
    CSI1000IMBasisHistoryResult,
    IMBasisObservation,
)

STUDY_IDS = ("im-basis-baseline", "im-basis-forward-return-association")


def weekdays(start: str, count: int) -> list[str]:
    current = date.fromisoformat(start)
    result: list[str] = []
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current.isoformat())
        current += timedelta(days=1)
    return result


def snapshot_result(count: int = 30) -> CSI1000IMBasisHistoryResult:
    dates = weekdays("2025-12-01", count)
    observations: list[IMBasisObservation] = []
    for index, trade_date in enumerate(dates):
        underlying = 100.0 + index + index**2 * 0.02
        for slot_index, slot in enumerate(("M0", "M1", "Q1", "Q2")):
            observations.append(
                IMBasisObservation(
                    trade_date=trade_date,
                    ts_code=f"IM{slot_index}",
                    contract_slot=slot,
                    delist_date="2026-12-31",
                    days_to_delist=100 + slot_index,
                    annualization_days=100 + slot_index,
                    underlying_close=underlying,
                    future_close=underlying + slot_index + 1,
                    basis_points=float(slot_index + 1),
                    basis_pct=float(slot_index + 1),
                    annualized_basis_pct=slot_index + index * 0.1 + index**2 * 0.001,
                )
            )
    return CSI1000IMBasisHistoryResult(
        start_trade_date=dates[0],
        end_trade_date=dates[-1],
        underlying_ts_code="000852.SH",
        observations=tuple(observations),
    )


def patch_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    config_path = tmp_path / "market-research" / "research.toml"
    output_root = tmp_path / "retained"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(f'[output]\nroot = "{output_root}"\n', encoding="utf-8")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", config_path)
    return config_path, output_root


def test_catalog_is_explicit_and_dispatchable() -> None:
    assert tuple(entry.study_id for entry in catalog.CATALOG) == STUDY_IDS
    assert all(callable(entry.execute) for entry in catalog.CATALOG)
    resolved = [catalog.find_study(study_id) for study_id in STUDY_IDS]
    assert all(entry is not None for entry in resolved)
    assert [entry.study_id for entry in resolved if entry is not None] == list(STUDY_IDS)


def test_list_is_local_catalog_inspection_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        catalog.snapshot_product,
        "run_csi1000_im_basis_history",
        lambda _request: (_ for _ in ()).throw(AssertionError("Snapshot must not run")),
    )
    monkeypatch.setattr(
        configuration,
        "load_config",
        lambda: (_ for _ in ()).throw(AssertionError("config must not load")),
    )

    assert cli.main(["list"]) == 0

    output = capsys.readouterr().out
    assert all(study_id in output for study_id in STUDY_IDS)


def test_config_reports_only_source_and_resolved_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path, output_root = patch_config(tmp_path, monkeypatch)
    monkeypatch.setenv("TUSHARE_TOKEN", "must-not-be-printed")

    assert cli.main(["config"]) == 0

    captured = capsys.readouterr()
    assert str(config_path.resolve()) in captured.out
    assert str(output_root.resolve()) in captured.out
    assert "must-not-be-printed" not in captured.out
    assert captured.err == ""


def test_config_failure_is_presented_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "market-research" / "research.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("invalid toml =", encoding="utf-8")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", config_path)

    assert cli.main(["config"]) == 3

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Configuration error:")
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("study_id", "plot_name"),
    [
        ("im-basis-baseline", "baseline.png"),
        ("im-basis-forward-return-association", "correlation_by_horizon.png"),
    ],
)
def test_run_completes_each_vertical_slice_and_reports_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    study_id: str,
    plot_name: str,
) -> None:
    _config_path, output_root = patch_config(tmp_path, monkeypatch)
    snapshot = snapshot_result()
    requests: list[CSI1000IMBasisHistoryRequest] = []

    def execute(request: CSI1000IMBasisHistoryRequest) -> CSI1000IMBasisHistoryResult:
        requests.append(request)
        return snapshot

    monkeypatch.setattr(catalog.snapshot_product, "run_csi1000_im_basis_history", execute)

    assert (
        cli.main(
            [
                "run",
                study_id,
                "--start",
                snapshot.start_trade_date,
                "--end",
                snapshot.end_trade_date,
            ]
        )
        == 0
    )

    run_dir = output_root / study_id / (
        f"{snapshot.start_trade_date}__{snapshot.end_trade_date}"
    )
    assert requests == [
        CSI1000IMBasisHistoryRequest(
            snapshot.start_trade_date, snapshot.end_trade_date
        )
    ]
    assert sorted(path.name for path in run_dir.iterdir()) == [
        plot_name,
        "report.md",
        "result.json",
    ]
    output = capsys.readouterr().out
    assert "Study completed" in output
    assert str(run_dir.resolve()) in output
    assert plot_name in output


@pytest.mark.parametrize(
    "argv",
    [
        ["run", "unknown", "--start", "2025-01-01", "--end", "2025-02-01"],
        ["run", STUDY_IDS[0], "--start", "20250101", "--end", "2025-02-01"],
        ["run", STUDY_IDS[0], "--start", "2025-02-01", "--end", "2025-01-01"],
    ],
)
def test_invalid_run_input_fails_before_config_or_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    monkeypatch.setattr(
        configuration,
        "load_config",
        lambda: (_ for _ in ()).throw(AssertionError("config must not load")),
    )

    assert cli.main(argv) == 2
    assert "Input error" in capsys.readouterr().err


def test_missing_required_arguments_are_parser_input_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["run", STUDY_IDS[0]])

    assert excinfo.value.code == 2
    assert "Input error" in capsys.readouterr().err


def test_existing_run_fails_before_snapshot_without_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _config_path, output_root = patch_config(tmp_path, monkeypatch)
    run_dir = output_root / STUDY_IDS[0] / "2025-01-01__2025-02-01"
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("old", encoding="utf-8")
    monkeypatch.setattr(
        catalog.snapshot_product,
        "run_csi1000_im_basis_history",
        lambda _request: (_ for _ in ()).throw(AssertionError("Snapshot must not run")),
    )

    assert (
        cli.main(
            [
                "run",
                STUDY_IDS[0],
                "--start",
                "2025-01-01",
                "--end",
                "2025-02-01",
            ]
        )
        == 6
    )
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "old"
    assert "Output error" in capsys.readouterr().err


def test_non_directory_run_path_fails_before_snapshot_even_with_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _config_path, output_root = patch_config(tmp_path, monkeypatch)
    run_path = output_root / STUDY_IDS[0] / "2025-01-01__2025-02-01"
    run_path.parent.mkdir(parents=True)
    run_path.write_text("not a run directory", encoding="utf-8")
    monkeypatch.setattr(
        catalog.snapshot_product,
        "run_csi1000_im_basis_history",
        lambda _request: (_ for _ in ()).throw(AssertionError("Snapshot must not run")),
    )

    assert (
        cli.main(
            [
                "run",
                STUDY_IDS[0],
                "--start",
                "2025-01-01",
                "--end",
                "2025-02-01",
                "--overwrite",
            ]
        )
        == 6
    )
    assert run_path.read_text(encoding="utf-8") == "not a run directory"
    assert "not a directory" in capsys.readouterr().err


def test_overwrite_replaces_whole_run_without_stale_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config_path, output_root = patch_config(tmp_path, monkeypatch)
    snapshot = snapshot_result()
    run_dir = output_root / STUDY_IDS[0] / (
        f"{snapshot.start_trade_date}__{snapshot.end_trade_date}"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "stale.txt").write_text("stale", encoding="utf-8")
    monkeypatch.setattr(
        catalog.snapshot_product, "run_csi1000_im_basis_history", lambda _request: snapshot
    )

    assert (
        cli.main(
            [
                "run",
                STUDY_IDS[0],
                "--start",
                snapshot.start_trade_date,
                "--end",
                snapshot.end_trade_date,
                "--overwrite",
            ]
        )
        == 0
    )
    assert not (run_dir / "stale.txt").exists()
    assert (run_dir / "result.json").is_file()


def test_failed_overwrite_preserves_prior_evidence_and_cleans_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _config_path, output_root = patch_config(tmp_path, monkeypatch)
    short_snapshot = snapshot_result(1)
    run_dir = output_root / STUDY_IDS[0] / (
        f"{short_snapshot.start_trade_date}__{short_snapshot.end_trade_date}"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve me", encoding="utf-8")
    monkeypatch.setattr(
        catalog.snapshot_product,
        "run_csi1000_im_basis_history",
        lambda _request: short_snapshot,
    )

    assert (
        cli.main(
            [
                "run",
                STUDY_IDS[0],
                "--start",
                short_snapshot.start_trade_date,
                "--end",
                short_snapshot.end_trade_date,
                "--overwrite",
            ]
        )
        == 5
    )
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve me"
    assert not list(run_dir.parent.glob(".*.staging-*"))
    assert "Study/sample error" in capsys.readouterr().err


def test_snapshot_failure_is_classified_and_preserves_prior_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _config_path, output_root = patch_config(tmp_path, monkeypatch)
    run_dir = output_root / STUDY_IDS[0] / "2025-01-01__2025-02-01"
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve me", encoding="utf-8")

    def fail(_request: CSI1000IMBasisHistoryRequest) -> CSI1000IMBasisHistoryResult:
        raise CSI1000IMBasisHistoryError("source unavailable")

    monkeypatch.setattr(catalog.snapshot_product, "run_csi1000_im_basis_history", fail)
    assert (
        cli.main(
            [
                "run",
                STUDY_IDS[0],
                "--start",
                "2025-01-01",
                "--end",
                "2025-02-01",
                "--overwrite",
            ]
        )
        == 4
    )
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve me"
    assert "Snapshot/data error" in capsys.readouterr().err


def test_publication_failure_restores_previous_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = canonical_run_directory(
        tmp_path, STUDY_IDS[0], "2025-01-01", "2025-02-01"
    )
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve me", encoding="utf-8")

    def adapter(_request: CSI1000IMBasisHistoryRequest, output: Path) -> tuple[Path, ...]:
        artifact = output / "new.txt"
        artifact.write_text("new", encoding="utf-8")
        return (artifact,)

    entry = StudyEntry(STUDY_IDS[0], "test", adapter)
    request = CSI1000IMBasisHistoryRequest("2025-01-01", "2025-02-01")
    original_rename = Path.rename
    calls = 0

    def fail_publish(path: Path, target: Path) -> Path:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated publish failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", fail_publish)

    with pytest.raises(ResearchOutputError, match="simulated publish failure"):
        execute_run(entry, request, run_dir, overwrite=True)

    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve me"


def test_research_ui_does_not_import_snapshot_source_or_capture() -> None:
    ui_root = Path(__file__).resolve().parents[1] / "src" / "market_research" / "ui"
    source = "\n".join(path.read_text(encoding="utf-8") for path in ui_root.rglob("*.py"))
    for forbidden in (
        "market_snapshot.sources",
        "market_snapshot.capture",
        "TushareApi",
        "TUSHARE_TOKEN",
        "backend_api",
    ):
        assert forbidden not in source
