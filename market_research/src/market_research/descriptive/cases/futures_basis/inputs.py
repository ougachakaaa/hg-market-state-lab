"""Case-specific immutable input retention and explicit preparation failures."""

from dataclasses import dataclass
from datetime import date

from data_lake import EnsureResult
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRange
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRange
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange

PROFILE = "futures_basis_inputs_v1"
DEFINITION_VERSION = "futures_basis_definition_v1"
# Consumption of the published Futures FACTS.md mapping, including empty populations.
UNDERLYING = {"IF": "000300.SH", "IH": "000016.SH", "IC": "000905.SH", "IM": "000852.SH"}
PublicRequest = TradeCalendarRange | FuturesDailyRange | IndexDailyRange
PublicExport = TradeCalendarExport | FuturesDailyExport | IndexDailyExport


@dataclass(frozen=True, slots=True)
class FuturesBasisRequest:
    product_code: str
    start_date: date
    end_date: date
    case: str = "futures_basis_v1"


@dataclass(frozen=True, slots=True)
class InputAttempt:
    dependency: str
    request: PublicRequest
    preliminary_export: object = None
    ensure_result: EnsureResult | None = None
    final_export: object = None


@dataclass(frozen=True, slots=True)
class PreparedFuturesBasisInputs:
    request: FuturesBasisRequest
    calendar_cffex: TradeCalendarExport
    calendar_sse: TradeCalendarExport
    futures: FuturesDailyExport
    index: IndexDailyExport
    candidate_dates: tuple[date, ...]
    underlying_sessions: tuple[date, ...]
    attempts: tuple[InputAttempt, ...]
    canonical_bytes: bytes
    input_fingerprint: str
    definition_version: str = DEFINITION_VERSION


class InputPreparationError(Exception):
    """Obtained public evidence remains accessible even when preparation fails."""

    stage = "input_preparation"

    def __init__(
        self,
        category: str,
        dependency: str,
        reason: str,
        evidence: tuple[InputAttempt, ...] = (),
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.dependency = dependency
        self.reason = reason
        self.evidence = evidence
