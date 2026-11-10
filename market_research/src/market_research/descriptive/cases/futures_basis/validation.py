"""Validate and copy the selected public contracts, without upstream operations."""

import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from math import isfinite
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

from data_lake import CoverageResult, EnsureResult, UnitFailure
from data_lake.datasets.tushare_equity_index_futures import (
    FuturesDailyExport,
    FuturesDailyRange,
    FuturesDailyRow,
    FuturesDailyScope,
)
from data_lake.datasets.tushare_index_daily import (
    IndexDailyExport,
    IndexDailyRange,
    IndexDailyRow,
    IndexDailyScope,
)
from data_lake.datasets.tushare_trade_calendar import (
    TradeCalendarExport,
    TradeCalendarRange,
    TradeCalendarRecord,
)

from .inputs import PROFILE, UNDERLYING, FuturesBasisRequest, PublicExport, PublicRequest


@dataclass(frozen=True, slots=True)
class Window:
    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class CalendarScope:
    exchange: str


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


class RequestValidationError(ValueError):
    """Fixed safe L1 feedback; upstream failures never use this type."""

    def __init__(
        self, message: str, param: Literal["product_code", "start_date", "end_date"] | None = None
    ) -> None:
        super().__init__(message)
        self.param = param


def _request_require(
    ok: bool, message: str, param: Literal["product_code", "start_date", "end_date"] | None = None
) -> None:
    if not ok:
        raise RequestValidationError(message, param)


def validate_request(
    request: FuturesBasisRequest, *, check_today: bool = True, today: date | None = None
) -> None:
    _request_require(isinstance(request, FuturesBasisRequest), "Expected FuturesBasisRequest")
    _request_require(
        type(request.case) is str and request.case == "futures_basis_v1", "Invalid case"
    )
    _request_require(
        type(request.product_code) is str and request.product_code in UNDERLYING,
        "请选择合法产品 IM、IC、IF 或 IH。",
        "product_code",
    )
    _request_require(type(request.start_date) is date, "开始日期必须为日期。", "start_date")
    _request_require(type(request.end_date) is date, "结束日期必须为日期。", "end_date")
    _request_require(
        request.start_date <= request.end_date, "结束日期不能早于开始日期。", "end_date"
    )
    if check_today:
        _request_require(
            request.end_date
            <= (today if today is not None else datetime.now(ZoneInfo("Asia/Shanghai")).date()),
            "结束日期不能晚于上海当天。",
            "end_date",
        )


def validate_online_request(request: FuturesBasisRequest, *, today: date | None = None) -> None:
    """Online-only L1; offline observation requests retain their existing bounds."""
    validate_request(request, today=today)
    _request_require(
        (request.end_date - request.start_date).days + 1 <= 1096,
        "在线研究范围最多为 1,096 个自然日（含首尾）。",
        "end_date",
    )


def coverage(raw: Any, expected: int) -> CoverageResult:
    names = (
        "requested_units",
        "successful_units",
        "missing_units",
        "pending_units",
        "failed_units",
    )
    counts = tuple(getattr(raw, name) for name in names)
    require(all(type(n) is int and n >= 0 for n in counts), "Invalid coverage counters")
    require(counts[0] == expected and sum(counts[1:]) == expected, "Coverage accounting mismatch")
    require(
        type(raw.complete) is bool and raw.complete == (counts[1] == expected),
        "Invalid coverage complete",
    )
    return CoverageResult(*cast(Any, (*counts, raw.complete)))


def sequence(raw: Any) -> tuple[Any, ...]:
    require(isinstance(raw, Sequence) and not isinstance(raw, str | bytes), "Expected sequence")
    return tuple(raw)


def text(raw: Any, name: str) -> None:
    require(type(raw) is str and bool(raw.strip()), "Invalid " + name)


def row_copy(raw: Any, row_type: Any) -> Any:
    """Copy every published row field, including legal nullable Source facts."""
    result: dict[str, Any] = {}
    for field in fields(row_type):
        name = field.name
        value = getattr(raw, name)
        if name.endswith("date"):
            nullable = name == "pretrade_date"
            require((nullable and value is None) or type(value) is date, "Invalid " + name)
        elif name == "is_open":
            require(type(value) is int and value in (0, 1), "Invalid is_open")
        elif name in {
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
            "change",
            "pct_change",
        }:
            nullable = name == "delivery_settlement_price" or (
                row_type is FuturesDailyRow
                and name in {"pre_close", "open_interest_change"}
                and raw.trade_date == raw.list_date
            )
            require(
                (nullable and value is None) or (type(value) is float and isfinite(value)),
                "Invalid finite float " + name,
            )
            if value is not None:
                if name in {"volume", "amount", "open_interest"}:
                    require(value >= 0, "Negative " + name)
                if name in {"multiplier", "per_unit"}:
                    require(value > 0, "Nonpositive " + name)
        elif name in {"publisher", "category"} and value is None:
            pass
        else:
            text(value, name)
        result[name] = value
    return row_type(**result)


def validate_export(
    raw: Any, request: PublicRequest, sessions: tuple[date, ...] = ()
) -> PublicExport:
    query = cast(Any, request)
    calendar = isinstance(request, TradeCalendarRange)
    futures = isinstance(request, FuturesDailyRange)
    dataset, view, version = (
        ("tushare_trade_calendar", "calendar", 1)
        if calendar
        else ("tushare_equity_index_futures", "futures_daily", 2)
        if futures
        else ("tushare_index_daily", "index_daily", 1)
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
        "Wrong window",
    )
    if calendar:
        require(
            type(raw.scope.exchange) is str and raw.scope.exchange == query.exchange,
            "Wrong calendar scope",
        )
        scope: Any = CalendarScope(query.exchange)
        expected = (request.end_date - request.start_date).days + 1
        kind: Any = TradeCalendarRecord
    elif futures:
        require(
            sequence(raw.scope.product_codes) == tuple(query.product_codes), "Wrong Futures scope"
        )
        scope = FuturesDailyScope(tuple(query.product_codes))
        expected = len(sessions)
        kind = FuturesDailyRow
    else:
        index_request = cast(IndexDailyRange, request)
        require(
            sequence(raw.scope.index_codes) == tuple(index_request.index_codes), "Wrong Index scope"
        )
        scope = IndexDailyScope(tuple(index_request.index_codes))
        expected = len(sessions)
        kind = IndexDailyRow
    proof = coverage(raw.coverage, expected)
    rows = tuple(row_copy(row, kind) for row in sequence(raw.records))
    if not futures:
        require(len(rows) == proof.successful_units, "Record/success count mismatch")
    previous: tuple[Any, ...] | None = None
    key: tuple[Any, ...]
    units: set[date] = set()
    index_metadata = None
    for row in rows:
        day = row.cal_date if calendar else row.trade_date
        require(request.start_date <= day <= request.end_date, "Record outside window")
        if calendar:
            require(row.exchange == query.exchange, "Wrong row exchange")
            key = (day,)
        else:
            require(day in sessions, "Record outside exchange sessions")
            units.add(day)
            if futures:
                product = query.product_codes[0]
                require(
                    row.product_code == product
                    and row.exchange == "CFFEX"
                    and row.underlying_index_code == UNDERLYING[product],
                    "Wrong Futures binding",
                )
                month = row.delivery_month
                require(
                    re.fullmatch(r"[0-9]{6}", month) is not None
                    and 1 <= int(month[:4]) <= 9999
                    and 1 <= int(month[4:]) <= 12,
                    "Invalid delivery_month",
                )
                require(
                    row.symbol == product + month[2:] and row.contract_code == row.symbol + ".CFX",
                    "Invalid ordinary contract identity",
                )
                require(row.list_date <= day <= row.delist_date, "Invalid active lifecycle")
                key = (row.product_code, day, row.contract_code)
            else:
                code = cast(IndexDailyRange, request).index_codes[0]
                require(row.index_code == code and row.symbol == code[:6], "Wrong Index identity")
                current = (row.symbol, row.name, row.market, row.publisher, row.category)
                require(
                    index_metadata is None or index_metadata == current,
                    "Conflicting Index metadata",
                )
                index_metadata = current
                key = (row.index_code, day)
        require(previous is None or previous < key, "Duplicate or unordered record identity")
        previous = key
    if futures:
        require(len(units) <= proof.successful_units, "More product-days than successes")
        require(proof.successful_units != 0 or not rows, "Rows without successful units")
    window = Window(request.start_date, request.end_date)
    args = (dataset, view, version, scope, window, proof, rows)
    if calendar:
        return TradeCalendarExport(*cast(Any, args))
    if futures:
        return FuturesDailyExport(*cast(Any, args))
    return IndexDailyExport(*cast(Any, args))


def validate_ensure(
    raw: Any, targets: set[tuple[str, date]], *, calendar: bool, index: bool
) -> EnsureResult:
    names = (
        "requested_units",
        "already_successful_units",
        "attempted_units",
        "succeeded_units",
        "failed_units",
        "records_written",
    )
    counts = tuple(getattr(raw, name) for name in names)
    require(all(type(n) is int and n >= 0 for n in counts), "Invalid ensure counters")
    requested, already, attempted, succeeded, failed, written = counts
    require(
        requested == len(targets)
        and already + attempted == requested
        and succeeded + failed == attempted,
        "Ensure accounting mismatch",
    )
    require(
        type(raw.complete) is bool and raw.complete == (already + succeeded == requested),
        "Invalid ensure complete",
    )
    require(succeeded > 0 or written == 0, "Records written without successful attempts")
    if calendar or index:
        require(written == succeeded, "Ensure records_written mismatch")
    failures = []
    identities: set[tuple[str, date]] = set()
    for failure in sequence(raw.failures):
        identity = failure.identity
        require(
            isinstance(identity, tuple)
            and len(identity) == 2
            and type(identity[0]) is str
            and type(identity[1]) is date
            and identity in targets
            and identity not in identities,
            "Invalid UnitFailure identity",
        )
        text(failure.reason, "failure reason")
        identities.add(identity)
        failures.append(UnitFailure(identity, failure.reason))
    require(len(failures) == failed, "Ensure failure count mismatch")
    return EnsureResult(*cast(Any, (*counts, raw.complete, tuple(failures))))


def canonical_value(value: Any) -> Any:
    """The case's published input profile; not a general artifact serializer."""
    if type(value) is date:
        return value.isoformat()
    if type(value) is float:
        require(isfinite(value), "Nonfinite canonical float")
        return ["float64", value.hex()]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: canonical_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {key: canonical_value(item) for key, item in value.items()}
    require(value is None or type(value) in (str, int, bool), "Unsupported canonical field")
    return value


def input_identity(
    cffex: TradeCalendarExport,
    sse: TradeCalendarExport,
    futures: FuturesDailyExport,
    index: IndexDailyExport,
) -> tuple[bytes, str]:
    payload = dict(
        profile=PROFILE, calendar_cffex=cffex, calendar_sse=sse, futures=futures, index=index
    )
    data = json.dumps(
        canonical_value(payload),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return data, hashlib.sha256(data).hexdigest()
