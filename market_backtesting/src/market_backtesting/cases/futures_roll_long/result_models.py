"""Immutable RESULT.md carriers; financial values are projections only."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from .application_models import FuturesRollRequest, PublicInputRequests
from .models import DailyPerformance, ExecutionReason, RollEvent, SelectionSlot, Side
from .visualization import ViewV2

DEFINITION_VERSION = "futures_roll_long_definition_v1"
RESULT_PROFILE = "futures_roll_long_result_v1"
LIMITATIONS = (
    "Ideal session Close execution and valuation; historical executable fills are not guaranteed.",
    "Gross PnL excludes fees and slippage.",
    "No margin, funding or collateral mechanics; no dividends.",
    "One long futures contract (one lot) at a time.",
    "Fixed initial index-equivalent notional.",
    "Simple non-compounded strategy return.",
    "The index price benchmark is not directly tradable.",
    "Cache completeness is not Source freshness.",
    "Historical decision-time metadata and active-set availability are explicit assumptions.",
)


@dataclass(frozen=True, slots=True)
class ObservedWindow:
    first_session: date
    last_session: date
    cffex_session_count: int


@dataclass(frozen=True, slots=True)
class Benchmark:
    index_code: str
    index_name: str
    first_close: float
    last_close: float


@dataclass(frozen=True, slots=True)
class InitialNotional:
    index_first_close: float
    multiplier: float
    currency: Literal["CNY"]
    value: float


@dataclass(frozen=True, slots=True)
class ResultDaily(DailyPerformance):
    position_contract_code: str | None
    pnl_contract_code: str
    previous_close: float | None
    close: float


@dataclass(frozen=True, slots=True)
class Trade:
    trade_date: date
    side: Side
    contract_code: str
    price: float
    multiplier: float
    reason: ExecutionReason
    selection_slot: SelectionSlot | None


@dataclass(frozen=True, slots=True)
class ResultSummary:
    initial_notional: float
    total_pnl: float
    gross_return: float
    benchmark_return: float
    excess_return: float
    strategy_max_drawdown: float
    benchmark_max_drawdown: float
    execution_count: int
    roll_count: int


@dataclass(frozen=True, slots=True)
class CoverageEvidence:
    dependency: str
    requested_units: int
    successful_units: int
    missing_units: int
    pending_units: int
    failed_units: int
    complete: bool


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    dataset: str
    view: str
    export_schema_version: int


@dataclass(frozen=True, slots=True)
class EvidenceSummary:
    input_profile: str
    input_fingerprint: str
    public_requests: PublicInputRequests
    coverage: tuple[CoverageEvidence, ...]
    sources: tuple[SourceIdentity, ...]
    slot_resolution_authority: str
    definition_version: str
    result_profile: str
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResultViews:
    returns: ViewV2
    drawdown: ViewV2


@dataclass(frozen=True, slots=True)
class BacktestResult:
    profile: str
    case: str
    definition_version: str
    status: Literal["complete"]
    request: FuturesRollRequest
    window: ObservedWindow
    benchmark: Benchmark
    initial_notional: InitialNotional
    daily: tuple[ResultDaily, ...]
    trades: tuple[Trade, ...]
    rolls: tuple[RollEvent, ...]
    summary: ResultSummary
    evidence: EvidenceSummary
    views: ResultViews
