"""Dataset-owned composition and public Calendar prerequisite."""

from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError
from data_lake.application import Core
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as calendar_service
from data_lake.ports import Repository, Source

from ._composition import compose, create_repository, prepare_source
from ._domain import targets
from ._models import (
    FuturesDailyExport,
    FuturesDailyRange,
)


def trading_days(calendar: Any, request: FuturesDailyRange, ensure: bool) -> tuple[date, ...]:
    try:
        dependency = TradeCalendarRange("CFFEX", request.start_date, request.end_date)
        view = calendar.export(dependency)
        if not view.coverage.complete and ensure:
            if not calendar.ensure(dependency).complete:
                raise OperationError("Calendar ensure did not complete")
            view = calendar.export(dependency)
        desired = tuple(
            request.start_date + timedelta(days=i)
            for i in range((request.end_date - request.start_date).days + 1)
        )
        if (
            not view.coverage.complete
            or view.dataset != "tushare_trade_calendar"
            or view.view != "calendar"
            or view.scope.exchange != "CFFEX"
            or view.window.start_date != request.start_date
            or view.window.end_date != request.end_date
            or tuple(row.cal_date for row in view.records) != desired
            or view.coverage.requested_units != len(desired)
            or view.coverage.successful_units != len(desired)
            or any(
                (
                    view.coverage.missing_units,
                    view.coverage.pending_units,
                    view.coverage.failed_units,
                )
            )
            or any(
                (
                    row.exchange != "CFFEX"
                    or type(row.is_open) is not int
                    or row.is_open not in (0, 1)
                    or type(row.cal_date) is not date
                    or (row.pretrade_date is not None and type(row.pretrade_date) is not date)
                )
                for row in view.records
            )
        ):
            raise OperationError("Calendar prerequisite view is incomplete or invalid")
        return tuple(row.cal_date for row in view.records if row.is_open == 1)
    except Exception as exc:
        raise OperationError("Calendar prerequisite could not be used") from exc


class FuturesDailyService:
    def __init__(self) -> None:
        self._repository = create_repository()
        self._calendar = calendar_service()
        self._source_factory: Callable[[], Source] = self._prepare

    def _prepare(self) -> Source:
        return prepare_source()

    def _core(
        self,
        request: FuturesDailyRange,
        ensure: bool = False,
        *,
        reuse_rows: bool = False,
    ) -> Core:
        if not isinstance(request, FuturesDailyRange):
            raise InvalidRequestError("request must be a FuturesDailyRange")
        request.__post_init__()
        days = trading_days(self._calendar, request, ensure)
        units = targets(request, days)
        return compose(self._repository, units, self._source_factory, reuse_rows=reuse_rows)

    def coverage(self, request: FuturesDailyRange) -> CoverageResult:
        return self._core(request).coverage(request)

    def ensure(self, request: FuturesDailyRange) -> EnsureResult:
        return self._core(request, True).ensure(request)

    def export(self, request: FuturesDailyRange) -> FuturesDailyExport:
        return self._core(request, reuse_rows=True).export(request)


def _create_service(
    repository: Repository, calendar: Any, source_factory: Callable[[], Source]
) -> FuturesDailyService:
    service = FuturesDailyService.__new__(FuturesDailyService)
    service._repository = repository
    service._calendar = calendar
    service._source_factory = source_factory
    return service


def create_service() -> FuturesDailyService:
    return FuturesDailyService()
