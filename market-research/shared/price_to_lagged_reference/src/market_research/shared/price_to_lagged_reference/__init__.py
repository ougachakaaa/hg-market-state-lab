"""Shared price-to-lagged-reference observation and deviation calculations.

Canonical authority: ../../../../ARCHITECTURE.md (owner root).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryResult,
    IndexDailyObservation,
)

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


class LaggedReferenceError(ValueError):
    """A Snapshot result cannot produce complete lagged-reference observations."""


@dataclass(frozen=True)
class PriceToLaggedMAObservation:
    trade_date: str
    instrument: str
    close: float
    reference_ma: float
    deviation: float


def _date(value: object, name: str) -> str:
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        raise LaggedReferenceError(f"{name} must be a valid YYYY-MM-DD date.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise LaggedReferenceError(f"{name} must be a valid YYYY-MM-DD date.") from exc
    return value


def _finite_fact(value: object, name: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LaggedReferenceError(f"Snapshot {name} must be finite numeric.")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise LaggedReferenceError(f"Snapshot {name} must be finite numeric.") from exc
    if not math.isfinite(number) or (number <= 0 if positive else number < 0):
        raise LaggedReferenceError(f"Snapshot {name} violates its numeric contract.")
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
        raise LaggedReferenceError("Snapshot result does not match the Study request.")
    warmup = snapshot.warmup_observations
    sample = snapshot.sample_observations
    if len(warmup) != reference_window or not sample:
        raise LaggedReferenceError("Snapshot result has incomplete warm-up or sample.")
    previous: str | None = None
    for row in (*warmup, *sample):
        trade_date = _date(row.trade_date, "Snapshot trade_date")
        if previous is not None and trade_date <= previous:
            raise LaggedReferenceError("Snapshot observations must be unique and ascending.")
        previous = trade_date
        _finite_fact(row.close, "close", positive=True)
        if row.volume is not None:
            _finite_fact(row.volume, "volume", positive=False)
    if warmup[-1].trade_date >= start_trade_date:
        raise LaggedReferenceError("Snapshot warm-up must precede the sample bounds.")
    if sample[0].trade_date < start_trade_date or sample[-1].trade_date > end_trade_date:
        raise LaggedReferenceError("Snapshot sample is outside requested bounds.")


def _reference(window: tuple[IndexDailyObservation, ...], method: str) -> float:
    try:
        if method == "sma":
            value = math.fsum(row.close / len(window) for row in window)
        else:
            volumes = [row.volume for row in window]
            if any(volume is None for volume in volumes):
                raise LaggedReferenceError("volume_weighted requires every prior volume.")
            usable = [volume for volume in volumes if volume is not None]
            largest = max(usable)
            if largest <= 0:
                raise LaggedReferenceError("volume_weighted requires positive total volume.")
            scaled = [volume / largest for volume in usable]
            total = math.fsum(scaled)
            value = math.fsum(
                row.close * (weight / total)
                for row, weight in zip(window, scaled, strict=True)
            )
    except LaggedReferenceError:
        raise
    except (OverflowError, ValueError, ZeroDivisionError) as exc:
        raise LaggedReferenceError("reference_ma cannot be calculated.") from exc
    if not math.isfinite(value) or value <= 0:
        raise LaggedReferenceError("reference_ma must be finite and positive.")
    return value


def compute_daily_observations(
    instrument: str,
    start_trade_date: str,
    end_trade_date: str,
    reference_window: int,
    reference_method: str,
    snapshot: IndexDailyHistoryResult,
) -> tuple[PriceToLaggedMAObservation, ...]:
    """Calculate one lagged reference and deviation per Snapshot sample row."""
    _validate_snapshot(instrument, start_trade_date, end_trade_date, reference_window, snapshot)
    history = list(snapshot.warmup_observations)
    daily: list[PriceToLaggedMAObservation] = []
    for row in snapshot.sample_observations:
        window = tuple(history[-reference_window:])
        reference = _reference(window, reference_method)
        try:
            deviation = float(Decimal(str(row.close)) / Decimal(str(reference)) - 1)
        except (OverflowError, ValueError) as exc:
            raise LaggedReferenceError("deviation must be finite.") from exc
        if not math.isfinite(deviation):
            raise LaggedReferenceError("deviation must be finite.")
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
