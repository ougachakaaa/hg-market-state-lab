"""Immutable retained public market inputs and preparation failure evidence."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from data_lake import EnsureResult
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRange
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange

CASE: Literal["futures_calendar_spread_v1"] = "futures_calendar_spread_v1"
DEFINITION_VERSION: Literal["futures_calendar_spread_definition_v1"] = (
    "futures_calendar_spread_definition_v1"
)
# Published Futures FACTS.md product/underlying association; no Index prices are acquired.
UNDERLYING = {"IF": "000300.SH", "IH": "000016.SH", "IC": "000905.SH", "IM": "000852.SH"}


@dataclass(frozen=True, slots=True)
class CalendarSpreadRequest:
    product_code: str
    start_date: date
    end_date: date
    case: Literal["futures_calendar_spread_v1"] = CASE


@dataclass(frozen=True, slots=True)
class InputEvidence:
    dependency: Literal["calendar", "futures"]
    request: TradeCalendarRange | FuturesDailyRange
    export: TradeCalendarExport | FuturesDailyExport


@dataclass(frozen=True, slots=True)
class InputPreparationAttempt:
    dependency: Literal["calendar", "futures"]
    request: TradeCalendarRange | FuturesDailyRange
    preliminary_export: TradeCalendarExport | FuturesDailyExport | None = None
    ensure_result: EnsureResult | None = None
    final_export: TradeCalendarExport | FuturesDailyExport | None = None
    reason_code: str | None = None


@dataclass(frozen=True, slots=True)
class PreparedCalendarSpreadInputs:
    request: CalendarSpreadRequest
    calendar_request: TradeCalendarRange
    calendar_export: TradeCalendarExport
    futures_request: FuturesDailyRange
    futures_export: FuturesDailyExport
    candidate_dates: tuple[date, ...]
    definition_version: Literal["futures_calendar_spread_definition_v1"] = DEFINITION_VERSION

    attempts: tuple[InputPreparationAttempt, ...] = ()

    @property
    def evidence(self) -> tuple[InputEvidence, ...]:
        return (
            InputEvidence("calendar", self.calendar_request, self.calendar_export),
            InputEvidence("futures", self.futures_request, self.futures_export),
        )


class InputPreparationError(Exception):
    """Classified failure, retaining only already validated public export evidence."""

    stage = "input_preparation"

    def __init__(
        self,
        category: str,
        dependency: str,
        reason: str,
        evidence: tuple[InputEvidence, ...] = (),
        *,
        reason_code: str | None = None,
        operation: str | None = None,
        attempts: tuple[InputPreparationAttempt, ...] = (),
    ) -> None:
        super().__init__(reason)
        self.category = category
        self.dependency = dependency
        self.reason = reason
        self.evidence = evidence
        self.reason_code = reason_code
        self.operation = operation
        self.attempts = attempts
