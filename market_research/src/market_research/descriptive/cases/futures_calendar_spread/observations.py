"""Immutable case-owned Pair-day observations, accounting and classified failures."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRow
from market_research.descriptive.cases.futures_basis import (
    DailySlotResolution,
    DailyUniverseEvidence,
    Slot,
)

from .financial import CalendarSpreadResult
from .inputs import CASE, DEFINITION_VERSION, PreparedCalendarSpreadInputs

PAIRS: tuple[tuple[Slot, Slot], ...] = (
    ("M0", "M1"),
    ("M0", "Q1"),
    ("M0", "Q2"),
    ("M1", "Q1"),
    ("M1", "Q2"),
    ("Q1", "Q2"),
)
ExpiryStage = Literal["0_7", "8_21", "22_plus"]


@dataclass(frozen=True, slots=True)
class PairDayObservation:
    product_code: str
    trade_date: date
    near_slot: Slot
    far_slot: Slot
    near: FuturesDailyRow | None
    far: FuturesDailyRow | None
    delta_days: int | None
    near_dte_days: int | None
    expiry_stage: ExpiryStage | None
    metrics: CalendarSpreadResult | None
    outcome: Literal["valid", "not_applicable", "excluded"]
    reason: Literal["no_active_contract", "nonpositive_close"] | None
    source_evidence: DailyUniverseEvidence
    case: Literal["futures_calendar_spread_v1"] = CASE
    definition_version: Literal["futures_calendar_spread_definition_v1"] = DEFINITION_VERSION


@dataclass(frozen=True, slots=True)
class CalendarSpreadDay:
    trade_date: date
    status: Literal["open", "closed"]
    reason: Literal["non_trading_day"] | None
    resolution: DailySlotResolution | None
    observations: tuple[PairDayObservation, ...]


@dataclass(frozen=True, slots=True)
class OutcomeAccounting:
    candidate_count: int
    valid_count: int
    not_applicable_count: int
    excluded_count: int


@dataclass(frozen=True, slots=True)
class CalendarSpreadObservationSet:
    prepared_inputs: PreparedCalendarSpreadInputs
    days: tuple[CalendarSpreadDay, ...]
    accounting: OutcomeAccounting
    case: Literal["futures_calendar_spread_v1"] = CASE
    definition_version: Literal["futures_calendar_spread_definition_v1"] = DEFINITION_VERSION

    @property
    def observations(self) -> tuple[PairDayObservation, ...]:
        return tuple(pair for day in self.days for pair in day.observations)


class ObservationConstructionError(Exception):
    """A whole-call failure with retained input and applicable pair/date context."""

    stage = "observation_construction"

    def __init__(
        self,
        category: str,
        dependency: str,
        reason: str,
        prepared_inputs: object,
        trade_date: date | None = None,
        near_slot: Slot | None = None,
        far_slot: Slot | None = None,
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.dependency = dependency
        self.reason = reason
        self.prepared_inputs = prepared_inputs
        self.trade_date = trade_date
        self.near_slot = near_slot
        self.far_slot = far_slot
