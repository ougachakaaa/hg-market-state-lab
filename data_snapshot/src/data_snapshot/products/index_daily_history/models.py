"""Public semantic request and result types for Index Daily History."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexDailyHistoryRequest:
    ts_code: str
    start_trade_date: str
    end_trade_date: str
    pre_start_observation_count: int


@dataclass(frozen=True)
class IndexDailyObservation:
    trade_date: str
    close: float
    volume: float | None


@dataclass(frozen=True)
class IndexDailyHistoryResult:
    ts_code: str
    requested_start_trade_date: str
    requested_end_trade_date: str
    requested_pre_start_observation_count: int
    warmup_observations: tuple[IndexDailyObservation, ...]
    sample_observations: tuple[IndexDailyObservation, ...]
