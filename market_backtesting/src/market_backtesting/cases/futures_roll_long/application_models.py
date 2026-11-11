"""Frozen WP3 application values and case-specific public service ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Protocol
from zoneinfo import ZoneInfo

from data_lake import CoverageResult, EnsureResult
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRange
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRange
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange

from .failures import FuturesRollError
from .models import (
    PRODUCT_CODES,
    STRATEGY_PROFILES,
    FuturesRollInput,
    FuturesRollPerformance,
    FuturesRollReplay,
    ProductCode,
    StrategyProfile,
)

Dependency = Literal["calendar_cffex", "calendar_sse", "futures", "index"]
ReadinessState = Literal["complete", "incomplete", "unavailable", "unknown"]


@dataclass(frozen=True, slots=True)
class FuturesRollRequest:
    product_code: ProductCode
    start_date: date
    end_date: date
    strategy_profile: StrategyProfile
    case: Literal["futures_roll_long_v1"] = field(default="futures_roll_long_v1", init=False)

    @property
    def identity(self) -> tuple[str, str, date, date, str]:
        return (self.case, self.product_code, self.start_date, self.end_date, self.strategy_profile)


@dataclass(frozen=True, slots=True)
class EnsureDiagnostic:
    dependency: Dependency
    result: EnsureResult


class FuturesRollApplicationError(FuturesRollError):
    """Safe stage/dependency context; never a partial successful execution."""

    def __init__(
        self,
        category: str,
        reason: str,
        *,
        stage: str = "prepare",
        dependency: Dependency | None = None,
        diagnostics: tuple[EnsureDiagnostic, ...] = (),
        trade_date: date | None = None,
        contract_code: str | None = None,
    ) -> None:
        self.stage = stage
        self.dependency = dependency
        self.diagnostics = diagnostics
        super().__init__(category, reason, trade_date=trade_date, contract_code=contract_code)


def validate_futures_roll_request(request: FuturesRollRequest) -> None:
    """Validate semantic input without consulting any market dependency."""
    reason: str | None = None
    if not isinstance(request, FuturesRollRequest):
        reason = "invalid_request_type"
    elif request.case != "futures_roll_long_v1":
        reason = "invalid_case"
    elif type(request.product_code) is not str or request.product_code not in PRODUCT_CODES:
        reason = "invalid_product_code"
    elif (
        type(request.strategy_profile) is not str
        or request.strategy_profile not in STRATEGY_PROFILES
    ):
        reason = "invalid_strategy_profile"
    elif type(request.start_date) is not date or type(request.end_date) is not date:
        reason = "date_only_required"
    elif request.start_date > request.end_date:
        reason = "inverted_window"
    elif request.end_date > datetime.now(ZoneInfo("Asia/Shanghai")).date():
        reason = "future_window"
    elif (request.end_date - request.start_date).days + 1 > 1096:
        reason = "window_too_large"
    if reason is not None:
        raise FuturesRollApplicationError("invalid_request", reason, stage="request")


class CalendarPublicService(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...
    def ensure(self, request: TradeCalendarRange) -> EnsureResult: ...


class FuturesPublicService(Protocol):
    def export(self, request: FuturesDailyRange) -> FuturesDailyExport: ...
    def ensure(self, request: FuturesDailyRange) -> EnsureResult: ...


class IndexPublicService(Protocol):
    def export(self, request: IndexDailyRange) -> IndexDailyExport: ...
    def ensure(self, request: IndexDailyRange) -> EnsureResult: ...


@dataclass(frozen=True, slots=True)
class PublicInputExports:
    calendar_cffex: TradeCalendarExport
    futures: FuturesDailyExport
    index: IndexDailyExport


@dataclass(frozen=True, slots=True)
class PublicInputRequests:
    calendar_cffex: TradeCalendarRange
    futures: FuturesDailyRange
    index: IndexDailyRange


@dataclass(frozen=True, slots=True)
class PreparedFuturesRollInputs:
    request: FuturesRollRequest
    replay_input: FuturesRollInput
    exports: PublicInputExports
    public_requests: PublicInputRequests
    diagnostics: tuple[EnsureDiagnostic, ...]
    input_fingerprint: str
    index_calendar_request: TradeCalendarRange
    index_calendar_export: TradeCalendarExport
    fingerprint_profile: str = field(default="futures_roll_long_inputs_v1", init=False)
    definition_version: str = field(default="futures_roll_long_v1", init=False)


@dataclass(frozen=True, slots=True)
class FuturesRollExecution:
    request: FuturesRollRequest
    observed_start_date: date
    observed_end_date: date
    replay: FuturesRollReplay
    performance: FuturesRollPerformance
    inputs: PreparedFuturesRollInputs

    @property
    def input_fingerprint(self) -> str:
        return self.inputs.input_fingerprint


@dataclass(frozen=True, slots=True)
class DependencyReadiness:
    dependency: Dependency
    state: ReadinessState
    reason: str
    coverage: CoverageResult | None = None


@dataclass(frozen=True, slots=True)
class FuturesRollReadiness:
    request: FuturesRollRequest
    calendar_cffex: DependencyReadiness
    futures: DependencyReadiness
    index: DependencyReadiness

    @property
    def ready(self) -> bool:
        return all(
            item.state == "complete" for item in (self.calendar_cffex, self.futures, self.index)
        )
