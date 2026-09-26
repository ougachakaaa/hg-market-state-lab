"""Deterministic preparation for the CSI1000 IM Basis History result."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from ...artifacts import RawRecord
from ...preparation.im_basis import (
    IMBasisError,
    assign_contract_slots,
    basis_values,
    observation_sort_key,
)
from .models import CSI1000IMBasisHistoryResult, IMBasisObservation

UNDERLYING_TS_CODE = "000852.SH"


class IMBasisHistoryError(ValueError):
    """The requested facts cannot produce a complete semantic result."""


def _number(record: Mapping[str, Any], field: str) -> float:
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise IMBasisHistoryError(f"{field} must be numeric, got {value!r}.")
    result = float(value)
    if not math.isfinite(result):
        raise IMBasisHistoryError(f"{field} must be finite, got {value!r}.")
    return result


def _contracts_by_code(
    basics: Sequence[RawRecord], start_trade_date: str, end_trade_date: str
) -> dict[str, RawRecord]:
    result: dict[str, RawRecord] = {}
    for contract in basics:
        code = contract.get("ts_code")
        listed = contract.get("list_date")
        delisted = contract.get("delist_date")
        if not all(isinstance(value, str) and value for value in (code, listed, delisted)):
            raise IMBasisHistoryError("IM contract identity and lifecycle facts are required.")
        assert isinstance(code, str) and isinstance(listed, str) and isinstance(delisted, str)
        if code in result:
            raise IMBasisHistoryError(f"duplicate IM basic fact for ts_code={code}.")
        if listed <= end_trade_date and delisted >= start_trade_date:
            result[code] = contract
    if not result:
        raise IMBasisHistoryError("no IM contract lifecycle intersects the requested interval.")
    return result


def prepare_history(
    start_trade_date: str,
    end_trade_date: str,
    index_facts: Sequence[RawRecord],
    basic_facts: Sequence[RawRecord],
    daily_facts: Sequence[RawRecord],
) -> CSI1000IMBasisHistoryResult:
    """Build the complete canonical panel from already captured Source facts."""
    underlying_by_date: dict[str, float] = {}
    for record in index_facts:
        trade_date = record.get("trade_date")
        if record.get("ts_code") != UNDERLYING_TS_CODE or not isinstance(trade_date, str):
            raise IMBasisHistoryError("index fact has an unexpected identity or trade_date.")
        if trade_date in underlying_by_date:
            raise IMBasisHistoryError(f"duplicate underlying row on {trade_date}.")
        close = _number(record, "close")
        if close == 0:
            raise IMBasisHistoryError(f"underlying close is zero on {trade_date}.")
        underlying_by_date[trade_date] = close
    if not underlying_by_date:
        raise IMBasisHistoryError("the requested interval has no CSI1000 observation date.")

    basics = _contracts_by_code(basic_facts, start_trade_date, end_trade_date)
    daily_by_key: dict[tuple[str, str], RawRecord] = {}
    for record in daily_facts:
        code = record.get("ts_code")
        trade_date = record.get("trade_date")
        if not isinstance(code, str) or not isinstance(trade_date, str):
            raise IMBasisHistoryError("IM daily identity facts are required.")
        contract = basics.get(code)
        if contract is None:
            raise IMBasisHistoryError(f"daily fact maps to unknown contract {code}.")
        if not str(contract["list_date"]) <= trade_date <= str(contract["delist_date"]):
            raise IMBasisHistoryError(f"daily fact for {code} is outside its lifecycle.")
        key = trade_date, code
        if key in daily_by_key:
            raise IMBasisHistoryError(f"duplicate IM daily row for {code} on {trade_date}.")
        daily_by_key[key] = record

    rows: list[dict[str, Any]] = []
    for trade_date in sorted(underlying_by_date):
        active = [
            contract
            for contract in basics.values()
            if str(contract["list_date"]) <= trade_date <= str(contract["delist_date"])
        ]
        try:
            slots = assign_contract_slots(trade_date, active)
        except IMBasisError as exc:
            raise IMBasisHistoryError(str(exc)) from exc
        active_codes = set(slots)
        unexpected = sorted(
            code
            for observed_date, code in daily_by_key
            if observed_date == trade_date and code not in active_codes
        )
        if unexpected:
            raise IMBasisHistoryError(
                f"inactive IM daily row(s) on {trade_date}: {', '.join(unexpected)}."
            )
        for code, slot in slots.items():
            daily = daily_by_key.get((trade_date, code))
            if daily is None:
                raise IMBasisHistoryError(f"missing IM daily row for {code} on {trade_date}.")
            contract = basics[code]
            future_close = _number(daily, "close")
            try:
                calculated = basis_values(
                    trade_date,
                    str(contract["delist_date"]),
                    underlying_by_date[trade_date],
                    future_close,
                )
            except IMBasisError as exc:
                raise IMBasisHistoryError(str(exc)) from exc
            rows.append(
                {
                    "trade_date": trade_date,
                    "ts_code": code,
                    "contract_slot": slot,
                    "delist_date": str(contract["delist_date"]),
                    "underlying_close": underlying_by_date[trade_date],
                    "future_close": future_close,
                    **calculated,
                }
            )
    rows.sort(key=observation_sort_key)
    observations = tuple(IMBasisObservation(**row) for row in rows)
    return CSI1000IMBasisHistoryResult(
        start_trade_date=start_trade_date,
        end_trade_date=end_trade_date,
        underlying_ts_code=UNDERLYING_TS_CODE,
        observations=observations,
    )
