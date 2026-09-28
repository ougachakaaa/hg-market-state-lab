"""Semantic request, conditional reversion calculation, and retained evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from bisect import bisect_right
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
)

from ...shared.distribution import linear_quantile
from ..price_to_lagged_ma_distribution import (
    PriceToLaggedMAObservation,
    PriceToLaggedMAStudyError,
    compute_daily_observations,
)

STUDY_ID = "price-to-lagged-ma-short-horizon-reversion"
DEFAULT_EDGES = ("0", "0.05", "0.10", "0.20", "0.80", "0.90", "0.95", "1")
DEFAULT_HORIZONS = (1, 3, 5)
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


class ReversionStudyError(ValueError):
    """A Study request or sample cannot produce complete evidence."""


def _date(value: object, name: str) -> str:
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        raise ReversionStudyError(f"{name} must be a valid YYYY-MM-DD date.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ReversionStudyError(f"{name} must be a valid YYYY-MM-DD date.") from exc
    return value


def _decimal(value: object, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal | int | float | str):
        raise ReversionStudyError(f"{name} must be a finite decimal ratio.")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ReversionStudyError(f"{name} must be a finite decimal ratio.") from exc
    if not number.is_finite():
        raise ReversionStudyError(f"{name} must be a finite decimal ratio.")
    return number


def _decimal_text(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    plain = format(value, "f")
    return plain.rstrip("0").rstrip(".") if "." in plain else plain


@dataclass(frozen=True)
class ReversionRequest:
    instrument: str
    sample_start_trade_date: str
    sample_end_trade_date: str
    reference_method: str = "sma"
    reference_window: int = 60
    percentile_bucket_edges: tuple[Decimal, ...] = tuple(Decimal(p) for p in DEFAULT_EDGES)
    forward_horizons: tuple[int, ...] = DEFAULT_HORIZONS

    def __post_init__(self) -> None:
        code = self.instrument
        if (
            not isinstance(code, str)
            or not code
            or code != code.strip()
            or any(char.isspace() or char == "," for char in code)
        ):
            raise ReversionStudyError("instrument must be one index identity without whitespace.")
        _date(self.sample_start_trade_date, "sample_start_trade_date")
        _date(self.sample_end_trade_date, "sample_end_trade_date")
        if self.sample_start_trade_date > self.sample_end_trade_date:
            raise ReversionStudyError("sample start must be on or before sample end.")
        if self.reference_method not in ("sma", "volume_weighted"):
            raise ReversionStudyError("reference_method must be sma or volume_weighted.")
        if type(self.reference_window) is not int or self.reference_window <= 0:
            raise ReversionStudyError("reference_window must be a positive integer.")
        try:
            edges = tuple(
                _decimal(value, "percentile_bucket_edge") for value in self.percentile_bucket_edges
            )
        except TypeError as exc:
            raise ReversionStudyError(
                "percentile_bucket_edges must contain at least two values."
            ) from exc
        if (
            len(edges) < 2
            or edges[0] != 0
            or edges[-1] != 1
            or any(left >= right for left, right in zip(edges, edges[1:], strict=False))
        ):
            raise ReversionStudyError("bucket edges must increase strictly from 0 to 1.")
        object.__setattr__(
            self, "percentile_bucket_edges", tuple(Decimal(_decimal_text(p)) for p in edges)
        )
        try:
            horizons = tuple(self.forward_horizons)
        except TypeError as exc:
            raise ReversionStudyError(
                "forward_horizons must be non-empty positive integers."
            ) from exc
        if not horizons or any(type(h) is not int or h <= 0 for h in horizons):
            raise ReversionStudyError("forward_horizons must be non-empty positive integers.")
        if len(set(horizons)) != len(horizons):
            raise ReversionStudyError("forward_horizons must be distinct.")
        object.__setattr__(self, "forward_horizons", tuple(sorted(horizons)))


def canonical_request(request: ReversionRequest) -> dict[str, object]:
    return {
        "instrument": request.instrument,
        "sample_start_trade_date": request.sample_start_trade_date,
        "sample_end_trade_date": request.sample_end_trade_date,
        "reference_method": request.reference_method,
        "reference_method_parameters": {},
        "reference_window": request.reference_window,
        "percentile_bucket_edges": [_decimal_text(p) for p in request.percentile_bucket_edges],
        "forward_horizons": list(request.forward_horizons),
    }


def run_key(request: ReversionRequest) -> str:
    payload = json.dumps(
        canonical_request(request), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def derive_snapshot_request(request: ReversionRequest) -> IndexDailyHistoryRequest:
    return IndexDailyHistoryRequest(
        ts_code=request.instrument,
        start_trade_date=request.sample_start_trade_date,
        end_trade_date=request.sample_end_trade_date,
        pre_start_observation_count=request.reference_window,
    )


@dataclass(frozen=True)
class Bucket:
    bucket_index: int
    percentile_lower_edge: float
    percentile_upper_edge: float
    deviation_lower_threshold: float
    deviation_upper_threshold: float
    bucket_observation_count: int


@dataclass(frozen=True)
class MRStatistics:
    bucket_index: int
    horizon: int
    configured_horizon: bool
    sample_count: int
    zero_deviation_excluded_count: int
    insufficient_forward_excluded_count: int
    mean: float | None
    median: float | None
    positive_rate: float | None


@dataclass(frozen=True)
class MFEStatistics:
    bucket_index: int
    sample_count: int
    mean: float | None
    median: float | None


@dataclass(frozen=True)
class ReversionResult:
    request: ReversionRequest
    run_key: str
    daily_observations: tuple[PriceToLaggedMAObservation, ...]
    observation_bucket_indices: tuple[int, ...]
    buckets: tuple[Bucket, ...]
    mr_statistics: tuple[MRStatistics, ...]
    mfe_statistics: tuple[MFEStatistics, ...]


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    try:
        result = math.fsum(value / len(values) for value in values)
    except (OverflowError, ValueError) as exc:
        raise ReversionStudyError("outcome mean is not finite.") from exc
    if not math.isfinite(result):
        raise ReversionStudyError("outcome mean is not finite.")
    return result


def _return(start: float, end: float) -> float:
    value = end / start - 1
    if not math.isfinite(value):
        raise ReversionStudyError("forward return is not finite.")
    return value


def compute(request: ReversionRequest, snapshot: IndexDailyHistoryResult) -> ReversionResult:
    try:
        daily = compute_daily_observations(
            request.instrument,
            request.sample_start_trade_date,
            request.sample_end_trade_date,
            request.reference_window,
            request.reference_method,
            snapshot,
        )
    except PriceToLaggedMAStudyError as exc:
        raise ReversionStudyError(str(exc)) from exc
    deviations = tuple(row.deviation for row in daily)
    thresholds = tuple(
        linear_quantile(deviations, float(p)) for p in request.percentile_bucket_edges
    )
    bucket_indices = tuple(bisect_right(thresholds[1:-1], value) for value in deviations)
    buckets = tuple(
        Bucket(
            bucket_index=index,
            percentile_lower_edge=float(request.percentile_bucket_edges[index]),
            percentile_upper_edge=float(request.percentile_bucket_edges[index + 1]),
            deviation_lower_threshold=thresholds[index],
            deviation_upper_threshold=thresholds[index + 1],
            bucket_observation_count=bucket_indices.count(index),
        )
        for index in range(len(thresholds) - 1)
    )
    mr_rows: list[MRStatistics] = []
    mfe_rows: list[MFEStatistics] = []
    evaluation_horizons = sorted(set((*request.forward_horizons, 5)))
    total_5d = 0
    for bucket in buckets:
        member_indices = [
            i for i, assigned in enumerate(bucket_indices) if assigned == bucket.bucket_index
        ]
        for horizon in evaluation_horizons:
            zero_count = 0
            insufficient_count = 0
            mr_values: list[float] = []
            mfe_values: list[float] = []
            for i in member_indices:
                deviation = daily[i].deviation
                if deviation == 0:
                    zero_count += 1
                elif i + horizon >= len(daily):
                    insufficient_count += 1
                else:
                    direction = 1 if deviation < 0 else -1
                    mr = direction * _return(daily[i].close, daily[i + horizon].close)
                    mr_values.append(mr)
                    if horizon == 5:
                        mfe_values.append(
                            max(
                                0.0,
                                *(
                                    direction * _return(daily[i].close, daily[i + step].close)
                                    for step in range(1, 6)
                                ),
                            )
                        )
            count = len(mr_values)
            mr_rows.append(
                MRStatistics(
                    bucket_index=bucket.bucket_index,
                    horizon=horizon,
                    configured_horizon=horizon in request.forward_horizons,
                    sample_count=count,
                    zero_deviation_excluded_count=zero_count,
                    insufficient_forward_excluded_count=insufficient_count,
                    mean=_mean(mr_values),
                    median=linear_quantile(mr_values, 0.5) if mr_values else None,
                    positive_rate=sum(value > 0 for value in mr_values) / count if count else None,
                )
            )
            if horizon == 5:
                total_5d += count
                mfe_rows.append(
                    MFEStatistics(
                        bucket_index=bucket.bucket_index,
                        sample_count=count,
                        mean=_mean(mfe_values),
                        median=linear_quantile(mfe_values, 0.5) if mfe_values else None,
                    )
                )
    if total_5d == 0:
        raise ReversionStudyError("no valid 5D MR/MFE observation within the sample.")
    return ReversionResult(
        request=request,
        run_key=run_key(request),
        daily_observations=daily,
        observation_bucket_indices=bucket_indices,
        buckets=buckets,
        mr_statistics=tuple(mr_rows),
        mfe_statistics=tuple(mfe_rows),
    )


def _value(value: float | None) -> str:
    return "—" if value is None else f"{value:.6g}"


def _write_chart(result: ReversionResult, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure, axis = plt.subplots(figsize=(10, 5))
    horizons = result.request.forward_horizons
    width = 0.8 / len(horizons)
    for position, horizon in enumerate(horizons):
        rows = [row for row in result.mr_statistics if row.horizon == horizon]
        x_values = [
            bucket.bucket_index - 0.4 + width * (position + 0.5) for bucket in result.buckets
        ]
        axis.bar(
            x_values,
            [float("nan") if row.mean is None else row.mean for row in rows],
            width=width,
            label=f"{horizon}D",
        )
    axis.axhline(0, color="black", linewidth=0.7)
    axis.set_xticks([bucket.bucket_index for bucket in result.buckets])
    axis.set_xticklabels(
        [
            f"{bucket.percentile_lower_edge:g}–{bucket.percentile_upper_edge:g}"
            for bucket in result.buckets
        ],
        rotation=30,
        ha="right",
    )
    axis.set_xlabel("Full-sample deviation percentile bucket")
    axis.set_ylabel("Mean direction-adjusted return (ratio)")
    axis.set_title("Historical short-horizon mean reversion by bucket")
    axis.legend(title="Configured horizon")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def retain(
    result: ReversionResult, snapshot: IndexDailyHistoryResult, output_dir: Path
) -> tuple[Path, ...]:
    """Write complete evidence into the Research UI staging directory."""
    result_path = output_dir / "result.json"
    observations_path = output_dir / "observations.csv"
    table_path = output_dir / "table.md"
    report_path = output_dir / "report.md"
    chart_path = output_dir / "mr_by_bucket.png"
    payload = {
        "study_id": STUDY_ID,
        "run_key": result.run_key,
        "semantic_request": canonical_request(result.request),
        "snapshot": {
            "product": "Index Daily History",
            "public_request": asdict(derive_snapshot_request(result.request)),
            "requested_start_trade_date": snapshot.requested_start_trade_date,
            "requested_end_trade_date": snapshot.requested_end_trade_date,
            "requested_pre_start_observation_count": snapshot.requested_pre_start_observation_count,
            "warmup_observation_count": len(snapshot.warmup_observations),
            "sample_observation_count": len(snapshot.sample_observations),
            "sample_first_trade_date": snapshot.sample_observations[0].trade_date,
            "sample_last_trade_date": snapshot.sample_observations[-1].trade_date,
        },
        "buckets": [asdict(row) for row in result.buckets],
        "mr_statistics": [asdict(row) for row in result.mr_statistics],
        "mfe_5d_statistics": [asdict(row) for row in result.mfe_statistics],
    }
    result_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    with observations_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ("trade_date", "instrument", "close", "reference_ma", "deviation", "bucket_index")
        )
        writer.writerows(
            (
                row.trade_date,
                row.instrument,
                row.close,
                row.reference_ma,
                row.deviation,
                bucket_index,
            )
            for row, bucket_index in zip(
                result.daily_observations, result.observation_bucket_indices, strict=True
            )
        )

    header = ["Bucket", "Count", "Thresholds"]
    for horizon in result.request.forward_horizons:
        header += [
            f"{horizon}D MR n",
            f"{horizon}D mean",
            f"{horizon}D median",
            f"{horizon}D positive",
        ]
    if 5 not in result.request.forward_horizons:
        header += ["5D MR n", "5D MR mean", "5D MR median", "5D MR positive"]
    header += ["5D MFE n", "5D MFE mean", "5D MFE median"]
    lines = [
        "# Price-to-Lagged-MA Short-Horizon Reversion — main table",
        "",
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for bucket in result.buckets:
        cells = [
            f"{bucket.percentile_lower_edge:g}–{bucket.percentile_upper_edge:g}",
            str(bucket.bucket_observation_count),
            f"{bucket.deviation_lower_threshold:.6g}–{bucket.deviation_upper_threshold:.6g}",
        ]
        shown = list(result.request.forward_horizons)
        if 5 not in shown:
            shown.append(5)
        for horizon in shown:
            row = next(
                row
                for row in result.mr_statistics
                if row.bucket_index == bucket.bucket_index and row.horizon == horizon
            )
            cells += [
                str(row.sample_count),
                _value(row.mean),
                _value(row.median),
                _value(row.positive_rate),
            ]
        mfe = result.mfe_statistics[bucket.bucket_index]
        cells += [str(mfe.sample_count), _value(mfe.mean), _value(mfe.median)]
        lines.append("| " + " | ".join(cells) + " |")
    table_path.write_text("\n".join((*lines, "")), encoding="utf-8")
    zero_exclusions = sum(row.zero_deviation_excluded_count for row in result.mr_statistics)
    forward_exclusions = sum(
        row.insufficient_forward_excluded_count for row in result.mr_statistics
    )
    report_lines = [
        "# Price-to-Lagged-MA Short-Horizon Reversion",
        "",
        "## Question",
        "How strong was subsequent opposite-direction price movement at each historical "
        "deviation percentile bucket?",
        "The default 60-observation SMA / 1–5D relationship is a hypothesis to examine, "
        "not a finding.",
        "",
        "## Inputs",
        "```json",
        json.dumps(canonical_request(result.request), indent=2, sort_keys=True),
        "```",
        "",
        (
            "This configuration is exploratory relative to the default 60-observation "
            "SMA / 1–5D hypothesis."
            if result.request.reference_method != "sma"
            or result.request.reference_window != 60
            or result.request.forward_horizons != DEFAULT_HORIZONS
            or result.request.percentile_bucket_edges
            != tuple(Decimal(edge) for edge in DEFAULT_EDGES)
            else "This run uses the default reference, buckets, and evaluation horizons."
        ),
        "Percentile thresholds use every sample deviation, including zero-deviation and "
        "forward-ineligible dates.",
        "",
        "## Sample and exclusions",
        f"Warm-up observations: {len(snapshot.warmup_observations)}; "
        f"sample observations: {len(snapshot.sample_observations)}; actual sample dates: "
        f"{snapshot.sample_observations[0].trade_date} through "
        f"{snapshot.sample_observations[-1].trade_date}.",
        f"Across bucket × evaluation-horizon groups: {zero_exclusions} zero-deviation "
        f"and {forward_exclusions} insufficient-forward exclusions.",
        "",
        "| Bucket | Horizon | Zero deviation | Insufficient forward | Valid |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    report_lines.extend(
        f"| {row.bucket_index} | {row.horizon} | {row.zero_deviation_excluded_count} | "
        f"{row.insufficient_forward_excluded_count} | {row.sample_count} |"
        for row in result.mr_statistics
    )
    report_lines += ["", "## Bucket thresholds and main table", *lines, ""]
    report_lines += [
        "## Fixed 5D MR and MFE",
        "The main table compares 5D endpoint MR with the strongest favorable movement "
        "through T+5 on exactly the same eligible dates.",
        "",
        "## Limitations",
        "These are conditional historical descriptions of the selected index, reference, "
        "sample, buckets and horizons. In-sample thresholds change with the sample.",
        "Opposite-direction movement does not prove causal attraction to the moving "
        "reference, long-term trend reversal, or net profitability after costs.",
        "The result is not a forecast, signal, decision, or recommendation.",
        "",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    _write_chart(result, chart_path)
    return result_path, observations_path, table_path, report_path, chart_path
