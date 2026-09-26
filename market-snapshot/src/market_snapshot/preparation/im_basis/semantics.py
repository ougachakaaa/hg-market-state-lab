"""Shared IM slot, calendar-distance, and basis semantics.

The semantic authority is co-located in ``ARCHITECTURE.md``.  This module is
deliberately narrow: products still own their input scope, completeness, and
result shape.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

SLOT_ORDER = {"M0": 0, "M1": 1, "Q1": 2, "Q2": 3}
CALENDAR_DAYS_PER_YEAR = 365
_IM_IDENTITY = re.compile(r"IM(?P<year>\d{2})(?P<month>\d{2})(?:\.[A-Z]+)?$")


class IMBasisError(ValueError):
    """Required IM facts cannot produce the canonical basis semantics."""


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise IMBasisError(f"{field} must be a non-empty string, got {value!r}.")
    return value


def _required_date(record: Mapping[str, Any], field: str) -> date:
    value = _required_text(record, field)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise IMBasisError(f"{field} must use YYYY-MM-DD, got {value!r}.") from exc
    if parsed.isoformat() != value:
        raise IMBasisError(f"{field} must use YYYY-MM-DD, got {value!r}.")
    return parsed


def _required_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise IMBasisError(f"{field} must be numeric, got {value!r}.")
    number = float(value)
    if not math.isfinite(number):
        raise IMBasisError(f"{field} must be finite, got {value!r}.")
    return number


def _month_index(value: tuple[int, int]) -> int:
    return value[0] * 12 + value[1] - 1


def _quarter_months_after(value: tuple[int, int]) -> list[tuple[int, int]]:
    year, month = value
    candidates: list[tuple[int, int]] = []
    probe_year = year
    while len(candidates) < 2:
        for probe_month in (3, 6, 9, 12):
            candidate = (probe_year, probe_month)
            if _month_index(candidate) > _month_index((year, month)):
                candidates.append(candidate)
                if len(candidates) == 2:
                    return candidates
        probe_year += 1
    return candidates


def contract_month(record: Mapping[str, Any]) -> tuple[int, int]:
    """Return a contract's verified maturity month."""
    ts_code = _required_text(record, "ts_code")
    delist = _required_date(record, "delist_date")
    match = _IM_IDENTITY.fullmatch(ts_code)
    if match is None:
        raise IMBasisError(f"ts_code={ts_code!r} does not express an IM delivery month.")
    identity = (int(match.group("year")), int(match.group("month")))
    if not 1 <= identity[1] <= 12:
        raise IMBasisError(f"ts_code={ts_code!r} has an invalid delivery month.")
    if identity != (delist.year % 100, delist.month):
        raise IMBasisError(f"ts_code={ts_code!r} conflicts with delist_date={delist.isoformat()}.")
    return delist.year, delist.month


def assign_contract_slots(
    trade_date: str, contracts: Sequence[Mapping[str, Any]]
) -> dict[str, str]:
    """Validate one day's complete active universe and return its slot mapping."""
    try:
        observed_on = date.fromisoformat(trade_date)
    except (TypeError, ValueError) as exc:
        raise IMBasisError(f"trade_date must use YYYY-MM-DD, got {trade_date!r}.") from exc
    if observed_on.isoformat() != trade_date:
        raise IMBasisError(f"trade_date must use YYYY-MM-DD, got {trade_date!r}.")

    by_month: dict[tuple[int, int], tuple[str, Mapping[str, Any]]] = {}
    seen_codes: set[str] = set()
    for contract in contracts:
        ts_code = _required_text(contract, "ts_code")
        if ts_code in seen_codes:
            raise IMBasisError(f"duplicate IM contract fact for ts_code={ts_code}.")
        seen_codes.add(ts_code)
        listed = _required_date(contract, "list_date")
        delisted = _required_date(contract, "delist_date")
        if listed > delisted:
            raise IMBasisError(f"contract {ts_code} has an inverted lifecycle.")
        if not listed <= observed_on <= delisted:
            raise IMBasisError(f"contract {ts_code} is not active on {trade_date}.")
        month = contract_month(contract)
        if month in by_month:
            raise IMBasisError(f"more than one active IM contract has month={month}.")
        by_month[month] = (ts_code, contract)

    months = sorted(by_month)
    if len(months) != 4:
        raise IMBasisError(
            f"trade_date={trade_date} has {len(months)} active IM contract months; expected 4."
        )
    if _month_index(months[1]) != _month_index(months[0]) + 1:
        raise IMBasisError(f"front IM months are not consecutive on {trade_date}: {months[:2]}.")
    expected_quarters = _quarter_months_after(months[1])
    if months[2:] != expected_quarters:
        raise IMBasisError(
            f"quarter IM months on {trade_date} are {months[2:]}, expected {expected_quarters}."
        )
    return {
        by_month[month][0]: slot
        for month, slot in zip(months, ("M0", "M1", "Q1", "Q2"), strict=True)
    }


def basis_values(
    trade_date: str,
    delist_date: str,
    underlying_close: Any,
    futures_close: Any,
) -> dict[str, float | int]:
    """Calculate the canonical remaining-days and IM basis fields."""
    try:
        observed_on = date.fromisoformat(trade_date)
        delisted_on = date.fromisoformat(delist_date)
    except (TypeError, ValueError) as exc:
        raise IMBasisError("trade_date and delist_date must use YYYY-MM-DD.") from exc
    spot = _required_number(underlying_close, "underlying_close")
    future = _required_number(futures_close, "futures_close")
    if spot == 0:
        raise IMBasisError("underlying_close must not be zero.")
    days_to_delist = (delisted_on - observed_on).days
    if days_to_delist < 0:
        raise IMBasisError(f"trade_date={trade_date} is after delist_date={delist_date}.")
    annualization_days = max(days_to_delist, 1)
    basis_points = future - spot
    basis_pct = (future / spot - 1) * 100
    return {
        "days_to_delist": days_to_delist,
        "annualization_days": annualization_days,
        "basis_points": basis_points,
        "basis_pct": basis_pct,
        "annualized_basis_pct": basis_pct * CALENDAR_DAYS_PER_YEAR / annualization_days,
    }


def observation_sort_key(observation: Mapping[str, Any]) -> tuple[str, int, str]:
    """Return the shared canonical flat-panel ordering key."""
    slot = observation.get("contract_slot")
    if slot not in SLOT_ORDER:
        raise IMBasisError(f"unknown contract_slot={slot!r}.")
    return (
        str(observation.get("trade_date")),
        SLOT_ORDER[str(slot)],
        str(observation.get("ts_code")),
    )
