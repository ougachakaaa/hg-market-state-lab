"""Deterministic MO option-chain Preparation from this goal's five Raw artifacts.

The output mirrors the read-model shape as plain typed data. The Data Service
wraps it in its existing application types. No Source access, date fallback, or
HTTP behavior belongs here.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import TypedDict

from .. import artifacts
from ..artifacts import RawRecord

UNDERLYING_ID = "000852.SH"
MO_OPT_CODE = "OP000852.SH"


class PreparedPoint(TypedDict):
    instrument_id: str
    strike: float
    price: float | None


class PreparedFuturesRef(TypedDict):
    instrument_id: str
    price: float


class PreparedExpiry(TypedDict):
    expiry_date: str
    futures: PreparedFuturesRef
    calls: list[PreparedPoint]
    puts: list[PreparedPoint]


class PreparedChain(TypedDict):
    underlying_instrument_id: str
    underlying_price: float
    expiries: list[PreparedExpiry]


class PreparationError(Exception):
    """The Raw facts cannot form a complete MO option chain."""


def required_text(row: RawRecord, field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PreparationError(f"{field} must be a non-empty string, got {value!r}")
    return value


def required_date(row: RawRecord, field: str) -> str:
    value = required_text(row, field)
    try:
        if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
            raise ValueError(value)
    except ValueError as exc:
        raise PreparationError(f"{field} must be YYYY-MM-DD, got {value!r}") from exc
    return value


def numeric(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise PreparationError(f"{field} must be a finite number, got {value!r}")
    return float(value)


def raw_rows(raw_dir: Path, name: str) -> list[RawRecord]:
    try:
        payload = artifacts.read_raw_artifact(raw_dir, name)
    except (OSError, ValueError) as exc:
        raise PreparationError(f"cannot read {name} Raw artifact: {exc}") from exc
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise PreparationError(f"{name} Raw artifact must be an array of objects")
    return payload


def underlying_price(rows: Sequence[RawRecord], target_trade_date: str, price_type: str) -> float:
    if len(rows) != 1:
        raise PreparationError("exactly one target-date underlying row is required")
    row = rows[0]
    if required_text(row, "ts_code") != UNDERLYING_ID:
        raise PreparationError("underlying instrument does not match MO")
    if required_date(row, "trade_date") != target_trade_date:
        raise PreparationError("underlying trade date does not match the query")
    return numeric(row.get(price_type), f"underlying {price_type}")


def active_contracts(rows: Sequence[RawRecord], target_trade_date: str) -> dict[str, RawRecord]:
    if not rows:
        raise PreparationError("active MO contract universe is empty")
    active: dict[str, RawRecord] = {}
    for row in rows:
        identity = required_text(row, "ts_code")
        if (
            required_text(row, "exchange") != "CFFEX"
            or required_text(row, "opt_code") != MO_OPT_CODE
        ):
            raise PreparationError(f"contract {identity} is outside the MO/CFFEX universe")
        listed = required_date(row, "list_date")
        delisted = required_date(row, "delist_date")
        if listed > delisted or not listed <= target_trade_date <= delisted:
            raise PreparationError(f"contract {identity} has inconsistent lifecycle facts")
        if identity in active:
            raise PreparationError(f"duplicate active contract {identity}")
        active[identity] = row
    return active


def daily_rows(rows: Sequence[RawRecord], target_trade_date: str) -> dict[str, RawRecord]:
    daily: dict[str, RawRecord] = {}
    for row in rows:
        identity = required_text(row, "ts_code")
        if required_date(row, "trade_date") != target_trade_date:
            raise PreparationError(f"daily row {identity} has a different trade date")
        if required_text(row, "exchange") != "CFFEX":
            raise PreparationError(f"daily row {identity} has inconsistent exchange")
        if identity in daily:
            raise PreparationError(f"duplicate daily row for {identity}")
        daily[identity] = row
    return daily


def selected_option_price(row: RawRecord, field: str) -> float | None:
    value = row.get(field)
    return None if value is None else numeric(value, f"option {field}")


def futures_references(
    basic_rows: Sequence[RawRecord],
    daily_rows: Sequence[RawRecord],
    target_trade_date: str,
    price_type: str,
    expiries: set[str],
) -> dict[str, PreparedFuturesRef]:
    """Match each MO expiry to exactly one active IM contract and daily price."""
    candidates: dict[str, list[str]] = {expiry: [] for expiry in expiries}
    seen: set[str] = set()
    for row in basic_rows:
        identity = required_text(row, "ts_code")
        symbol = required_text(row, "symbol")
        if (
            required_text(row, "exchange") != "CFFEX"
            or required_text(row, "fut_code") != "IM"
            or not symbol.startswith("IM")
            or not symbol[2:].isdigit()
        ):
            raise PreparationError(f"IM basic Raw has an out-of-scope contract {identity}")
        if identity in seen:
            raise PreparationError(f"duplicate IM basic contract {identity}")
        seen.add(identity)
        listed = required_date(row, "list_date")
        delisted = required_date(row, "delist_date")
        if listed > delisted:
            raise PreparationError(f"IM contract {identity} has inverted lifecycle")
        if listed <= target_trade_date <= delisted and delisted in candidates:
            candidates[delisted].append(identity)

    required_codes: dict[str, str] = {}
    for expiry, matches in candidates.items():
        if len(matches) != 1:
            raise PreparationError(
                f"MO expiry {expiry} requires exactly one active IM contract; got {len(matches)}"
            )
        required_codes[expiry] = matches[0]

    required_rows: dict[str, list[RawRecord]] = {code: [] for code in required_codes.values()}
    for row in daily_rows:
        identity = required_text(row, "ts_code")
        if identity in required_rows:
            required_rows[identity].append(row)

    references: dict[str, PreparedFuturesRef] = {}
    for expiry, identity in required_codes.items():
        rows = required_rows[identity]
        if len(rows) != 1:
            raise PreparationError(
                f"matched IM contract {identity} requires one target-date daily row; "
                f"got {len(rows)}"
            )
        if required_date(rows[0], "trade_date") != target_trade_date:
            raise PreparationError(f"matched IM contract {identity} has a different trade date")
        references[expiry] = {
            "instrument_id": identity,
            "price": numeric(rows[0].get(price_type), f"futures {identity} {price_type}"),
        }
    return references


def build_chain(target_trade_date: str, price_type: str, raw_dir: Path) -> PreparedChain:
    """Read only the requested date's Raw scope and construct the complete chain."""
    underlying = underlying_price(raw_rows(raw_dir, "index_daily"), target_trade_date, price_type)
    contracts = active_contracts(raw_rows(raw_dir, "mo_option_basic"), target_trade_date)
    daily = daily_rows(raw_rows(raw_dir, "mo_option_daily"), target_trade_date)
    missing = sorted(contracts.keys() - daily.keys())
    if missing:
        raise PreparationError(
            f"active contracts have no target-date daily row: {', '.join(missing)}"
        )
    if daily.keys() - contracts.keys():
        raise PreparationError("MO daily Raw has rows outside the active contract universe")

    grouped: dict[str, dict[str, list[PreparedPoint]]] = {}
    for identity, contract in contracts.items():
        expiry = required_date(contract, "maturity_date")
        option_type = required_text(contract, "call_put")
        if option_type not in ("C", "P"):
            raise PreparationError(f"contract {identity} has invalid call_put={option_type!r}")
        point: PreparedPoint = {
            "instrument_id": identity,
            "strike": numeric(contract.get("exercise_price"), "exercise_price"),
            "price": selected_option_price(daily[identity], price_type),
        }
        grouped.setdefault(expiry, {"C": [], "P": []})[option_type].append(point)

    def ordered(points: list[PreparedPoint]) -> list[PreparedPoint]:
        return sorted(points, key=lambda point: (point["strike"], point["instrument_id"]))

    references = futures_references(
        raw_rows(raw_dir, "im_futures_basic"),
        raw_rows(raw_dir, "im_futures_daily"),
        target_trade_date,
        price_type,
        set(grouped),
    )
    expiries: list[PreparedExpiry] = [
        {
            "expiry_date": expiry,
            "futures": references[expiry],
            "calls": ordered(grouped[expiry]["C"]),
            "puts": ordered(grouped[expiry]["P"]),
        }
        for expiry in sorted(grouped)
    ]
    return {
        "underlying_instrument_id": UNDERLYING_ID,
        "underlying_price": underlying,
        "expiries": expiries,
    }
