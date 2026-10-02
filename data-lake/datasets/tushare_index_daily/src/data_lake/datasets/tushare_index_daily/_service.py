"""Dataset-owned composition and public Calendar prerequisite."""

import json
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast

from data_lake import CoverageResult, EnsureResult, InvalidRequestError, OperationError
from data_lake._application import Core, Source
from data_lake._domain import CachedUnit, Unit, UnitRecords
from data_lake._repository import Repository
from data_lake._runtime import database_path
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange
from data_lake.datasets.tushare_trade_calendar import create_service as calendar_service
from data_lake.providers.tushare import TushareExecutor

from ._models import DailyWindow, IndexDailyExport, IndexDailyRange, IndexDailyScope
from ._source import DailySource, check_complete, normalize, read_row

DATASET = "tushare_index_daily"


def trading_days(calendar: Any, request: IndexDailyRange, ensure: bool) -> tuple[date, ...]:
    try:
        dependency = TradeCalendarRange("SSE", request.start_date, request.end_date)
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
            or view.scope.exchange != "SSE"
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
                    row.exchange != "SSE"
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


def project(
    request: IndexDailyRange, coverage: CoverageResult, cached: tuple[CachedUnit, ...]
) -> IndexDailyExport:
    records = tuple(read_row(record) for item in cached for record in item.records)
    records = tuple(sorted(records, key=lambda row: (row.index_code, row.trade_date)))
    return IndexDailyExport(
        DATASET,
        "index_daily",
        1,
        IndexDailyScope(tuple(request.index_codes)),
        DailyWindow(request.start_date, request.end_date),
        coverage,
        records,
    )


class IndexDailyService:
    def __init__(self) -> None:
        self._repository = Repository(
            database_path(DATASET, Path(__file__).resolve().parents[4] / "data"), DATASET, "tushare"
        )
        self._calendar = calendar_service()
        self._source_factory: Callable[[], Source] = self._prepare

    def _prepare(self) -> Source:
        cached: dict[str, dict[str, Any]] = {}
        units = tuple(
            Unit((json.loads(key)[0], date.fromisoformat(json.loads(key)[1])))
            for key in self._repository.successful_keys()
        )
        for unit in self._repository.snapshot(units).successful:
            check_complete(unit.unit, UnitRecords(unit.records, unit.instruments, unit.basis))
            cached[cast(tuple[str, date], unit.unit.identity)[0]] = cast(
                dict[str, Any], unit.basis
            )["metadata"]
        return DailySource(TushareExecutor().prepare(), cached)

    def _core(self, request: IndexDailyRange, ensure: bool = False) -> Core:
        if not isinstance(request, IndexDailyRange):
            raise InvalidRequestError("request must be a IndexDailyRange")
        request.__post_init__()
        days = trading_days(self._calendar, request, ensure)
        units = tuple(Unit((code, day)) for code in request.index_codes for day in days)
        return Core(
            self._repository,
            targets=lambda _: units,
            prepare_source=self._source_factory,
            normalize=normalize,
            check_complete=check_complete,
            project=project,
            batches=lambda selected: ((unit,) for unit in selected),
        )

    def coverage(self, request: IndexDailyRange) -> CoverageResult:
        return self._core(request).coverage(request)

    def ensure(self, request: IndexDailyRange) -> EnsureResult:
        return self._core(request, True).ensure(request)

    def export(self, request: IndexDailyRange) -> IndexDailyExport:
        return self._core(request).export(request)


def _create_service(
    repository: Repository, calendar: Any, source_factory: Callable[[], Source]
) -> IndexDailyService:
    service = IndexDailyService.__new__(IndexDailyService)
    service._repository = repository
    service._calendar = calendar
    service._source_factory = source_factory
    return service


def create_service() -> IndexDailyService:
    return IndexDailyService()
