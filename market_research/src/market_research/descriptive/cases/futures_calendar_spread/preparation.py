"""Read-only and explicitly authorized preparation through public Dataset services."""

from dataclasses import replace
from datetime import date
from typing import Literal, Protocol, cast

from data_lake import (
    CacheIncompatibleError,
    CredentialMissingError,
    EnsureResult,
    InvalidRequestError,
    OperationError,
)
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRange
from data_lake.datasets.tushare_equity_index_futures import create_service as create_futures_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from .inputs import (
    CalendarSpreadRequest,
    InputEvidence,
    InputPreparationAttempt,
    InputPreparationError,
    PreparedCalendarSpreadInputs,
)
from .validation import (
    PublicInputError,
    validate_calendar,
    validate_ensure,
    validate_futures,
    validate_request,
)


class CalendarService(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...


class FuturesService(Protocol):
    def export(self, request: FuturesDailyRange) -> FuturesDailyExport: ...


class ExecutionCalendarService(CalendarService, Protocol):
    def ensure(self, request: TradeCalendarRange) -> EnsureResult: ...


class ExecutionFuturesService(FuturesService, Protocol):
    def ensure(self, request: FuturesDailyRange) -> EnsureResult: ...


def prepare_inputs(
    product_code: str,
    start_date: date,
    end_date: date,
    *,
    calendar_service: CalendarService | None = None,
    futures_service: FuturesService | None = None,
) -> PreparedCalendarSpreadInputs:
    """Export once per dependency, without Ensure or cache writes."""
    return _prepare(
        product_code, start_date, end_date, calendar_service, futures_service, execution=False
    )


def prepare_inputs_for_execution(
    product_code: str,
    start_date: date,
    end_date: date,
    *,
    calendar_service: ExecutionCalendarService | None = None,
    futures_service: ExecutionFuturesService | None = None,
) -> PreparedCalendarSpreadInputs:
    """Prepare legal missing inputs once per dependency and require final complete proof."""
    return _prepare(
        product_code, start_date, end_date, calendar_service, futures_service, execution=True
    )


def _prepare(
    product_code: str,
    start_date: date,
    end_date: date,
    calendar_service: CalendarService | None,
    futures_service: FuturesService | None,
    *,
    execution: bool,
) -> PreparedCalendarSpreadInputs:
    request = CalendarSpreadRequest(product_code, start_date, end_date)
    try:
        validate_request(request)
        calendar_request = TradeCalendarRange("CFFEX", start_date, end_date)
        futures_request = FuturesDailyRange((product_code,), start_date, end_date)
    except (PublicInputError, InvalidRequestError) as exc:
        raise InputPreparationError("invalid_request", "request", str(exc)) from exc

    evidence: list[InputEvidence] = []
    attempts: list[InputPreparationAttempt] = []
    sessions: tuple[date, ...] = ()
    dependency: Literal["calendar", "futures"] = "calendar"
    operation = "export"

    def fail(category: str, code: str) -> InputPreparationError:
        if execution:
            attempts[-1] = replace(attempts[-1], reason_code=code)
        return InputPreparationError(
            category,
            dependency,
            "Input preparation failed: " + code,
            tuple(evidence),
            reason_code=code,
            operation=operation,
            attempts=tuple(attempts),
        )

    def obtain(dep: Literal["calendar", "futures"]) -> TradeCalendarExport | FuturesDailyExport:
        nonlocal dependency, operation
        dependency, operation = dep, "export"
        public_request = calendar_request if dep == "calendar" else futures_request
        if execution:
            attempts.append(InputPreparationAttempt(dep, public_request))
        # Factory failures are operation failures too; factories remain in dependency order.
        service: CalendarService | FuturesService
        if dep == "calendar":
            service = (
                calendar_service if calendar_service is not None else create_calendar_service()
            )
        else:
            service = futures_service if futures_service is not None else create_futures_service()

        def export() -> TradeCalendarExport | FuturesDailyExport:
            # Catch malformed payloads only around local validation, never service calls.
            raw = (
                cast(CalendarService, service).export(calendar_request)
                if dep == "calendar"
                else cast(FuturesService, service).export(futures_request)
            )
            try:
                return (
                    validate_calendar(raw, request)
                    if dep == "calendar"
                    else validate_futures(raw, request, sessions)
                )
            except (PublicInputError, AttributeError, TypeError) as exc:
                raise fail("input_contract_error", "malformed_export") from exc

        initial = export()
        if execution:
            attempts[-1] = replace(attempts[-1], preliminary_export=initial)
        if execution and not initial.coverage.complete:
            operation = "ensure"
            raw_result = (
                cast(ExecutionCalendarService, service).ensure(calendar_request)
                if dep == "calendar"
                else cast(ExecutionFuturesService, service).ensure(futures_request)
            )
            try:
                result = validate_ensure(raw_result, request, dep, sessions)
            except (PublicInputError, AttributeError, TypeError) as exc:
                raise fail("input_contract_error", "malformed_ensure_result") from exc
            attempts[-1] = replace(attempts[-1], ensure_result=result)
            operation = "final_export"
            final = export()
        else:
            final = initial
        if execution:
            attempts[-1] = replace(attempts[-1], final_export=final)
        evidence.append(InputEvidence(dep, public_request, final))
        if not final.coverage.complete:
            code = "final_export_incomplete" if execution else "cache_incomplete"
            raise fail("incomplete_inputs", code)
        return final

    try:
        cal = cast(TradeCalendarExport, obtain("calendar"))
        sessions = tuple(row.cal_date for row in cal.records if row.is_open == 1)
        fut = cast(FuturesDailyExport, obtain("futures"))
        return PreparedCalendarSpreadInputs(
            request,
            calendar_request,
            cal,
            futures_request,
            fut,
            sessions,
            attempts=tuple(attempts),
        )
    except CredentialMissingError as exc:
        raise fail("upstream_unavailable", "credential_missing") from exc
    except CacheIncompatibleError as exc:
        raise fail("upstream_unavailable", "cache_incompatible") from exc
    except InvalidRequestError as exc:
        raise fail("input_contract_error", "upstream_request_rejected") from exc
    except OperationError as exc:
        raise fail("upstream_unavailable", "operation_unavailable") from exc
