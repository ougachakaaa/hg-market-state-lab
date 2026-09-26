"""Implementation and retained outputs for IM basis/forward-return association."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryResult,
)

from ...shared.im_basis import daily_im_basis, linear_quantile

HORIZONS = (1, 3, 5, 10, 15, 20)


class AssociationStudyError(ValueError):
    """The common eligible sample cannot produce complete association evidence."""


@dataclass(frozen=True)
class AssociationSummary:
    horizon: int
    sample_count: int
    pearson_correlation: float
    ols_alpha: float
    ols_beta: float
    ols_r_squared: float


@dataclass(frozen=True)
class QuintileStatistics:
    basis_quintile: str
    horizon: int
    sample_count: int
    mean_forward_return_pct: float
    median_forward_return_pct: float
    positive_return_rate: float


@dataclass(frozen=True)
class AssociationResult:
    requested_start_trade_date: str
    requested_end_trade_date: str
    effective_predictor_start_trade_date: str
    effective_predictor_end_trade_date: str
    common_sample_count: int
    horizons: tuple[int, ...]
    predictor_identity: str
    quintile_breakpoints: dict[str, float]
    association: tuple[AssociationSummary, ...]
    quintiles: tuple[QuintileStatistics, ...]


def _mean(values: list[float]) -> float:
    return math.fsum(values) / len(values)


def _fit(x: list[float], y: list[float], horizon: int) -> AssociationSummary:
    if len(x) < 2:
        raise AssociationStudyError("association needs at least two common observations.")
    x_mean = _mean(x)
    y_mean = _mean(y)
    ss_x = math.fsum((value - x_mean) ** 2 for value in x)
    ss_y = math.fsum((value - y_mean) ** 2 for value in y)
    if ss_x == 0 or ss_y == 0:
        raise AssociationStudyError(f"zero variance for horizon={horizon}.")
    covariance_sum = math.fsum(
        (x_value - x_mean) * (y_value - y_mean) for x_value, y_value in zip(x, y, strict=True)
    )
    correlation = covariance_sum / math.sqrt(ss_x * ss_y)
    beta = covariance_sum / ss_x
    alpha = y_mean - beta * x_mean
    residual_ss = math.fsum(
        (y_value - (alpha + beta * x_value)) ** 2 for x_value, y_value in zip(x, y, strict=True)
    )
    return AssociationSummary(
        horizon=horizon,
        sample_count=len(x),
        pearson_correlation=correlation,
        ols_alpha=alpha,
        ols_beta=beta,
        ols_r_squared=1 - residual_ss / ss_y,
    )


def _bucket(value: float, thresholds: tuple[float, float, float, float]) -> int:
    for index, threshold in enumerate(thresholds, start=1):
        if value <= threshold:
            return index
    return 5


def compute(snapshot: CSI1000IMBasisHistoryResult) -> AssociationResult:
    """Compute V1 association statistics on one common eligible sample."""
    daily = daily_im_basis(snapshot)
    common_count = len(daily) - max(HORIZONS)
    if common_count < 5:
        raise AssociationStudyError(
            "at least 25 observation dates are required for a five-row common sample."
        )
    eligible = daily[:common_count]
    predictors = [row.non_front_mean_basis for row in eligible]
    thresholds = (
        linear_quantile(predictors, 0.2),
        linear_quantile(predictors, 0.4),
        linear_quantile(predictors, 0.6),
        linear_quantile(predictors, 0.8),
    )
    buckets = [_bucket(value, thresholds) for value in predictors]
    if set(buckets) != {1, 2, 3, 4, 5}:
        raise AssociationStudyError("quintile threshold ties leave at least one empty bucket.")

    returns_by_horizon: dict[int, list[float]] = {}
    associations: list[AssociationSummary] = []
    for horizon in HORIZONS:
        outcomes = [
            (daily[index + horizon].underlying_close / daily[index].underlying_close - 1) * 100
            for index in range(common_count)
        ]
        returns_by_horizon[horizon] = outcomes
        associations.append(_fit(predictors, outcomes, horizon))

    quintile_rows: list[QuintileStatistics] = []
    for quintile in range(1, 6):
        indices = [index for index, bucket in enumerate(buckets) if bucket == quintile]
        if not indices:
            raise AssociationStudyError(f"basis quintile Q{quintile} is empty.")
        for horizon in HORIZONS:
            values = [returns_by_horizon[horizon][index] for index in indices]
            quintile_rows.append(
                QuintileStatistics(
                    basis_quintile=f"Q{quintile}",
                    horizon=horizon,
                    sample_count=len(values),
                    mean_forward_return_pct=_mean(values),
                    median_forward_return_pct=linear_quantile(values, 0.5),
                    positive_return_rate=sum(value > 0 for value in values) / len(values),
                )
            )

    return AssociationResult(
        requested_start_trade_date=snapshot.start_trade_date,
        requested_end_trade_date=snapshot.end_trade_date,
        effective_predictor_start_trade_date=eligible[0].trade_date,
        effective_predictor_end_trade_date=eligible[-1].trade_date,
        common_sample_count=common_count,
        horizons=HORIZONS,
        predictor_identity="non_front_mean_basis",
        quintile_breakpoints={
            label: value
            for label, value in zip(("P20", "P40", "P60", "P80"), thresholds, strict=True)
        },
        association=tuple(associations),
        quintiles=tuple(quintile_rows),
    )


def _write_plot(result: AssociationResult, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(
        [row.horizon for row in result.association],
        [row.pearson_correlation for row in result.association],
        marker="o",
    )
    axis.axhline(0, color="black", linewidth=0.8)
    axis.set_xlabel("Forward horizon (trading observations)")
    axis.set_ylabel("Pearson correlation")
    axis.set_title("IM basis and CSI1000 forward-return association")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def retain(result: AssociationResult, output_dir: Path) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.json"
    report_path = output_dir / "report.md"
    plot_path = output_dir / "correlation_by_horizon.png"
    result_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# IM Basis Forward Return Association",
        "",
        f"Query: {result.requested_start_trade_date} through "
        f"{result.requested_end_trade_date} (inclusive).",
        f"Common eligible sample: {result.common_sample_count} observations.",
        "",
        "| Horizon | N | Pearson | Alpha | Beta | R² |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    lines.extend(
        f"| {row.horizon} | {row.sample_count} | {row.pearson_correlation:.6g} | "
        f"{row.ols_alpha:.6g} | {row.ols_beta:.6g} | {row.ols_r_squared:.6g} |"
        for row in result.association
    )
    lines.extend(
        [
            "",
            "This is in-sample exploratory association evidence, not causal or predictive proof.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_plot(result, plot_path)
    return result_path, report_path, plot_path


def run_and_retain(
    snapshot: CSI1000IMBasisHistoryResult,
    output_dir: Path,
) -> AssociationResult:
    result = compute(snapshot)
    retain(result, output_dir)
    return result
