"""Public semantic types for CFFEX equity-index basis history."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CFFEXEquityIndexBasisHistoryRequest:
    futures_family: str
    start_trade_date: str
    end_trade_date: str


@dataclass(frozen=True)
class CFFEXEquityIndexBasisObservation:
    trade_date: str
    futures_family: str
    underlying_code: str
    contract_code: str
    contract_slot: str
    delist_date: str
    days_to_delist: int
    annualization_days: int
    underlying_close: float
    futures_close: float
    basis_points: float
    basis_pct: float
    annualized_basis_pct: float


@dataclass(frozen=True)
class CFFEXEquityIndexBasisHistoryResult:
    futures_family: str
    start_trade_date: str
    end_trade_date: str
    family_listing_date: str
    first_observation_date: str
    last_observation_date: str
    underlying_code: str
    source_identity: str
    observations: tuple[CFFEXEquityIndexBasisObservation, ...]
