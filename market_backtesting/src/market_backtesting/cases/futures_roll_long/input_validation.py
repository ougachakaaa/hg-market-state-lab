"""Validate published semantic exports, never reconstruct producer universes."""

from __future__ import annotations

import re
from datetime import date
from math import isfinite
from typing import NoReturn

from data_lake import CoverageResult, ExportEnvelope
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRow
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord

from .application_models import Dependency, FuturesRollApplicationError, FuturesRollRequest

CALENDAR_FIELDS = ("exchange", "cal_date", "is_open", "pretrade_date")
FUTURES_TEXT = (
    "contract_code",
    "product_code",
    "symbol",
    "name",
    "exchange",
    "underlying_index_code",
    "trade_unit",
    "quote_unit",
    "delivery_month",
)
FUTURES_DATES = ("list_date", "delist_date", "last_delivery_date", "trade_date")
FUTURES_FLOATS = (
    "multiplier",
    "per_unit",
    "pre_close",
    "pre_settle",
    "open",
    "high",
    "low",
    "close",
    "settle",
    "close_change_from_pre_settle",
    "settle_change_from_pre_settle",
    "volume",
    "amount",
    "open_interest",
    "open_interest_change",
    "delivery_settlement_price",
)
FUTURES_FIELDS = FUTURES_TEXT + FUTURES_DATES + FUTURES_FLOATS
INDEX_TEXT = ("index_code", "symbol", "name", "market", "publisher", "category")
INDEX_FLOATS = (
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_change",
    "volume",
    "amount",
)
INDEX_FIELDS = INDEX_TEXT + ("trade_date",) + INDEX_FLOATS
COVERAGE_FIELDS = (
    "requested_units",
    "successful_units",
    "missing_units",
    "pending_units",
    "failed_units",
    "complete",
)


def invalid(dependency: Dependency, reason: str) -> NoReturn:
    raise FuturesRollApplicationError("invalid_public_input", reason, dependency=dependency)


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def number(value: object, *, positive: bool = False, nonnegative: bool = False) -> bool:
    if type(value) not in (float, int):
        return False
    try:
        return isfinite(value) and (not positive or value > 0) and (not nonnegative or value >= 0)  # type: ignore[arg-type, operator]
    except OverflowError:
        return False


def envelope(
    export: ExportEnvelope,
    dependency: Dependency,
    request: FuturesRollRequest,
    *,
    underlying: str | None = None,
    requested_units: int | None = None,
) -> CoverageResult:
    """Minimum proof validation also used by advisory preflight."""
    dataset, view, schema, scope_field, scope = {
        "calendar_cffex": ("tushare_trade_calendar", "calendar", 1, "exchange", "CFFEX"),
        "futures": (
            "tushare_equity_index_futures",
            "futures_daily",
            2,
            "product_codes",
            (request.product_code,),
        ),
        "index": ("tushare_index_daily", "index_daily", 1, "index_codes", (underlying,)),
    }[dependency]
    expected_type = {
        "calendar_cffex": TradeCalendarExport,
        "futures": FuturesDailyExport,
        "index": IndexDailyExport,
    }[dependency]
    if not isinstance(export, expected_type):
        invalid(dependency, "invalid_export_type")
    if (
        (export.dataset, export.view) != (dataset, view)
        or type(export.export_schema_version) is not int
        or export.export_schema_version != schema
    ):
        invalid(dependency, "invalid_export_identity")
    if getattr(export.scope, scope_field, None) != scope:
        invalid(dependency, "scope_mismatch")
    start = getattr(export.window, "start_date", None)
    end = getattr(export.window, "end_date", None)
    if (
        type(start) is not date
        or type(end) is not date
        or (start, end) != (request.start_date, request.end_date)
    ):
        invalid(dependency, "window_mismatch")
    coverage = export.coverage
    if not isinstance(coverage, CoverageResult):
        invalid(dependency, "invalid_coverage_type")
    counters = tuple(getattr(coverage, field) for field in COVERAGE_FIELDS[:-1])
    if any(type(value) is not int or value < 0 for value in counters):
        invalid(dependency, "invalid_coverage_counters")
    if (
        sum(counters[1:]) != counters[0]
        or type(coverage.complete) is not bool
        or coverage.complete != (coverage.successful_units == coverage.requested_units)
    ):
        invalid(dependency, "inconsistent_coverage")
    if requested_units is not None and coverage.requested_units != requested_units:
        invalid(dependency, "requested_units_mismatch")
    if not isinstance(getattr(export, "records", None), tuple):
        invalid(dependency, "immutable_records_required")
    return coverage


def validate_calendar(export: TradeCalendarExport, request: FuturesRollRequest) -> tuple[date, ...]:
    dep: Dependency = "calendar_cffex"
    coverage = envelope(
        export, dep, request, requested_units=(request.end_date - request.start_date).days + 1
    )
    previous: date | None = None
    sessions: list[date] = []
    for row in export.records:
        if not isinstance(row, TradeCalendarRecord):
            invalid(dep, "invalid_calendar_record")
        if (
            row.exchange != "CFFEX"
            or type(row.cal_date) is not date
            or not request.start_date <= row.cal_date <= request.end_date
        ):
            invalid(dep, "invalid_calendar_identity")
        if previous is not None and row.cal_date <= previous:
            invalid(dep, "unordered_or_duplicate_calendar")
        if (
            type(row.is_open) is not int
            or row.is_open not in (0, 1)
            or (row.pretrade_date is not None and type(row.pretrade_date) is not date)
        ):
            invalid(dep, "invalid_calendar_fact")
        previous = row.cal_date
        if row.is_open == 1:
            sessions.append(row.cal_date)
    if len(export.records) != coverage.successful_units:
        invalid(dep, "calendar_payload_count_mismatch")
    # Complete, ordered unique, in-window natural-day rows prove the exact date set.
    return tuple(sessions)


def validate_futures(
    export: FuturesDailyExport, request: FuturesRollRequest, sessions: tuple[date, ...]
) -> str | None:
    dep: Dependency = "futures"
    coverage = envelope(export, dep, request, requested_units=len(sessions))
    metadata: dict[str, tuple[object, ...]] = {}
    underlyings: set[str] = set()
    days: set[date] = set()
    previous: tuple[str, date, str] | None = None
    for row in export.records:
        if not isinstance(row, FuturesDailyRow):
            invalid(dep, "invalid_futures_record")
        if any(not text(getattr(row, field)) for field in FUTURES_TEXT):
            invalid(dep, "invalid_futures_text")
        if any(type(getattr(row, field)) is not date for field in FUTURES_DATES):
            invalid(dep, "invalid_futures_date")
        month = row.delivery_month
        if (
            not re.fullmatch(r"[0-9]{6}", month)
            or not 1 <= int(month[:4]) <= 9999
            or not 1 <= int(month[4:]) <= 12
        ):
            invalid(dep, "invalid_delivery_month")
        symbol = request.product_code + month[2:]
        if (
            row.product_code != request.product_code
            or row.exchange != "CFFEX"
            or row.symbol != symbol
            or row.contract_code != symbol + ".CFX"
        ):
            invalid(dep, "invalid_contract_identity")
        if not re.fullmatch(r"[0-9]{6}\.(SH|SZ|CSI)", row.underlying_index_code):
            invalid(dep, "invalid_underlying_identity")
        if row.trade_date not in sessions or not row.list_date <= row.trade_date <= row.delist_date:
            invalid(dep, "invalid_contract_lifecycle")
        if (
            request.start_date <= row.delist_date <= request.end_date
            and row.delist_date not in sessions
        ):
            invalid(dep, "delist_date_not_session")
        for name in FUTURES_FLOATS:
            value = getattr(row, name)
            nullable = name == "delivery_settlement_price" or (
                name in ("pre_close", "open_interest_change") and row.trade_date == row.list_date
            )
            if value is None and nullable:
                continue
            if not number(
                value,
                positive=name in ("close", "multiplier", "per_unit"),
                nonnegative=name in ("volume", "amount", "open_interest"),
            ):
                invalid(dep, "invalid_futures_numeric")
        key = (row.product_code, row.trade_date, row.contract_code)
        if previous is not None and key <= previous:
            invalid(dep, "unordered_or_duplicate_contract_date")
        previous = key
        identity = tuple(
            getattr(row, field)
            for field in FUTURES_TEXT + FUTURES_DATES[:-1] + ("multiplier", "per_unit")
        )
        if row.contract_code in metadata and metadata[row.contract_code] != identity:
            invalid(dep, "conflicting_contract_metadata")
        metadata[row.contract_code] = identity
        underlyings.add(row.underlying_index_code)
        days.add(row.trade_date)
    if len(days) > coverage.successful_units:
        invalid(dep, "futures_payload_count_mismatch")
    if len(underlyings) > 1:
        invalid(dep, "conflicting_underlying")
    return next(iter(underlyings), None)


def validate_index(
    export: IndexDailyExport,
    request: FuturesRollRequest,
    sessions: tuple[date, ...],
    underlying: str,
) -> None:
    dep: Dependency = "index"
    coverage = envelope(export, dep, request, underlying=underlying)
    previous: tuple[str, date] | None = None
    days: set[date] = set()
    metadata: tuple[object, ...] | None = None
    for row in export.records:
        if not isinstance(row, IndexDailyRow):
            invalid(dep, "invalid_index_record")
        if (
            row.index_code != underlying
            or type(row.trade_date) is not date
            or not request.start_date <= row.trade_date <= request.end_date
        ):
            invalid(dep, "invalid_index_identity")
        for name in INDEX_TEXT:
            value = getattr(row, name)
            if value is None and name in ("publisher", "category"):
                continue
            if not text(value):
                invalid(dep, "invalid_index_metadata")
        if row.symbol != underlying.split(".")[0]:
            invalid(dep, "invalid_index_identity")
        identity = tuple(getattr(row, field) for field in INDEX_TEXT)
        if metadata is not None and metadata != identity:
            invalid(dep, "conflicting_index_metadata")
        metadata = identity
        if any(not number(getattr(row, name), positive=name == "close") for name in INDEX_FLOATS):
            invalid(dep, "invalid_index_numeric")
        key = (row.index_code, row.trade_date)
        if previous is not None and key <= previous:
            invalid(dep, "unordered_or_duplicate_index_date")
        previous = key
        days.add(row.trade_date)
    if len(export.records) != coverage.successful_units:
        invalid(dep, "index_payload_count_mismatch")
    if coverage.complete and not set(sessions) <= days:
        invalid(dep, "missing_cffex_index_close")
