"""Public semantic request/result types for CSI1000 IM Basis History."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CSI1000IMBasisHistoryRequest:
    start_trade_date: str
    end_trade_date: str


@dataclass(frozen=True)
class IMBasisObservation:
    trade_date: str
    ts_code: str
    contract_slot: str
    delist_date: str
    days_to_delist: int
    annualization_days: int
    underlying_close: float
    future_close: float
    basis_points: float
    basis_pct: float
    annualized_basis_pct: float


@dataclass(frozen=True)
class CSI1000IMBasisHistoryResult:
    start_trade_date: str
    end_trade_date: str
    underlying_ts_code: str
    observations: tuple[IMBasisObservation, ...]
