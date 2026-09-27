"""Executable retained Price-to-Lagged-MA Study coverage."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from market_research.studies.price_to_lagged_ma_distribution import cli, study
from market_research.ui import configuration
from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryError,
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
    IndexDailyObservation,
)

ARGS = [
    "--instrument", "000852.SH", "--window", "2", "--method", "sma",
    "--start", "2026-09-03", "--end", "2026-09-04",
    "--granularity", "0.05", "--percentiles", "0.5,0.25",
]
ARTIFACTS = {
    "request.json", "observations.csv", "distribution.csv", "percentiles.csv",
    "summary.json", "report.md", "distribution.png",
}


def snapshot(*, sample_count: int = 2) -> IndexDailyHistoryResult:
    return IndexDailyHistoryResult(
        ts_code="000852.SH",
        requested_start_trade_date="2026-09-03",
        requested_end_trade_date="2026-09-04",
        requested_pre_start_observation_count=2,
        warmup_observations=(
            IndexDailyObservation("2026-09-01", 100.0, 1.0),
            IndexDailyObservation("2026-09-02", 110.0, 3.0),
        ),
        sample_observations=(
            IndexDailyObservation("2026-09-03", 120.0, 2.0),
            IndexDailyObservation("2026-09-04", 130.0, 4.0),
        )[:sample_count],
    )


def configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config_path = tmp_path / "market-research" / "research.toml"
    config_path.parent.mkdir()
    config_path.write_text('[output]\nroot = "retained"\n', encoding="utf-8")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", config_path)
    return tmp_path / "retained"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_cli_flags_create_canonical_request_and_equivalent_identity() -> None:
    first = cli._request(cli.build_parser().parse_args(ARGS))
    equivalent = cli._request(cli.build_parser().parse_args([
        *ARGS[:-3], "0.0500", "--percentiles", "0.250,5e-1",
    ]))
    assert first == equivalent
    assert study.run_key(first) == study.run_key(equivalent)
    assert study.canonical_request(first) == {
        "instrument": "000852.SH",
        "reference_window": 2,
        "reference_method": "sma",
        "reference_method_parameters": {},
        "sample_start_trade_date": "2026-09-03",
        "sample_end_trade_date": "2026-09-04",
        "distribution_granularity": "0.05",
        "percentile_probabilities": ["0.25", "0.5"],
    }


@pytest.mark.parametrize("change", [
    ["--window", "0"], ["--window", "1.5"], ["--granularity", "NaN"],
    ["--percentiles", "0.5,0.50"], ["--percentiles", "0.5,"],
    ["--start", "2026-09-31"],
])
def test_invalid_semantic_input_fails_before_configuration(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    change: list[str],
) -> None:
    monkeypatch.setattr(configuration, "load_config", lambda: pytest.fail("config loaded"))
    arguments = ARGS.copy()
    arguments[arguments.index(change[0]) + 1] = change[1]
    assert cli.main(arguments) == 2
    assert capsys.readouterr().err.startswith("Input error:")


def test_help_is_study_local_and_requires_no_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(configuration, "load_config", lambda: pytest.fail("config loaded"))
    with pytest.raises(SystemExit) as caught:
        cli.main(["--help"])
    assert caught.value.code == 0
    output = capsys.readouterr().out
    assert "dev.py research run price-to-lagged-ma-distribution" in output
    for flag in ("--instrument", "--window", "--method", "--granularity", "--percentiles"):
        assert flag in output


def test_success_uses_public_snapshot_entry_and_retains_complete_matching_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = configure(tmp_path, monkeypatch)
    supplied = snapshot()
    calls: list[IndexDailyHistoryRequest] = []

    def execute(request: IndexDailyHistoryRequest) -> IndexDailyHistoryResult:
        calls.append(request)
        return supplied

    monkeypatch.setattr(cli.snapshot_product, "run_index_daily_history", execute)
    assert cli.main(ARGS) == 0
    request = cli._request(cli.build_parser().parse_args(ARGS))
    run_dir = root / cli.STUDY_ID / study.run_key(request)
    assert calls == [IndexDailyHistoryRequest("000852.SH", "2026-09-03", "2026-09-04", 2)]
    assert {path.name for path in run_dir.iterdir()} == ARTIFACTS
    assert (run_dir / "distribution.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert "Study completed" in capsys.readouterr().out

    expected = study.compute(request, supplied)
    retained_request = json.loads((run_dir / "request.json").read_text(encoding="utf-8"))
    assert retained_request["study_id"] == cli.STUDY_ID
    assert retained_request["run_key"] == expected.run_key
    assert retained_request["semantic_request"] == study.canonical_request(request)
    assert retained_request["snapshot"] == {
        "requested_start_trade_date": "2026-09-03",
        "requested_end_trade_date": "2026-09-04",
        "requested_pre_start_observation_count": 2,
        "warmup_observation_count": 2,
        "sample_observation_count": 2,
    }
    observations = read_csv(run_dir / "observations.csv")
    assert [row["trade_date"] for row in observations] == [
        row.trade_date for row in supplied.sample_observations
    ]
    assert len(observations) == expected.summary.sample_count
    for retained, computed in zip(observations, expected.daily_observations, strict=True):
        assert retained["instrument"] == computed.instrument
        for field in ("close", "reference_ma", "deviation"):
            assert float(retained[field]) == getattr(computed, field)
    distribution = read_csv(run_dir / "distribution.csv")
    assert [
        (float(row["lower_bound"]), float(row["upper_bound"]),
         int(row["count"]), float(row["frequency"]))
        for row in distribution
    ] == [
        (row.lower_bound, row.upper_bound, row.count, row.frequency)
        for row in expected.distribution_bins
    ]
    assert [
        (float(row["probability"]), float(row["value"]))
        for row in read_csv(run_dir / "percentiles.csv")
    ] == [(row.probability, row.value) for row in expected.percentiles]
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8")) == {
        "sample_count": expected.summary.sample_count,
        "mean": expected.summary.mean,
        "median": expected.summary.median,
        "sample_standard_deviation": expected.summary.sample_standard_deviation,
        "min": expected.summary.min,
        "max": expected.summary.max,
    }
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    for section in (
        "Question", "Inputs", "Method and sample", "Distribution result", "Limitations"
    ):
        assert section in report


def test_collision_precedes_snapshot_and_equivalent_spelling_uses_same_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = configure(tmp_path, monkeypatch)
    request = cli._request(cli.build_parser().parse_args(ARGS))
    run_dir = root / cli.STUDY_ID / study.run_key(request)
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("old", encoding="utf-8")
    monkeypatch.setattr(
        cli.snapshot_product,
        "run_index_daily_history",
        lambda _request: pytest.fail("Snapshot ran"),
    )
    equivalent = ARGS.copy()
    equivalent[equivalent.index("--granularity") + 1] = "0.0500"
    equivalent[equivalent.index("--percentiles") + 1] = "0.250,0.50"
    assert cli.main(equivalent) == 6
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "old"
    assert "Output error" in capsys.readouterr().err


def test_overwrite_replaces_whole_run_and_singleton_summary_is_null(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = configure(tmp_path, monkeypatch)
    request = cli._request(cli.build_parser().parse_args(ARGS))
    run_dir = root / cli.STUDY_ID / study.run_key(request)
    run_dir.mkdir(parents=True)
    (run_dir / "stale.txt").write_text("stale", encoding="utf-8")
    monkeypatch.setattr(
        cli.snapshot_product,
        "run_index_daily_history",
        lambda _request: snapshot(sample_count=1),
    )
    assert cli.main([*ARGS, "--overwrite"]) == 0
    assert {path.name for path in run_dir.iterdir()} == ARTIFACTS
    assert json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))[
        "sample_standard_deviation"
    ] is None


@pytest.mark.parametrize(("failure", "expected_code", "category"), [
    ("snapshot", 4, "Snapshot/data error"),
    ("study", 5, "Study/sample error"),
    ("output", 6, "Output error"),
])
def test_failed_overwrite_preserves_previous_evidence_and_classifies_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str], failure: str, expected_code: int, category: str,
) -> None:
    root = configure(tmp_path, monkeypatch)
    request = cli._request(cli.build_parser().parse_args(ARGS))
    run_dir = root / cli.STUDY_ID / study.run_key(request)
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve", encoding="utf-8")

    def execute(_request: IndexDailyHistoryRequest) -> IndexDailyHistoryResult:
        if failure == "snapshot":
            raise IndexDailyHistoryError("source unavailable")
        if failure == "study":
            return snapshot(sample_count=0)
        return snapshot()

    monkeypatch.setattr(cli.snapshot_product, "run_index_daily_history", execute)
    if failure == "output":
        def fail_plot(_result: study.PriceToLaggedMAResult, _path: Path) -> None:
            raise OSError("plot write failed")
        monkeypatch.setattr(study, "_write_plot", fail_plot)
    assert cli.main([*ARGS, "--overwrite"]) == expected_code
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve"
    assert not list(run_dir.parent.glob(".*.staging-*"))
    assert category in capsys.readouterr().err


def test_bad_configuration_is_classified_before_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure(tmp_path, monkeypatch)
    configuration.CANONICAL_CONFIG_PATH.write_text("invalid toml =", encoding="utf-8")
    monkeypatch.setattr(
        cli.snapshot_product,
        "run_index_daily_history",
        lambda _request: pytest.fail("Snapshot ran"),
    )
    assert cli.main(ARGS) == 3
    assert "Configuration error" in capsys.readouterr().err
