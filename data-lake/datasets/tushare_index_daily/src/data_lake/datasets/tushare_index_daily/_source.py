"""Dataset Source adapter: provider requests, pagination and target partitioning."""

from collections.abc import Iterable
from typing import Any

from data_lake.domain import ExecutionFailure, Unit
from data_lake.providers.tushare import Executor
from data_lake.providers.tushare._executor import CancellableExecutor

from ._domain import (
    day,
    fail,
    identity,
    normalize_daily,
    select_metadata,
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
        for row in page:
            text(row.get("ts_code"))
            if endpoint == "index_daily":
                text(row.get("trade_date"))
        result.extend(page)
    return fail("Source exhaustion could not be proven")


BASIC_FIELDS = "ts_code,name,market,publisher,category,list_date,exp_date"


DAILY_FIELDS = "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"


class DailySource:
    def __init__(
        self,
        executor: Executor,
        cached: dict[str, dict[str, Any]],
        pending_codes: tuple[str, ...] = (),
    ) -> None:
        self.executor = CancellableExecutor(executor)
        self.metadata = cached
        self.pending_codes = tuple(sorted(set(pending_codes) - cached.keys()))
        self.errors: dict[str, ExecutionFailure] = {}

    def cancel(self) -> None:
        self.executor.cancel()

    def _load_metadata(self, code: str) -> None:
        if code in self.errors:
            raise self.errors[code]
        if code not in self.metadata:
            selected = (code,) + tuple(
                item
                for item in self.pending_codes
                if item != code and item not in self.metadata and item not in self.errors
            )[:63]
            try:
                catalog = []
                # Query all markets; symbol is only a transport filter, never identity.
                for market in ("SSE", "SZSE", "CSI", "CICC", "OTH", "MSCI", "SW"):
                    catalog.extend(
                        exhaust(
                            self.executor,
                            "index_basic",
                            market=market,
                            symbol=",".join(sorted({item[:6] for item in selected})),
                            fields=BASIC_FIELDS,
                        )
                    )
            except ExecutionFailure as exc:
                self.errors.update(dict.fromkeys(selected, exc))
            else:
                selected_metadata, errors = select_metadata(catalog, selected)
                self.metadata.update(selected_metadata)
                self.errors.update(errors)
            if code in self.errors:
                raise self.errors[code]

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
        unit = units[0]
        return {unit.key: normalize_daily(unit, response, self.metadata[identity(unit)[0]])}


def batches(units: tuple[Unit, ...]) -> Iterable[tuple[Unit, ...]]:
    grouped: dict[tuple[str, int], list[Unit]] = {}
    for unit in units:
        code, day = identity(unit)
        grouped.setdefault((code, day.year), []).append(unit)
    for group in grouped.values():
        for offset in range(0, len(group), 250):
            yield tuple(group[offset : offset + 250])
