"""Read-only acquisition through the two selected public DataLake services."""

from datetime import date
from typing import Protocol

from data_lake import InvalidRequestError, OperationError
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRange
from data_lake.datasets.tushare_equity_index_futures import create_service as create_futures_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from .inputs import (
    CalendarSpreadRequest,
    InputEvidence,
    InputPreparationError,
    PreparedCalendarSpreadInputs,
)
from .validation import PublicInputError, validate_calendar, validate_futures, validate_request


class CalendarService(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...


class FuturesService(Protocol):
    def export(self, request: FuturesDailyRange) -> FuturesDailyExport: ...


def prepare_inputs(
    product_code: str,
    start_date: date,
    end_date: date,
    *,
    calendar_service: CalendarService | None = None,
    futures_service: FuturesService | None = None,
) -> PreparedCalendarSpreadInputs:
    """Export once per dependency, with no Ensure, retries, fallback or cache writes."""
    request = CalendarSpreadRequest(product_code, start_date, end_date)
    try:
        validate_request(request)
        calendar_request = TradeCalendarRange("CFFEX", start_date, end_date)
        futures_request = FuturesDailyRange((product_code,), start_date, end_date)
    except (PublicInputError, InvalidRequestError) as exc:
        raise InputPreparationError("invalid_request", "request", str(exc)) from exc

    evidence: list[InputEvidence] = []
    dependency = "calendar"
    try:
        calendar = calendar_service if calendar_service is not None else create_calendar_service()
        raw_calendar = calendar.export(calendar_request)
        # Only validation is allowed to classify malformed data; service defects propagate.
        try:
            cal = validate_calendar(raw_calendar, request)
        except (PublicInputError, AttributeError, TypeError) as exc:
            raise InputPreparationError("input_contract_error", dependency, str(exc)) from exc
        evidence.append(InputEvidence("calendar", calendar_request, cal))
        if not cal.coverage.complete:
            raise InputPreparationError("incomplete_inputs", dependency, "Incomplete Calendar")
        sessions = tuple(row.cal_date for row in cal.records if row.is_open == 1)

        dependency = "futures"
        futures = futures_service if futures_service is not None else create_futures_service()
        raw_futures = futures.export(futures_request)
        try:
            fut = validate_futures(raw_futures, request, sessions)
        except (PublicInputError, AttributeError, TypeError) as exc:
            raise InputPreparationError("input_contract_error", dependency, str(exc)) from exc
        evidence.append(InputEvidence("futures", futures_request, fut))
        if not fut.coverage.complete:
            raise InputPreparationError("incomplete_inputs", dependency, "Incomplete Futures")
        return PreparedCalendarSpreadInputs(
            request, calendar_request, cal, futures_request, fut, sessions
        )
    except InputPreparationError as exc:
        exc.evidence = tuple(evidence)
        raise
    except (InvalidRequestError, OperationError) as exc:
        category = (
            "upstream_unavailable" if isinstance(exc, OperationError) else "input_contract_error"
        )
        raise InputPreparationError(category, dependency, str(exc), tuple(evidence)) from exc
