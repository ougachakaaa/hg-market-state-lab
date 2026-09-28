"""Hand-checkable semantics and retained evidence for the reversion Study."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

import pytest

from market_research.shared.distribution import linear_quantile
from market_research.studies.price_to_lagged_ma_short_horizon_reversion import cli, study
from market_research.ui import configuration
from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryError,
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
    IndexDailyObservation,
)

BASE_ARGS = ["--instrument", "000852.SH", "--start", "2026-09-02", "--end", "2026-09-14"]
PRICES = (90.0, 100.0, 100.0, 100.0, 110.0, 100.0, 95.0, 105.0, 100.0)


def dates(count: int) -> tuple[str, ...]:
    current = date(2026, 9, 2)
    values: list[str] = []
    while len(values) < count:
        if current.weekday() < 5:
            values.append(current.isoformat())
        current += timedelta(days=1)
    return tuple(values)


def snapshot(
    *, prices: tuple[float, ...] = PRICES, volume: float | None = 1.0
) -> IndexDailyHistoryResult:
    return IndexDailyHistoryResult(
        ts_code="000852.SH",
        requested_start_trade_date="2026-09-02",
        requested_end_trade_date="2026-09-14",
        requested_pre_start_observation_count=1,
        warmup_observations=(IndexDailyObservation("2026-09-01", 100.0, 3.0),),
        sample_observations=tuple(
            IndexDailyObservation(day, close, volume)
            for day, close in zip(dates(len(prices)), prices, strict=True)
        ),
    )


def request(**changes: object) -> study.ReversionRequest:
    values: dict[str, object] = {
        "instrument": "000852.SH",
        "sample_start_trade_date": "2026-09-02",
        "sample_end_trade_date": "2026-09-14",
        "reference_window": 1,
        "percentile_bucket_edges": ("0", "0.25", "0.5", "0.75", "1"),
        "forward_horizons": (1, 3, 5),
    }
    values.update(changes)
    return study.ReversionRequest(**values)  # type: ignore[arg-type]


def configure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    config_path = tmp_path / "market-research" / "research.toml"
    config_path.parent.mkdir()
    config_path.write_text('[output]\nroot = "retained"\n', encoding="utf-8")
    monkeypatch.setattr(configuration, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(configuration, "CANONICAL_CONFIG_PATH", config_path)
    return tmp_path / "retained"


def test_cli_defaults_canonicalization_and_full_sha256_identity() -> None:
    default = cli._request(cli.build_parser().parse_args(BASE_ARGS))
    explicit = cli._request(
        cli.build_parser().parse_args(
            [
                *BASE_ARGS,
                "--method",
                "sma",
                "--window",
                "060",
                "--bucket-edges=-0,0.0500,0.1,0.20,0.8,0.90,0.950,1.000",
                "--horizons",
                "5,01,3",
            ]
        )
    )
    assert default == explicit
    canonical = study.canonical_request(default)
    assert canonical["reference_method_parameters"] == {}
    assert canonical["percentile_bucket_edges"] == [
        "0",
        "0.05",
        "0.1",
        "0.2",
        "0.8",
        "0.9",
        "0.95",
        "1",
    ]
    assert canonical["forward_horizons"] == [1, 3, 5]
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert study.run_key(default) == hashlib.sha256(payload.encode()).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", study.run_key(default))


@pytest.mark.parametrize(
    "change",
    [
        {"instrument": "000001.SH"},
        {"sample_start_trade_date": "2026-09-03"},
        {"sample_end_trade_date": "2026-09-15"},
        {"reference_method": "volume_weighted"},
        {"reference_window": 2},
        {"percentile_bucket_edges": ("0", "0.4", "1")},
        {"forward_horizons": (1, 2, 5)},
    ],
)
def test_each_semantic_change_changes_identity(change: dict[str, object]) -> None:
    original = study.ReversionRequest("000852.SH", "2026-09-02", "2026-09-14")
    changed = replace(original, **change)  # type: ignore[arg-type]
    assert study.run_key(changed) != study.run_key(original)


@pytest.mark.parametrize(
    "extra",
    [
        ["--window", "0"],
        ["--window", "1.5"],
        ["--bucket-edges", "0,0.5,0.50,1"],
        ["--bucket-edges", "0,NaN,1"],
        ["--bucket-edges", "0,1.1,1"],
        ["--bucket-edges", "0%,100%"],
        ["--horizons", "1,01"],
        ["--horizons", "0,5"],
        ["--horizons", "1.5,5"],
        ["--start", "2026-09-31"],
        ["--instrument", " 000852.SH"],
    ],
)
def test_invalid_cli_input_fails_before_config(
    extra: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(configuration, "load_config", lambda: pytest.fail("configuration loaded"))
    args = BASE_ARGS.copy()
    if extra[0] in args:
        args[args.index(extra[0]) + 1] = extra[1]
    else:
        args += extra
    assert cli.main(args) == 2
    assert "Input error" in capsys.readouterr().err


def test_lagged_reference_buckets_horizons_and_mfe() -> None:
    result = study.compute(request(), snapshot())
    daily = result.daily_observations
    assert daily[0].reference_ma == 100.0
    assert daily[1].reference_ma == 90.0
    assert daily[0].deviation == pytest.approx(-0.1)
    deviations = [row.deviation for row in daily]
    assert [bucket.deviation_lower_threshold for bucket in result.buckets] == pytest.approx(
        [linear_quantile(deviations, p) for p in (0, 0.25, 0.5, 0.75)]
    )
    assert sum(bucket.bucket_observation_count for bucket in result.buckets) == len(PRICES)
    assert result.observation_bucket_indices[2] == result.observation_bucket_indices[3]
    assert result.observation_bucket_indices[2] == 2  # tie at median goes higher
    first_bucket = result.observation_bucket_indices[0]
    mr5 = next(
        row for row in result.mr_statistics if row.bucket_index == first_bucket and row.horizon == 5
    )
    mfe5 = result.mfe_statistics[first_bucket]
    assert mr5.eligible_sample_count == mfe5.sample_count
    assert mr5.unconditional_mr_mean == pytest.approx(100 / 90 - 1)
    assert mfe5.mean == pytest.approx(110 / 90 - 1)
    assert {row.horizon for row in result.mr_statistics} == {1, 3, 5}
    assert sum(row.eligible_sample_count for row in result.mr_statistics if row.horizon == 1) > sum(
        row.eligible_sample_count for row in result.mr_statistics if row.horizon == 5
    )
    for bucket in result.buckets:
        for row in (row for row in result.mr_statistics if row.bucket_index == bucket.bucket_index):
            assert bucket.bucket_observation_count == (
                row.zero_deviation_excluded_count
                + row.insufficient_forward_excluded_count
                + row.eligible_sample_count
            )
            assert row.conditional_reversal_magnitude_sample_count == row.reversal_count
            if row.eligible_sample_count:
                assert row.reversal_probability == pytest.approx(
                    row.reversal_count / row.eligible_sample_count
                )


def test_configurable_horizons_fixed_five_and_empty_groups() -> None:
    result = study.compute(
        request(
            percentile_bucket_edges=("0", "0.1", "0.2", "0.3", "0.4", "1"),
            forward_horizons=(2, 7),
        ),
        snapshot(),
    )
    assert {row.horizon for row in result.mr_statistics} == {2, 5, 7}
    assert all(not row.configured_horizon for row in result.mr_statistics if row.horizon == 5)
    assert len(result.mfe_statistics) == len(result.buckets)
    assert sum(row.eligible_sample_count for row in result.mr_statistics if row.horizon == 7) == 2
    empty = [row for row in result.mr_statistics if row.eligible_sample_count == 0]
    assert empty
    assert all(
        row.reversal_count == row.conditional_reversal_magnitude_sample_count == 0
        and row.reversal_probability is None
        and row.conditional_reversal_magnitude_mean is None
        and row.conditional_reversal_magnitude_median is None
        and row.unconditional_mr_mean is None
        and row.unconditional_mr_median is None
        for row in empty
    )
    assert all(
        row.mean is row.median is None for row in result.mfe_statistics if row.sample_count == 0
    )


def test_coincident_thresholds_keep_tied_states_in_one_bucket() -> None:
    geometric = snapshot(prices=(200.0, 400.0, 800.0, 1600.0, 3200.0, 6400.0))
    result = study.compute(request(), geometric)
    assert {row.deviation for row in result.daily_observations} == {1.0}
    assert set(result.observation_bucket_indices) == {3}
    assert [bucket.bucket_observation_count for bucket in result.buckets] == [0, 0, 0, 6]
    assert all(
        row.eligible_sample_count == 0 and row.unconditional_mr_mean is None
        for row in result.mr_statistics
        if row.bucket_index != 3
    )


def test_zero_deviation_is_in_population_but_excluded_and_no_5d_fails() -> None:
    result = study.compute(request(), snapshot())
    assert (
        sum(row.zero_deviation_excluded_count for row in result.mr_statistics if row.horizon == 5)
        == 2
    )
    assert (
        sum(
            row.insufficient_forward_excluded_count
            for row in result.mr_statistics
            if row.horizon == 5
        )
        == 5
    )
    with pytest.raises(study.ReversionStudyError, match="5D"):
        study.compute(request(), snapshot(prices=(90.0, 100.0, 100.0, 100.0, 110.0)))


def test_no_favorable_price_move_gives_zero_mfe(tmp_path: Path) -> None:
    rising = snapshot(prices=(110.0, 120.0, 130.0, 140.0, 150.0, 160.0))
    result = study.compute(request(), rising)
    bucket_index = result.observation_bucket_indices[0]
    mr5 = next(
        row for row in result.mr_statistics if row.bucket_index == bucket_index and row.horizon == 5
    )
    mfe5 = result.mfe_statistics[bucket_index]
    assert mr5.eligible_sample_count == mfe5.sample_count == 1
    assert mr5.unconditional_mr_mean == pytest.approx(-(160 / 110 - 1))
    assert mr5.reversal_count == mr5.conditional_reversal_magnitude_sample_count == 0
    assert mr5.reversal_probability == 0
    assert mr5.conditional_reversal_magnitude_mean is None
    assert mr5.conditional_reversal_magnitude_median is None
    assert mfe5.mean == mfe5.median == 0
    study.retain(result, rising, tmp_path)
    assert "no reversal occurred" in (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "0.00% | —" in (tmp_path / "table.md").read_text(encoding="utf-8")


def test_mixed_reversal_zero_move_and_conditional_denominator() -> None:
    prices = (90.0, 100.0, 100.0, 80.0, 100.0, 110.0, 100.0)
    result = study.compute(
        request(percentile_bucket_edges=("0", "1"), forward_horizons=(1, 5)),
        snapshot(prices=prices),
    )
    row = next(row for row in result.mr_statistics if row.horizon == 1)
    reversals = [100 / 90 - 1, 100 / 80 - 1, -(100 / 110 - 1)]
    assert row.eligible_sample_count == 5  # Zero deviation is excluded; zero MR remains.
    assert row.reversal_count == row.conditional_reversal_magnitude_sample_count == 3
    assert row.reversal_probability == pytest.approx(3 / 5)
    assert row.conditional_reversal_magnitude_mean == pytest.approx(sum(reversals) / 3)
    assert row.conditional_reversal_magnitude_median == pytest.approx(sorted(reversals)[1])
    assert row.unconditional_mr_mean != pytest.approx(row.conditional_reversal_magnitude_mean)
    row5 = next(row for row in result.mr_statistics if row.horizon == 5)
    assert row5.eligible_sample_count == 2
    assert row5.reversal_count == 1
    assert row5.reversal_probability == pytest.approx(0.5)


def test_volume_weighted_uses_prior_volumes_and_rejects_missing_volume() -> None:
    result = study.compute(request(reference_method="volume_weighted"), snapshot())
    assert result.daily_observations[0].reference_ma == 100
    with pytest.raises(study.ReversionStudyError, match="volume"):
        study.compute(request(reference_method="volume_weighted"), snapshot(volume=None))


def test_cli_public_boundary_evidence_collision_and_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = configure(tmp_path, monkeypatch)
    args = [*BASE_ARGS, "--window", "1", "--bucket-edges", "0,0.25,0.5,0.75,1"]
    calls: list[IndexDailyHistoryRequest] = []
    chart_labels: list[tuple[str, ...]] = []
    from matplotlib.axes import Axes

    original_set_xticklabels = Axes.set_xticklabels

    def capture_labels(
        self: Axes, labels: Sequence[str], *args: object, **kwargs: object
    ) -> object:
        chart_labels.append(tuple(str(label) for label in labels))
        return original_set_xticklabels(self, labels, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Axes, "set_xticklabels", capture_labels)

    def run_snapshot(value: IndexDailyHistoryRequest) -> IndexDailyHistoryResult:
        calls.append(value)
        return snapshot()

    monkeypatch.setattr(cli.snapshot_product, "run_index_daily_history", run_snapshot)
    assert cli.main(args) == 0
    semantic = cli._request(cli.build_parser().parse_args(args))
    run_dir = root / cli.STUDY_ID / study.run_key(semantic)
    assert calls == [IndexDailyHistoryRequest("000852.SH", "2026-09-02", "2026-09-14", 1)]
    assert {path.name for path in run_dir.iterdir()} == {
        "result.json",
        "observations.csv",
        "table.md",
        "report.md",
        "reversal_probability_by_deviation.png",
        "conditional_reversal_magnitude_by_deviation.png",
    }
    payload = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert payload["study_id"] == cli.STUDY_ID
    assert payload["run_key"] == study.run_key(semantic)
    assert payload["semantic_request"] == study.canonical_request(semantic)
    assert payload["snapshot"]["public_request"] == {
        "ts_code": "000852.SH",
        "start_trade_date": "2026-09-02",
        "end_trade_date": "2026-09-14",
        "pre_start_observation_count": 1,
    }
    assert payload["snapshot"]["sample_first_trade_date"] == "2026-09-02"
    assert len(list(csv.DictReader((run_dir / "observations.csv").open(encoding="utf-8")))) == 9
    assert len(payload["mr_statistics"]) == len(payload["buckets"]) * 3
    assert len(payload["mfe_5d_statistics"]) == len(payload["buckets"])
    assert chart_labels[0] == chart_labels[1]
    assert chart_labels[0][0].startswith("< ")
    assert chart_labels[0][-1].startswith("≥ ")
    assert all("%" in label for label in chart_labels[0])
    for row in payload["mr_statistics"]:
        bucket = payload["buckets"][row["bucket_index"]]
        assert bucket["bucket_observation_count"] == (
            row["zero_deviation_excluded_count"]
            + row["insufficient_forward_excluded_count"]
            + row["eligible_sample_count"]
        )
        assert row["conditional_reversal_magnitude_sample_count"] == row["reversal_count"]
        if row["eligible_sample_count"]:
            assert row["reversal_probability"] == pytest.approx(
                row["reversal_count"] / row["eligible_sample_count"]
            )
        else:
            assert row["reversal_probability"] is None
        if row["reversal_count"] == 0:
            assert row["conditional_reversal_magnitude_mean"] is None
            assert row["conditional_reversal_magnitude_median"] is None
    table = (run_dir / "table.md").read_text(encoding="utf-8")
    assert "Deviation range | Percentile range | Bucket count" in table
    assert "1D reversal probability | 1D reversal magnitude median" in table
    assert "5D MFE n" in table
    assert chart_labels[0][0] in table
    assert "highest conditional reversal median" in (
        run_dir / "report.md"
    ).read_text(encoding="utf-8")
    for chart in (
        "reversal_probability_by_deviation.png",
        "conditional_reversal_magnitude_by_deviation.png",
    ):
        assert (run_dir / chart).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    for heading in (
        "Question",
        "Inputs",
        "Sample and exclusions",
        "Deviation ranges and results",
        "Observed relationship",
        "Fixed 5D MR and MFE",
        "Limitations",
    ):
        assert heading in (run_dir / "report.md").read_text(encoding="utf-8")
    assert "exploratory relative to the default" in (
        run_dir / "report.md"
    ).read_text(encoding="utf-8")

    calls.clear()
    assert cli.main([*args, "--horizons", "5,3,1"]) == 6
    assert calls == []
    assert "Output error" in capsys.readouterr().err
    (run_dir / "stale.txt").write_text("stale", encoding="utf-8")
    assert cli.main([*args, "--overwrite"]) == 0
    assert not (run_dir / "stale.txt").exists()


@pytest.mark.parametrize("failure", ["snapshot", "insufficient_5d"])
def test_failed_overwrite_preserves_prior_evidence(
    failure: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = configure(tmp_path, monkeypatch)
    args = [*BASE_ARGS, "--window", "1"]
    semantic = cli._request(cli.build_parser().parse_args(args))
    run_dir = root / cli.STUDY_ID / study.run_key(semantic)
    run_dir.mkdir(parents=True)
    (run_dir / "old.txt").write_text("preserve", encoding="utf-8")

    def failing_snapshot(_value: IndexDailyHistoryRequest) -> IndexDailyHistoryResult:
        if failure == "snapshot":
            raise IndexDailyHistoryError("unavailable")
        return snapshot(prices=(90.0, 100.0, 100.0, 100.0, 110.0))

    monkeypatch.setattr(cli.snapshot_product, "run_index_daily_history", failing_snapshot)
    assert cli.main([*args, "--overwrite"]) != 0
    assert (run_dir / "old.txt").read_text(encoding="utf-8") == "preserve"
    assert not list(run_dir.parent.glob(".*.staging-*"))


def test_insufficient_five_day_sample_does_not_publish_new_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = configure(tmp_path, monkeypatch)
    args = [*BASE_ARGS, "--window", "1"]
    semantic = cli._request(cli.build_parser().parse_args(args))
    monkeypatch.setattr(
        cli.snapshot_product,
        "run_index_daily_history",
        lambda _value: snapshot(prices=(90.0, 100.0, 100.0, 100.0, 110.0)),
    )
    assert cli.main(args) == 5
    run_dir = root / cli.STUDY_ID / study.run_key(semantic)
    assert not run_dir.exists()
    assert not list(run_dir.parent.glob(".*.staging-*"))


def test_help_and_required_flags_do_not_access_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(configuration, "load_config", lambda: pytest.fail("configuration loaded"))
    with pytest.raises(SystemExit, match="0"):
        cli.main(["--help"])
    output = capsys.readouterr().out
    assert cli.STUDY_ID in output
    for flag in (
        "--instrument",
        "--start",
        "--end",
        "--method",
        "--window",
        "--bucket-edges",
        "--horizons",
        "--overwrite",
    ):
        assert flag in output
    with pytest.raises(SystemExit, match="2"):
        cli.main(["--instrument", "000852.SH"])
