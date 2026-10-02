"""Dataset-owned Source normalization and completeness."""

import math
import re
from dataclasses import fields
from datetime import date
from typing import Any, NoReturn, cast

from data_lake._domain import ExecutionFailure, Instrument, Record, Unit, UnitRecords
from data_lake.providers.tushare import Executor
from data_lake.providers.tushare._executor import CancellableExecutor

from ._models import IndexDailyRow


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


def rows(response: Any) -> list[dict[str, Any]]:
    try:
        result = response.to_dict(orient="records")
    except Exception:
        return fail("Source response cannot be partitioned")
    if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
        fail("Source response cannot be partitioned")
    return result


def exhaust(executor: Executor, endpoint: str, **params: object) -> list[dict[str, Any]]:
    # Continue even after a short page. Empty terminal page proves exhaustion;
    # Repeated pages detect non-progress; Dataset reconciliation detects duplicates.
    result: list[dict[str, Any]] = []
    seen: set[object] = set()
    for _ in range(10000):
        page = rows(executor.call(endpoint, offset=len(result), limit=4000, **params))
        if not page:
            return result
        for row in page:
            code = text(row.get("ts_code"))
            key = (code, text(row.get("trade_date"))) if endpoint == "index_daily" else code
            if key in seen:
                fail("Catalog/daily pagination contains duplicate identity or ignored offset")
            seen.add(key)
        result.extend(page)
    return fail("Source exhaustion could not be proven")


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


def read_row(record: Record) -> IndexDailyRow:
    data: dict[str, Any] = dict(record.fields)
    if set(data) != {field.name for field in fields(IndexDailyRow)}:
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


BASIC_FIELDS = "ts_code,name,market,publisher,category,list_date,exp_date"
DAILY_FIELDS = "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"


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


class DailySource:
    def __init__(self, executor: Executor, cached: dict[str, dict[str, Any]]) -> None:
        self.executor = CancellableExecutor(executor)
        self.metadata = cached
        self.errors: dict[str, ExecutionFailure] = {}

    def cancel(self) -> None:
        self.executor.cancel()

    def _load_metadata(self, code: str) -> None:
        if code in self.errors:
            raise self.errors[code]
        if code not in self.metadata:
            try:
                catalog = []
                # A Source suffix is not a market identifier: .SH indices may
                # be published by CSI. Query relevant markets explicitly.
                for market in ("SSE", "SZSE", "CSI", "CICC", "OTH", "MSCI", "SW"):
                    catalog.extend(
                        exhaust(
                            self.executor,
                            "index_basic",
                            market=market,
                            ts_code=code,
                            fields=BASIC_FIELDS,
                        )
                    )
                matches = [raw for raw in catalog if raw.get("ts_code") == code]
                if len(matches) != 1:
                    fail("Index requires exactly one legal instrument")
                self.metadata[code] = metadata(matches[0], code)
            except ExecutionFailure as exc:
                self.errors[code] = exc
                raise

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        code, first = identity(units[0])
        self._load_metadata(code)
        last = identity(units[-1])[1]
        response = exhaust(
            self.executor,
            "index_daily",
            ts_code=code,
            start_date=first.strftime("%Y%m%d"),
            end_date=last.strftime("%Y%m%d"),
            fields=DAILY_FIELDS,
        )
        by_day: dict[str, list[dict[str, Any]]] = {}
        for raw in response:
            target = day(raw.get("trade_date"))
            assert isinstance(target, str)
            by_day.setdefault(target, []).append(raw)
        result: dict[str, object] = {}
        for unit in units:
            try:
                result[unit.key] = self._fetch_unit(
                    (unit,), by_day.get(identity(unit)[1].isoformat(), [])
                )[unit.key]
            except ExecutionFailure as exc:
                result[unit.key] = exc
        return result

    def _fetch_unit(
        self, units: tuple[Unit, ...], response: list[dict[str, Any]]
    ) -> dict[str, object]:
        code, target = identity(units[0])
        meta = self.metadata[code]
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
            key: value
            for key, value in meta.items()
            if key not in ("published_on", "terminated_on")
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
        check_complete(units[0], facts)
        return {units[0].key: facts}


def normalize(unit: Unit, raw: object) -> UnitRecords:
    if isinstance(raw, ExecutionFailure):
        raise raw
    if not isinstance(raw, UnitRecords):
        fail("Invalid normalized facts")
    return raw


def check_complete(unit: Unit, facts: UnitRecords) -> None:
    code, target = identity(unit)
    if len(facts.records) != 1 or len(facts.instruments) != 1:
        fail("Index unit must own one record and instrument")
    row = read_row(facts.records[0])
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
