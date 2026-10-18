"""Dataset Source adapter: provider requests, pagination and target partitioning."""

import re
from collections.abc import Iterable
from datetime import date
from typing import Any, cast

from data_lake._serialization import Json
from data_lake.domain import ExecutionFailure, Unit
from data_lake.providers.tushare import Executor
from data_lake.providers.tushare._executor import CancellableExecutor

from ._domain import (
    ContractIndex,
    day,
    exclusion_codes,
    fail,
    freeze_catalog,
    identity,
    normalize_daily,
    reconcile_catalog,
    text,
)


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


BASIC_FIELDS = (
    "ts_code,symbol,name,exchange,fut_code,multiplier,trade_unit,per_unit,"
    "quote_unit,list_date,delist_date,d_month,last_ddate"
)


DAILY_FIELDS = (
    "ts_code,trade_date,pre_close,pre_settle,open,high,low,close,settle,change1,"
    "change2,vol,amount,oi,oi_chg,delv_settle"
)


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
                catalog, self.product_errors = reconcile_catalog(raw_catalog)
                self.catalog = catalog
                excluded = exhaust(
                    self.executor,
                    "fut_basic",
                    exchange="CFFEX",
                    fut_type="2",
                    fields="ts_code,symbol,fut_code,exchange",
                )
                self.exclusions = exclusion_codes(
                    excluded, {meta["contract_code"] for meta in catalog}
                )
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
            self.bases[product] = freeze_catalog(self.catalog, product)
        frozen = self.bases[product]
        basis = cast(list[dict[str, Any]], frozen["catalog"])
        if product not in self.indices:
            self.indices[product] = ContractIndex({meta["contract_code"]: meta for meta in basis})
        expected = self.indices[product].at(target)
        response = self.daily_cache[product, target]
        return {units[0].key: normalize_daily(units[0], response, expected, frozen)}


def batches(units: tuple[Unit, ...]) -> Iterable[tuple[Unit, ...]]:
    grouped: dict[date, list[Unit]] = {}
    for unit in units:
        _, target = identity(unit)
        grouped.setdefault(target, []).append(unit)
    window: list[date] = []
    for target_day in sorted(grouped):
        if window and (len(window) == 5 or (target_day - window[0]).days >= 31):
            yield tuple(unit for target in window for unit in grouped[target])
            window.clear()
        window.append(target_day)
    if window:
        yield tuple(unit for target in window for unit in grouped[target])
