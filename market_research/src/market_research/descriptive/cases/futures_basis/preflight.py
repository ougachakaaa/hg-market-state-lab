"""Read-only case-owned assessment; coverage never promises Source availability."""

import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from typing import Literal, Protocol, cast
from zoneinfo import ZoneInfo

from data_lake import CoverageResult, InvalidRequestError, OperationError
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange
from data_lake.datasets.tushare_equity_index_futures import create_service as create_futures_service
from data_lake.datasets.tushare_index_daily import IndexDailyRange
from data_lake.datasets.tushare_index_daily import create_service as create_index_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from .inputs import UNDERLYING, FuturesBasisRequest
from .online import PROFILE
from .validation import coverage, validate_export, validate_online_request

Dependency = Literal["calendar_cffex", "calendar_sse", "futures", "index"]
Scope = Literal["window", "today"]
State = Literal["complete", "needs_fetch", "unknown", "operation_error", "contract_error"]
Reason = Literal[
    "cache_incomplete",
    "prerequisite_incomplete",
    "prerequisite_unavailable",
    "operation_failed",
    "invalid_evidence",
]
logger = logging.getLogger(__name__)


class CalendarReader(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...


class FuturesReader(Protocol):
    def coverage(self, request: FuturesDailyRange) -> CoverageResult: ...


class IndexReader(Protocol):
    def coverage(self, request: IndexDailyRange) -> CoverageResult: ...


@dataclass(frozen=True, slots=True)
class PreflightDependency:
    dependency: Dependency
    scope: Scope
    state: State
    coverage: CoverageResult | None
    reason_code: Reason | None
    message: str


@dataclass(frozen=True, slots=True)
class FuturesBasisPreflight:
    request: dict[str, str]
    checked_at: str
    market_date: date
    submission: Literal["allowed", "confirm_required", "blocked"]
    today_gate: Literal["not_applicable", "ready", "not_ready", "unknown"]
    dependencies: tuple[PreflightDependency, ...]


def preflight_inputs(
    request: FuturesBasisRequest,
    *,
    calendar_service: CalendarReader | None = None,
    futures_service: FuturesReader | None = None,
    index_service: IndexReader | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> FuturesBasisPreflight:
    now = clock()
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Preflight clock must be timezone-aware")
    today = now.astimezone(ZoneInfo("Asia/Shanghai")).date()
    validate_online_request(request, today=today)
    calendar = calendar_service if calendar_service is not None else create_calendar_service()
    futures = futures_service if futures_service is not None else create_futures_service()
    index = index_service if index_service is not None else create_index_service()
    correlation = uuid.uuid4().hex

    def inspect_window(start: date, end: date, scope: Scope) -> list[PreflightDependency]:
        results: list[PreflightDependency] = []
        sessions: dict[str, tuple[date, ...]] = {}

        def inspect(
            dependency: Dependency,
            operation: str,
            read: Callable[[], CoverageResult],
        ) -> PreflightDependency:
            started = time.monotonic()
            proof = None
            exception_type = None
            try:
                proof = read()
                state: State = "complete" if proof.complete else "needs_fetch"
                reason: Reason | None = None if proof.complete else "cache_incomplete"
                message = (
                    "本地数据覆盖完整。"
                    if proof.complete
                    else "本地数据覆盖不完整，正式执行可能需要获取数据。"
                )
            except (OperationError, InvalidRequestError) as exc:
                # A valid Research request rejected downstream is an operation defect,
                # never a user input error or evidence of unavailable market facts.
                state, reason, message = (
                    "operation_error",
                    "operation_failed",
                    "无法完成本地数据检查，请重查或联系维护者。",
                )
                exception_type = type(exc).__name__
            except (ValueError, TypeError, AttributeError) as exc:
                state, reason, message = (
                    "contract_error",
                    "invalid_evidence",
                    "公共数据证据不符合契约，请联系维护者。",
                )
                exception_type = type(exc).__name__
            except Exception as exc:
                exception_type = type(exc).__name__
                raise
            finally:
                logger.info(
                    "futures_basis_preflight_check",
                    extra={
                        "correlation_id": correlation,
                        "dependency": dependency,
                        "scope": scope,
                        "operation": operation,
                        "exception_type": exception_type,
                        "coverage": proof,
                        "duration_seconds": time.monotonic() - started,
                    },
                )
            return PreflightDependency(dependency, scope, state, proof, reason, message)

        for name, exchange in (("calendar_cffex", "CFFEX"), ("calendar_sse", "SSE")):
            query = TradeCalendarRange(exchange, start, end)

            def read_calendar(query: TradeCalendarRange = query) -> CoverageResult:
                exported = cast(TradeCalendarExport, validate_export(calendar.export(query), query))
                if exported.coverage.complete:
                    sessions[query.exchange] = tuple(
                        row.cal_date for row in exported.records if row.is_open == 1
                    )
                return exported.coverage

            dependency: Dependency = (
                "calendar_cffex" if name == "calendar_cffex" else "calendar_sse"
            )
            results.append(inspect(dependency, "export", read_calendar))

        for dependency, exchange, prerequisite in (
            ("futures", "CFFEX", results[0]),
            ("index", "SSE", results[1]),
        ):
            if exchange not in sessions:
                results.append(
                    PreflightDependency(
                        dependency,
                        scope,
                        "unknown",
                        None,
                        "prerequisite_incomplete"
                        if prerequisite.state == "needs_fetch"
                        else "prerequisite_unavailable",
                        "前置交易日历尚未完整就绪，无法确定行情目标。",
                    )
                )
                continue

            def read_market(
                dependency: Dependency = dependency, exchange: str = exchange
            ) -> CoverageResult:
                raw = (
                    futures.coverage(FuturesDailyRange((request.product_code,), start, end))
                    if dependency == "futures"
                    else index.coverage(
                        IndexDailyRange((UNDERLYING[request.product_code],), start, end)
                    )
                )
                return coverage(raw, len(sessions[exchange]))

            results.append(inspect(dependency, "coverage", read_market))
        return results

    dependencies = inspect_window(request.start_date, request.end_date, "window")
    gate: Literal["not_applicable", "ready", "not_ready", "unknown"] = "not_applicable"
    if request.end_date == today:
        daily = (
            [replace(item, scope="today") for item in dependencies]
            if request.start_date == today
            else inspect_window(today, today, "today")
        )
        dependencies.extend(daily)
        gate = (
            "ready"
            if all(item.state == "complete" for item in daily)
            else "unknown"
            if any(item.state in ("unknown", "operation_error", "contract_error") for item in daily)
            else "not_ready"
        )
    submission: Literal["allowed", "confirm_required", "blocked"] = (
        "blocked"
        if gate in ("not_ready", "unknown")
        or any(item.state in ("operation_error", "contract_error") for item in dependencies)
        else "confirm_required"
        if any(item.state != "complete" for item in dependencies)
        else "allowed"
    )
    return FuturesBasisPreflight(
        {
            "case": request.case,
            "product_code": request.product_code,
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "analysis_profile": PROFILE,
        },
        now.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        today,
        submission,
        gate,
        tuple(dependencies),
    )
