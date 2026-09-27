"""Deterministic Index Daily History projection and validation."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from ...artifacts import RawRecord
from ...sources import tushare
from .models import IndexDailyHistoryRequest, IndexDailyHistoryResult, IndexDailyObservation


class IndexDailyHistoryPreparationError(ValueError):
    """Captured facts cannot produce a complete history result."""


def _number(value: Any, field: str, *, positive: bool) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise IndexDailyHistoryPreparationError(f"{field} must be numeric, got {value!r}.")
    try:
        result = float(value)
    except OverflowError as exc:
        raise IndexDailyHistoryPreparationError(f"{field} is not finite.") from exc
    if not math.isfinite(result) or (result <= 0 if positive else result < 0):
        raise IndexDailyHistoryPreparationError(f"{field} is unusable: {value!r}.")
    return result


def _observations(
    facts: Sequence[RawRecord],
    request: IndexDailyHistoryRequest,
    *,
    before_start: bool,
    seen_dates: set[str],
) -> tuple[IndexDailyObservation, ...]:
    observations: list[IndexDailyObservation] = []
    for fact in facts:
        trade_date = fact.get("trade_date")
        if fact.get("ts_code") != request.ts_code or not tushare.is_iso_date(trade_date):
            raise IndexDailyHistoryPreparationError("index fact has an invalid identity or date.")
        assert isinstance(trade_date, str)
        if before_start:
            if trade_date >= request.start_trade_date:
                raise IndexDailyHistoryPreparationError(
                    "warm-up fact is outside its requested scope."
                )
        elif not request.start_trade_date <= trade_date <= request.end_trade_date:
            raise IndexDailyHistoryPreparationError("sample fact is outside its requested scope.")
        if trade_date in seen_dates:
            raise IndexDailyHistoryPreparationError(f"duplicate index observation on {trade_date}.")
        seen_dates.add(trade_date)

        close = _number(fact.get("close"), "close", positive=True)
        raw_volume = fact.get("vol")
        volume = None if raw_volume is None else _number(raw_volume, "vol", positive=False)
        observations.append(IndexDailyObservation(trade_date, close, volume))
    return tuple(sorted(observations, key=lambda observation: observation.trade_date))


def prepare_history(
    request: IndexDailyHistoryRequest,
    sample_facts: Sequence[RawRecord],
    pre_start_facts: Sequence[RawRecord],
) -> IndexDailyHistoryResult:
    """Validate all captured rows, then select the exact preceding observations."""
    seen_dates: set[str] = set()
    sample = _observations(sample_facts, request, before_start=False, seen_dates=seen_dates)
    if not sample:
        raise IndexDailyHistoryPreparationError("no sample observation in the requested interval.")
    previous = _observations(pre_start_facts, request, before_start=True, seen_dates=seen_dates)
    required = request.pre_start_observation_count
    if len(previous) < required:
        raise IndexDailyHistoryPreparationError(
            f"insufficient pre-start observations: required {required}, found {len(previous)}."
        )
    warmup = previous[-required:] if required else ()
    return IndexDailyHistoryResult(
        ts_code=request.ts_code,
        requested_start_trade_date=request.start_trade_date,
        requested_end_trade_date=request.end_trade_date,
        requested_pre_start_observation_count=required,
        warmup_observations=warmup,
        sample_observations=sample,
    )
