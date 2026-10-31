"""Replay complete CSI1000 public evidence and build a local human review pack."""

import argparse
import csv
import json
import platform
import shutil
import statistics
import subprocess
import time
from dataclasses import replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_index_daily import IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRecord
from live_e2e_acceptance import ROOT, public, require
from market_research.descriptive.cases.price_segmentation import (
    SegmentationRequest,
    construct_observations,
    prepare_inputs,
)
from segmentation_live_e2e import verify
from segmentation_review import chart
from segmentation_review_smoothing import PROFILES, diagnostics, smooth

EPSILONS = (0.01, 0.02, 0.03, 0.05)
START_DATE = "2020-01-01"
END_DATE = "2026-10-31"


class SavedExport:
    """Replay the retained public operation sequence without provider access."""

    def __init__(self, attempt: dict[str, Any], calendar: bool):
        self.attempt = attempt
        self.calendar = calendar
        self.ensured = False

    def _view(self, value: dict[str, Any]) -> Any:
        calendar = self.calendar
        rows: list[Any] = []
        for original in value["records"]:
            row = dict(original)
            if calendar:
                row["cal_date"] = date.fromisoformat(row["cal_date"])
                if row["pretrade_date"] is not None:
                    row["pretrade_date"] = date.fromisoformat(row["pretrade_date"])
                rows.append(TradeCalendarRecord(**row))
            else:
                row["trade_date"] = date.fromisoformat(row["trade_date"])
                rows.append(IndexDailyRow(**row))
        if calendar:
            require(value["scope"] == ["SSE"], "Invalid saved Calendar scope")
        scope = (
            SimpleNamespace(exchange=value["scope"][0])
            if calendar
            else SimpleNamespace(index_codes=tuple(value["scope"]))
        )
        return SimpleNamespace(
            dataset=value["dataset"],
            view=value["view"],
            export_schema_version=value["schema_version"],
            scope=scope,
            window=SimpleNamespace(
                start_date=date.fromisoformat(value["start_date"]),
                end_date=date.fromisoformat(value["end_date"]),
            ),
            coverage=CoverageResult(**value["coverage"]),
            records=tuple(rows),
        )

    def export(self, request: Any) -> Any:
        require(public(request) == self.attempt["request"], "Saved request mismatch")
        value = self.attempt["final_export" if self.ensured else "preliminary_export"]
        return self._view(value)

    def ensure(self, request: Any) -> Any:
        require(public(request) == self.attempt["request"], "Saved request mismatch")
        value = self.attempt["ensure_result"]
        require(value is not None and not self.ensured, "Missing or repeated saved Ensure")
        self.ensured = True
        failures = tuple(
            UnitFailure(
                (item["identity"][0], date.fromisoformat(item["identity"][1])), item["reason"]
            )
            for item in value["failures"]
        )
        return EnsureResult(**{**value, "failures": failures})


def replay(path: Path) -> tuple[Any, list[Any], list[float]]:
    evidence = json.loads(path.read_text(encoding="utf-8"))
    request = evidence["request"]
    require(
        request["index_code"] == "000852.SH"
        and request["start_date"] == START_DATE
        and request["end_date"] == END_DATE,
        "Wrong research scope",
    )
    req = SegmentationRequest(
        **{
            **request,
            "start_date": date.fromisoformat(request["start_date"]),
            "end_date": date.fromisoformat(request["end_date"]),
        }
    )
    attempts = evidence["input_evidence"]
    require(len(attempts) == 2, "Two public input attempts required")
    prepared = prepare_inputs(
        req,
        calendar_service=SavedExport(attempts[0], True),
        index_service=SavedExport(attempts[1], False),
    )
    require(public(prepared.input_provenance) == attempts, "Saved input evidence mismatch")
    require(prepared.input_fingerprint == evidence["input_fingerprint"], "Fingerprint mismatch")
    results = []
    elapsed = []
    for epsilon in EPSILONS:
        identity = replace(req, epsilon=epsilon)
        inputs = replace(prepared, request_identity=identity)
        start = time.perf_counter()
        result = construct_observations(identity, inputs)
        elapsed.append(time.perf_counter() - start)
        verify(result)
        again = construct_observations(identity, inputs)
        require(
            (result.important_points, result.segments, result.diagnostics)
            == (again.important_points, again.segments, again.diagnostics),
            "Replay mismatch",
        )
        results.append(result)
    return prepared, results, elapsed


def generate(evidence: Path, output: Path) -> None:
    prepared, results, elapsed = replay(evidence)
    output.mkdir(parents=True, exist_ok=True)
    retained_results = [
        {
            "request": public(r.request_identity),
            "important_points": public(r.important_points),
            "segments": public(r.segments),
            "diagnostics": public(r.diagnostics),
        }
        for r in results
    ]
    result_path = output / "result_evidence.json"
    if result_path.exists():
        require(
            json.loads(result_path.read_text(encoding="utf-8")) == retained_results,
            "Saved result replay mismatch",
        )
    else:
        result_path.write_text(
            json.dumps(retained_results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if evidence.resolve() != (output / "input_evidence.json").resolve():
        shutil.copyfile(evidence, output / "input_evidence.json")
    with (output / "daily_prices.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("date", "close"))
        writer.writerows(zip(prepared.session_dates, prepared.closes, strict=True))
    comparisons = []
    segments = []
    views = []
    for result, runtime in zip(results, elapsed, strict=True):
        durations = [s.duration_sessions for s in result.segments]
        amplitudes = [abs(s.amplitude_ratio) for s in result.segments]
        comparison = {
            **public(result.diagnostics),
            "runtime_seconds": runtime,
            "average_duration": statistics.mean(durations),
            "median_duration": statistics.median(durations),
            "minimum_duration": min(durations),
            "maximum_duration": max(durations),
            "single_session_ratio": durations.count(1) / len(durations),
            "duration_le_3_ratio": sum(d <= 3 for d in durations) / len(durations),
            "average_absolute_amplitude": statistics.mean(amplitudes),
            "median_absolute_amplitude": statistics.median(amplitudes),
            **{
                f"{direction}_count": sum(s.direction == direction for s in result.segments)
                for direction in ("up", "down", "flat")
            },
        }
        profile_views = {}
        for name, profile in PROFILES.items():
            merged = smooth(result.segments, profile)
            profile_views[name] = merged
            comparison.update(
                {f"{name}_{key}": value for key, value in diagnostics(merged).items()}
            )
        comparisons.append(comparison)
        views.append(profile_views)
        for ordinal, segment in enumerate(result.segments):
            row = public(segment)
            del row["segment_identity"]
            segments.append(
                {
                    "epsilon": result.request_identity.epsilon,
                    "profile": "base",
                    "base_segments": str(ordinal),
                    **row,
                }
            )
        for name, merged in profile_views.items():
            for segment in merged:
                segments.append(
                    {
                        "epsilon": result.request_identity.epsilon,
                        "profile": name,
                        "base_segments": ";".join(map(str, segment.base_segments)),
                        "start_index": segment.start_index,
                        "end_index": segment.end_index,
                        "start_date": segment.start_date.isoformat(),
                        "end_date": segment.end_date.isoformat(),
                        "start_close": segment.start_close,
                        "end_close": segment.end_close,
                        "duration_sessions": segment.duration_sessions,
                        "amplitude_ratio": segment.amplitude_ratio,
                        "direction": segment.direction,
                        "touches_start_boundary": segment.start_index
                        == result.segments[0].start_index,
                        "touches_end_boundary": segment.end_index == result.segments[-1].end_index,
                    }
                )
    for name, rows in (("comparison.csv", comparisons), ("segments.csv", segments)):
        with (output / name).open("w", encoding="utf-8", newline="") as f:
            dict_writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            dict_writer.writeheader()
            dict_writer.writerows(rows)
    facts = {"dates": [d.isoformat() for d in prepared.session_dates], "closes": prepared.closes}
    panels = "".join(
        f"<h2>ε = {r.request_identity.epsilon}: {len(r.segments)} segments; "
        f"max log error {r.diagnostics.max_reconstruction_error:.8f}</h2>"
        + "".join(
            f'<h3>{name} · {len(indices) - 1} segments</h3><div class="overview">'
            + chart(facts, {"indices": indices})
            + '</div><p>Expanded view (scroll horizontally):</p><div class="zoom">'
            + chart(facts, {"indices": indices})
            + "</div>"
            for name, indices in [
                ("Base", tuple(p.index for p in r.important_points)),
                *[
                    (
                        name.title() + " experimental",
                        (parts[0].start_index, *(s.end_index for s in parts)),
                    )
                    for name, parts in view.items()
                ],
            ]
        )
        for r, view in zip(results, views, strict=True)
    )
    table_rows = "".join(
        "<tr>" + "".join(f"<td>{v}</td>" for v in r.values()) + "</tr>" for r in comparisons
    )
    headers = "".join(f"<th>{k}</th>" for k in comparisons[0])
    explanation = (
        "PIP fits natural log Close. Straight lines in Close space are visual aids. "
        "Epsilon is not minimum segment return; segments are not necessarily complete "
        "peak-to-trough swings. Duration is measured in trading-session intervals. "
        "These are human diagnostic measures, not formal market statistics."
        " Blue is original Close; orange dots are retained endpoints and dashed orange "
        "lines connect them. Experimental merged views do not retain the PIP error bound "
        "and are not canonical results. Light: duration ≤ 1 or absolute return ≤ 0.015; "
        "medium: duration ≤ 2 or absolute return ≤ 0.025. Base segment ordinals are zero-based."
    )
    (output / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>CSI1000 segmentation</title>'
        "<style>body{font:15px system-ui;margin:2em;color:#173047} .zoom{overflow-x:auto}"
        ".overview svg{width:100%;height:auto;background:#f8fafc}"
        ".zoom svg{width:2500px;height:auto;background:#f8fafc} svg text{font:12px sans-serif}"
        "table{border-collapse:collapse}td,th{border:1px solid #ccd8e2;padding:5px}"
        ".table{overflow:auto}</style><h1>CSI1000 full-history segmentation</h1>"
        f"<p>{facts['dates'][0]} to {facts['dates'][-1]} · {len(facts['dates'])} sessions</p>"
        f"<p>Fingerprint: {prepared.input_fingerprint}</p><p>{explanation}</p>"
        "<p>Scroll each chart horizontally to inspect intervals; "
        "all charts use the same scale.</p>"
        f'<div class="table"><table><tr>{headers}</tr>{table_rows}</table></div>{panels}</html>',
        encoding="utf-8",
    )
    (output / "README.md").write_text(
        f"# CSI1000 full-history review\n\n{explanation}\n\nOpen index.html offline. "
        "Scroll horizontally to inspect a specific interval. Regenerate with:\n\n"
        f"`poetry run python market_research/tests/segmentation_full_history.py --evidence "
        f'"{evidence.resolve()}" --output "{output.resolve()}"`\n',
        encoding="utf-8",
    )
    status_path = evidence.parent / "acquisition_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    manifest = {
        "verdict": "BLOCKED",
        "gates": {
            "source_completeness": "PASS",
            "mathematical_correctness": "PASS",
            "offline_reproducibility": "PASS",
            "human_review_usability": "NOT_VERIFIED",
        },
        "scope": public(results[0].request_identity),
        "epsilons": EPSILONS,
        "input_fingerprint": prepared.input_fingerprint,
        "session_count": prepared.input_point_count,
        "first_session": facts["dates"][0],
        "last_session": facts["dates"][-1],
        "results": comparisons,
        "coverage": {
            a.final_export.dataset: public(a.final_export.coverage)
            for a in prepared.input_provenance
        },
        "files": [
            "input_evidence.json",
            "daily_prices.csv",
            "comparison.csv",
            "segments.csv",
            "result_evidence.json",
            "index.html",
            "README.md",
        ],
        "git_commit": commit,
        "python": platform.python_version(),
        "acquisition": status,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "verdict": "BLOCKED: browser usability not verified",
                "sessions": len(facts["dates"]),
                "fingerprint": prepared.input_fingerprint,
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    generate(args.evidence, args.output)


if __name__ == "__main__":
    main()
