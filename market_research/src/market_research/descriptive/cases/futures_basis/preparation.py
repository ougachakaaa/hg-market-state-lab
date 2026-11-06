"""The only market-I/O phase: exact public exports, validated before handoff."""

from dataclasses import replace
from datetime import date, timedelta
from typing import Any, Protocol, cast

from data_lake import EnsureResult, InvalidRequestError, OperationError
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRange
from data_lake.datasets.tushare_equity_index_futures import create_service as create_futures_service
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRange
from data_lake.datasets.tushare_index_daily import create_service as create_index_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from .inputs import (
    UNDERLYING,
    FuturesBasisRequest,
    InputAttempt,
    InputPreparationError,
    PreparedFuturesBasisInputs,
    PublicExport,
    PublicRequest,
)
from .validation import input_identity, require, validate_ensure, validate_export, validate_request


class CalendarService(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...
    def ensure(self, request: TradeCalendarRange) -> EnsureResult: ...


class FuturesService(Protocol):
    def export(self, request: FuturesDailyRange) -> FuturesDailyExport: ...
    def ensure(self, request: FuturesDailyRange) -> EnsureResult: ...


class IndexService(Protocol):
    def export(self, request: IndexDailyRange) -> IndexDailyExport: ...
    def ensure(self, request: IndexDailyRange) -> EnsureResult: ...


def prepare_inputs(
    request: FuturesBasisRequest,
    *,
    calendar_service: CalendarService | None = None,
    futures_service: FuturesService | None = None,
    index_service: IndexService | None = None,
) -> PreparedFuturesBasisInputs:
    attempts: list[InputAttempt] = []
    dependency = "request"
    try:
        validate_request(request)
        calendar = calendar_service if calendar_service is not None else create_calendar_service()
        futures = futures_service if futures_service is not None else create_futures_service()
        index = index_service if index_service is not None else create_index_service()

        def acquire(
            name: str,
            service: Any,
            query: PublicRequest,
            sessions: tuple[date, ...] = (),
            *,
            partial: bool = False,
        ) -> PublicExport:
            nonlocal dependency
            dependency = name
            attempts.append(InputAttempt(name, query))
            raw = service.export(query)
            attempts[-1] = replace(attempts[-1], preliminary_export=raw)
            first = validate_export(raw, query, sessions)
            attempts[-1] = replace(attempts[-1], preliminary_export=first)
            final = first
            if not first.coverage.complete:
                if isinstance(query, TradeCalendarRange):
                    dates = tuple(
                        query.start_date + timedelta(days=i)
                        for i in range((query.end_date - query.start_date).days + 1)
                    )
                    code = query.exchange
                else:
                    dates = sessions
                    code = (
                        query.product_codes[0]
                        if isinstance(query, FuturesDailyRange)
                        else query.index_codes[0]
                    )
                result = service.ensure(query)
                attempts[-1] = replace(attempts[-1], ensure_result=result)
                ensured = validate_ensure(
                    result,
                    {(code, day) for day in dates},
                    calendar=isinstance(query, TradeCalendarRange),
                    index=isinstance(query, IndexDailyRange),
                )
                attempts[-1] = replace(attempts[-1], ensure_result=ensured)
                raw = service.export(query)
                attempts[-1] = replace(attempts[-1], final_export=raw)
                final = validate_export(raw, query, sessions)
            attempts[-1] = replace(attempts[-1], final_export=final)
            require(partial or final.coverage.complete, "Required final Export is incomplete")
            return final

        cffex = cast(
            TradeCalendarExport,
            acquire(
                "calendar_cffex",
                calendar,
                TradeCalendarRange("CFFEX", request.start_date, request.end_date),
            ),
        )
        sse = cast(
            TradeCalendarExport,
            acquire(
                "calendar_sse",
                calendar,
                TradeCalendarRange("SSE", request.start_date, request.end_date),
            ),
        )
        candidates = tuple(row.cal_date for row in cffex.records if row.is_open == 1)
        sessions = tuple(row.cal_date for row in sse.records if row.is_open == 1)
        fut = cast(
            FuturesDailyExport,
            acquire(
                "futures",
                futures,
                FuturesDailyRange((request.product_code,), request.start_date, request.end_date),
                candidates,
            ),
        )
        idx = cast(
            IndexDailyExport,
            acquire(
                "index",
                index,
                IndexDailyRange(
                    (UNDERLYING[request.product_code],), request.start_date, request.end_date
                ),
                sessions,
                partial=True,
            ),
        )
        data, digest = input_identity(cffex, sse, fut, idx)
        return PreparedFuturesBasisInputs(
            request, cffex, sse, fut, idx, candidates, sessions, tuple(attempts), data, digest
        )
    except (ValueError, TypeError, AttributeError, InvalidRequestError, OperationError) as exc:
        category = (
            "invalid_request"
            if dependency == "request"
            else "upstream_operation"
            if isinstance(exc, OperationError)
            else "invalid_public_input"
        )
        raise InputPreparationError(category, dependency, str(exc), tuple(attempts)) from exc
