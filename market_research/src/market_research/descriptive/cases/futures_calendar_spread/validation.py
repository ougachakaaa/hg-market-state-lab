"""Case-local validation and lossless immutable copies of the two public exports."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, fields
from datetime import date, datetime
from math import isfinite
from typing import Any, cast
from zoneinfo import ZoneInfo

from data_lake import CoverageResult
from data_lake.datasets.tushare_equity_index_futures import (
    FuturesDailyExport,
    FuturesDailyRow,
    FuturesDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord

from .inputs import CASE, DEFINITION_VERSION, UNDERLYING, CalendarSpreadRequest


class PublicInputError(ValueError):
    """A failed local contract assertion; never an arbitrary service exception."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise PublicInputError(reason)


@dataclass(frozen=True, slots=True)
class _Window:
    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class _CalendarScope:
    exchange: str


def validate_request(request: CalendarSpreadRequest, *, check_today: bool = True) -> None:
    require(type(request) is CalendarSpreadRequest, "Expected CalendarSpreadRequest")
    require(type(request.case) is str and request.case == CASE, "Wrong case identity")
    require(
        type(request.product_code) is str and request.product_code in UNDERLYING,
        "Expected canonical IF/IH/IC/IM",
    )
    require(
        type(request.start_date) is date and type(request.end_date) is date,
        "Expected date-only bounds",
    )
    require(request.start_date <= request.end_date, "Inverted window")
    if check_today:
        require(
            request.end_date <= datetime.now(ZoneInfo("Asia/Shanghai")).date(),
            "Window extends beyond today in Asia/Shanghai",
        )


def _sequence(raw: Any) -> tuple[Any, ...]:
    require(
        isinstance(raw, Sequence) and not isinstance(raw, str | bytes | bytearray),
        "Expected record/selection sequence",
    )
    return tuple(raw)


def _coverage(raw: Any, expected: int) -> CoverageResult:
    counts = tuple(
        getattr(raw, name)
        for name in (
            "requested_units",
            "successful_units",
            "missing_units",
            "pending_units",
            "failed_units",
        )
    )
    require(all(type(n) is int and n >= 0 for n in counts), "Invalid coverage counters")
    require(counts[0] == expected and sum(counts[1:]) == expected, "Wrong coverage accounting")
    require(
        type(raw.complete) is bool and raw.complete == (counts[1] == expected),
        "Wrong coverage complete formula",
    )
    return CoverageResult(*counts, raw.complete)


def _header(
    raw: Any, request: CalendarSpreadRequest, *, calendar: bool, expected: int
) -> CoverageResult:
    dataset, view, version = (
        ("tushare_trade_calendar", "calendar", 1)
        if calendar
        else ("tushare_equity_index_futures", "futures_daily", 2)
    )
    require(type(raw.dataset) is str and raw.dataset == dataset, "Wrong dataset")
    require(type(raw.view) is str and raw.view == view, "Wrong view")
    require(
        type(raw.export_schema_version) is int and raw.export_schema_version == version,
        "Wrong export schema",
    )
    require(
        type(raw.window.start_date) is date
        and type(raw.window.end_date) is date
        and raw.window.start_date == request.start_date
        and raw.window.end_date == request.end_date,
        "Wrong export window",
    )
    if calendar:
        require(
            type(raw.scope.exchange) is str and raw.scope.exchange == "CFFEX",
            "Wrong calendar scope",
        )
    else:
        codes = _sequence(raw.scope.product_codes)
        require(
            all(type(code) is str for code in codes) and codes == (request.product_code,),
            "Wrong Futures scope",
        )
    return _coverage(raw.coverage, expected)


def validate_calendar(raw: Any, request: CalendarSpreadRequest) -> TradeCalendarExport:
    expected = (request.end_date - request.start_date).days + 1
    proof = _header(raw, request, calendar=True, expected=expected)
    records = []
    previous = None
    for row in _sequence(raw.records):
        require(type(row.exchange) is str and row.exchange == "CFFEX", "Wrong row exchange")
        require(
            type(row.cal_date) is date and request.start_date <= row.cal_date <= request.end_date,
            "Calendar date outside window or not date-only",
        )
        require(type(row.is_open) is int and row.is_open in (0, 1), "Invalid is_open")
        require(
            row.pretrade_date is None or type(row.pretrade_date) is date, "Invalid pretrade_date"
        )
        require(previous is None or previous < row.cal_date, "Duplicate/unordered calendar dates")
        previous = row.cal_date
        records.append(
            TradeCalendarRecord(row.exchange, row.cal_date, row.is_open, row.pretrade_date)
        )
    require(len(records) == proof.successful_units, "Calendar row/success count mismatch")
    # Unique ordered in-window records plus the successful count prove every natural date.
    return TradeCalendarExport(
        "tushare_trade_calendar",
        "calendar",
        1,
        cast(Any, _CalendarScope("CFFEX")),
        cast(Any, _Window(request.start_date, request.end_date)),
        proof,
        tuple(records),
    )


def _futures_row(raw: Any) -> FuturesDailyRow:
    values: dict[str, Any] = {}
    text_fields = {
        "contract_code",
        "product_code",
        "symbol",
        "name",
        "exchange",
        "underlying_index_code",
        "trade_unit",
        "quote_unit",
        "delivery_month",
    }
    for field in fields(FuturesDailyRow):
        name = field.name
        value = getattr(raw, name)
        if name.endswith("date"):
            require(type(value) is date, "Expected date-only " + name)
        elif name in text_fields:
            require(type(value) is str and bool(value.strip()), "Invalid text " + name)
        else:
            nullable = name == "delivery_settlement_price" or (
                name in {"pre_close", "open_interest_change"} and raw.trade_date == raw.list_date
            )
            require(
                (nullable and value is None) or (type(value) is float and isfinite(value)),
                "Invalid finite float " + name,
            )
            if value is not None:
                if name in {"multiplier", "per_unit"}:
                    require(value > 0, "Nonpositive " + name)
                if name in {"volume", "amount", "open_interest"}:
                    require(value >= 0, "Negative " + name)
        values[name] = value
    return FuturesDailyRow(**values)


def validate_futures(
    raw: Any, request: CalendarSpreadRequest, sessions: tuple[date, ...]
) -> FuturesDailyExport:
    proof = _header(raw, request, calendar=False, expected=len(sessions))
    records = []
    previous = None
    units: set[date] = set()
    session_set = set(sessions)
    for raw_row in _sequence(raw.records):
        row = _futures_row(raw_row)
        require(row.trade_date in session_set, "Futures row outside candidate sessions")
        require(
            row.product_code == request.product_code
            and row.exchange == "CFFEX"
            and row.underlying_index_code == UNDERLYING[request.product_code],
            "Wrong Futures product/exchange/underlying binding",
        )
        month = row.delivery_month
        require(
            re.fullmatch(r"[0-9]{6}", month) is not None
            and 1 <= int(month[:4]) <= 9999
            and 1 <= int(month[4:]) <= 12,
            "Invalid delivery month",
        )
        require(
            row.symbol == row.product_code + month[2:] and row.contract_code == row.symbol + ".CFX",
            "Wrong ordinary contract identity",
        )
        require(row.list_date <= row.trade_date <= row.delist_date, "Invalid active lifecycle")
        key = (row.product_code, row.trade_date, row.contract_code)
        require(previous is None or previous < key, "Duplicate/unordered Futures records")
        previous = key
        units.add(row.trade_date)
        records.append(row)
    require(len(units) <= proof.successful_units, "Rows exceed successful product-days")
    return FuturesDailyExport(
        "tushare_equity_index_futures",
        "futures_daily",
        2,
        FuturesDailyScope((request.product_code,)),
        _Window(request.start_date, request.end_date),
        proof,
        tuple(records),
    )


def validate_prepared(prepared: Any) -> None:
    # Revalidate without factories, clock reads or public request reconstruction.
    from .inputs import PreparedCalendarSpreadInputs

    require(type(prepared) is PreparedCalendarSpreadInputs, "Expected PreparedCalendarSpreadInputs")
    validate_request(prepared.request, check_today=False)
    request = prepared.request
    require(prepared.definition_version == DEFINITION_VERSION, "Wrong definition version")
    cal_request, fut_request = prepared.calendar_request, prepared.futures_request
    from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRange
    from data_lake.datasets.tushare_trade_calendar import TradeCalendarRange

    require(
        type(cal_request) is TradeCalendarRange
        and cal_request.exchange == "CFFEX"
        and type(cal_request.start_date) is date
        and type(cal_request.end_date) is date
        and cal_request.start_date == request.start_date
        and cal_request.end_date == request.end_date,
        "Calendar request association mismatch",
    )
    require(
        type(fut_request) is FuturesDailyRange
        and type(fut_request.product_codes) is tuple
        and fut_request.product_codes == (request.product_code,)
        and type(fut_request.start_date) is date
        and type(fut_request.end_date) is date
        and fut_request.start_date == request.start_date
        and fut_request.end_date == request.end_date,
        "Futures request association mismatch",
    )
    calendar = validate_calendar(prepared.calendar_export, request)
    sessions = tuple(row.cal_date for row in calendar.records if row.is_open == 1)
    require(
        type(prepared.candidate_dates) is tuple
        and all(type(day) is date for day in prepared.candidate_dates)
        and prepared.candidate_dates == sessions,
        "Candidate date association mismatch",
    )
    futures = validate_futures(prepared.futures_export, request, sessions)
    require(calendar.coverage.complete and futures.coverage.complete, "Incomplete prepared inputs")
    require(
        type(prepared.calendar_export.records) is tuple
        and type(prepared.futures_export.records) is tuple,
        "Mutable prepared records",
    )
    require(
        prepared.calendar_export == calendar and prepared.futures_export == futures,
        "Noncanonical prepared exports",
    )
