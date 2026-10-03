"""Prove Calendar dates and exact product-day facts using read-first exports."""

from dataclasses import fields
from datetime import date, timedelta
from typing import Any

from data_lake.datasets import tushare_equity_index_options as options
from data_lake.datasets import tushare_trade_calendar as calendar

from ._models import CalendarProvenance, CalendarScope, Coverage, Window
from ._upstream import require, require_ensure, validate_coverage, validate_options_export


def ideal_date(expiry: date, target_dte: int) -> date:
    return expiry - timedelta(days=target_dte - 1)


def validate_calendar_context(context: Any, start: date, end: date) -> None:
    require(
        context.dataset == "tushare_trade_calendar"
        and context.view == "calendar"
        and type(context.export_schema_version) is int
        and context.export_schema_version == 1,
        "Invalid Calendar export identity / schema",
    )
    require(context.scope.exchange == "CFFEX", "Wrong Calendar scope")
    window = context.window
    require(
        type(window.start_date) is date
        and type(window.end_date) is date
        and window.start_date == start
        and window.end_date == end,
        "Wrong Calendar window",
    )
    coverage = context.coverage
    validate_coverage(coverage)
    require(coverage.requested_units == (end - start).days + 1, "Wrong Calendar target count")


def _validate_calendar(view: calendar.TradeCalendarExport, start: date, end: date) -> None:
    require(isinstance(view, calendar.TradeCalendarExport), "Invalid Calendar export type")
    validate_calendar_context(view, start, end)
    require(len(view.records) == view.coverage.successful_units, "Wrong Calendar record count")
    dates = []
    for row in view.records:
        require(isinstance(row, calendar.TradeCalendarRecord), "Invalid Calendar public row type")
        require(
            row.exchange == "CFFEX"
            and type(row.cal_date) is date
            and start <= row.cal_date <= end
            and type(row.is_open) is int
            and row.is_open in (0, 1)
            and (row.pretrade_date is None or type(row.pretrade_date) is date),
            "Illegal Calendar record",
        )
        dates.append(row.cal_date)
    require(dates == sorted(set(dates)), "Unordered / duplicate Calendar dates")


def calendar_window(
    service: calendar.TradeCalendarService, start: date, end: date
) -> calendar.TradeCalendarExport:
    request = calendar.TradeCalendarRange("CFFEX", start, end)
    view = service.export(request)
    _validate_calendar(view, start, end)
    if not view.coverage.complete:
        require_ensure(
            service.ensure(request),
            context=(
                f"tushare_trade_calendar exchange=CFFEX start_date={start.isoformat()} "
                f"end_date={end.isoformat()}"
            ),
        )
        view = service.export(request)
        _validate_calendar(view, start, end)
    require(view.coverage.complete is True, "Calendar export incomplete after ensure")
    return view


def candidate_day(
    service: options.OptionsDailyService, product: str, candidate: date
) -> options.OptionsDailyExport:
    request = options.OptionsDailyRange((product,), candidate, candidate)
    view = service.export(request)
    validate_options_export(view, product, candidate, candidate)
    require(view.coverage.requested_units == 1, "Open candidate must have one Options target")
    if not view.coverage.complete:
        require_ensure(
            service.ensure(request),
            context=(
                f"tushare_equity_index_options product_code={product} "
                f"start_date={candidate.isoformat()} end_date={candidate.isoformat()}"
            ),
        )
        view = service.export(request)
        validate_options_export(view, product, candidate, candidate)
    require(
        view.coverage.complete is True
        and view.coverage.requested_units == 1
        and view.coverage.successful_units == 1,
        "Candidate Options export incomplete",
    )
    return view


def calendar_provenance(view: calendar.TradeCalendarExport) -> CalendarProvenance:
    return CalendarProvenance(
        view.dataset,
        view.view,
        view.export_schema_version,
        CalendarScope(view.scope.exchange),
        Window(view.window.start_date, view.window.end_date),
        Coverage(**{field.name: getattr(view.coverage, field.name) for field in fields(Coverage)}),
    )
