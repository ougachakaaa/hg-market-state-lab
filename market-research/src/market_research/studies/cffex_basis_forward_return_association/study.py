"""Study-local observations, analyses and retained evidence."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult,
)

FAMILIES = ("IF", "IH", "IC", "IM")
SLOTS = ("M0", "M1", "Q1", "Q2")
HORIZONS = (1, 3, 5, 10, 20)
PERCENTILES = (10, 20, 40, 50, 60, 80, 90)
STUDY_ID = "cffex-basis-forward-return-association"
PREDICTOR = "mean(M1,Q1,Q2 annualized_basis_pct)"


class CFFEXStudyError(ValueError):
    """Required Study observations or populations cannot produce evidence."""


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CFFEXStudyError(f"{label} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise CFFEXStudyError(f"{label} must be finite.")
    return result


def _mean(values: list[float]) -> float:
    result = math.fsum(values) / len(values)
    return _finite(result, "mean")


def _quantile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    h = (len(ordered) - 1) * p
    lower = math.floor(h)
    upper = math.ceil(h)
    result = (
        ordered[lower]
        if lower == upper
        else (ordered[lower] + (ordered[upper] - ordered[lower]) * (h - lower))
    )
    return _finite(result, "quantile")


def _distribution(values: list[float]) -> dict[str, Any]:
    if not values:
        return {
            "sample_count": 0,
            "mean": None,
            "median": None,
            "p25": None,
            "p75": None,
            "positive_return_rate": None,
        }
    return {
        "sample_count": len(values),
        "mean": _mean(values),
        "median": _quantile(values, 0.5),
        "p25": _quantile(values, 0.25),
        "p75": _quantile(values, 0.75),
        "positive_return_rate": sum(value > 0 for value in values) / len(values),
    }


def _breakpoints(values: list[float], family: str, population: str) -> dict[str, Any]:
    return {
        "family": family,
        "population": population,
        "sample_count": len(values),
        "p20": _quantile(values, 0.2),
        "p40": _quantile(values, 0.4),
        "p60": _quantile(values, 0.6),
        "p80": _quantile(values, 0.8),
    }


def _regime(
    eligible: list[dict[str, Any]], family: str, population: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    thresholds = _breakpoints(
        [row["daily_non_front_basis"] for row in eligible], family, population
    )
    bounds = [thresholds[key] for key in ("p20", "p40", "p60", "p80")]
    groups: dict[int, list[dict[str, Any]]] = {index: [] for index in range(1, 6)}
    for row in eligible:
        bucket = next(
            (i for i, bound in enumerate(bounds, 1) if row["daily_non_front_basis"] <= bound), 5
        )
        groups[bucket].append(row)
    table = [
        {
            "family": family,
            "population": population,
            "quintile": f"Q{bucket}",
            "horizon": horizon,
            **_distribution([row[f"forward_return_{horizon}d_pct"] for row in groups[bucket]]),
        }
        for bucket in range(1, 6)
        for horizon in HORIZONS
    ]
    return thresholds, table


def _association(eligible: list[dict[str, Any]], family: str, horizon: int) -> dict[str, Any]:
    x = [row["daily_non_front_basis"] for row in eligible]
    y = [row[f"forward_return_{horizon}d_pct"] for row in eligible]
    n = len(x)
    x_mean, y_mean = _mean(x), _mean(y)
    ss_x = math.fsum((v - x_mean) ** 2 for v in x)
    ss_y = math.fsum((v - y_mean) ** 2 for v in y)
    covariance = math.fsum((a - x_mean) * (b - y_mean) for a, b in zip(x, y, strict=True))
    correlation: float | None = None
    alpha: float | None = None
    beta: float | None = None
    r_squared: float | None = None
    reasons: dict[str, str] = {}
    if n < 2:
        reasons["pearson_correlation"] = "sample_count_below_two"
    elif ss_x == 0:
        reasons["pearson_correlation"] = "zero_predictor_variance"
    elif ss_y == 0:
        reasons["pearson_correlation"] = "zero_outcome_variance"
    else:
        correlation = _finite(covariance / math.sqrt(ss_x * ss_y), "Pearson correlation")
    if ss_x == 0:
        reason = "sample_count_below_two" if n < 2 else "zero_predictor_variance"
        reasons.update({"ols_alpha": reason, "ols_beta": reason, "ols_r_squared": reason})
    else:
        beta = _finite(covariance / ss_x, "OLS beta")
        alpha = _finite(y_mean - beta * x_mean, "OLS alpha")
        if ss_y == 0:
            reasons["ols_r_squared"] = "zero_outcome_variance"
        else:
            residual = math.fsum(
                (value - (alpha + beta * predictor)) ** 2
                for predictor, value in zip(x, y, strict=True)
            )
            r_squared = _finite(1 - residual / ss_y, "OLS R squared")
    return {
        "family": family,
        "horizon": horizon,
        "sample_count": n,
        "pearson_correlation": correlation,
        "ols_alpha": alpha,
        "ols_beta": beta,
        "ols_r_squared": r_squared,
        "null_reasons": reasons,
    }


def _artifact_identity(
    name: str, snapshots: dict[str, CFFEXEquityIndexBasisHistoryResult]
) -> dict[str, Any]:
    def public_input_digest(snapshot: CFFEXEquityIndexBasisHistoryResult) -> str:
        digest = hashlib.sha256()
        for observation in snapshot.observations:
            digest.update(
                json.dumps(
                    asdict(observation),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode("utf-8")
            )
            digest.update(b"\n")
        return digest.hexdigest()

    descriptor: dict[str, Any] = {
        "component": name,
        "inputs": [
            {
                "family": family,
                "start_trade_date": snapshots[family].start_trade_date,
                "effective_start_trade_date": max(
                    snapshots[family].start_trade_date, snapshots[family].family_listing_date
                ),
                "end_trade_date": snapshots[family].end_trade_date,
                "underlying_code": snapshots[family].underlying_code,
                "source_identity": snapshots[family].source_identity,
                "public_input_sha256": public_input_digest(snapshots[family]),
            }
            for family in FAMILIES
        ],
    }
    if name == "daily_basis_environment":
        descriptor["calculation"] = PREDICTOR
    if name == "underlying_forward_returns":
        descriptor["horizons"] = list(HORIZONS)
        descriptor["future_support_end_trade_date"] = snapshots["IF"].end_trade_date
    canonical = json.dumps(descriptor, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "semantic_inputs": descriptor,
    }


def compute(snapshots_input: list[CFFEXEquityIndexBasisHistoryResult]) -> dict[str, Any]:
    """Compute all three Observations and four Analyses from public Product results."""
    snapshots = {result.futures_family: result for result in snapshots_input}
    if len(snapshots_input) != 4 or set(snapshots) != set(FAMILIES):
        raise CFFEXStudyError("one public Snapshot result is required for each family.")
    start = snapshots["IF"].start_trade_date
    end = snapshots["IF"].end_trade_date
    if any(
        (result.start_trade_date, result.end_trade_date) != (start, end)
        for result in snapshots_input
    ):
        raise CFFEXStudyError("Snapshot request bounds do not match across families.")

    term: list[dict[str, Any]] = []
    daily_basis: list[dict[str, Any]] = []
    returns: list[dict[str, Any]] = []
    historical_series: list[dict[str, Any]] = []
    historical_summary: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    eligible_by_family: dict[str, list[dict[str, Any]]] = {}
    for family in FAMILIES:
        snapshot = snapshots[family]
        by_date: dict[str, dict[str, Any]] = {}
        for observation in snapshot.observations:
            if (
                observation.futures_family != family
                or observation.underlying_code != snapshot.underlying_code
            ):
                raise CFFEXStudyError("Snapshot observation family or underlying mismatch.")
            day = by_date.setdefault(observation.trade_date, {})
            if observation.contract_slot not in SLOTS or observation.contract_slot in day:
                raise CFFEXStudyError("Snapshot contains duplicate or unknown contract slot.")
            day[observation.contract_slot] = observation
        if not by_date:
            raise CFFEXStudyError(f"{family} has no basis history.")
        basis_rows: list[dict[str, Any]] = []
        return_rows: list[dict[str, Any]] = []
        dates = sorted(by_date)
        closes: list[float] = []
        for trade_date in dates:
            slots = by_date[trade_date]
            if set(slots) != set(SLOTS):
                raise CFFEXStudyError(f"{family} has incomplete slots on {trade_date}.")
            close = _finite(slots["M0"].underlying_close, "underlying close")
            if close == 0 or any(
                _finite(row.underlying_close, "underlying close") != close for row in slots.values()
            ):
                raise CFFEXStudyError("Snapshot underlying closes are inconsistent.")
            closes.append(close)
            for slot in SLOTS:
                contract_row = slots[slot]
                _finite(contract_row.annualized_basis_pct, "annualized basis")
                term.append({"family": family, **asdict(contract_row)})
            component = {
                slot: _finite(slots[slot].annualized_basis_pct, "annualized basis")
                for slot in ("M1", "Q1", "Q2")
            }
            predictor = _mean(list(component.values()))
            basis_row = {
                "family": family,
                "trade_date": trade_date,
                "daily_non_front_basis": predictor,
                **{f"{slot.lower()}_annualized_basis_pct": component[slot] for slot in component},
            }
            basis_rows.append(basis_row)
            daily_basis.append(basis_row)
            historical_series.append(
                {
                    "family": family,
                    "trade_date": trade_date,
                    "underlying_close": close,
                    "normalized_underlying_close": _finite(
                        close / closes[0] * 100, "normalized close"
                    ),
                    "daily_non_front_basis": predictor,
                    **{
                        f"{slot.lower()}_annualized_basis_pct": _finite(
                            slots[slot].annualized_basis_pct, "annualized basis"
                        )
                        for slot in SLOTS
                    },
                }
            )
        for index, trade_date in enumerate(dates):
            row: dict[str, Any] = {
                "family": family,
                "trade_date": trade_date,
                "underlying_close": closes[index],
            }
            for horizon in HORIZONS:
                row[f"forward_return_{horizon}d_pct"] = (
                    _finite((closes[index + horizon] / closes[index] - 1) * 100, "forward return")
                    if index + horizon < len(dates)
                    else None
                )
            return_rows.append(row)
            returns.append(row)
        eligible = [
            {**basis, **future}
            for basis, future in zip(basis_rows, return_rows, strict=True)
            if future["forward_return_20d_pct"] is not None
        ]
        if not eligible:
            raise CFFEXStudyError(f"{family} has no complete 20D predictor observation.")
        eligible_by_family[family] = eligible
        values = [row["daily_non_front_basis"] for row in basis_rows]
        mean = _mean(values)
        historical_summary.append(
            {
                "family": family,
                "population": "full_basis_history",
                "sample_count": len(values),
                "mean": mean,
                "median": _quantile(values, 0.5),
                "sample_standard_deviation": (
                    _finite(
                        math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1)),
                        "standard deviation",
                    )
                    if len(values) >= 2
                    else None
                ),
                "min": min(values),
                "max": max(values),
                **{f"p{p}": _quantile(values, p / 100) for p in PERCENTILES},
                **{
                    f"{label}_{measure}": count if measure == "count" else count / len(values)
                    for label, count in (
                        ("premium", sum(v > 0 for v in values)),
                        ("discount", sum(v < 0 for v in values)),
                        ("zero", sum(v == 0 for v in values)),
                    )
                    for measure in ("count", "rate")
                },
            }
        )
        samples.append(
            {
                "family": family,
                "requested_start_trade_date": start,
                "requested_end_trade_date": end,
                "family_listing_date": snapshot.family_listing_date,
                "first_basis_date": dates[0],
                "last_basis_date": dates[-1],
                "basis_date_count": len(dates),
                "first_predictor_date": eligible[0]["trade_date"],
                "last_predictor_date": eligible[-1]["trade_date"],
                "predictor_date_count": len(eligible),
                "future_insufficient_exclusion_count": len(dates) - len(eligible),
            }
        )

    common_dates = set.intersection(
        *({row["trade_date"] for row in eligible_by_family[family]} for family in FAMILIES)
    )
    if not common_dates:
        raise CFFEXStudyError("four-family common-period predictor intersection is empty.")
    full_breakpoints: list[dict[str, Any]] = []
    full_regime: list[dict[str, Any]] = []
    linear: list[dict[str, Any]] = []
    common_breakpoints: list[dict[str, Any]] = []
    common_regime: list[dict[str, Any]] = []
    for family in FAMILIES:
        eligible = eligible_by_family[family]
        thresholds, rows = _regime(eligible, family, "full_history_20d_predictor")
        full_breakpoints.append(thresholds)
        full_regime.extend(rows)
        linear.extend(_association(eligible, family, horizon) for horizon in HORIZONS)
        common = [row for row in eligible if row["trade_date"] in common_dates]
        thresholds, rows = _regime(common, family, "common_period")
        common_breakpoints.append(thresholds)
        common_regime.extend(rows)
    identities = {
        name: _artifact_identity(name, snapshots)
        for name in (
            "basis_term_structure",
            "daily_basis_environment",
            "underlying_forward_returns",
        )
    }
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
            "observation_artifacts": identities,
        },
        "observations": {
            "basis_term_structure": term,
            "daily_basis_environment": daily_basis,
            "underlying_forward_returns": returns,
        },
        "sample_summary": {
            "families": samples,
            "common_period": {
                "population": "common_period",
                "first_date": min(common_dates),
                "last_date": max(common_dates),
                "date_count": len(common_dates),
            },
        },
        "historical_basis_context": {
            "population": "full_basis_history",
            "summary": historical_summary,
            "series": historical_series,
        },
        "basis_regime_forward_returns": {
            "population": "full_history_20d_predictor",
            "breakpoints": full_breakpoints,
            "table": full_regime,
        },
        "linear_association": {
            "population": "full_history_20d_predictor",
            "table": linear,
        },
        "common_period_cross_family_comparison": {
            "population": "common_period",
            "breakpoints": common_breakpoints,
            "table": common_regime,
        },
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


def run_and_retain(
    snapshots: list[CFFEXEquityIndexBasisHistoryResult], output_dir: Path
) -> dict[str, Any]:
    result = compute(snapshots)
    retain(result, output_dir)
    return result
