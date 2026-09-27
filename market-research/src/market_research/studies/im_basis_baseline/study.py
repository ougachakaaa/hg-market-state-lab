"""Implementation and retained outputs for the IM basis baseline study."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import stdev

from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryResult,
)

from ...shared.distribution import linear_quantile
from ...shared.im_basis import daily_im_basis

SERIES = ("M0", "M1", "Q1", "Q2", "non_front_mean_basis")
PERCENTILES = (5, 10, 25, 50, 75, 90, 95)


class BaselineStudyError(ValueError):
    """The input sample cannot produce the complete baseline."""


@dataclass(frozen=True)
class BaselineStatistics:
    count: int
    mean: float
    median: float
    standard_deviation: float
    percentiles: dict[str, float]
    min: float
    max: float


@dataclass(frozen=True)
class BaselineResult:
    requested_start_trade_date: str
    requested_end_trade_date: str
    statistics: dict[str, BaselineStatistics]


def _statistics(values: list[float]) -> BaselineStatistics:
    if len(values) < 2:
        raise BaselineStudyError("each baseline series needs at least two observations.")
    percentiles = {
        f"P{percentile:02d}": linear_quantile(values, percentile / 100)
        for percentile in PERCENTILES
    }
    median = linear_quantile(values, 0.5)
    if not math.isclose(median, percentiles["P50"], rel_tol=0, abs_tol=0):
        raise AssertionError("median and P50 conventions diverged")
    return BaselineStatistics(
        count=len(values),
        mean=math.fsum(values) / len(values),
        median=median,
        standard_deviation=stdev(values),
        percentiles=percentiles,
        min=min(values),
        max=max(values),
    )


def compute(snapshot: CSI1000IMBasisHistoryResult) -> BaselineResult:
    """Compute all five deterministic daily-series baselines."""
    daily = daily_im_basis(snapshot)
    series = {slot: [row.annualized_basis_by_slot[slot] for row in daily] for slot in SERIES[:4]}
    series["non_front_mean_basis"] = [row.non_front_mean_basis for row in daily]
    return BaselineResult(
        requested_start_trade_date=snapshot.start_trade_date,
        requested_end_trade_date=snapshot.end_trade_date,
        statistics={name: _statistics(values) for name, values in series.items()},
    )


def _write_plot(result: BaselineResult, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    names = list(result.statistics)
    means = [result.statistics[name].mean for name in names]
    medians = [result.statistics[name].median for name in names]
    figure, axis = plt.subplots(figsize=(9, 5))
    positions = range(len(names))
    axis.plot(positions, means, marker="o", label="Mean")
    axis.plot(positions, medians, marker="s", label="Median")
    axis.set_xticks(list(positions), names, rotation=15)
    axis.set_ylabel("Annualized basis (%)")
    axis.set_title("IM annualized basis baseline")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def retain(result: BaselineResult, output_dir: Path) -> tuple[Path, Path, Path]:
    """Write study-owned machine, human, and static-plot evidence."""
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "result.json"
    report_path = output_dir / "report.md"
    plot_path = output_dir / "baseline.png"
    result_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# IM Annualized Basis Baseline",
        "",
        f"Query: {result.requested_start_trade_date} through "
        f"{result.requested_end_trade_date} (inclusive).",
        "",
        "| Series | Count | Mean | Median | Std dev | P05 | P95 | Min | Max |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, stats in result.statistics.items():
        lines.append(
            f"| {name} | {stats.count} | {stats.mean:.6g} | {stats.median:.6g} | "
            f"{stats.standard_deviation:.6g} | {stats.percentiles['P05']:.6g} | "
            f"{stats.percentiles['P95']:.6g} | {stats.min:.6g} | {stats.max:.6g} |"
        )
    lines.extend(
        [
            "",
            "This retained output is descriptive research evidence, "
            "not a signal or recommendation.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_plot(result, plot_path)
    return result_path, report_path, plot_path


def run_and_retain(
    snapshot: CSI1000IMBasisHistoryResult,
    output_dir: Path,
) -> BaselineResult:
    result = compute(snapshot)
    retain(result, output_dir)
    return result
