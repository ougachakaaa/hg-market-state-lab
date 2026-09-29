"""Four named Analyses over Study Observation outputs and their populations."""

from __future__ import annotations

import math
from typing import Any

from .context import FAMILIES, HORIZONS, PERCENTILES, SLOTS, CFFEXStudyError
from .statistics import _distribution, _finite, _linear_association, _mean, _quantile


def _by_family(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {family: [] for family in FAMILIES}
    for row in rows:
        grouped[row["family"]].append(row)
    return grouped


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


def run(observations: dict[str, Any]) -> dict[str, Any]:
    """Run historical context, full-history regime/linear and common-period analyses."""
    terms = _by_family(observations["basis_term_structure"])
    bases = _by_family(observations["daily_basis_environment"])
    returns = _by_family(observations["underlying_forward_returns"])
    historical_series: list[dict[str, Any]] = []
    historical_summary: list[dict[str, Any]] = []
    sample_evidence: list[dict[str, Any]] = []
    eligible_by_family: dict[str, list[dict[str, Any]]] = {}
    for family in FAMILIES:
        basis_rows = sorted(bases[family], key=lambda row: row["trade_date"])
        returns_by_date = {row["trade_date"]: row for row in returns[family]}
        basis_dates = [row["trade_date"] for row in basis_rows]
        if set(basis_dates) != set(returns_by_date):
            raise CFFEXStudyError(f"{family} basis and forward-return dates do not match.")
        return_rows = [returns_by_date[trade_date] for trade_date in basis_dates]
        eligible = _eligible_sample(basis_rows, return_rows)
        if not eligible:
            raise CFFEXStudyError(f"{family} has no complete 20D predictor observation.")
        eligible_by_family[family] = eligible
        summary, series = _historical_basis_context(family, terms[family], basis_rows, return_rows)
        historical_summary.append(summary)
        historical_series.extend(series)
        sample_evidence.append(
            {
                "family": family,
                "first_basis_date": basis_dates[0],
                "last_basis_date": basis_dates[-1],
                "basis_date_count": len(basis_dates),
                "first_predictor_date": eligible[0]["trade_date"],
                "last_predictor_date": eligible[-1]["trade_date"],
                "predictor_date_count": len(eligible),
                "future_insufficient_exclusion_count": len(basis_dates) - len(eligible),
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
        for horizon in HORIZONS:
            mechanics = _linear_association(
                [row["daily_non_front_basis"] for row in eligible],
                [row[f"forward_return_{horizon}d_pct"] for row in eligible],
            )
            linear.append(
                {"family": family, "horizon": horizon, "sample_count": len(eligible), **mechanics}
            )
        common = [row for row in eligible if row["trade_date"] in common_dates]
        thresholds, table = _regime(common, family, "common_period")
        common_breakpoints.append(thresholds)
        common_regime.extend(table)
    return {
        "_sample_evidence": {
            "families": sample_evidence,
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
