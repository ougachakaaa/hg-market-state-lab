"""Study-local finite checks and mathematical statistics."""

from __future__ import annotations

import math
from typing import Any

from .context import CFFEXStudyError


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
