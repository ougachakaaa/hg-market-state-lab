"""Dataset targets, canonical facts, completeness and business export policies."""

import json
import math
import re
from collections.abc import Callable, Sequence
from dataclasses import fields
from datetime import date
from typing import Any, NoReturn, cast

from data_lake import CoverageResult
from data_lake.domain import CachedUnit, ExecutionFailure, Instrument, Record, Unit, UnitRecords

from ._models import DailyWindow, IndexDailyExport, IndexDailyRange, IndexDailyRow, IndexDailyScope


def fail(reason: str) -> NoReturn:
    raise ExecutionFailure(reason, "completeness")


def text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        fail("Invalid required text fact")
    return value


def absent(value: object) -> bool:
    return value is None or value == "" or (type(value) is float and math.isnan(value))


def day(value: object, nullable: bool = False) -> str | None:
    if nullable and absent(value):
        return None
    value = text(value)
    if not re.fullmatch(r"[0-9]{8}", value):
        fail("Invalid Source date")
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:])).isoformat()
    except ValueError:
        return fail("Invalid Source date")


def _parse_number(
    value: object, *, nullable: bool = False, positive: bool = False, nonnegative: bool = False
) -> float | None:
    if nullable and absent(value):
        return None
    if isinstance(value, bool) or value is None:
        fail("Missing required numeric fact")
    try:
        result = float(cast(Any, value))
    except (ValueError, TypeError, OverflowError):
        return fail("Invalid numeric fact")
    if not math.isfinite(result) or (positive and result <= 0) or (nonnegative and result < 0):
        fail("Invalid numeric fact")
    return result


def number(
    value: object,
    *,
    nullable: bool = False,
    positive: bool = False,
    nonnegative: bool = False,
    field: str | None = None,
    context: str = "",
) -> float | None:
    try:
        return _parse_number(value, nullable=nullable, positive=positive, nonnegative=nonnegative)
    except ExecutionFailure as exc:
        if field is None:
            raise
        raise ExecutionFailure(f"{exc.reason}; field={field} {context}", exc.code) from None


def identity(unit: Unit) -> tuple[str, date]:
    code, target = cast(tuple[str, date], unit.identity)
    return code, target


def instrument(metadata: dict[str, Any]) -> Instrument:
    code = text(metadata.get("contract_code", metadata.get("index_code")))
    return Instrument(
        code,
        code,
        "source",
        metadata["symbol"],
        metadata.get("exchange"),
        metadata["name"],
        metadata.get("list_date"),
        metadata.get("delist_date"),
    )


STRINGS = ["index_code", "symbol", "name", "market"]


OPTIONAL_STRINGS = ["publisher", "category"]


DATES = ["trade_date"]


OPTIONAL_DATES: list[str] = []


NUMBERS = ["open", "high", "low", "close", "pre_close", "change", "pct_change", "volume", "amount"]


OPTIONAL_NUMBERS: list[str] = []


CANONICAL_FIELDS = frozenset(field.name for field in fields(IndexDailyRow))


def read_row(record: Record) -> IndexDailyRow:
    data: dict[str, Any] = dict(record.fields)
    if set(data) != CANONICAL_FIELDS:
        fail("Canonical fields are incompatible")
    for key in STRINGS:
        text(data[key])
    for key in OPTIONAL_STRINGS:
        if data[key] is not None:
            text(data[key])
    for key in DATES + OPTIONAL_DATES:
        value = data[key]
        if value is None and key in OPTIONAL_DATES:
            continue
        if not isinstance(value, str):
            fail("Invalid canonical date")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            fail("Invalid canonical date")
        if parsed.isoformat() != value:
            fail("Invalid canonical date")
        data[key] = parsed
    for key in NUMBERS + OPTIONAL_NUMBERS:
        data[key] = number(
            data[key],
            nullable=key in OPTIONAL_NUMBERS,
            positive=key in ("multiplier", "per_unit", "opt_multiplier", "strike"),
            nonnegative=key in ("volume", "amount", "open_interest"),
        )
    return IndexDailyRow(**data)


def metadata(raw: dict[str, Any], code: str) -> dict[str, Any]:
    if raw.get("ts_code") != code:
        fail("Index metadata identity mismatch")
    result: dict[str, Any] = {
        "index_code": code,
        "symbol": code[:6],
        "name": text(raw.get("name")),
        "market": text(raw.get("market")),
    }
    for key in ("publisher", "category"):
        if key not in raw:
            fail("Missing optional metadata field")
        result[key] = None if absent(raw[key]) else text(raw[key])
    if "list_date" not in raw or "exp_date" not in raw:
        fail("Missing lifecycle metadata fields")
    result["published_on"] = day(raw.get("list_date"), nullable=True)
    result["terminated_on"] = day(raw.get("exp_date"), nullable=True)
    return result


def normalize(unit: Unit, raw: object) -> UnitRecords:
    if isinstance(raw, ExecutionFailure):
        raise raw
    if not isinstance(raw, UnitRecords):
        fail("Invalid normalized facts")
    return raw


class CompletenessChecker:
    """Dataset-owned typed rows, retained only during a single export."""

    def __init__(self, *, reuse_rows: bool = False) -> None:
        self.reuse_rows = reuse_rows
        self.rows: dict[int, tuple[Record, IndexDailyRow]] = {}

    def row(self, record: Record) -> IndexDailyRow:
        if not self.reuse_rows:
            return read_row(record)
        cached = self.rows.get(id(record))
        if cached is None:
            cached = record, read_row(record)
            self.rows[id(record)] = cached
        return cached[1]

    def __call__(self, unit: Unit, facts: UnitRecords) -> None:
        check_complete(unit, facts, self.row)


def check_complete(
    unit: Unit,
    facts: UnitRecords,
    reader: Callable[[Record], IndexDailyRow] | None = None,
) -> None:
    code, target = identity(unit)
    if len(facts.records) != 1 or len(facts.instruments) != 1:
        fail("Index unit must own one record and instrument")
    row = (reader or read_row)(facts.records[0])
    if row.index_code != code or row.trade_date != target or row.symbol != code[:6]:
        fail("Canonical index identity mismatch")
    if facts.records[0].instrument_key != code or facts.instruments[0].key != code:
        fail("Index instrument mismatch")
    if not isinstance(facts.basis, dict) or not isinstance(facts.basis.get("metadata"), dict):
        fail("Missing instrument metadata")
    meta = cast(dict[str, Any], facts.basis["metadata"])
    if set(meta) != {
        "index_code",
        "symbol",
        "name",
        "market",
        "publisher",
        "category",
        "published_on",
        "terminated_on",
    }:
        fail("Incomplete cached instrument facts")
    for key in ("index_code", "symbol", "name", "market", "publisher", "category"):
        if facts.records[0].fields[key] != meta.get(key):
            fail("Index metadata mismatch")
    for key in ("published_on", "terminated_on"):
        if meta.get(key) is not None:
            value = meta[key]
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                fail("Invalid canonical instrument date")


DATASET = "tushare_index_daily"


def project(
    request: IndexDailyRange,
    coverage: CoverageResult,
    cached: tuple[CachedUnit, ...],
    reader: Callable[[Record], IndexDailyRow] | None = None,
) -> IndexDailyExport:
    records = tuple((reader or read_row)(record) for item in cached for record in item.records)
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


def targets(request: IndexDailyRange, days: tuple[date, ...]) -> tuple[Unit, ...]:
    """Expand the complete selection over an already fixed prerequisite view."""
    return tuple(Unit((code, target)) for code in request.index_codes for target in days)


def normalize_daily(
    unit: Unit, response: list[dict[str, Any]], meta: dict[str, Any]
) -> UnitRecords:
    code, target = identity(unit)
    matches = []
    for raw in response:
        source_code = text(raw.get("ts_code"))
        if not re.fullmatch(r"[0-9]{6}\.(SH|SZ|CSI)", source_code):
            fail("Unclassifiable index daily identity")
        if source_code != code:
            continue
        source_day = day(raw.get("trade_date"))
        if source_day != target.isoformat():
            continue
        matches.append(raw)
    if len(matches) != 1:
        fail("Index unit requires exactly one daily row")
    raw = matches[0]
    result: dict[str, Any] = {
        key: value for key, value in meta.items() if key not in ("published_on", "terminated_on")
    }
    result["trade_date"] = target.isoformat()
    for key in NUMBERS:
        source = {"pct_change": "pct_chg", "volume": "vol"}.get(key, key)
        result[key] = number(
            raw.get(source),
            nonnegative=key in ("volume", "amount"),
            field=source,
            context=f"index={code} date={target}",
        )
    facts = UnitRecords((Record(result, code),), (instrument(meta),), {"metadata": meta})
    check_complete(unit, facts)
    return facts


def metadata_representatives(keys: tuple[str, ...], codes: Sequence[str]) -> tuple[Unit, ...]:
    """Choose only the latest success per selected code, without trusting its facts."""
    selected = set(codes)
    representatives: dict[str, Unit] = {}
    for key in keys:
        code, target = json.loads(key)
        if code in selected:
            unit = Unit((code, date.fromisoformat(target)))
            previous = representatives.get(code)
            if previous is None or identity(unit)[1] > identity(previous)[1]:
                representatives[code] = unit
    return tuple(representatives.values())


def select_metadata(
    catalog: list[dict[str, Any]], codes: tuple[str, ...]
) -> tuple[dict[str, dict[str, Any]], dict[str, ExecutionFailure]]:
    by_code: dict[str, list[dict[str, Any]]] = {}
    for raw in catalog:
        candidate = raw.get("ts_code")
        if isinstance(candidate, str) and candidate in codes:
            by_code.setdefault(candidate, []).append(raw)
    selected: dict[str, dict[str, Any]] = {}
    errors: dict[str, ExecutionFailure] = {}
    for code in codes:
        try:
            matches = by_code.get(code, [])
            if len(matches) != 1:
                fail("Index requires exactly one legal instrument")
            selected[code] = metadata(matches[0], code)
        except ExecutionFailure as exc:
            errors[code] = exc
    return selected, errors
