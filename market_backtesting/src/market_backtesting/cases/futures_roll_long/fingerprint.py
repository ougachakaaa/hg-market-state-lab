"""The case-specific futures_roll_long_inputs_v1 canonical encoding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Any, cast

from data_lake import CoverageResult, ExportEnvelope
from data_lake.datasets.tushare_equity_index_futures import FuturesDailyExport, FuturesDailyRow
from data_lake.datasets.tushare_index_daily import IndexDailyExport, IndexDailyRow
from data_lake.datasets.tushare_trade_calendar import TradeCalendarExport, TradeCalendarRecord

from .application_models import PublicInputExports
from .failures import FuturesRollError
from .input_validation import (
    CALENDAR_FIELDS,
    COVERAGE_FIELDS,
    FUTURES_FIELDS,
    FUTURES_FLOATS,
    INDEX_FIELDS,
    INDEX_FLOATS,
)


def _fields(
    value: object, names: tuple[str, ...], floats: tuple[str, ...] = ()
) -> dict[str, object]:
    result: dict[str, object] = {}
    for name in names:
        item = getattr(value, name)
        if item is not None and name in floats:
            result[name] = ["float64", float(item).hex()]
        elif type(item) is date:
            result[name] = item.isoformat()
        else:
            result[name] = item
    return result


def _header(export: ExportEnvelope, scope_field: str) -> dict[str, object]:
    return {
        "dataset": export.dataset,
        "view": export.view,
        "export_schema_version": export.export_schema_version,
        "scope": _fields(export.scope, (scope_field,)),
        "window": _fields(export.window, ("start_date", "end_date")),
        "coverage": _fields(export.coverage, COVERAGE_FIELDS),
    }


def canonical_input_bytes(exports: PublicInputExports) -> bytes:
    """Internal encoding of already fully validated, complete retained exports."""
    calendar = _header(exports.calendar_cffex, "exchange")
    calendar["records"] = [_fields(row, CALENDAR_FIELDS) for row in exports.calendar_cffex.records]
    futures = _header(exports.futures, "product_codes")
    futures["records"] = [
        _fields(row, FUTURES_FIELDS, FUTURES_FLOATS) for row in exports.futures.records
    ]
    index = _header(exports.index, "index_codes")
    index["records"] = [_fields(row, INDEX_FIELDS, INDEX_FLOATS) for row in exports.index.records]
    return json.dumps(
        {
            "profile": "futures_roll_long_inputs_v1",
            "calendar_cffex": calendar,
            "futures": futures,
            "index": index,
        },
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def input_fingerprint(exports: PublicInputExports) -> str:
    return hashlib.sha256(canonical_input_bytes(exports)).hexdigest()


# These immutable shapes implement documented public envelope fields; they do not
# import Dataset-private scope/window classes.


@dataclass(frozen=True, slots=True)
class _CalendarScope:
    exchange: str


@dataclass(frozen=True, slots=True)
class _FuturesScope:
    product_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _IndexScope:
    index_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Window:
    start_date: date
    end_date: date


def evidence_error() -> Any:
    raise FuturesRollError("invalid_evidence", "malformed_evidence")


def strict_json(payload: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                evidence_error()
            result[key] = value
        return result

    try:
        if type(payload) is not bytes:
            evidence_error()
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=lambda _: evidence_error(),
        )
    except (ValueError, UnicodeError, TypeError, OverflowError):
        return evidence_error()


def exact_object(value: Any, names: tuple[str, ...]) -> Any:
    if type(value) is not dict or set(value) != set(names):
        evidence_error()
    return value


def decode_date(value: Any) -> date:
    if type(value) is not str:
        evidence_error()
    try:
        day = date.fromisoformat(value)
        if day.isoformat() != value:
            evidence_error()
        return day
    except ValueError:
        return evidence_error()


def _decode_export(value: Any, kind: str) -> Any:
    exact_object(
        value,
        ("dataset", "view", "export_schema_version", "scope", "window", "coverage", "records"),
    )
    scope_field = {"calendar": "exchange", "futures": "product_codes", "index": "index_codes"}[kind]
    scope = exact_object(value["scope"], (scope_field,))[scope_field]
    if kind == "calendar":
        if type(scope) is not str:
            evidence_error()
        scope_value: Any = _CalendarScope(scope)
    else:
        if type(scope) is not list or any(type(s) is not str for s in scope):
            evidence_error()
        scope_value = (
            _FuturesScope(tuple(scope)) if kind == "futures" else _IndexScope(tuple(scope))
        )
    window = exact_object(value["window"], ("start_date", "end_date"))
    coverage = exact_object(value["coverage"], COVERAGE_FIELDS)
    if (
        any(type(coverage[n]) is not int for n in COVERAGE_FIELDS[:-1])
        or type(coverage["complete"]) is not bool
        or type(value["export_schema_version"]) is not int
        or any(type(value[n]) is not str for n in ("dataset", "view"))
    ):
        evidence_error()
    names, floats, dates = {
        "calendar": (CALENDAR_FIELDS, (), ("cal_date", "pretrade_date")),
        "futures": (
            FUTURES_FIELDS,
            FUTURES_FLOATS,
            ("list_date", "delist_date", "last_delivery_date", "trade_date"),
        ),
        "index": (INDEX_FIELDS, INDEX_FLOATS, ("trade_date",)),
    }[kind]
    if type(value["records"]) is not list:
        evidence_error()
    rows = []
    row_type: Any = {
        "calendar": TradeCalendarRecord,
        "futures": FuturesDailyRow,
        "index": IndexDailyRow,
    }[kind]
    for raw in value["records"]:
        row = dict(exact_object(raw, names))
        for name in dates:
            if row[name] is not None:
                row[name] = decode_date(row[name])
        for name in floats:
            number = row[name]
            if number is not None:
                if (
                    type(number) is not list
                    or len(number) != 2
                    or number[0] != "float64"
                    or type(number[1]) is not str
                ):
                    evidence_error()
                try:
                    decoded = float.fromhex(number[1])
                except (ValueError, OverflowError):
                    evidence_error()
                if not isfinite(decoded) or decoded.hex() != number[1]:
                    evidence_error()
                row[name] = decoded
        rows.append(row_type(**row))
    export_type: Any = {
        "calendar": TradeCalendarExport,
        "futures": FuturesDailyExport,
        "index": IndexDailyExport,
    }[kind]
    return export_type(
        value["dataset"],
        value["view"],
        value["export_schema_version"],
        scope_value,
        _Window(decode_date(window["start_date"]), decode_date(window["end_date"])),
        CoverageResult(**coverage),
        tuple(rows),
    )


def decode_canonical_inputs(payload: bytes) -> PublicInputExports:
    """Small inverse of the frozen three-export encoding; semantic checks follow."""
    raw = exact_object(strict_json(payload), ("profile", "calendar_cffex", "futures", "index"))
    if raw["profile"] != "futures_roll_long_inputs_v1":
        evidence_error()
    exports = PublicInputExports(
        _decode_export(raw["calendar_cffex"], "calendar"),
        _decode_export(raw["futures"], "futures"),
        _decode_export(raw["index"], "index"),
    )
    # Check representational field types as well as data; bool and noncanonical floats
    # must not be accepted by equality's Python numeric coercions.
    if canonical_input_bytes(exports) != payload:
        evidence_error()
    return exports


def canonical_calendar_bytes(export: TradeCalendarExport) -> bytes:
    raw = _header(export, "exchange")
    raw["records"] = [_fields(row, CALENDAR_FIELDS) for row in export.records]
    return json.dumps(
        raw, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def decode_calendar_bytes(payload: bytes) -> TradeCalendarExport:
    export = cast(TradeCalendarExport, _decode_export(strict_json(payload), "calendar"))
    if canonical_calendar_bytes(export) != payload:
        evidence_error()
    return export
