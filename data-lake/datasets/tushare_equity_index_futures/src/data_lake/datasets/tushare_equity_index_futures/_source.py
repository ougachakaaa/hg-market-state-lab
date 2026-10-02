"""Dataset-owned Source normalization and completeness."""

import math
import re
from collections.abc import Callable
from dataclasses import fields
from datetime import date
from typing import Any, NoReturn, cast

from data_lake._domain import ExecutionFailure, Instrument, Record, Unit, UnitRecords
from data_lake._serialization import Json
from data_lake.providers.tushare import Executor
from data_lake.providers.tushare._executor import CancellableExecutor

from ._models import FuturesDailyRow


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
    seen_pages: set[str] = set()
    for _ in range(10000):
        page = rows(executor.call(endpoint, offset=len(result), limit=4000, **params))
        if not page:
            return result
        signature = repr(page)
        if signature in seen_pages:
            fail("Source pagination repeated a page; exhaustion cannot be proven")
        seen_pages.add(signature)
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


STRINGS = [
    "contract_code",
    "product_code",
    "symbol",
    "name",
    "exchange",
    "underlying_index_code",
    "trade_unit",
    "quote_unit",
    "delivery_month",
]
OPTIONAL_STRINGS: list[str] = []
DATES = ["list_date", "delist_date", "last_delivery_date", "trade_date"]
OPTIONAL_DATES: list[str] = []
NUMBERS = [
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
]
OPTIONAL_NUMBERS = ["delivery_settlement_price"]


CANONICAL_FIELDS = frozenset(field.name for field in fields(FuturesDailyRow))


def read_row(record: Record) -> FuturesDailyRow:
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
            or (
                key in ("pre_close", "open_interest_change")
                and data["trade_date"] == data["list_date"]
            ),
            positive=key in ("multiplier", "per_unit", "opt_multiplier", "strike"),
            nonnegative=key in ("volume", "amount", "open_interest"),
        )
    return FuturesDailyRow(**data)


UNDERLYING = {"IF": "000300.SH", "IH": "000016.SH", "IC": "000905.SH", "IM": "000852.SH"}

BASIC_FIELDS = (
    "ts_code,symbol,name,exchange,fut_code,multiplier,trade_unit,per_unit,"
    "quote_unit,list_date,delist_date,d_month,last_ddate"
)
DAILY_FIELDS = (
    "ts_code,trade_date,pre_close,pre_settle,open,high,low,close,settle,change1,"
    "change2,vol,amount,oi,oi_chg,delv_settle"
)


def metadata(raw: dict[str, Any]) -> dict[str, Any]:
    product = text(raw.get("fut_code"))
    symbol = text(raw.get("symbol"))
    match = re.fullmatch(r"([A-Z]+)([0-9]{2})(0[1-9]|1[0-2])", symbol)
    if not match or match[1] != product or product not in UNDERLYING:
        fail("Invalid ordinary futures identity")
    if raw.get("ts_code") != symbol + ".CFX" or raw.get("exchange") != "CFFEX":
        fail("Contract identity or exchange mismatch")
    month = text(raw.get("d_month"))
    if not re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", month) or month[2:] != symbol[len(product) :]:
        fail("Delivery month identity mismatch")
    result: dict[str, Any] = {
        key: text(raw.get(key))
        for key in ("symbol", "name", "exchange", "trade_unit", "quote_unit")
    }
    result.update(
        contract_code=raw["ts_code"],
        product_code=product,
        underlying_index_code=UNDERLYING[product],
        delivery_month=month,
        multiplier=number(raw.get("multiplier"), positive=True),
        per_unit=number(raw.get("per_unit"), positive=True),
        list_date=day(raw.get("list_date")),
        delist_date=day(raw.get("delist_date")),
        last_delivery_date=day(raw.get("last_ddate")),
    )
    if result["list_date"] > result["delist_date"]:
        fail("Invalid contract lifecycle")
    return result


def daily(raw: dict[str, Any], meta: dict[str, Any], target: date) -> Record:
    if (
        raw.get("ts_code") != meta["contract_code"]
        or day(raw.get("trade_date")) != target.isoformat()
    ):
        fail("Daily identity mismatch")
    result = dict(meta, trade_date=target.isoformat())
    mapping = {
        "close_change_from_pre_settle": "change1",
        "settle_change_from_pre_settle": "change2",
        "volume": "vol",
        "open_interest": "oi",
        "open_interest_change": "oi_chg",
        "delivery_settlement_price": "delv_settle",
    }
    for key in NUMBERS + OPTIONAL_NUMBERS:
        if key in meta:
            continue
        source = mapping.get(key, key)
        if source not in raw:
            fail(
                f"Missing required daily field; field={source} "
                f"contract={meta['contract_code']} date={target}"
            )
        result[key] = number(
            raw[source],
            field=source,
            context=f"contract={meta['contract_code']} date={target}",
            nullable=key in OPTIONAL_NUMBERS
            or (
                key in ("pre_close", "open_interest_change")
                and target.isoformat() == meta["list_date"]
            ),
            nonnegative=key in ("volume", "amount", "open_interest"),
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


class DailySource:
    def __init__(self, executor: Executor) -> None:
        self.executor = CancellableExecutor(executor)
        self.catalog: list[dict[str, Any]] | None = None
        self.catalog_error: ExecutionFailure | None = None
        self.exclusions: set[str] = set()
        self.product_errors: dict[str, ExecutionFailure] = {}
        self.bases: dict[str, dict[str, Json]] = {}
        self.daily_cache: dict[tuple[str, date], list[dict[str, Any]]] = {}
        self.daily_errors: dict[tuple[str, date], ExecutionFailure] = {}
        self.indices: dict[str, ContractIndex] = {}

    def cancel(self) -> None:
        self.executor.cancel()

    def _load_catalog(self) -> None:
        if self.catalog is None and self.catalog_error is None:
            try:
                raw_catalog = exhaust(
                    self.executor, "fut_basic", exchange="CFFEX", fields=BASIC_FIELDS, fut_type="1"
                )
                catalog: list[dict[str, Any]] = []
                catalog_codes: set[str] = set()
                for raw in raw_catalog:
                    # Only known unrelated families may be excluded.
                    raw_product = raw.get("fut_code")
                    if not isinstance(raw_product, str) or not raw_product:
                        fail("Unclassifiable metadata product")
                    code_match = re.match(r"^([A-Z]+)", str(raw.get("ts_code", "")))
                    if code_match and code_match[1] in UNDERLYING and raw_product != code_match[1]:
                        self.product_errors[code_match[1]] = ExecutionFailure(
                            "Catalog product identity conflict"
                        )
                        continue
                    if raw_product not in UNDERLYING:
                        if not raw_product:
                            fail("Unclassifiable metadata")
                        continue
                    try:
                        normalized = metadata(raw)
                        if normalized["contract_code"] in catalog_codes:
                            fail("Duplicate catalog contract identity")
                        catalog_codes.add(normalized["contract_code"])
                        catalog.append(normalized)
                    except ExecutionFailure as exc:
                        self.product_errors[raw_product] = exc
                self.catalog = catalog
                excluded = exhaust(
                    self.executor,
                    "fut_basic",
                    exchange="CFFEX",
                    fut_type="2",
                    fields="ts_code,symbol,fut_code,exchange",
                )
                for raw in excluded:
                    code = text(raw.get("ts_code"))
                    if raw.get("exchange") != "CFFEX" or code != text(raw.get("symbol")) + ".CFX":
                        fail("Invalid nonordinary exclusion evidence")
                    if code in catalog_codes:
                        fail("Conflicting ordinary/nonordinary classification")
                    self.exclusions.add(code)
            except ExecutionFailure as exc:
                self.catalog_error = exc
        if self.catalog_error is not None:
            raise self.catalog_error
        assert self.catalog is not None

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        self._load_catalog()
        if all(identity(unit)[0] in self.product_errors for unit in units):
            return {unit.key: self.product_errors[identity(unit)[0]] for unit in units}
        days = sorted({identity(unit)[1] for unit in units})
        response = exhaust(
            self.executor,
            "fut_daily",
            exchange="CFFEX",
            start_date=days[0].strftime("%Y%m%d"),
            end_date=days[-1].strftime("%Y%m%d"),
            fields=DAILY_FIELDS,
        )
        self.daily_cache = {identity(unit): [] for unit in units}
        self.daily_errors.clear()
        selected_days = {target.isoformat(): target for target in days}
        for raw in response:
            try:
                source_day = day(raw.get("trade_date"))
            except ExecutionFailure:
                self.daily_cache.clear()
                self.daily_errors.clear()
                raise
            if source_day not in selected_days:
                continue
            target = selected_days[source_day]
            try:
                code = text(raw.get("ts_code"))
            except ExecutionFailure as exc:
                for key in self.daily_cache:
                    if key[1] == target:
                        self.daily_errors.setdefault(key, exc)
                continue
            if code in self.exclusions:
                continue
            match = re.fullmatch(r"([A-Z]+)[0-9]{4}\.CFX", code)
            if not match:
                prefix = re.match(r"^([A-Z]+)", code)
                failure = ExecutionFailure("Unclassifiable daily contract", "completeness")
                for key in self.daily_cache:
                    if key[1] == target and (prefix is None or prefix[1] == key[0]):
                        self.daily_errors.setdefault(key, failure)
                continue
            key = match[1], target
            if key in self.daily_cache:
                self.daily_cache[key].append(raw)
        result: dict[str, object] = {}
        try:
            for unit in units:
                try:
                    result[unit.key] = self._fetch_unit((unit,))[unit.key]
                except ExecutionFailure as exc:
                    result[unit.key] = exc
            return result
        finally:
            self.daily_cache.clear()
            self.daily_errors.clear()

    def _fetch_unit(self, units: tuple[Unit, ...]) -> dict[str, object]:
        product, target = identity(units[0])
        assert self.catalog is not None
        if product in self.product_errors:
            raise self.product_errors[product]
        if (product, target) in self.daily_errors:
            raise self.daily_errors[product, target]
        if product not in self.bases:
            self.bases[product] = cast(
                dict[str, Json],
                {
                    "catalog": [meta for meta in self.catalog if meta["product_code"] == product],
                    "exhausted": True,
                },
            )
        frozen = self.bases[product]
        basis = cast(list[dict[str, Any]], frozen["catalog"])
        if product not in self.indices:
            self.indices[product] = ContractIndex({meta["contract_code"]: meta for meta in basis})
        expected = self.indices[product].at(target)
        response = self.daily_cache[product, target]
        observed: list[Record] = []
        for raw in response:
            code = raw["ts_code"]
            if code not in expected:
                fail("Unexpected active contract")
            observed.append(daily(raw, expected[code], target))
        facts = UnitRecords(
            tuple(observed),
            tuple(instrument(meta) for meta in expected.values()),
            frozen,
        )
        return {units[0].key: facts}


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
        self.rows: dict[int, tuple[Record, FuturesDailyRow]] = {}

    def row(self, record: Record) -> FuturesDailyRow:
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
    reader: Callable[[Record], FuturesDailyRow] | None = None,
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
        fut_code=meta["product_code"],
        d_month=meta["delivery_month"],
        last_ddate=meta["last_delivery_date"].replace("-", ""),
    )
    return raw
