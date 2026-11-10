"""Immutable synthetic inputs and real-contract holding timeline carriers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from market_research.descriptive.cases.futures_basis import (
    ContractMetadata,
    DailyUniverseEvidence,
)

ProductCode = Literal["IF", "IH", "IC", "IM"]
PRODUCT_CODES: tuple[ProductCode, ...] = ("IF", "IH", "IC", "IM")

StrategyProfile = Literal["expiry_to_M1_v1", "expiry_to_Q1_v1"]
STRATEGY_PROFILES: tuple[StrategyProfile, ...] = ("expiry_to_M1_v1", "expiry_to_Q1_v1")

# Public Slot vocabulary used only for typed output/evidence. The W1 public facade
# remains the owner of Slot resolution; this alias does not implement it.
Slot = Literal["M0", "M1", "Q1", "Q2"]
SelectionSlot = Literal["M1", "Q1"]

Side = Literal["BUY", "SELL"]
ExecutionReason = Literal["entry", "expiry_close", "expiry_open", "study_end_close"]
RollReason = Literal["expiry"]


@dataclass(frozen=True, slots=True)
class ContractClose:
    """One contract's ideal session Close within a synthetic session fact."""

    contract_code: str
    close: float


@dataclass(frozen=True, slots=True)
class SessionFacts:
    """Required synthetic facts for one ordered CFFEX session."""

    trade_date: date
    closes: tuple[ContractClose, ...]


@dataclass(frozen=True, slots=True)
class DecisionSlotEvidence:
    """One validated decision-session active set and completeness handoff."""

    trade_date: date
    evidence: DailyUniverseEvidence


@dataclass(frozen=True, slots=True)
class HoldingSimulationInput:
    """Everything the pure holding simulation may consume."""

    product_code: ProductCode
    sessions: tuple[date, ...]
    contracts: tuple[ContractMetadata, ...]
    session_facts: tuple[SessionFacts, ...]
    decision_slots: tuple[DecisionSlotEvidence, ...]
    strategy_profile: StrategyProfile


@dataclass(frozen=True, slots=True)
class DailyHolding:
    """Session-level identities, not PnL values."""

    trade_date: date
    pnl_contract_code: str
    position_contract_code: str | None


@dataclass(frozen=True, slots=True)
class Execution:
    """One ordered real-contract execution leg."""

    trade_date: date
    side: Side
    contract_code: str
    price: float
    reason: ExecutionReason
    selection_slot: SelectionSlot | None


@dataclass(frozen=True, slots=True)
class RollEvent:
    """One expiry roll: a close leg followed by an open leg."""

    trade_date: date
    old_contract_code: str
    old_slot: Slot
    old_close: float
    new_contract_code: str
    new_slot: SelectionSlot
    new_close: float
    reason: RollReason


@dataclass(frozen=True, slots=True)
class StrategyTimeline:
    """The complete immutable result of one holding simulation."""

    product_code: ProductCode
    strategy_profile: StrategyProfile
    sessions: tuple[date, ...]
    daily: tuple[DailyHolding, ...]
    executions: tuple[Execution, ...]
    rolls: tuple[RollEvent, ...]

    @property
    def entry_execution(self) -> Execution:
        return self.executions[0]

    @property
    def exit_execution(self) -> Execution:
        return self.executions[-1]
