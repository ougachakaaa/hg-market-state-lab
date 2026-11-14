"""Advisory public-cache readiness. Only read-only exports are invoked."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TypeVar

from data_lake import (
    CacheIncompatibleError,
    CoverageResult,
    ExportEnvelope,
    InvalidRequestError,
    OperationError,
)
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange, FuturesDailyRow
from data_lake.datasets.tushare_index_daily import IndexDailyRange
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRange

from .application_models import (
    CalendarPublicService,
    Dependency,
    DependencyReadiness,
    FuturesPublicService,
    FuturesRollApplicationError,
    FuturesRollReadiness,
    FuturesRollRequest,
    IndexPublicService,
    validate_futures_roll_request,
)
from .input_validation import envelope, validate_calendar

View = TypeVar("View", bound=ExportEnvelope)


def _assess(
    read: Callable[[], View],
    validate: Callable[[View], CoverageResult],
    dependency: Dependency,
) -> tuple[DependencyReadiness, View | None]:
    try:
        view = read()
        coverage = validate(view)
    except CacheIncompatibleError:
        return DependencyReadiness(dependency, "unavailable", "cache_incompatible"), None
    except (OperationError, InvalidRequestError, FuturesRollApplicationError):
        return DependencyReadiness(dependency, "unavailable", "public_export_unavailable"), None
    return DependencyReadiness(
        dependency,
        "complete" if coverage.complete else "incomplete",
        "cache_complete" if coverage.complete else "cache_incomplete",
        coverage,
    ), view


def assess_readiness(
    request: FuturesRollRequest,
    calendar: CalendarPublicService,
    futures: FuturesPublicService,
    index: IndexPublicService,
) -> FuturesRollReadiness:
    validate_futures_roll_request(request)
    futures_state = DependencyReadiness("futures", "unknown", "calendar_target_unknown")
    index_state = DependencyReadiness("index", "unknown", "underlying_unknown")
    calendar_request = TradeCalendarRange("CFFEX", request.start_date, request.end_date)

    def calendar_proof(view: TradeCalendarExport) -> CoverageResult:
        # A complete calendar is necessary to determine downstream targets.
        validate_calendar(view, request)
        return view.coverage

    calendar_state, calendar_view = _assess(
        lambda: calendar.export(calendar_request),
        calendar_proof,
        "calendar_cffex",
    )
    if calendar_view is None or calendar_state.state != "complete":
        return FuturesRollReadiness(request, calendar_state, futures_state, index_state)
    sessions = tuple(row.cal_date for row in calendar_view.records if row.is_open == 1)
    futures_request = FuturesDailyRange(
        (request.product_code,), request.start_date, request.end_date
    )
    futures_state, futures_view = _assess(
        lambda: futures.export(futures_request),
        lambda view: envelope(view, "futures", request, requested_units=len(sessions)),
        "futures",
    )
    if futures_view is None or not futures_view.records:
        return FuturesRollReadiness(request, calendar_state, futures_state, index_state)
    # Derive identity only. Price values and Slot structures belong to preparation.
    underlyings: set[str] = set()
    for row in futures_view.records:
        if (
            not isinstance(row, FuturesDailyRow)
            or row.product_code != request.product_code
            or not isinstance(row.underlying_index_code, str)
            or not re.fullmatch(r"[0-9]{6}\.(SH|SZ|CSI)", row.underlying_index_code)
        ):
            return FuturesRollReadiness(request, calendar_state, futures_state, index_state)
        underlyings.add(row.underlying_index_code)
    if len(underlyings) != 1:
        return FuturesRollReadiness(request, calendar_state, futures_state, index_state)
    underlying = next(iter(underlyings))
    index_request = IndexDailyRange((underlying,), request.start_date, request.end_date)
    index_state, _ = _assess(
        lambda: index.export(index_request),
        lambda view: envelope(view, "index", request, underlying=underlying),
        "index",
    )
    return FuturesRollReadiness(request, calendar_state, futures_state, index_state)
