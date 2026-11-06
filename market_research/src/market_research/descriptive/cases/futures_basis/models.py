"""Immutable price-free Slot resolution inputs, outputs and diagnostics."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

Slot = Literal["M0", "M1", "Q1", "Q2"]
SLOTS: tuple[Slot, ...] = ("M0", "M1", "Q1", "Q2")


@dataclass(frozen=True, slots=True)
class ContractMetadata:
    contract_code: str
    product_code: str
    underlying_index_code: str
    delivery_month: str
    list_date: date
    delist_date: date


@dataclass(frozen=True, slots=True)
class DailyUniverseEvidence:
    product_code: str
    trade_date: date
    complete: bool
    active_contract_codes: tuple[str, ...]
    source_export_ref: str


@dataclass(frozen=True, slots=True)
class SlotMapping:
    slot: Slot
    contract: ContractMetadata | None
    evidence: DailyUniverseEvidence
    status: Literal["resolved", "not_applicable"]
    reason: Literal["no_active_contract"] | None

    @property
    def contract_code(self) -> str | None:
        return self.contract.contract_code if self.contract is not None else None


@dataclass(frozen=True, slots=True)
class DailySlotResolution:
    product_code: str
    trade_date: date
    mappings: tuple[SlotMapping, ...]
    evidence: DailyUniverseEvidence


@dataclass(frozen=True, slots=True)
class CandidateSessions:
    dates: tuple[date, ...]
    calendar_export_ref: str


@dataclass(frozen=True, slots=True)
class ContractTransition:
    product_code: str
    slot: Slot
    previous_date: date
    trade_date: date
    previous_contract_code: str
    contract_code: str
    previous_metadata: ContractMetadata
    metadata: ContractMetadata
    previous_evidence: DailyUniverseEvidence
    evidence: DailyUniverseEvidence


@dataclass(frozen=True, slots=True)
class AbsenceBoundary:
    product_code: str
    slot: Slot
    previous_date: date
    trade_date: date
    kind: Literal["appeared", "disappeared"]
    previous_resolution: SlotMapping
    resolution: SlotMapping


@dataclass(frozen=True, slots=True)
class TransitionResult:
    product_code: str
    candidate_sessions: CandidateSessions
    transitions: tuple[ContractTransition, ...]
    absence_boundaries: tuple[AbsenceBoundary, ...]


class SlotResolutionError(Exception):
    """Explicit failure retaining the supplied identity and evidence for diagnosis."""

    def __init__(
        self,
        category: str,
        product_code: object,
        trade_date: object,
        reason: str,
        metadata: object,
        evidence: object,
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.product_code = product_code
        self.trade_date = trade_date
        self.reason = reason
        self.metadata = metadata
        self.evidence = evidence
