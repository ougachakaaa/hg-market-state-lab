"""Pure, whole-panel preparation for one CFFEX equity-index futures family."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from ...artifacts import RawRecord
from ...cffex_equity_index_basis.semantics import (
    FAMILY_FACTS,
    CFFEXBasisError,
    assign_contract_slots,
    basis_values,
    contract_month,
    observation_sort_key,
)
from .models import CFFEXEquityIndexBasisHistoryResult, CFFEXEquityIndexBasisObservation

SOURCE_IDENTITY = "tushare:index_daily+fut_basic+fut_daily"


class IncompletePanelError(ValueError):
    """Source facts cannot produce the complete requested panel."""


class NoObservationsError(ValueError):
    """The effective interval has no underlying observations."""


def _iso(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise IncompletePanelError(f"{field} must be a date string.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise IncompletePanelError(f"{field} is invalid: {value!r}.") from exc
    if parsed.isoformat() != value:
        raise IncompletePanelError(f"{field} must use YYYY-MM-DD.")
    return value


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise IncompletePanelError(f"{field} must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise IncompletePanelError(f"{field} must be finite.")
    return result


def prepare_history(
    family: str,
    start_trade_date: str,
    end_trade_date: str,
    index_facts: Sequence[RawRecord],
    basic_facts: Sequence[RawRecord],
    daily_facts: Sequence[RawRecord],
) -> CFFEXEquityIndexBasisHistoryResult:
    underlying_code, listing_date = FAMILY_FACTS[family]
    effective_start = max(start_trade_date, listing_date)
    index_by_date: dict[str, float] = {}
    for row in index_facts:
        trade_date = _iso(row.get("trade_date"), "index trade_date")
        if (
            row.get("ts_code") != underlying_code
            or not effective_start <= trade_date <= end_trade_date
        ):
            raise IncompletePanelError("underlying row has an unexpected identity or date.")
        if trade_date in index_by_date:
            raise IncompletePanelError(f"duplicate underlying row on {trade_date}.")
        close = _number(row.get("close"), "underlying close")
        if close == 0:
            raise IncompletePanelError(f"underlying close is zero on {trade_date}.")
        index_by_date[trade_date] = close
    if not index_by_date:
        raise NoObservationsError("effective interval has no underlying observation dates.")

    basic_by_code: dict[str, Mapping[str, Any]] = {}
    for row in basic_facts:
        code = row.get("ts_code")
        if not isinstance(code, str) or not code:
            raise IncompletePanelError("contract code is required.")
        listed = _iso(row.get("list_date"), "list_date")
        delisted = _iso(row.get("delist_date"), "delist_date")
        if listed > delisted:
            raise IncompletePanelError(f"contract {code} has inverted lifecycle.")
        try:
            contract_month(row, family)
        except CFFEXBasisError as exc:
            raise IncompletePanelError(str(exc)) from exc
        if code in basic_by_code:
            raise IncompletePanelError(f"duplicate contract fact for {code}.")
        if listed <= end_trade_date and delisted >= effective_start:
            basic_by_code[code] = row
    if not basic_by_code:
        raise IncompletePanelError("no contract lifecycle intersects the effective interval.")

    daily_by_key: dict[tuple[str, str], RawRecord] = {}
    for row in daily_facts:
        code = row.get("ts_code")
        trade_date = _iso(row.get("trade_date"), "futures trade_date")
        if not isinstance(code, str) or code not in basic_by_code:
            raise IncompletePanelError(f"unknown futures contract {code!r}.")
        basic = basic_by_code[code]
        if not str(basic["list_date"]) <= trade_date <= str(basic["delist_date"]):
            raise IncompletePanelError(f"futures row for {code} is outside its lifecycle.")
        if not effective_start <= trade_date <= end_trade_date:
            raise IncompletePanelError("futures row is outside the effective interval.")
        key = trade_date, code
        if key in daily_by_key:
            raise IncompletePanelError(f"duplicate futures row for {code} on {trade_date}.")
        daily_by_key[key] = row

    rows: list[dict[str, Any]] = []
    for trade_date in sorted(index_by_date):
        active = [
            basic
            for basic in basic_by_code.values()
            if str(basic["list_date"]) <= trade_date <= str(basic["delist_date"])
        ]
        try:
            slots = assign_contract_slots(trade_date, active, family)
        except CFFEXBasisError as exc:
            raise IncompletePanelError(str(exc)) from exc
        unexpected = [
            code
            for observed_date, code in daily_by_key
            if observed_date == trade_date and code not in slots
        ]
        if unexpected:
            raise IncompletePanelError(f"inactive futures row on {trade_date}: {unexpected}.")
        for code, slot in slots.items():
            fact = daily_by_key.get((trade_date, code))
            if fact is None:
                raise IncompletePanelError(f"missing futures row for {code} on {trade_date}.")
            future_close = _number(fact.get("close"), "futures close")
            basic = basic_by_code[code]
            try:
                calculated = basis_values(
                    trade_date, str(basic["delist_date"]), index_by_date[trade_date], future_close
                )
            except CFFEXBasisError as exc:
                raise IncompletePanelError(str(exc)) from exc
            rows.append(
                {
                    "trade_date": trade_date,
                    "futures_family": family,
                    "underlying_code": underlying_code,
                    "contract_code": code,
                    "contract_slot": slot,
                    "delist_date": str(basic["delist_date"]),
                    "underlying_close": index_by_date[trade_date],
                    "futures_close": future_close,
                    **calculated,
                }
            )
    rows.sort(key=observation_sort_key)
    return CFFEXEquityIndexBasisHistoryResult(
        futures_family=family,
        start_trade_date=start_trade_date,
        end_trade_date=end_trade_date,
        family_listing_date=listing_date,
        first_observation_date=rows[0]["trade_date"],
        last_observation_date=rows[-1]["trade_date"],
        underlying_code=underlying_code,
        source_identity=SOURCE_IDENTITY,
        observations=tuple(CFFEXEquityIndexBasisObservation(**row) for row in rows),
    )
