"""The only Research responsibility allowed to acquire upstream facts."""

from dataclasses import replace
from datetime import date
from typing import Protocol

from data_lake import EnsureResult, InvalidRequestError, OperationError
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRange
from data_lake.datasets.tushare_index_daily import create_service as create_index_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from ...observation.models import ObservationJobSpec
from .inputs import (
    CalendarInput,
    HistoryInsufficient,
    IncompleteInput,
    IndexInput,
    InputAttempt,
    InputPreparationFailure,
    InputRequest,
    PreparedInputs,
    UpstreamFailure,
    job_identity,
    resolve_calendar,
    validate_calendar,
    validate_ensure,
    validate_index,
    validate_job,
)


class CalendarService(Protocol):
    def export(self, request: TradeCalendarRange) -> TradeCalendarExport: ...
    def ensure(self, request: TradeCalendarRange) -> EnsureResult: ...


class IndexService(Protocol):
    def export(self, request: IndexDailyRange) -> IndexDailyExport: ...
    def ensure(self, request: IndexDailyRange) -> EnsureResult: ...


def prepare_inputs(
    job: ObservationJobSpec,
    *,
    calendar_service: CalendarService | None = None,
    index_service: IndexService | None = None,
) -> PreparedInputs:
    validate_job(job)
    attempts: list[InputAttempt] = []
    slices: list[CalendarInput] = []
    current_request: InputRequest | None = None
    operation = "create Calendar service"
    try:
        calendar = calendar_service if calendar_service is not None else create_calendar_service()

        def calendar_range(request: TradeCalendarRange) -> TradeCalendarExport:
            nonlocal current_request, operation
            current_request = request
            position = len(attempts)
            attempts.append(InputAttempt(request))
            operation = "Calendar export"
            raw = calendar.export(request)
            attempts[position] = replace(attempts[position], preliminary_export=raw)
            view = validate_calendar(raw, request)
            if not view.coverage.complete:
                operation = "Calendar ensure"
                result = calendar.ensure(request)
                attempts[position] = replace(attempts[position], ensure_result=result)
                targets = {
                    ("SSE", date.fromordinal(n))
                    for n in range(request.start_date.toordinal(), request.end_date.toordinal() + 1)
                }
                validate_ensure(result, request, targets)
                operation = "Calendar final export"
                raw = calendar.export(request)
                attempts[position] = replace(attempts[position], final_export=raw)
                view = validate_calendar(raw, request)
            else:
                attempts[position] = replace(attempts[position], final_export=view)
            if not view.coverage.complete:
                raise IncompleteInput(
                    "Final Calendar cannot prove all natural dates", request=request
                )
            slices.append(CalendarInput(request, view))
            return view

        window = job.historical_sample_window
        sample = calendar_range(TradeCalendarRange("SSE", window.start_date, window.end_date))
        anchors = tuple(row.cal_date for row in sample.records if row.is_open == 1)
        if not anchors:
            return PreparedInputs(job_identity(job), tuple(slices), None, tuple(attempts))
        upper = anchors[0].toordinal() - 1
        width = job.horizon
        history: tuple[date, ...] = ()
        while len(history) < job.horizon:
            if upper < 1:
                raise HistoryInsufficient("Fewer than H preceding sessions before date.min")
            lower = max(1, upper - width + 1)
            block = calendar_range(
                TradeCalendarRange("SSE", date.fromordinal(lower), date.fromordinal(upper))
            )
            history = tuple(row.cal_date for row in block.records if row.is_open == 1) + history
            upper = lower - 1
            width *= 2
        _, sessions = resolve_calendar(job, tuple(slices))
        request = IndexDailyRange((job.subject,), sessions[0], anchors[-1])
        current_request = request
        operation = "create Index service"
        index = index_service if index_service is not None else create_index_service()
        position = len(attempts)
        attempts.append(InputAttempt(request))
        operation = "Index export"
        raw_index = index.export(request)
        attempts[position] = replace(attempts[position], preliminary_export=raw_index)
        view_index = validate_index(raw_index, request, sessions)
        if not view_index.coverage.complete:
            operation = "Index ensure"
            result = index.ensure(request)
            attempts[position] = replace(attempts[position], ensure_result=result)
            validate_ensure(result, request, {(job.subject, day) for day in sessions})
            operation = "Index final export"
            raw_index = index.export(request)
            attempts[position] = replace(attempts[position], final_export=raw_index)
            view_index = validate_index(raw_index, request, sessions)
        else:
            attempts[position] = replace(attempts[position], final_export=view_index)
        return PreparedInputs(
            job_identity(job), tuple(slices), IndexInput(request, view_index), tuple(attempts)
        )
    except InputPreparationFailure as exc:
        exc.request = exc.request or current_request
        exc.evidence = tuple(attempts)
        raise
    except (InvalidRequestError, OperationError) as exc:
        raise UpstreamFailure(
            f"{operation}: {type(exc).__name__}: {exc}",
            request=current_request,
            evidence=tuple(attempts),
        ) from exc
