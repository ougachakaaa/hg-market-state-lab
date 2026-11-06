"""Immutable case-specific observation grains, source linkage and accounting."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from .inputs import PreparedFuturesBasisInputs
from .models import ContractMetadata, DailySlotResolution, Slot, SlotMapping, TransitionResult

Outcome = Literal["eligible", "unavailable", "excluded", "not_applicable"]
Metric = Literal["base", "basis_value", "basis_ratio", "annualized_basis_ratio"]
SlotDayKey = tuple[str, date, Slot]
OUTCOMES: tuple[Outcome, ...] = ("eligible", "unavailable", "excluded", "not_applicable")
METRICS: tuple[Metric, ...] = ("base", "basis_value", "basis_ratio", "annualized_basis_ratio")


@dataclass(frozen=True, slots=True)
class SourceReference:
    export_ref: str
    identity: tuple[str, date]


@dataclass(frozen=True, slots=True)
class SourceIssue:
    reason: str
    source: SourceReference
    value: float | None


@dataclass(frozen=True, slots=True)
class ObservationOutcome:
    status: Outcome
    value: float | None = None
    unit: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ContractDayObservation:
    product_code: str
    underlying_index_code: str
    trade_date: date
    contract: ContractMetadata
    futures_close: float
    underlying_close: float | None
    days_to_expiry: int
    base: ObservationOutcome
    basis_value: ObservationOutcome
    basis_ratio: ObservationOutcome
    annualized_basis_ratio: ObservationOutcome
    basis_state: Literal["Premium", "Parity", "Discount"] | None
    issues: tuple[SourceIssue, ...]
    futures_source: SourceReference
    underlying_source: SourceReference
    input_fingerprint: str
    definition_version: str

    @property
    def contract_code(self) -> str:
        return self.contract.contract_code

    @property
    def identity(self) -> tuple[str, date]:
        return self.contract_code, self.trade_date


@dataclass(frozen=True, slots=True)
class SlotDayObservation:
    product_code: str
    trade_date: date
    slot: Slot
    resolution: SlotMapping
    observation: ContractDayObservation | None

    @property
    def identity(self) -> SlotDayKey:
        return self.product_code, self.trade_date, self.slot

    @property
    def contract_code(self) -> str | None:
        return self.resolution.contract_code

    def outcome(self, metric: Metric = "base") -> ObservationOutcome:
        if self.observation is not None:
            return getattr(self.observation, metric)
        unit = (
            None
            if metric == "base"
            else "index_points"
            if metric == "basis_value"
            else "decimal_ratio"
        )
        return ObservationOutcome("not_applicable", unit=unit, reason="no_active_contract")


@dataclass(frozen=True, slots=True)
class OutcomeCollection:
    status: Outcome
    identities: tuple[SlotDayKey, ...]
    candidate_ratio: float | None

    @property
    def count(self) -> int:
        return len(self.identities)


@dataclass(frozen=True, slots=True)
class OutcomeAccounting:
    slot: Slot
    metric: Metric
    candidate_count: int
    outcomes: tuple[OutcomeCollection, ...]

    def count(self, status: Outcome) -> int:
        return next(item.count for item in self.outcomes if item.status == status)

    @property
    def eligible_count(self) -> int:
        return self.count("eligible")

    @property
    def unavailable_count(self) -> int:
        return self.count("unavailable")

    @property
    def excluded_count(self) -> int:
        return self.count("excluded")

    @property
    def not_applicable_count(self) -> int:
        return self.count("not_applicable")


@dataclass(frozen=True, slots=True)
class FuturesBasisResult:
    prepared: PreparedFuturesBasisInputs
    contract_days: tuple[ContractDayObservation, ...]
    slot_days: tuple[SlotDayObservation, ...]
    resolutions: tuple[DailySlotResolution, ...]
    transitions: TransitionResult
    accounting: tuple[OutcomeAccounting, ...]


class ObservationConstructionError(Exception):
    stage = "observation_construction"

    def __init__(
        self,
        category: str,
        reason: str,
        prepared: PreparedFuturesBasisInputs,
        identity: tuple[str, date] | None = None,
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.reason = reason
        self.prepared = prepared
        self.identity = identity
