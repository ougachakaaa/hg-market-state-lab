"""WP3 public-service preparation and the single existing replay/analyzer path."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from data_lake import EnsureResult, InvalidRequestError, OperationError, UnitFailure
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange
from data_lake.datasets.tushare_equity_index_futures import create_service as create_futures_service
from data_lake.datasets.tushare_index_daily import IndexDailyRange
from data_lake.datasets.tushare_index_daily import create_service as create_index_service
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as create_calendar_service

from .application_models import (
    CalendarPublicService,
    Dependency,
    EnsureDiagnostic,
    FuturesPublicService,
    FuturesRollApplicationError,
    FuturesRollExecution,
    FuturesRollReadiness,
    FuturesRollRequest,
    IndexPublicService,
    PreparedFuturesRollInputs,
    PublicInputExports,
    PublicInputRequests,
    validate_futures_roll_request,
)
from .failures import FuturesRollError
from .fingerprint import input_fingerprint
from .input_validation import validate_calendar, validate_futures, validate_index
from .performance import analyze_futures_roll
from .public_inputs import build_replay_input
from .replay import replay_futures_roll

Export = TypeVar("Export")


def _ensure_diagnostic(result: EnsureResult, dependency: Dependency) -> EnsureDiagnostic:
    if not isinstance(result, EnsureResult):
        raise FuturesRollApplicationError(
            "invalid_public_input", "invalid_ensure_result", dependency=dependency
        )
    counters = (
        result.requested_units,
        result.already_successful_units,
        result.attempted_units,
        result.succeeded_units,
        result.failed_units,
        result.records_written,
    )
    if (
        any(type(value) is not int or value < 0 for value in counters)
        or result.succeeded_units + result.failed_units != result.attempted_units
        or result.already_successful_units + result.attempted_units > result.requested_units
        or type(result.complete) is not bool
        or not isinstance(result.failures, tuple)
        or len(result.failures) != result.failed_units
        or any(
            not isinstance(item, UnitFailure) or not isinstance(item.reason, str)
            for item in result.failures
        )
    ):
        raise FuturesRollApplicationError(
            "invalid_public_input", "invalid_ensure_result", dependency=dependency
        )
    return EnsureDiagnostic(dependency, result)


def _acquire(
    read: Callable[[], Export],
    ensure: Callable[[], EnsureResult],
    validate: Callable[[Export], object],
    complete: Callable[[Export], bool],
    dependency: Dependency,
    diagnostics: list[EnsureDiagnostic],
) -> Export:
    """One exact request, at most one ensure, always validate the final snapshot."""
    stage = "export"
    try:
        value = read()
        validate(value)
        if not complete(value):
            stage = "ensure"
            diagnostics.append(_ensure_diagnostic(ensure(), dependency))
            stage = "export"
            value = read()
            validate(value)
        if not complete(value):
            raise FuturesRollApplicationError(
                "incomplete_input", "final_export_incomplete", dependency=dependency
            )
        return value
    except FuturesRollApplicationError as exc:
        raise FuturesRollApplicationError(
            exc.category,
            exc.reason,
            stage=stage,
            dependency=dependency,
            diagnostics=tuple(diagnostics),
        ) from exc
    except (OperationError, InvalidRequestError) as exc:
        raise FuturesRollApplicationError(
            "upstream_operation",
            "operation_unavailable"
            if isinstance(exc, OperationError)
            else "upstream_request_rejected",
            stage=stage,
            dependency=dependency,
            diagnostics=tuple(diagnostics),
        ) from None


class FuturesRollService:
    """Case-owned orchestration; services are public boundaries, never repositories."""

    def __init__(
        self,
        *,
        calendar: CalendarPublicService,
        futures: FuturesPublicService,
        index: IndexPublicService,
    ) -> None:
        self._calendar = calendar
        self._futures = futures
        self._index = index

    def prepare(self, request: FuturesRollRequest) -> PreparedFuturesRollInputs:
        validate_futures_roll_request(request)
        diagnostics: list[EnsureDiagnostic] = []
        calendar_request = TradeCalendarRange("CFFEX", request.start_date, request.end_date)
        calendar = _acquire(
            lambda: self._calendar.export(calendar_request),
            lambda: self._calendar.ensure(calendar_request),
            lambda value: validate_calendar(value, request),
            lambda value: value.coverage.complete,
            "calendar_cffex",
            diagnostics,
        )
        sessions = validate_calendar(calendar, request)
        if len(sessions) < 2:
            raise FuturesRollApplicationError(
                "invalid_case_input",
                "insufficient_sessions",
                dependency="calendar_cffex",
                diagnostics=tuple(diagnostics),
            )
        futures_request = FuturesDailyRange(
            (request.product_code,), request.start_date, request.end_date
        )
        futures = _acquire(
            lambda: self._futures.export(futures_request),
            lambda: self._futures.ensure(futures_request),
            lambda value: validate_futures(value, request, sessions),
            lambda value: value.coverage.complete,
            "futures",
            diagnostics,
        )
        underlying = validate_futures(futures, request, sessions)
        if underlying is None:
            raise FuturesRollApplicationError(
                "invalid_public_input",
                "unknown_underlying",
                dependency="futures",
                diagnostics=tuple(diagnostics),
            )
        index_request = IndexDailyRange((underlying,), request.start_date, request.end_date)
        index = _acquire(
            lambda: self._index.export(index_request),
            lambda: self._index.ensure(index_request),
            lambda value: validate_index(value, request, sessions, underlying),
            lambda value: value.coverage.complete,
            "index",
            diagnostics,
        )
        exports = PublicInputExports(calendar, futures, index)
        fingerprint = input_fingerprint(exports)
        return PreparedFuturesRollInputs(
            request,
            build_replay_input(request, exports, fingerprint),
            exports,
            PublicInputRequests(calendar_request, futures_request, index_request),
            tuple(diagnostics),
            fingerprint,
        )

    def run(self, request: FuturesRollRequest) -> FuturesRollExecution:
        inputs = self.prepare(request)
        stage = "replay"
        try:
            replay = replay_futures_roll(inputs.replay_input)
            stage = "analysis"
            performance = analyze_futures_roll(replay)
        except FuturesRollError as exc:
            raise FuturesRollApplicationError(
                exc.category,
                exc.reason,
                stage=stage,
                diagnostics=inputs.diagnostics,
                trade_date=exc.trade_date,
                contract_code=exc.contract_code,
            ) from None
        return FuturesRollExecution(
            request,
            replay.sessions[0],
            replay.sessions[-1],
            replay,
            performance,
            inputs,
        )

    def preflight(self, request: FuturesRollRequest) -> FuturesRollReadiness:
        # Local import keeps the read-only assessment separate from preparation.
        from .preflight import assess_readiness

        return assess_readiness(request, self._calendar, self._futures, self._index)


def create_futures_roll_service(
    *,
    calendar: CalendarPublicService | None = None,
    futures: FuturesPublicService | None = None,
    index: IndexPublicService | None = None,
) -> FuturesRollService:
    return FuturesRollService(
        calendar=create_calendar_service() if calendar is None else calendar,
        futures=create_futures_service() if futures is None else futures,
        index=create_index_service() if index is None else index,
    )
