"""Pure semantic request, identity, and lagged-reference Study computation."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import ntpath
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType

from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
    IndexDailyObservation,
)

from ...shared.distribution import (
    DescriptiveSummary,
    DistributionBin,
    descriptive_summary,
    fixed_width_distribution,
    linear_quantile,
)

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


class PriceToLaggedMAStudyError(ValueError):
    """A Study request or supplied Snapshot result cannot produce complete evidence."""


def _date(value: object, name: str) -> str:
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        raise PriceToLaggedMAStudyError(f"{name} must be a valid YYYY-MM-DD date.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise PriceToLaggedMAStudyError(f"{name} must be a valid YYYY-MM-DD date.") from exc
    return value


def _decimal(value: object, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal | int | float | str):
        raise PriceToLaggedMAStudyError(f"{name} must be a finite decimal ratio.")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise PriceToLaggedMAStudyError(f"{name} must be a finite decimal ratio.") from exc
    if not number.is_finite():
        raise PriceToLaggedMAStudyError(f"{name} must be a finite decimal ratio.")
    return number


def _decimal_text(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    plain = format(value, "f")
    if "." in plain:
        plain = plain.rstrip("0").rstrip(".")
    return plain


@dataclass(frozen=True)
class PriceToLaggedMARequest:
    instrument: str
    reference_window: int
    reference_method: str
    reference_method_parameters: Mapping[str, object]
    sample_start_trade_date: str
    sample_end_trade_date: str
    distribution_granularity: Decimal
    percentile_probabilities: tuple[Decimal, ...]

    def __post_init__(self) -> None:
        code = self.instrument
        if (
            not isinstance(code, str)
            or not code
            or code != code.strip()
            or any(char.isspace() or char == "," for char in code)
            or code in {".", ".."}
            or code.endswith(".")
            or any(char in '<>:"/\\|?*' or ord(char) < 32 for char in code)
            or ntpath.isreserved(code)
        ):
            raise PriceToLaggedMAStudyError(
                "instrument must identify one filesystem-safe index without changing its spelling."
            )
        if type(self.reference_window) is not int or self.reference_window <= 0:
            raise PriceToLaggedMAStudyError("reference_window must be a positive integer.")
        if self.reference_method not in ("sma", "volume_weighted"):
            raise PriceToLaggedMAStudyError("reference_method must be sma or volume_weighted.")
        if (
            not isinstance(self.reference_method_parameters, Mapping)
            or self.reference_method_parameters
        ):
            raise PriceToLaggedMAStudyError("reference_method_parameters must be empty in V1.")
        object.__setattr__(self, "reference_method_parameters", MappingProxyType({}))

        start = _date(self.sample_start_trade_date, "sample_start_trade_date")
        end = _date(self.sample_end_trade_date, "sample_end_trade_date")
        if start > end:
            raise PriceToLaggedMAStudyError("sample start must be on or before sample end.")

        granularity = _decimal(self.distribution_granularity, "distribution_granularity")
        if granularity <= 0:
            raise PriceToLaggedMAStudyError("distribution_granularity must be positive.")
        object.__setattr__(
            self, "distribution_granularity", Decimal(_decimal_text(granularity))
        )

        try:
            probabilities = tuple(self.percentile_probabilities)
        except TypeError as exc:
            raise PriceToLaggedMAStudyError("percentile_probabilities must be non-empty.") from exc
        if not probabilities:
            raise PriceToLaggedMAStudyError("percentile_probabilities must be non-empty.")
        normalized = tuple(
            _decimal(value, "percentile_probability") for value in probabilities
        )
        if any(value < 0 or value > 1 for value in normalized):
            raise PriceToLaggedMAStudyError("percentile probabilities must be in [0, 1].")
        if len(set(normalized)) != len(normalized):
            raise PriceToLaggedMAStudyError("percentile probabilities must be distinct.")
        object.__setattr__(
            self,
            "percentile_probabilities",
            tuple(Decimal(_decimal_text(value)) for value in sorted(normalized)),
        )


@dataclass(frozen=True)
class PriceToLaggedMAObservation:
    trade_date: str
    instrument: str
    close: float
    reference_ma: float
    deviation: float


@dataclass(frozen=True)
class RequestedPercentile:
    probability: float
    value: float


@dataclass(frozen=True)
class PriceToLaggedMAResult:
    request: PriceToLaggedMARequest
    run_key: str
    daily_observations: tuple[PriceToLaggedMAObservation, ...]
    distribution_bins: tuple[DistributionBin, ...]
    percentiles: tuple[RequestedPercentile, ...]
    summary: DescriptiveSummary


def canonical_request(request: PriceToLaggedMARequest) -> dict[str, object]:
    """Represent the validated request with its canonical decimal spellings."""
    return {
        "instrument": request.instrument,
        "reference_window": request.reference_window,
        "reference_method": request.reference_method,
        "reference_method_parameters": {},
        "sample_start_trade_date": request.sample_start_trade_date,
        "sample_end_trade_date": request.sample_end_trade_date,
        "distribution_granularity": _decimal_text(request.distribution_granularity),
        "percentile_probabilities": [
            _decimal_text(value) for value in request.percentile_probabilities
        ],
    }


def semantic_digest(request: PriceToLaggedMARequest) -> str:
    """Hash the complete, normalized Study semantic request."""
    payload = json.dumps(
        canonical_request(request), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_key(request: PriceToLaggedMARequest) -> str:
    """Name one Study run using readable fields and a compact semantic digest."""
    dates = (
        f"{request.sample_start_trade_date.replace('-', '')}-"
        f"{request.sample_end_trade_date.replace('-', '')}"
    )
    return (
        f"{request.instrument}__{request.reference_method}{request.reference_window}"
        f"__{dates}__g{_decimal_text(request.distribution_granularity)}"
        f"__{semantic_digest(request)[:12]}"
    )


def derive_snapshot_request(request: PriceToLaggedMARequest) -> IndexDailyHistoryRequest:
    """Map the Study request to the Snapshot product's public request type."""
    return IndexDailyHistoryRequest(
        ts_code=request.instrument,
        start_trade_date=request.sample_start_trade_date,
        end_trade_date=request.sample_end_trade_date,
        pre_start_observation_count=request.reference_window,
    )


def _finite_fact(value: object, name: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise PriceToLaggedMAStudyError(f"Snapshot {name} must be finite numeric.")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise PriceToLaggedMAStudyError(f"Snapshot {name} must be finite numeric.") from exc
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        raise PriceToLaggedMAStudyError(f"Snapshot {name} violates its numeric contract.")
    return number


def _validate_snapshot(
    instrument: str,
    start_trade_date: str,
    end_trade_date: str,
    reference_window: int,
    snapshot: IndexDailyHistoryResult,
) -> None:
    if (
        snapshot.ts_code != instrument
        or snapshot.requested_start_trade_date != start_trade_date
        or snapshot.requested_end_trade_date != end_trade_date
        or snapshot.requested_pre_start_observation_count != reference_window
    ):
        raise PriceToLaggedMAStudyError("Snapshot result does not match the Study request.")
    warmup = snapshot.warmup_observations
    sample = snapshot.sample_observations
    if len(warmup) != reference_window or not sample:
        raise PriceToLaggedMAStudyError("Snapshot result has incomplete warm-up or sample.")
    previous: str | None = None
    for row in (*warmup, *sample):
        trade_date = _date(row.trade_date, "Snapshot trade_date")
        if previous is not None and trade_date <= previous:
            raise PriceToLaggedMAStudyError("Snapshot observations must be unique and ascending.")
        previous = trade_date
        _finite_fact(row.close, "close", positive=True)
        if row.volume is not None:
            _finite_fact(row.volume, "volume", positive=False)
    if warmup[-1].trade_date >= start_trade_date:
        raise PriceToLaggedMAStudyError("Snapshot warm-up must precede the sample bounds.")
    if (
        sample[0].trade_date < start_trade_date
        or sample[-1].trade_date > end_trade_date
    ):
        raise PriceToLaggedMAStudyError("Snapshot sample is outside requested bounds.")


def _reference(window: tuple[IndexDailyObservation, ...], method: str) -> float:
    try:
        if method == "sma":
            value = math.fsum(row.close / len(window) for row in window)
        else:
            volumes = [row.volume for row in window]
            if any(volume is None for volume in volumes):
                raise PriceToLaggedMAStudyError("volume_weighted requires every prior volume.")
            usable = [volume for volume in volumes if volume is not None]
            largest = max(usable)
            if largest <= 0:
                raise PriceToLaggedMAStudyError("volume_weighted requires positive total volume.")
            scaled = [volume / largest for volume in usable]
            total = math.fsum(scaled)
            value = math.fsum(
                row.close * (weight / total)
                for row, weight in zip(window, scaled, strict=True)
            )
    except PriceToLaggedMAStudyError:
        raise
    except (OverflowError, ValueError, ZeroDivisionError) as exc:
        raise PriceToLaggedMAStudyError("reference_ma cannot be calculated.") from exc
    if not math.isfinite(value) or value <= 0:
        raise PriceToLaggedMAStudyError("reference_ma must be finite and positive.")
    return value


def compute_daily_observations(
    instrument: str,
    start_trade_date: str,
    end_trade_date: str,
    reference_window: int,
    reference_method: str,
    snapshot: IndexDailyHistoryResult,
) -> tuple[PriceToLaggedMAObservation, ...]:
    """Calculate the Distribution Study's lagged reference and deviation rows."""
    _validate_snapshot(instrument, start_trade_date, end_trade_date, reference_window, snapshot)
    history = list(snapshot.warmup_observations)
    daily: list[PriceToLaggedMAObservation] = []
    for row in snapshot.sample_observations:
        window = tuple(history[-reference_window:])
        reference = _reference(window, reference_method)
        try:
            deviation = float(Decimal(str(row.close)) / Decimal(str(reference)) - 1)
        except (OverflowError, ValueError) as exc:
            raise PriceToLaggedMAStudyError("deviation must be finite.") from exc
        if not math.isfinite(deviation):
            raise PriceToLaggedMAStudyError("deviation must be finite.")
        daily.append(
            PriceToLaggedMAObservation(
                trade_date=row.trade_date,
                instrument=instrument,
                close=row.close,
                reference_ma=reference,
                deviation=deviation,
            )
        )
        history.append(row)
    return tuple(daily)


def compute(
    request: PriceToLaggedMARequest, snapshot: IndexDailyHistoryResult
) -> PriceToLaggedMAResult:
    """Compute one lagged deviation per Snapshot sample observation."""
    daily = compute_daily_observations(
        request.instrument,
        request.sample_start_trade_date,
        request.sample_end_trade_date,
        request.reference_window,
        request.reference_method,
        snapshot,
    )

    deviations = tuple(row.deviation for row in daily)
    granularity = float(request.distribution_granularity)
    probabilities = tuple(float(value) for value in request.percentile_probabilities)
    if not math.isfinite(granularity) or granularity <= 0:
        raise PriceToLaggedMAStudyError("granularity cannot be represented for distribution.")
    return PriceToLaggedMAResult(
        request=request,
        run_key=run_key(request),
        daily_observations=daily,
        distribution_bins=fixed_width_distribution(deviations, granularity),
        percentiles=tuple(
            RequestedPercentile(probability, linear_quantile(deviations, probability))
            for probability in probabilities
        ),
        summary=descriptive_summary(deviations),
    )


def _write_plot(result: PriceToLaggedMAResult, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(
        [row.lower_bound for row in result.distribution_bins],
        [row.frequency for row in result.distribution_bins],
        width=float(result.request.distribution_granularity),
        align="edge",
        edgecolor="black",
        linewidth=0.5,
    )
    axis.axvline(0, color="black", linewidth=0.8)
    axis.set_xlabel("Close / prior moving reference - 1 (ratio)")
    axis.set_ylabel("Empirical frequency")
    axis.set_title("Price-to-lagged-MA distribution")
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)


def retain(
    result: PriceToLaggedMAResult, snapshot: IndexDailyHistoryResult, output_dir: Path
) -> tuple[Path, ...]:
    """Write the Study's complete machine and human evidence into staging."""
    request_path = output_dir / "request.json"
    observations_path = output_dir / "observations.csv"
    distribution_path = output_dir / "distribution.csv"
    percentiles_path = output_dir / "percentiles.csv"
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    plot_path = output_dir / "distribution.png"

    request_record = {
        "study_id": "price-to-lagged-ma-distribution",
        "run_key": result.run_key,
        "semantic_digest": semantic_digest(result.request),
        "semantic_request": canonical_request(result.request),
        "snapshot": {
            "requested_start_trade_date": snapshot.requested_start_trade_date,
            "requested_end_trade_date": snapshot.requested_end_trade_date,
            "requested_pre_start_observation_count": snapshot.requested_pre_start_observation_count,
            "warmup_observation_count": len(snapshot.warmup_observations),
            "sample_observation_count": len(snapshot.sample_observations),
        },
    }
    request_path.write_text(
        json.dumps(request_record, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    with observations_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("trade_date", "instrument", "close", "reference_ma", "deviation"))
        writer.writerows(
            (row.trade_date, row.instrument, row.close, row.reference_ma, row.deviation)
            for row in result.daily_observations
        )
    with distribution_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("lower_bound", "upper_bound", "count", "frequency"))
        writer.writerows(
            (row.lower_bound, row.upper_bound, row.count, row.frequency)
            for row in result.distribution_bins
        )
    with percentiles_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("probability", "value"))
        writer.writerows((row.probability, row.value) for row in result.percentiles)
    summary_path.write_text(
        json.dumps(asdict(result.summary), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    study_request = result.request
    report_path.write_text(
        "\n".join(
            (
                "# Price-to-Lagged-MA Distribution",
                "",
                "## Question",
                "How are daily closes distributed relative to the prior moving reference?",
                "",
                "## Inputs",
                f"Instrument: {study_request.instrument}; sample calendar bounds: "
                f"{study_request.sample_start_trade_date} through "
                f"{study_request.sample_end_trade_date} (inclusive).",
                f"Reference: {study_request.reference_method} over "
                f"{study_request.reference_window} prior actual observations.",
                f"Distribution width: {study_request.distribution_granularity} (ratio); "
                "percentiles: "
                + ", ".join(str(p) for p in study_request.percentile_probabilities) + ".",
                "",
                "## Method and sample",
                "Each sample day uses Close_T / Reference_(T-1) - 1; the current close "
                "does not enter its reference.",
                f"{len(snapshot.warmup_observations)} warm-up observations and "
                f"{result.summary.sample_count} sample observations; one deviation per sample day.",
                "",
                "## Distribution result",
                f"{len(result.distribution_bins)} zero-anchored, left-closed, "
                "right-open fixed-width bins; see distribution.csv and distribution.png.",
                f"Mean: {result.summary.mean:.8g}; median: {result.summary.median:.8g}; "
                f"min: {result.summary.min:.8g}; max: {result.summary.max:.8g} (ratios).",
                "See percentiles.csv and summary.json for complete numeric results.",
                "",
                "## Limitations",
                "This in-sample description does not establish future returns, "
                "mean reversion, mispricing, or a trading signal.",
                "",
            )
        ),
        encoding="utf-8",
    )
    _write_plot(result, plot_path)
    return (
        request_path,
        observations_path,
        distribution_path,
        percentiles_path,
        summary_path,
        report_path,
        plot_path,
    )
