"""Dataset targets, canonical facts, completeness and business export policies."""

import math
import re
from collections.abc import Callable
from dataclasses import fields
from datetime import date
from typing import Any, NoReturn, cast

from data_lake import CoverageResult
from data_lake._serialization import Json
from data_lake.domain import CachedUnit, ExecutionFailure, Instrument, Record, Unit, UnitRecords

from ._models import (
    DailyWindow,
    OptionsDailyExport,
    OptionsDailyRange,
    OptionsDailyRow,
    OptionsDailyScope,
)


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


STRINGS = [
    "contract_code",
    "product_code",
    "symbol",
    "name",
    "exchange",
    "source_underlying_code",
    "underlying_index_code",
    "option_type",
    "exercise_type",
    "quote_unit",
    "settlement_month",
    "call_put",
]


OPTIONAL_STRINGS: list[str] = []


DATES = ["list_date", "delist_date", "expiry", "last_exercise_date", "trade_date"]


OPTIONAL_DATES = ["last_delivery_date"]


NUMBERS = [
    "per_unit",
    "opt_multiplier",
    "strike",
    "pre_settle",
    "pre_close",
    "close",
    "settle",
    "volume",
    "amount",
    "open_interest",
]


OPTIONAL_NUMBERS = ["open", "high", "low"]


CANONICAL_FIELDS = frozenset(field.name for field in fields(OptionsDailyRow))


def read_row(record: Record) -> OptionsDailyRow:
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
            nullable=key in OPTIONAL_NUMBERS
            or (key == "pre_close" and data["trade_date"] == data["list_date"]),
            positive=key in ("multiplier", "per_unit", "opt_multiplier", "strike"),
            nonnegative=key in ("volume", "amount", "open_interest"),
        )
    if data["call_put"] not in ("CALL", "PUT"):
        fail("Invalid option leg")
    if (data["volume"] != 0 or data["amount"] != 0) and any(
        data[key] is None for key in ("open", "high", "low")
    ):
        fail("Nullable price requires zero volume and amount")
    return OptionsDailyRow(**data)


UNDERLYING = {"IO": "000300.SH", "HO": "000016.SH", "MO": "000852.SH"}


def metadata_products(raw: dict[str, Any]) -> set[str]:
    candidates = set()
    for key in ("ts_code", "symbol"):
        value = raw.get(key)
        match = re.match(r"^([A-Z]+)", value) if isinstance(value, str) else None
        if match and match[1] in UNDERLYING:
            candidates.add(match[1])
    candidates.update(
        product for product, code in UNDERLYING.items() if raw.get("opt_code") == "OP" + code
    )
    return candidates


def classify_metadata(raw: dict[str, Any]) -> str | None:
    symbol = text(raw.get("symbol"))
    match = re.fullmatch(r"([A-Z]+)[0-9]{2}(0[1-9]|1[0-2])-[CP]-[0-9]+(?:\.[0-9]+)?", symbol)
    if (
        not match
        or raw.get("ts_code") != symbol + ".CFX"
        or raw.get("exchange") != "CFFEX"
        or raw.get("opt_type") != "指数期权"
    ):
        fail("Catalog product identity conflict or unclassifiable metadata")
    product = match[1]
    if metadata_products(raw) - {product}:
        fail("Catalog underlying/product identity conflict")
    if product not in UNDERLYING:
        if not isinstance(raw.get("opt_code"), str) or not re.fullmatch(
            r"OP[0-9]{6}\.(SH|SZ|CSI)", raw["opt_code"]
        ):
            fail("Unclassifiable catalog underlying")
        return None
    return product


def metadata(raw: dict[str, Any]) -> dict[str, Any]:
    symbol = text(raw.get("symbol"))
    match = re.fullmatch(r"([A-Z]+)([0-9]{2})(0[1-9]|1[0-2])-([CP])-([0-9]+(?:\.[0-9]+)?)", symbol)
    if not match or match[1] not in UNDERLYING:
        fail("Invalid option identity")
    product = match[1]
    if raw.get("ts_code") != symbol + ".CFX" or raw.get("exchange") != "CFFEX":
        fail("Contract identity or exchange mismatch")
    month = text(raw.get("s_month"))
    strike = number(raw.get("exercise_price"), positive=True)
    if (
        not re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", month)
        or month[2:] != match[2] + match[3]
        or raw.get("call_put") != match[4]
        or strike != number(match[5], positive=True)
    ):
        fail("Option month/strike/leg conflict")
    underlying = text(raw.get("opt_code"))
    if underlying != "OP" + UNDERLYING[product] or raw.get("opt_type") != "指数期权":
        fail("Option underlying or family conflict")
    result: dict[str, Any] = {
        key: text(raw.get(key))
        for key in ("symbol", "name", "exchange", "exercise_type", "quote_unit")
    }
    result.update(
        contract_code=raw["ts_code"],
        product_code=product,
        source_underlying_code=underlying,
        underlying_index_code=UNDERLYING[product],
        option_type=raw["opt_type"],
        settlement_month=month,
        strike=strike,
        call_put="CALL" if match[4] == "C" else "PUT",
        per_unit=number(raw.get("per_unit"), positive=True),
        opt_multiplier=number(raw.get("opt_multiplier"), positive=True),
        list_date=day(raw.get("list_date")),
        delist_date=day(raw.get("delist_date")),
        expiry=day(raw.get("maturity_date")),
        last_exercise_date=day(raw.get("last_edate")),
    )
    if "last_ddate" not in raw:
        fail("Missing last delivery field")
    result["last_delivery_date"] = day(raw["last_ddate"], nullable=True)
    if result["list_date"] > result["delist_date"]:
        fail("Invalid contract lifecycle")
    return result


def daily(raw: dict[str, Any], meta: dict[str, Any], target: date) -> Record:
    if (
        raw.get("ts_code") != meta["contract_code"]
        or day(raw.get("trade_date")) != target.isoformat()
        or raw.get("exchange") != "CFFEX"
    ):
        fail("Daily identity mismatch")
    result = dict(meta, trade_date=target.isoformat())
    mapping = {"volume": "vol", "open_interest": "oi"}
    for key in ("volume", "amount", "open_interest"):
        result[key] = number(
            raw.get(mapping.get(key, key)),
            nonnegative=True,
            field=key,
            context=f"contract={meta['contract_code']} date={target}",
        )
    zero = result["volume"] == 0 and result["amount"] == 0
    for key in ("pre_settle", "pre_close", "open", "high", "low", "close", "settle"):
        if key not in raw:
            fail(
                f"Missing required daily field; field={key} "
                f"contract={meta['contract_code']} date={target}"
            )
        result[key] = number(
            raw[key],
            nullable=(zero and key in OPTIONAL_NUMBERS)
            or (key == "pre_close" and target.isoformat() == meta["list_date"]),
            field=key,
            context=f"contract={meta['contract_code']} date={target}",
        )
    return Record(result, meta["contract_code"])


class ContractIndex:
    """Exact inclusive lifecycle sweep over an immutable, validated catalog."""

    def __init__(self, catalog: dict[str, dict[str, Any]]) -> None:
        self.catalog = catalog
        self.starts = sorted((meta["list_date"], code) for code, meta in catalog.items())
        self.ends = sorted((meta["delist_date"], code) for code, meta in catalog.items())
        self.active: dict[str, dict[str, Any]] = {}
        self.start = self.end = 0
        self.last = ""

    def at(self, target: date) -> dict[str, dict[str, Any]]:
        day = target.isoformat()
        if day < self.last:
            self.active.clear()
            self.start = self.end = 0
        while self.start < len(self.starts) and self.starts[self.start][0] <= day:
            _, code = self.starts[self.start]
            self.active[code] = self.catalog[code]
            self.start += 1
        while self.end < len(self.ends) and self.ends[self.end][0] < day:
            _, code = self.ends[self.end]
            self.active.pop(code, None)
            self.end += 1
        self.last = day
        return self.active


def normalize(unit: Unit, raw: object) -> UnitRecords:
    if isinstance(raw, ExecutionFailure):
        raise raw
    if not isinstance(raw, UnitRecords):
        fail("Invalid normalized Source facts")
    return raw


def validated_catalog(product: str, basis: object) -> dict[str, dict[str, Any]]:
    if not isinstance(basis, dict) or basis.get("exhausted") is not True:
        fail("Missing complete catalog basis")
    catalog = cast(list[dict[str, Any]], basis.get("catalog"))
    if not isinstance(catalog, list):
        fail("Invalid catalog basis")
    verified_catalog = {}
    seen = set()
    for meta in catalog:
        if not isinstance(meta, dict) or meta.get("product_code") != product:
            fail("Invalid frozen catalog product")
        code = meta["contract_code"]
        if code in seen:
            fail("Duplicate frozen catalog identity")
        seen.add(code)
        # Revalidate preserved metadata through the same canonical mapping.
        verified = metadata(to_provider_metadata(meta))
        if verified != meta:
            fail("Invalid frozen metadata")
        verified_catalog[code] = meta
    return verified_catalog


class CompletenessChecker:
    """Operation-local cache for internal immutable basis objects, retaining identity."""

    def __init__(self, *, reuse_rows: bool = False) -> None:
        self.catalogs: dict[int, tuple[object, str, ContractIndex]] = {}
        self.reuse_rows = reuse_rows
        self.rows: dict[int, tuple[Record, OptionsDailyRow]] = {}

    def row(self, record: Record) -> OptionsDailyRow:
        if not self.reuse_rows:
            return read_row(record)
        cached = self.rows.get(id(record))
        if cached is None:
            cached = record, read_row(record)
            self.rows[id(record)] = cached
        return cached[1]

    def __call__(self, unit: Unit, facts: UnitRecords) -> None:
        product, target = identity(unit)
        key = id(facts.basis)
        cached = self.catalogs.get(key)
        if cached is None:
            catalog = ContractIndex(validated_catalog(product, facts.basis))
            self.catalogs[key] = facts.basis, product, catalog
        else:
            _, cached_product, catalog = cached
            if cached_product != product:
                fail("Frozen catalog product mismatch")
        check_records(unit, facts, catalog.at(target), self.row)


def check_complete(unit: Unit, facts: UnitRecords) -> None:
    CompletenessChecker()(unit, facts)


def check_records(
    unit: Unit,
    facts: UnitRecords,
    expected: dict[str, dict[str, Any]],
    reader: Callable[[Record], OptionsDailyRow] | None = None,
) -> None:
    product, target = identity(unit)
    observed = []
    for record in facts.records:
        row = (reader or read_row)(record)
        if row.product_code != product or row.trade_date != target:
            fail("Record ownership mismatch")
        code = row.contract_code
        if code not in expected or record.instrument_key != code:
            fail("Unexpected canonical contract")
        for key, value in expected[code].items():
            if record.fields.get(key) != value:
                fail("Record metadata conflicts with success basis")
        observed.append(code)
    if len(observed) != len(set(observed)) or set(observed) != set(expected):
        fail("Incomplete product-day contract universe")
    if {item.key for item in facts.instruments} != set(expected):
        fail("Local instrument association is incomplete")


def to_provider_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    raw = dict(meta)
    raw["ts_code"] = meta["contract_code"]
    for key in ("list_date", "delist_date"):
        raw[key] = meta[key].replace("-", "")
    raw.update(
        opt_code=meta["source_underlying_code"],
        opt_type=meta["option_type"],
        s_month=meta["settlement_month"],
        maturity_date=meta["expiry"].replace("-", ""),
        exercise_price=meta["strike"],
        call_put="C" if meta["call_put"] == "CALL" else "P",
        last_edate=meta["last_exercise_date"].replace("-", ""),
        last_ddate=meta["last_delivery_date"].replace("-", "")
        if meta["last_delivery_date"]
        else None,
    )
    return raw


DATASET = "tushare_equity_index_options"


def project(
    request: OptionsDailyRange,
    coverage: CoverageResult,
    cached: tuple[CachedUnit, ...],
    reader: Callable[[Record], OptionsDailyRow] | None = None,
) -> OptionsDailyExport:
    records = tuple((reader or read_row)(record) for item in cached for record in item.records)
    records = tuple(
        sorted(records, key=lambda row: (row.product_code, row.trade_date, row.contract_code))
    )
    return OptionsDailyExport(
        DATASET,
        "options_daily",
        2,
        OptionsDailyScope(tuple(request.product_codes)),
        DailyWindow(request.start_date, request.end_date),
        coverage,
        records,
    )


def targets(request: OptionsDailyRange, days: tuple[date, ...]) -> tuple[Unit, ...]:
    """Expand the complete selection over an already fixed prerequisite view."""
    return tuple(Unit((code, target)) for code in request.product_codes for target in days)


def reconcile_catalog(
    raw_catalog: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, ExecutionFailure]]:
    errors: dict[str, ExecutionFailure] = {}
    catalog: list[dict[str, Any]] = []
    catalog_codes: set[str] = set()
    for raw in raw_catalog:
        candidates = metadata_products(raw)
        try:
            if classify_metadata(raw) is None:
                continue
            normalized = metadata(raw)
            if normalized["contract_code"] in catalog_codes:
                fail("Duplicate catalog contract identity")
            catalog_codes.add(normalized["contract_code"])
            catalog.append(normalized)
        except ExecutionFailure as exc:
            if not candidates:
                raise
            errors.update(dict.fromkeys(candidates, exc))
    return catalog, errors


def freeze_catalog(catalog: list[dict[str, Any]], product: str) -> dict[str, Json]:
    return cast(
        dict[str, Json],
        {
            "catalog": [meta for meta in catalog if meta["product_code"] == product],
            "exhausted": True,
        },
    )


def normalize_daily(
    unit: Unit,
    response: list[dict[str, Any]],
    expected: dict[str, dict[str, Any]],
    frozen: dict[str, Json],
) -> UnitRecords:
    _, target = identity(unit)
    observed: list[Record] = []
    for raw in response:
        code = raw["ts_code"]
        if code not in expected:
            fail("Unexpected active contract")
        observed.append(daily(raw, expected[code], target))
    return UnitRecords(
        tuple(observed), tuple(instrument(meta) for meta in expected.values()), frozen
    )
