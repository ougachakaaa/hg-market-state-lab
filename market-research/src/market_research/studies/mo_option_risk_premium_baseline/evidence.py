"""Retained machine and human evidence for the MO baseline Study."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .inputs import STUDY_ID, canonical_request, decimal_text
from .study import StudyResult


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _number(value: Any) -> str:
    return "—" if value is None else f"{value:.6g}"


def _table(rows: list[dict[str, Any]], columns: tuple[tuple[str, str], ...]) -> list[str]:
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(
            str(row[key]) if isinstance(row[key], str | int) else _number(row[key])
            for _, key in columns
        )
        + " |"
        for row in rows
    ]
    return [header, rule, *body]


def _report(result: StudyResult) -> str:
    request = result.request
    rows = list(result.summary)
    reasons = Counter(reason for cell in result.cells for reason in cell.exclusion_reasons)
    lines = [
        "# MO Option Risk Premium Baseline",
        "",
        "## Question and inputs",
        "",
        "Historical seller compensation of MO options held to expiry, by entry DTE, "
        "underlying-relative moneyness, and CALL / PUT.",
        "",
        f"Expiry range: {request.start_expiry_date} through "
        f"{request.end_expiry_date} (inclusive).  ",
        "DTE targets: " + ", ".join(map(str, request.dte_targets)) + ".  ",
        "Moneyness targets: "
        + ", ".join(decimal_text(value) for value in request.moneyness_targets)
        + ".  ",
        f"Discovered expiries: {result.expected_expiry_count}; "
        f"expected cells: {len(result.cells)}; "
        f"valid cells: {sum(not cell.exclusion_reasons for cell in result.cells)}.",
        "",
        "## DTE compensation profile",
        "",
        "Each row is a CALL or PUT and moneyness bucket at an entry DTE. "
        "Expiry events have equal weight.",
        "",
    ]
    dte_columns = (
        ("DTE", "target_dte"),
        ("Type", "option_type"),
        ("Moneyness", "moneyness_target"),
        ("Valid", "sample_count"),
        ("Coverage", "unique_expiry_coverage_ratio"),
        ("Excluded", "excluded_cell_count"),
        ("Mean points", "seller_compensation_points_mean"),
        ("Median points", "seller_compensation_points_median"),
        ("Minimum points", "seller_compensation_points_min"),
    )
    lines.extend(_table(rows, dte_columns))
    lines += [
        "",
        "## DTE × moneyness and CALL / PUT comparison",
        "",
        "The same grouped evidence is shown with moneyness as the comparison axis. "
        "An empty bucket has no estimated statistic.",
        "",
    ]
    surface_columns = (
        ("Type", "option_type"),
        ("DTE", "target_dte"),
        ("Moneyness", "moneyness_target"),
        ("Valid", "sample_count"),
        ("Mean ratio", "seller_compensation_ratio_mean"),
        ("Median annualized", "annualized_compensation_ratio_median"),
        ("P05 points", "seller_compensation_points_p05"),
        ("P50 points", "seller_compensation_points_p50"),
        ("P95 points", "seller_compensation_points_p95"),
    )
    lines.extend(
        _table(
            sorted(
                rows,
                key=lambda row: (
                    row["option_type"],
                    row["target_dte"],
                    float(row["moneyness_target"]),
                ),
            ),
            surface_columns,
        )
    )
    lines += [
        "",
        "## Coverage and exclusions",
        "",
        f"Excluded cells: {sum(bool(cell.exclusion_reasons) for cell in result.cells)}. "
        "Reasons can overlap and must not be summed as excluded cells.",
        "",
    ]
    lines.extend(["| Reason | Cells |", "| --- | ---: |"])
    lines.extend(f"| {reason} | {count} |" for reason, count in sorted(reasons.items()))
    lines += [
        "",
        "The full summary records each bucket's expected expiry count, coverage, "
        "excluded-cell count, reason counts, all central statistics, compensation "
        "quantiles, and sign frequencies.",
        "",
        "## Provenance and audit",
        "",
        f"Run key: `{result.run_key}`. Public query identities and deterministic content "
        "fingerprints are in `request.json`; all valid and excluded expected cells are "
        "in `option_outcome_panel.json`; grouped statistics are in "
        "`compensation_summary.json`.",
        "",
        "## Interpretation limits",
        "",
        "The entry (high + low) / 2 is a daily price proxy, not an executable price "
        "or VWAP; the high and low facts need not occur at the same instant. "
        "The expiry CSI1000 close gives a payoff proxy, not exact CFFEX settlement. "
        "Compensation is not portfolio CAGR or margin return. Same-expiry cells share "
        "a terminal market event and are dependent; repeated selections of one contract "
        "are not independent risk events. The result omits transaction costs, slippage, "
        "hedging, margin, and the holding path. It does not estimate a risk-neutral "
        "probability premium or a tradable strategy return.",
        "",
    ]
    return "\n".join(lines)


def retain(result: StudyResult, output_dir: Path) -> tuple[Path, ...]:
    """Write one Observation Artifact and two Analysis Evidence Products."""
    request_path = output_dir / "request.json"
    panel_path = output_dir / "option_outcome_panel.json"
    summary_path = output_dir / "compensation_summary.json"
    report_path = output_dir / "risk_premium_report.md"
    _write_json(
        request_path,
        {
            "study_id": STUDY_ID,
            "run_key": result.run_key,
            "semantic_request": canonical_request(result.request),
            "provenance": result.provenance,
            "expected_expiry_count": result.expected_expiry_count,
            "expected_cell_count": len(result.cells),
            "valid_cell_count": sum(not cell.exclusion_reasons for cell in result.cells),
            "excluded_cell_count": sum(bool(cell.exclusion_reasons) for cell in result.cells),
        },
    )
    _write_json(
        panel_path,
        {
            "name": "option_outcome_panel",
            "defined_by": "ExpiryDteOptionOutcome",
            "semantic_identity_sha256": result.provenance["observation_artifact_sha256"],
            "cells": [asdict(cell) for cell in result.cells],
        },
    )
    _write_json(
        summary_path,
        {
            "name": "compensation_summary",
            "defined_by": ["DteCompensationProfile", "MoneynessCompensationProfile"],
            "observation_artifact_sha256": result.provenance["observation_artifact_sha256"],
            "groups": list(result.summary),
        },
    )
    report_path.write_text(_report(result), encoding="utf-8")
    return request_path, panel_path, summary_path, report_path
