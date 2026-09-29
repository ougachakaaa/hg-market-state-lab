"""Four named Analyses over Study Observation outputs and their populations."""

from __future__ import annotations

import math
from typing import Any

from market_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult,
)

from .context import FAMILIES, HORIZONS, PERCENTILES, SLOTS, CFFEXStudyError
from .statistics import _association, _distribution, _finite, _mean, _quantile


def _regime(
    eligible: list[dict[str, Any]], family: str, population: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    thresholds = {
        "family": family,
        "population": population,
        "sample_count": len(eligible),
        **{
            f"p{p}": _quantile([row["daily_non_front_basis"] for row in eligible], p / 100)
            for p in (20, 40, 60, 80)
        },
    }
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


def _eligible_sample(
    basis_rows: list[dict[str, Any]], return_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {**basis, **future}
        for basis, future in zip(basis_rows, return_rows, strict=True)
        if future["forward_return_20d_pct"] is not None
    ]


def _historical_basis_context(
    family: str,
    term_rows: list[dict[str, Any]],
    basis_rows: list[dict[str, Any]],
    return_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    values = [row["daily_non_front_basis"] for row in basis_rows]
    mean = _mean(values)
    summary = {
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
    slots_by_date = {(row["trade_date"], row["contract_slot"]): row for row in term_rows}
    first_close = return_rows[0]["underlying_close"]
    series = [
        {
            "family": family,
            "trade_date": basis["trade_date"],
            "underlying_close": future["underlying_close"],
            "normalized_underlying_close": _finite(
                future["underlying_close"] / first_close * 100, "normalized close"
            ),
            "daily_non_front_basis": basis["daily_non_front_basis"],
            **{
                f"{slot.lower()}_annualized_basis_pct": _finite(
                    slots_by_date[(basis["trade_date"], slot)]["annualized_basis_pct"],
                    "annualized basis",
                )
                for slot in SLOTS
            },
        }
        for basis, future in zip(basis_rows, return_rows, strict=True)
    ]
    return summary, series


def run(
    observations: dict[str, Any],
    snapshots: dict[str, CFFEXEquityIndexBasisHistoryResult],
    start: str,
    end: str,
) -> dict[str, Any]:
    """Run historical context, full-history regime/linear and common-period analyses."""
    historical_series: list[dict[str, Any]] = []
    historical_summary: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    eligible_by_family: dict[str, list[dict[str, Any]]] = {}
    for family in FAMILIES:
        rows = observations["by_family"][family]
        basis_rows = rows["basis"]
        return_rows = rows["returns"]
        eligible = _eligible_sample(basis_rows, return_rows)
        if not eligible:
            raise CFFEXStudyError(f"{family} has no complete 20D predictor observation.")
        eligible_by_family[family] = eligible
        summary, series = _historical_basis_context(family, rows["term"], basis_rows, return_rows)
        historical_summary.append(summary)
        historical_series.extend(series)
        dates = [row["trade_date"] for row in basis_rows]
        samples.append(
            {
                "family": family,
                "requested_start_trade_date": start,
                "requested_end_trade_date": end,
                "family_listing_date": snapshots[family].family_listing_date,
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
        thresholds, table = _regime(eligible, family, "full_history_20d_predictor")
        full_breakpoints.append(thresholds)
        full_regime.extend(table)
        linear.extend(_association(eligible, family, horizon) for horizon in HORIZONS)
        common = [row for row in eligible if row["trade_date"] in common_dates]
        thresholds, table = _regime(common, family, "common_period")
        common_breakpoints.append(thresholds)
        common_regime.extend(table)
    return {
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
        "linear_association": {"population": "full_history_20d_predictor", "table": linear},
        "common_period_cross_family_comparison": {
            "population": "common_period",
            "breakpoints": common_breakpoints,
            "table": common_regime,
        },
    }
