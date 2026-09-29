"""Implementation and retained outputs for IM basis/forward-return association."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryResult,
)

from ...shared.distribution import linear_quantile
from ...shared.im_basis import daily_im_basis

HORIZONS = (1, 3, 5, 10, 15, 20)
SLOT_ORDER = {slot: index for index, slot in enumerate(("M0", "M1", "Q1", "Q2"))}


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
    source_observation_count: int
    common_sample_count: int
    future_support_only_count: int
    horizons: tuple[int, ...]
    predictor_identity: str
    quintile_breakpoints: dict[str, float]
    association: tuple[AssociationSummary, ...]
    quintiles: tuple[QuintileStatistics, ...]


def _mean(values: list[float]) -> float:
    try:
        return math.fsum(values) / len(values)
    except OverflowError as exc:
        raise AssociationStudyError("undefined mean from finite observations.") from exc


def _fit(x: list[float], y: list[float], horizon: int) -> AssociationSummary:
    if len(x) < 2:
        raise AssociationStudyError("association needs at least two common observations.")
    try:
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
    except AssociationStudyError:
        raise
    except (OverflowError, ValueError) as exc:
        raise AssociationStudyError(
            f"undefined association statistic for horizon={horizon}."
        ) from exc
    result = AssociationSummary(
        horizon=horizon,
        sample_count=len(x),
        pearson_correlation=correlation,
        ols_alpha=alpha,
        ols_beta=beta,
        ols_r_squared=1 - residual_ss / ss_y,
    )
    if not all(
        math.isfinite(value)
        for value in (
            result.pearson_correlation,
            result.ols_alpha,
            result.ols_beta,
            result.ols_r_squared,
        )
    ):
        raise AssociationStudyError(f"undefined association statistic for horizon={horizon}.")
    return result


def _bucket(value: float, thresholds: tuple[float, float, float, float]) -> int:
    for index, threshold in enumerate(thresholds, start=1):
        if value <= threshold:
            return index
    return 5


def _validate_snapshot_path(snapshot: CSI1000IMBasisHistoryResult) -> None:
    if snapshot.underlying_ts_code != "000852.SH":
        raise AssociationStudyError("Snapshot result has an unexpected underlying.")
    previous: tuple[str, int] | None = None
    for observation in snapshot.observations:
        trade_date = observation.trade_date
        try:
            if date.fromisoformat(trade_date).isoformat() != trade_date:
                raise ValueError
        except ValueError as exc:
            raise AssociationStudyError("Snapshot result has a malformed trade date.") from exc
        if not snapshot.start_trade_date <= trade_date <= snapshot.end_trade_date:
            raise AssociationStudyError("Snapshot observation is outside the requested dates.")
        slot_rank = SLOT_ORDER.get(observation.contract_slot)
        if slot_rank is None:
            raise AssociationStudyError("Snapshot result has an unknown contract slot.")
        current = (trade_date, slot_rank)
        if previous is not None and current <= previous:
            raise AssociationStudyError("Snapshot observation path is not canonically ordered.")
        previous = current


def compute(snapshot: CSI1000IMBasisHistoryResult) -> AssociationResult:
    """Compute V1 association statistics on one common eligible sample."""
    _validate_snapshot_path(snapshot)
    try:
        daily = daily_im_basis(snapshot)
    except OverflowError as exc:
        raise AssociationStudyError(
            "undefined basis predictor from Snapshot observations."
        ) from exc
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
    if not all(math.isfinite(value) for value in thresholds):
        raise AssociationStudyError("non-finite quintile breakpoint.")
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
        if not all(math.isfinite(value) for value in outcomes):
            raise AssociationStudyError(f"non-finite forward return for horizon={horizon}.")
        returns_by_horizon[horizon] = outcomes
        associations.append(_fit(predictors, outcomes, horizon))

    quintile_rows: list[QuintileStatistics] = []
    for quintile in range(1, 6):
        indices = [index for index, bucket in enumerate(buckets) if bucket == quintile]
        if not indices:
            raise AssociationStudyError(f"basis quintile Q{quintile} is empty.")
        for horizon in HORIZONS:
            values = [returns_by_horizon[horizon][index] for index in indices]
            mean_return = _mean(values)
            median_return = linear_quantile(values, 0.5)
            if not math.isfinite(mean_return) or not math.isfinite(median_return):
                raise AssociationStudyError(
                    f"undefined quintile statistic for Q{quintile}, horizon={horizon}."
                )
            quintile_rows.append(
                QuintileStatistics(
                    basis_quintile=f"Q{quintile}",
                    horizon=horizon,
                    sample_count=len(values),
                    mean_forward_return_pct=mean_return,
                    median_forward_return_pct=median_return,
                    positive_return_rate=sum(value > 0 for value in values) / len(values),
                )
            )

    return AssociationResult(
        requested_start_trade_date=snapshot.start_trade_date,
        requested_end_trade_date=snapshot.end_trade_date,
        effective_predictor_start_trade_date=eligible[0].trade_date,
        effective_predictor_end_trade_date=eligible[-1].trade_date,
        source_observation_count=len(daily),
        common_sample_count=common_count,
        future_support_only_count=len(daily) - common_count,
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
    axis.set_title(
        "IM non-front mean annualized basis vs CSI1000 forward return\n"
        f"Pearson correlation by horizon; common sample N={result.common_sample_count}"
    )
    axis.text(
        0.01,
        0.01,
        "Basis: annualized percentage points; return: percentage points",
        transform=axis.transAxes,
        fontsize=8,
    )
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
        json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    lines = [
        "# IM Basis Forward Return Association",
        "",
        f"Requested dates (inclusive): {result.requested_start_trade_date} through "
        f"{result.requested_end_trade_date}.",
        f"Effective predictor dates: {result.effective_predictor_start_trade_date} through "
        f"{result.effective_predictor_end_trade_date}.",
        f"Predictor: {result.predictor_identity} (annualized percentage points); "
        "mean of M1, Q1, Q2.",
        "Horizons (trading observations): "
        + ", ".join(str(horizon) for horizon in result.horizons)
        + ".",
        f"Source observation dates: {result.source_observation_count} observations; "
        f"common eligible predictor sample: {result.common_sample_count} observations; "
        f"future support only: {result.future_support_only_count} observations.",
        "Forward returns, OLS alpha, and quintile mean/median: percentage points. "
        "OLS beta: forward-return percentage points per annualized-basis percentage point. "
        "Pearson correlation and OLS R²: dimensionless.",
        "",
        "## Linear association",
        "",
        "| Horizon (trading observations) | N (observations) | Pearson (dimensionless) | "
        "OLS alpha (percentage points) | OLS beta (return pp / basis pp) | "
        "OLS R² (dimensionless) |",
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
            "## Quintile breakpoints",
            "",
            "| Percentile | Non-front mean annualized basis (percentage points) |",
            "| --- | ---: |",
        ]
    )
    lines.extend(
        f"| {label} | {value:.6g} |" for label, value in result.quintile_breakpoints.items()
    )
    lines.extend(
        [
            "",
            "Q1 is the lowest basis (x <= P20); boundaries belong to the lower group. "
            "Q5 is the highest basis (x > P80). The same boundaries apply to every horizon.",
            "",
            "## Forward returns by basis quintile",
            "",
            "| Quintile | Horizon (trading observations) | N (observations) | "
            "Mean return (percentage points) | Median return (percentage points) | "
            "Positive return rate (0–1, historical empirical) |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    lines.extend(
        f"| {row.basis_quintile} | {row.horizon} | {row.sample_count} | "
        f"{row.mean_forward_return_pct:.6g} | {row.median_forward_return_pct:.6g} | "
        f"{row.positive_return_rate:.6g} |"
        for row in result.quintiles
    )
    lines.extend(
        [
            "",
            "Positive return rate is a historical empirical conditional rate, "
            "not a forecast probability.",
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
