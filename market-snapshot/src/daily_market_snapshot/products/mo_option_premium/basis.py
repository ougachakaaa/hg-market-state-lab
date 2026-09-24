"""Construct ``OptionMarketBasis`` from Premium-owned Raw artifacts."""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from ... import artifacts
from ...artifacts import RawRecord
from .models import (
    FuturesReference,
    ObservationAnchor,
    OptionMarketBasis,
    OptionObservation,
    OptionProduct,
    OptionType,
    PriceType,
    UnderlyingReference,
)

UNDERLYING_ID = "000852.SH"
MO_OPT_CODE = "OP000852.SH"


class BasisConstructionError(Exception):
    """Premium Raw cannot form a complete, compatible market basis."""


def required_text(row: RawRecord, field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BasisConstructionError(f"{field} must be a non-empty string, got {value!r}")
    return value


def required_date(row: RawRecord, field: str) -> str:
    value = required_text(row, field)
    try:
        if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
            raise ValueError(value)
    except ValueError as exc:
        raise BasisConstructionError(f"{field} must be YYYY-MM-DD, got {value!r}") from exc
    return value


def numeric(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value):
        raise BasisConstructionError(f"{field} must be a finite number, got {value!r}")
    return float(value)


def raw_rows(raw_dir: Path, name: str) -> list[RawRecord]:
    try:
        payload = artifacts.read_raw_artifact(raw_dir, name)
    except (OSError, ValueError) as exc:
        raise BasisConstructionError(f"cannot read {name} Raw artifact: {exc}") from exc
    if not isinstance(payload, list) or any(not isinstance(row, dict) for row in payload):
        raise BasisConstructionError(f"{name} Raw artifact must be an array of objects")
    return payload


def active_options(rows: Sequence[RawRecord], as_of: str) -> dict[str, RawRecord]:
    if not rows:
        raise BasisConstructionError("active MO contract universe is empty")
    active: dict[str, RawRecord] = {}
    for row in rows:
        identity = required_text(row, "ts_code")
        if (
            required_text(row, "exchange") != "CFFEX"
            or required_text(row, "opt_code") != MO_OPT_CODE
        ):
            raise BasisConstructionError(f"contract {identity} is outside the MO/CFFEX universe")
        listed = required_date(row, "list_date")
        delisted = required_date(row, "delist_date")
        if listed > delisted or not listed <= as_of <= delisted:
            raise BasisConstructionError(f"contract {identity} has inconsistent lifecycle facts")
        if identity in active:
            raise BasisConstructionError(f"duplicate active contract {identity}")
        active[identity] = row
    return active


def indexed_daily(
    rows: Sequence[RawRecord], as_of: str, *, require_exchange: bool
) -> dict[str, RawRecord]:
    indexed: dict[str, RawRecord] = {}
    for row in rows:
        identity = required_text(row, "ts_code")
        if required_date(row, "trade_date") != as_of:
            raise BasisConstructionError(f"daily row {identity} has a different observation")
        if require_exchange and required_text(row, "exchange") != "CFFEX":
            raise BasisConstructionError(f"daily row {identity} has inconsistent exchange")
        if identity in indexed:
            raise BasisConstructionError(f"duplicate daily row for {identity}")
        indexed[identity] = row
    return indexed


def selected_premium(row: RawRecord, price_type: PriceType) -> float | None:
    value = row.get(price_type.value)
    return None if value is None else numeric(value, f"option {price_type.value}")


def underlying_reference(
    rows: Sequence[RawRecord], as_of: str, price_type: PriceType
) -> UnderlyingReference:
    matches = [
        row
        for row in rows
        if row.get("ts_code") == UNDERLYING_ID and row.get("trade_date") == as_of
    ]
    if len(matches) != 1:
        raise BasisConstructionError("exactly one admitted underlying observation is required")
    price = numeric(matches[0].get(price_type.value), f"underlying {price_type.value}")
    if price <= 0:
        raise BasisConstructionError("underlying selected price must be strictly positive")
    if len(rows) != 1:
        raise BasisConstructionError("index_daily Raw contains unexpected observations")
    return UnderlyingReference(UNDERLYING_ID, price)


def futures_by_expiry(
    basic_rows: Sequence[RawRecord],
    daily_rows: Sequence[RawRecord],
    as_of: str,
    price_type: PriceType,
    expiries: set[str],
) -> dict[str, FuturesReference | None]:
    candidates: dict[str, list[str]] = {expiry: [] for expiry in expiries}
    seen: set[str] = set()
    for row in basic_rows:
        identity = required_text(row, "ts_code")
        if identity in seen:
            raise BasisConstructionError(f"duplicate IM basic contract {identity}")
        seen.add(identity)
        if required_text(row, "exchange") != "CFFEX" or required_text(row, "fut_code") != "IM":
            raise BasisConstructionError(f"IM basic Raw has an out-of-scope contract {identity}")
        listed = required_date(row, "list_date")
        delisted = required_date(row, "delist_date")
        if listed > delisted:
            raise BasisConstructionError(f"IM contract {identity} has inverted lifecycle")
        if listed <= as_of <= delisted and delisted in candidates:
            candidates[delisted].append(identity)

    required_codes = {identity for matches in candidates.values() for identity in matches}
    daily: dict[str, RawRecord] = {}
    for row in daily_rows:
        identity_value = row.get("ts_code")
        if identity_value not in required_codes:
            continue
        identity = required_text(row, "ts_code")
        if required_date(row, "trade_date") != as_of:
            raise BasisConstructionError(
                f"matched IM contract {identity} has a different observation"
            )
        if identity in daily:
            raise BasisConstructionError(f"duplicate daily row for matched IM {identity}")
        daily[identity] = row
    references: dict[str, FuturesReference | None] = {}
    for expiry, matches in candidates.items():
        if len(matches) > 1:
            raise BasisConstructionError(f"MO expiry {expiry} has multiple active IM matches")
        if not matches:
            references[expiry] = None
            continue
        identity = matches[0]
        if identity not in daily:
            raise BasisConstructionError(f"matched IM contract {identity} has no daily row")
        price = numeric(
            daily[identity].get(price_type.value),
            f"futures {identity} {price_type.value}",
        )
        references[expiry] = FuturesReference(identity, price)
    return references


def construct_basis(
    as_of: str, option_product: OptionProduct, price_type: PriceType, raw_dir: Path
) -> OptionMarketBasis:
    """Deterministically construct the complete option-market fact boundary."""
    if option_product is not OptionProduct.MO:
        raise BasisConstructionError("only MO is supported")
    underlying = underlying_reference(raw_rows(raw_dir, "index_daily"), as_of, price_type)
    contracts = active_options(raw_rows(raw_dir, "mo_option_basic"), as_of)
    daily = indexed_daily(raw_rows(raw_dir, "mo_option_daily"), as_of, require_exchange=True)
    if set(daily) != set(contracts):
        missing = sorted(set(contracts) - set(daily))
        extra = sorted(set(daily) - set(contracts))
        raise BasisConstructionError(
            f"MO daily completeness mismatch; missing={missing}, extra={extra}"
        )

    expiries = {required_date(row, "maturity_date") for row in contracts.values()}
    futures = futures_by_expiry(
        raw_rows(raw_dir, "im_futures_basic"),
        raw_rows(raw_dir, "im_futures_daily"),
        as_of,
        price_type,
        expiries,
    )
    options: list[OptionObservation] = []
    for identity, contract in contracts.items():
        side = required_text(contract, "call_put")
        try:
            option_type = {"C": OptionType.CALL, "P": OptionType.PUT}[side]
        except KeyError as exc:
            raise BasisConstructionError(
                f"contract {identity} has invalid call_put={side!r}"
            ) from exc
        expiry = required_date(contract, "maturity_date")
        options.append(
            OptionObservation(
                instrument_id=identity,
                option_type=option_type,
                expiry_date=expiry,
                strike=numeric(contract.get("exercise_price"), "exercise_price"),
                premium=selected_premium(daily[identity], price_type),
                futures=futures[expiry],
            )
        )
    return OptionMarketBasis(
        observation=ObservationAnchor(as_of),
        option_product=option_product,
        price_type=price_type,
        underlying=underlying,
        options=tuple(options),
    )
