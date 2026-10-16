"""Dataset-owned composition and public Calendar prerequisite."""

from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError
from data_lake.application import Core
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as calendar_service
from data_lake.ports import Repository, Source

from ._composition import compose, create_repository, prepare_source
from ._domain import targets
from ._models import (
    OptionsDailyExport,
    OptionsDailyRange,
)


def _validated_days(view: Any, dependency: TradeCalendarRange) -> tuple[date, ...]:
    """Validate even partial producer views before granting prerequisite writes."""
    coverage = view.coverage
    counts = (
        coverage.requested_units,
        coverage.successful_units,
        coverage.missing_units,
        coverage.pending_units,
        coverage.failed_units,
    )
    if (
        type(view.dataset) is not str
        or view.dataset != "tushare_trade_calendar"
        or type(view.view) is not str
        or view.view != "calendar"
        or type(view.export_schema_version) is not int
        or view.export_schema_version != 1
        or type(view.scope.exchange) is not str
        or view.scope.exchange != dependency.exchange
        or type(view.window.start_date) is not date
        or type(view.window.end_date) is not date
        or view.window.start_date != dependency.start_date
        or view.window.end_date != dependency.end_date
        or any(type(count) is not int or count < 0 for count in counts)
        or type(coverage.complete) is not bool
        or coverage.requested_units != (dependency.end_date - dependency.start_date).days + 1
        or sum(counts[1:]) != coverage.requested_units
        or coverage.complete != (coverage.successful_units == coverage.requested_units)
        or not isinstance(view.records, Sequence)
        or isinstance(view.records, str | bytes | bytearray)
        or len(view.records) != coverage.successful_units
    ):
        raise OperationError("Calendar prerequisite envelope or coverage is invalid")
    previous = None
    days = []
    for row in view.records:
        if (
            type(row.exchange) is not str
            or row.exchange != dependency.exchange
            or type(row.cal_date) is not date
            or not dependency.start_date <= row.cal_date <= dependency.end_date
            or (previous is not None and row.cal_date <= previous)
            or type(row.is_open) is not int
            or row.is_open not in (0, 1)
            or (row.pretrade_date is not None and type(row.pretrade_date) is not date)
        ):
            raise OperationError("Calendar prerequisite facts are invalid")
        previous = row.cal_date
        if row.is_open == 1:
            days.append(row.cal_date)
    return tuple(days)


def trading_days(calendar: Any, request: OptionsDailyRange, ensure: bool) -> tuple[date, ...]:
    try:
        dependency = TradeCalendarRange("CFFEX", request.start_date, request.end_date)
        view = calendar.export(dependency)
        days = _validated_days(view, dependency)
        if not view.coverage.complete and ensure:
            if calendar.ensure(dependency).complete is not True:
                raise OperationError("Calendar ensure did not complete")
            view = calendar.export(dependency)
            days = _validated_days(view, dependency)
        if not view.coverage.complete:
            raise OperationError("Calendar prerequisite view is incomplete")
        return days
    except Exception as exc:
        raise OperationError("Calendar prerequisite could not be used") from exc


class OptionsDailyService:
    def __init__(self) -> None:
        self._repository = create_repository()
        self._calendar = calendar_service()
        self._source_factory: Callable[[], Source] = self._prepare

    def _prepare(self) -> Source:
        return prepare_source()

    def _core(
        self,
        request: OptionsDailyRange,
        ensure: bool = False,
        *,
        reuse_rows: bool = False,
    ) -> Core:
        if not isinstance(request, OptionsDailyRange):
            raise InvalidRequestError("request must be a OptionsDailyRange")
        request.__post_init__()
        days = trading_days(self._calendar, request, ensure)
        units = targets(request, days)
        return compose(self._repository, units, self._source_factory, reuse_rows=reuse_rows)

    def coverage(self, request: OptionsDailyRange) -> CoverageResult:
        return self._core(request).coverage(request)

    def ensure(self, request: OptionsDailyRange) -> EnsureResult:
        return self._core(request, True).ensure(request)

    def export(self, request: OptionsDailyRange) -> OptionsDailyExport:
        return self._core(request, reuse_rows=True).export(request)


def _create_service(
    repository: Repository, calendar: Any, source_factory: Callable[[], Source]
) -> OptionsDailyService:
    service = OptionsDailyService.__new__(OptionsDailyService)
    service._repository = repository
    service._calendar = calendar
    service._source_factory = source_factory
    return service


def create_service() -> OptionsDailyService:
    return OptionsDailyService()
