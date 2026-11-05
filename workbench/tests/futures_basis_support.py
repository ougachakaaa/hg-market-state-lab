"""Deterministic fixtures and public-service fakes for the futures basis monitor."""

from __future__ import annotations

import json
import runpy
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from data_lake import CoverageResult, EnsureResult, OperationError
from data_lake.datasets.tushare_trade_calendar import TradeCalendarRecord
from data_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryError,
)
from data_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisHistoryResult as Result,
)
from data_snapshot.products.cffex_equity_index_basis_history import (
    CFFEXEquityIndexBasisObservation as Observation,
)

RUNTIME_PATH = (
    Path(__file__).resolve().parents[1]
    / "tasks"
    / "equity_index_futures_basis_monitor"
    / "runtime"
    / "run_monitor.py"
)
RUNTIME = runpy.run_path(str(RUNTIME_PATH))
RUN_MONITOR = RUNTIME["run_monitor"]
RUN_STORE = RUNTIME["RunStore"]
TASK_PATH = RUNTIME_PATH.parents[1] / "task.json"

UNDERLYING = {
    "IF": "000300.SH",
    "IH": "000016.SH",
    "IC": "000905.SH",
    "IM": "000852.SH",
}
LISTING = {
    "IF": "2010-04-16",
    "IH": "2015-04-16",
    "IC": "2015-04-16",
    "IM": "2022-07-22",
}
SOURCE = "tushare:index_daily+fut_basic+fut_daily"
SLOTS = ("M0", "M1", "Q1", "Q2")
EXECUTION_DATE = date(2026, 11, 4)
EXECUTION_NOW = datetime(2026, 11, 3, 16, 17, tzinfo=UTC)


def weekdays(start: str, end: str, holidays: set[str] | None = None) -> list[date]:
    excluded = holidays or set()
    current = date.fromisoformat(start)
    final = date.fromisoformat(end)
    days: list[date] = []
    while current <= final:
        if current.weekday() < 5 and current.isoformat() not in excluded:
            days.append(current)
        current += timedelta(days=1)
    return days


def make_observation(family: str, day: date, slot: str) -> Observation:
    index = SLOTS.index(slot)
    delist = day + timedelta(days=30 + index * 30)
    days_to_delist = (delist - day).days
    annualization_days = max(days_to_delist, 1)
    underlying_close = 6000.0 + index
    futures_close = underlying_close - 12.5
    basis_points = futures_close - underlying_close
    basis_pct = (futures_close / underlying_close - 1) * 100
    annualized = basis_pct * 365 / annualization_days
    return Observation(
        trade_date=day.isoformat(),
        futures_family=family,
        underlying_code=UNDERLYING[family],
        contract_code=f"{family}{day:%y%m}{slot}.CFX",
        contract_slot=slot,
        delist_date=delist.isoformat(),
        days_to_delist=days_to_delist,
        annualization_days=annualization_days,
        underlying_close=underlying_close,
        futures_close=futures_close,
        basis_points=basis_points,
        basis_pct=basis_pct,
        annualized_basis_pct=annualized,
    )


def make_result(
    family: str,
    days: list[date],
    *,
    start: date,
    end: date,
    listing: str | None = None,
    drop: set[tuple[str, str]] | None = None,
    extra: list[Observation] | None = None,
    first: str | None = None,
    last: str | None = None,
) -> Result:
    dropped = drop or set()
    observations = [
        make_observation(family, day, slot)
        for day in days
        for slot in SLOTS
        if (day.isoformat(), slot) not in dropped
    ]
    observations.extend(extra or [])
    observations.sort(key=lambda item: (item.trade_date, SLOTS.index(item.contract_slot)))
    if not observations:
        raise ValueError("a synthetic successful result needs observations")
    return Result(
        futures_family=family,
        start_trade_date=start.isoformat(),
        end_trade_date=end.isoformat(),
        family_listing_date=listing or LISTING[family],
        first_observation_date=first or observations[0].trade_date,
        last_observation_date=last or observations[-1].trade_date,
        underlying_code=UNDERLYING[family],
        source_identity=SOURCE,
        observations=tuple(observations),
    )


class FakeCalendar:
    """Calendar public-service fake; it records every public call."""

    def __init__(
        self,
        open_dates: list[date] | set[date],
        *,
        complete: bool = True,
        unavailable: bool = False,
    ) -> None:
        self.open_dates = set(open_dates)
        self.complete = complete
        self.unavailable = unavailable
        self.calls: list[tuple[str, Any]] = []

    def _coverage(self, request: Any) -> CoverageResult:
        total = (request.end_date - request.start_date).days + 1
        successful = total if self.complete else max(total - 1, 0)
        missing = 0 if self.complete else 1
        return CoverageResult(total, successful, missing, 0, 0, self.complete)

    def coverage(self, request: Any) -> CoverageResult:
        self.calls.append(("coverage", request))
        if self.unavailable:
            raise OperationError("synthetic calendar unavailable")
        return self._coverage(request)

    def ensure(self, request: Any) -> EnsureResult:
        self.calls.append(("ensure", request))
        if self.unavailable:
            raise OperationError("synthetic calendar unavailable")
        if self.complete:
            return EnsureResult(0, 0, 0, 0, 0, 0, True, ())
        return EnsureResult(
            (request.end_date - request.start_date).days + 1,
            0,
            1,
            0,
            1,
            0,
            False,
            (),
        )

    def export(self, request: Any) -> Any:
        self.calls.append(("export", request))
        if self.unavailable:
            raise OperationError("synthetic calendar unavailable")
        records = []
        current = request.start_date
        while current <= request.end_date:
            records.append(
                TradeCalendarRecord(
                    exchange=request.exchange,
                    cal_date=current,
                    is_open=1 if current in self.open_dates else 0,
                    pretrade_date=None,
                )
            )
            current += timedelta(days=1)
        return SimpleNamespace(
            dataset="tushare_trade_calendar",
            view="calendar",
            export_schema_version=1,
            scope=SimpleNamespace(exchange=request.exchange),
            window=SimpleNamespace(
                start_date=request.start_date, end_date=request.end_date
            ),
            coverage=self._coverage(request),
            records=tuple(records),
        )


class FakeProduct:
    """Public CFFEX basis product fake with one request per family."""

    def __init__(self, outcomes: dict[str, Any]) -> None:
        self.outcomes = outcomes
        self.requests: list[Any] = []

    def __call__(self, request: Any) -> Any:
        self.requests.append(request)
        outcome = self.outcomes.get(request.futures_family)
        if outcome is None:
            raise CFFEXEquityIndexBasisHistoryError(
                "invalid_request", "synthetic family is not configured"
            )
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def explicit_params(
    families: tuple[str, ...] = ("IM",),
    *,
    start: str = "2026-10-21",
    end: str = "2026-11-03",
    original: str = "查询 IM 2026-10-21 至 2026-11-03 的年化基差",
) -> dict[str, Any]:
    return {
        "original_request": original,
        "futures_families": list(families),
        "start_date": start,
        "end_date": end,
    }


def relative_params(
    expression: str,
    families: tuple[str, ...] = ("IM",),
    *,
    anchor: str | None = None,
    original: str | None = None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "original_request": original or f"查询 IM {expression} 的年化基差",
        "futures_families": list(families),
        "date_expression": expression,
    }
    if anchor is not None:
        value["anchor_date"] = anchor
    return value


def run_case(
    tmp_path: Path,
    params: dict[str, Any],
    *,
    product: FakeProduct | None = None,
    calendar: FakeCalendar | None = None,
    authorization: str | None = "synthetic user authorization for deterministic tests",
    execution_date: date = EXECUTION_DATE,
    now: datetime = EXECUTION_NOW,
) -> dict[str, Any]:
    return RUN_MONITOR(
        params,
        authorization_reference=authorization,
        store_root=tmp_path / "runs",
        product_runner=product,
        calendar_service=calendar,
        execution_date=execution_date,
        now=now,
    )


def read_state(tmp_path: Path, outcome: dict[str, Any]) -> dict[str, Any]:
    return RUN_STORE(tmp_path / "runs").read(outcome["run_id"])


def artifact_bytes(tmp_path: Path, outcome: dict[str, Any], reference: dict[str, Any]) -> bytes:
    path = tmp_path / "runs" / outcome["run_id"] / reference["stored_path"]
    return path.read_bytes()


def artifact_json(tmp_path: Path, outcome: dict[str, Any], reference: dict[str, Any]) -> Any:
    return json.loads(artifact_bytes(tmp_path, outcome, reference).decode("utf-8"))


def csv_rows(tmp_path: Path, outcome: dict[str, Any]) -> list[list[str]]:
    import csv
    import io

    data = artifact_bytes(tmp_path, outcome, outcome["csv"]).decode("utf-8")
    return list(csv.reader(io.StringIO(data)))


def with_signed_zero(observation: Observation) -> Observation:
    return replace(observation, basis_pct=-0.0, annualized_basis_pct=-0.0)
