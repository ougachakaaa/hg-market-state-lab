"""Canonical evidence assembly, retention, report and plots."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult,
)

from .context import FAMILIES, HORIZONS, PREDICTOR, SLOTS, STUDY_ID


def assemble(
    snapshots: dict[str, CFFEXEquityIndexBasisHistoryResult],
    start: str,
    end: str,
    observations: dict[str, Any],
    analyses: dict[str, Any],
) -> dict[str, Any]:
    sample_evidence = analyses["_sample_evidence"]
    sample_by_family = {row["family"]: row for row in sample_evidence["families"]}
    return {
        "provenance": {
            "study_id": STUDY_ID,
            "run_key": f"{start}__{end}",
            "requested_start_trade_date": start,
            "requested_end_trade_date": end,
            "predictor": PREDICTOR,
            "horizons": list(HORIZONS),
            "upstream_product": "CFFEX Equity Index Futures Basis History",
            "families": [
                {
                    "family": family,
                    "underlying_code": snapshots[family].underlying_code,
                    "listing_date": snapshots[family].family_listing_date,
                    "source_identity": snapshots[family].source_identity,
                    "request": {
                        "futures_family": family,
                        "start_trade_date": start,
                        "end_trade_date": end,
                    },
                }
                for family in FAMILIES
            ],
            "observation_artifacts": observations["identities"],
        },
        "observations": {
            name: observations[name]
            for name in (
                "basis_term_structure",
                "daily_basis_environment",
                "underlying_forward_returns",
            )
        },
        "sample_summary": {
            "families": [
                {
                    "family": family,
                    "requested_start_trade_date": start,
                    "requested_end_trade_date": end,
                    "family_listing_date": snapshots[family].family_listing_date,
                    **sample_by_family[family],
                }
                for family in FAMILIES
            ],
            "common_period": sample_evidence["common_period"],
        },
        "historical_basis_context": analyses["historical_basis_context"],
        "basis_regime_forward_returns": analyses["basis_regime_forward_returns"],
        "linear_association": analyses["linear_association"],
        "common_period_cross_family_comparison": analyses[
            "common_period_cross_family_comparison"
        ],
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _format(value: Any) -> str:
    return "null" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)


def _table(
    lines: list[str], title: str, rows: list[dict[str, Any]], fields: tuple[str, ...]
) -> None:
    lines.extend(
        [
            f"## {title}",
            "",
            "| " + " | ".join(fields) + " |",
            "| " + " | ".join("---" for _ in fields) + " |",
        ]
    )
    lines.extend("| " + " | ".join(_format(row[field]) for field in fields) + " |" for row in rows)
    lines.append("")


def _report(result: dict[str, Any], path: Path) -> None:
    provenance = result["provenance"]
    summary = result["sample_summary"]
    lines = [
        "# CFFEX Basis and Forward Return Association",
        "",
        f"Requested dates: {provenance['requested_start_trade_date']} through "
        f"{provenance['requested_end_trade_date']} (inclusive).",
        "Historical association evidence; it does not establish causality, significance, "
        "forecasts or trading advice.",
        "Forward horizons count actual trading observations within the request. "
        "Overlapping windows and correlated indices limit interpretation.",
        "Basis and return statistics use percentage points; positive return rates are ratios.",
        "",
    ]
    _table(
        lines,
        "Sample summary",
        summary["families"],
        (
            "family",
            "family_listing_date",
            "first_basis_date",
            "last_basis_date",
            "basis_date_count",
            "first_predictor_date",
            "last_predictor_date",
            "predictor_date_count",
            "future_insufficient_exclusion_count",
        ),
    )
    common = summary["common_period"]
    lines.extend(
        [
            f"Common-period actual-date intersection: {common['first_date']} through "
            f"{common['last_date']}; N={common['date_count']}.",
            "",
        ]
    )
    _table(
        lines,
        "Historical basis summary (full basis history)",
        result["historical_basis_context"]["summary"],
        (
            "family",
            "sample_count",
            "mean",
            "median",
            "sample_standard_deviation",
            "min",
            "max",
            "p10",
            "p20",
            "p40",
            "p50",
            "p60",
            "p80",
            "p90",
            "premium_count",
            "premium_rate",
            "discount_count",
            "discount_rate",
            "zero_count",
            "zero_rate",
        ),
    )
    for key, title in (
        ("basis_regime_forward_returns", "Full-history 20D predictor"),
        ("common_period_cross_family_comparison", "Common-period predictor"),
    ):
        section = result[key]
        _table(
            lines,
            f"{title} breakpoints",
            section["breakpoints"],
            (
                "family",
                "population",
                "sample_count",
                "p20",
                "p40",
                "p60",
                "p80",
            ),
        )
        _table(
            lines,
            f"{title} quintile forward returns",
            section["table"],
            (
                "family",
                "population",
                "quintile",
                "horizon",
                "sample_count",
                "mean",
                "median",
                "p25",
                "p75",
                "positive_return_rate",
            ),
        )
    _table(
        lines,
        "Linear association (full-history 20D predictor)",
        result["linear_association"]["table"],
        (
            "family",
            "horizon",
            "sample_count",
            "pearson_correlation",
            "ols_alpha",
            "ols_beta",
            "ols_r_squared",
            "null_reasons",
        ),
    )
    lines.extend(
        [
            "## Figures",
            "",
            "- `historical_context.png`: normalized index close and non-front basis.",
            "- `term_structure.png`: M0/M1/Q1/Q2 annualized basis history.",
            "- `quintile_heatmaps.png`: median forward return and positive return rate.",
            "- `common_period_comparison.png`: common-period Q1 to Q5 median 20D return.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _plots(result: dict[str, Any], output_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    series = result["historical_basis_context"]["series"]
    figure, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    for family in FAMILIES:
        rows = [row for row in series if row["family"] == family]
        dates = [date.fromisoformat(row["trade_date"]) for row in rows]
        axes[0].plot(dates, [row["normalized_underlying_close"] for row in rows], label=family)
        axes[1].plot(dates, [row["daily_non_front_basis"] for row in rows], label=family)
    axes[0].set_ylabel("Index close (first = 100)")
    axes[1].set_ylabel("Annualized basis (pp)")
    axes[1].set_xlabel("Trade date")
    for axis in axes:
        axis.legend()
        axis.grid(alpha=0.2)
        axis.xaxis.set_major_locator(plt.MaxNLocator(8))
    figure.tight_layout()
    figure.savefig(output_dir / "historical_context.png", dpi=140)
    plt.close(figure)

    figure, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    for axis, family in zip(axes, FAMILIES, strict=True):
        rows = [row for row in series if row["family"] == family]
        for slot in SLOTS:
            axis.plot(
                [date.fromisoformat(row["trade_date"]) for row in rows],
                [row[f"{slot.lower()}_annualized_basis_pct"] for row in rows],
                label=slot,
            )
        axis.set_ylabel(f"{family} basis (pp)")
        axis.legend(ncol=4)
        axis.grid(alpha=0.2)
        axis.xaxis.set_major_locator(plt.MaxNLocator(8))
    axes[-1].set_xlabel("Trade date")
    figure.tight_layout()
    figure.savefig(output_dir / "term_structure.png", dpi=140)
    plt.close(figure)

    table = result["basis_regime_forward_returns"]["table"]
    figure, axes = plt.subplots(4, 2, figsize=(12, 13))
    for i, family in enumerate(FAMILIES):
        for j, (field, title) in enumerate(
            (("median", "Median return (pp)"), ("positive_return_rate", "Positive return rate"))
        ):
            grid = [
                [
                    next(
                        row[field]
                        for row in table
                        if row["family"] == family
                        and row["quintile"] == f"Q{q}"
                        and row["horizon"] == h
                    )
                    for h in HORIZONS
                ]
                for q in range(1, 6)
            ]
            import numpy as np

            image = axes[i, j].imshow(
                np.ma.masked_invalid(
                    np.array([[float("nan") if v is None else v for v in row] for row in grid])
                ),
                aspect="auto",
                cmap="coolwarm",
            )
            axes[i, j].set_title(f"{family}: {title}")
            axes[i, j].set_xticks(range(5), [f"{h}D" for h in HORIZONS])
            axes[i, j].set_yticks(range(5), [f"Q{q}" for q in range(1, 6)])
            figure.colorbar(image, ax=axes[i, j], shrink=0.7)
    figure.tight_layout()
    figure.savefig(output_dir / "quintile_heatmaps.png", dpi=140)
    plt.close(figure)

    common = result["common_period_cross_family_comparison"]["table"]
    figure, axis = plt.subplots(figsize=(9, 5))
    for family in FAMILIES:
        values = [
            next(
                row["median"]
                for row in common
                if row["family"] == family and row["quintile"] == f"Q{q}" and row["horizon"] == 20
            )
            for q in range(1, 6)
        ]
        axis.plot(range(1, 6), values, marker="o", label=family)
    axis.set_xticks(range(1, 6), [f"Q{q}" for q in range(1, 6)])
    axis.set_ylabel("Median 20D forward return (pp)")
    axis.set_title("Common-period actual-date intersection")
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_dir / "common_period_comparison.png", dpi=140)
    plt.close(figure)


def retain(result: dict[str, Any], output_dir: Path) -> tuple[Path, ...]:
    """Materialize observations and presentations from the computed canonical result."""
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "result.json", result)
    for name, rows in result["observations"].items():
        path = output_dir / f"{name}.jsonl"
        path.write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"
                for row in rows
            ),
            encoding="utf-8",
        )
    _report(result, output_dir / "report.md")
    _plots(result, output_dir)
    return tuple(sorted(path for path in output_dir.iterdir() if path.is_file()))
