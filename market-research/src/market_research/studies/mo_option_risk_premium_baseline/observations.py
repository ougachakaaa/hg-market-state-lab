"""Construct ExpiryDteOptionOutcome cells from public Snapshot facts."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
)
from market_snapshot.products.mo_option_chain.service import (
    OptionChain,
    OptionPoint,
    OptionProduct,
    PriceType,
)

from .inputs import (
    DTE_TOLERANCE,
    MONEYNESS_TOLERANCE,
    MOOptionRiskPremiumRequest,
    MOOptionRiskPremiumStudyError,
    _date,
    decimal_text,
    index_request,
)


class SnapshotContractError(MOOptionRiskPremiumStudyError):
    """A supplied public Snapshot result contradicts its application contract."""


@dataclass(frozen=True)
class OutcomeCell:
    expiry_date: str
    target_dte: int
    option_type: str
    moneyness_target: str
    exclusion_reasons: tuple[str, ...] = ()
    entry_trade_date: str | None = None
    actual_dte: int | None = None
    dte_error: int | None = None
    instrument_id: str | None = None
    strike: float | None = None
    actual_moneyness: str | None = None
    moneyness_error: str | None = None
    entry_option_high: float | None = None
    entry_option_low: float | None = None
    entry_premium_proxy: float | None = None
    entry_underlying_high: float | None = None
    entry_underlying_low: float | None = None
    entry_underlying_proxy: float | None = None
    expiry_underlying_proxy: float | None = None
    expiry_payoff_proxy: float | None = None
    seller_compensation_points: float | None = None
    seller_compensation_ratio: float | None = None
    annualized_compensation_ratio: float | None = None


def _numeric(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value)


def _validate_index(request: IndexDailyHistoryRequest, result: IndexDailyHistoryResult) -> None:
    if (
        result.ts_code != request.ts_code
        or result.requested_start_trade_date != request.start_trade_date
        or result.requested_end_trade_date != request.end_trade_date
        or result.requested_pre_start_observation_count != 0
        or result.warmup_observations
        or not result.sample_observations
    ):
        raise SnapshotContractError("Index Daily History result identity or sample is invalid.")
    seen: set[str] = set()
    for row in result.sample_observations:
        try:
            _date(row.trade_date, "index trade_date")
        except MOOptionRiskPremiumStudyError as exc:
            raise SnapshotContractError("Index Daily History has an invalid trade date.") from exc
        if (
            row.trade_date in seen
            or not request.start_trade_date <= row.trade_date <= request.end_trade_date
            or not _numeric(row.close)
            or row.close <= 0
            or (row.volume is not None and (not _numeric(row.volume) or row.volume < 0))
        ):
            raise SnapshotContractError("Index Daily History result violates its public contract.")
        seen.add(row.trade_date)
    if tuple(sorted(seen)) != tuple(row.trade_date for row in result.sample_observations):
        raise SnapshotContractError("Index Daily History sample dates are not ordered.")


def _structure(chain: OptionChain) -> tuple[tuple[object, ...], ...]:
    structure: list[tuple[object, ...]] = []
    expiry_seen: set[str] = set()
    all_ids: set[str] = set()
    for group in chain.expiries:
        try:
            _date(group.expiry_date, "chain expiry_date")
        except MOOptionRiskPremiumStudyError as exc:
            raise SnapshotContractError("MO Chain has an invalid expiry date.") from exc
        if group.expiry_date in expiry_seen:
            raise SnapshotContractError("MO Chain has duplicate expiry groups.")
        expiry_seen.add(group.expiry_date)
        for option_type, points in (("CALL", group.calls), ("PUT", group.puts)):
            ids: set[str] = set()
            members: list[tuple[str, float]] = []
            for point in points:
                if not isinstance(point.instrument_id, str) or not point.instrument_id:
                    raise SnapshotContractError("MO Chain has an invalid instrument identity.")
                if (
                    point.instrument_id in ids
                    or point.instrument_id in all_ids
                    or not _numeric(point.strike)
                ):
                    raise SnapshotContractError(
                        "MO Chain has duplicate or invalid structural facts."
                    )
                ids.add(point.instrument_id)
                all_ids.add(point.instrument_id)
                members.append((point.instrument_id, point.strike))
            if members != sorted(members, key=lambda x: (x[1], x[0])):
                raise SnapshotContractError("MO Chain contract order violates its public contract.")
            structure.append((group.expiry_date, option_type, tuple(sorted(members))))
    if tuple(group.expiry_date for group in chain.expiries) != tuple(sorted(expiry_seen)):
        raise SnapshotContractError("MO Chain expiry order violates its public contract.")
    return tuple(sorted(structure))


def _validate_chains(trade_date: str, high: OptionChain, low: OptionChain) -> None:
    for chain, kind in ((high, PriceType.HIGH), (low, PriceType.LOW)):
        if (
            chain.target_trade_date != trade_date
            or chain.option_product is not OptionProduct.MO
            or chain.price_type is not kind
            or chain.underlying.instrument_id != "000852.SH"
            or not _numeric(chain.underlying.price)
        ):
            raise SnapshotContractError("MO Chain result identity or underlying is invalid.")
    if _structure(high) != _structure(low):
        raise SnapshotContractError(f"MO high/low chain structure differs on {trade_date}.")


def _selected_cell(
    expiry: str,
    dte: int,
    kind: str,
    target: Decimal,
    entry: str | None,
    high: OptionChain | None,
    low: OptionChain | None,
    close: float | None,
) -> OutcomeCell:
    data: dict[str, Any] = {
        "expiry_date": expiry,
        "target_dte": dte,
        "option_type": kind,
        "moneyness_target": decimal_text(target),
    }
    reasons: list[str] = []
    if entry is None:
        reasons.append("no_eligible_entry_date")
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    actual_dte = (_date(expiry, "expiry") - _date(entry, "entry")).days
    data.update(entry_trade_date=entry, actual_dte=actual_dte, dte_error=actual_dte - dte)
    if actual_dte <= 0:
        reasons.append("invalid_expiry_contract_relationship")
    if abs(actual_dte - dte) > DTE_TOLERANCE:
        reasons.append("dte_out_of_tolerance")
    if reasons:
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    assert high is not None and low is not None
    data.update(
        entry_underlying_high=high.underlying.price, entry_underlying_low=low.underlying.price
    )
    underlying_ok = (
        _numeric(high.underlying.price)
        and _numeric(low.underlying.price)
        and 0 < low.underlying.price <= high.underlying.price
    )
    if not underlying_ok:
        reasons.append("invalid_entry_underlying")
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    proxy = (high.underlying.price + low.underlying.price) / 2
    if not math.isfinite(proxy) or proxy <= 0:
        reasons.append("invalid_entry_underlying")
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    data["entry_underlying_proxy"] = proxy
    high_group = next(group for group in high.expiries if group.expiry_date == expiry)
    low_group = next(group for group in low.expiries if group.expiry_date == expiry)
    high_points = high_group.calls if kind == "CALL" else high_group.puts
    low_points = low_group.calls if kind == "CALL" else low_group.puts
    low_by_id = {point.instrument_id: point for point in low_points}
    if not high_points or not any(
        _numeric(point.strike) and point.strike > 0 for point in high_points
    ):
        reasons.append("no_positive_strike_contract")
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    candidates: list[tuple[Decimal, OptionPoint]] = []
    decimal_proxy = Decimal(str(proxy))
    for point in high_points:
        if not _numeric(point.strike) or point.strike <= 0:
            continue
        decimal_strike = Decimal(str(point.strike))
        distance = (
            (decimal_strike - decimal_proxy) if kind == "CALL" else (decimal_proxy - decimal_strike)
        ) / decimal_proxy
        if distance >= 0:
            candidates.append((distance, point))
    if not candidates:
        reasons.append("no_atm_or_otm_contract")
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    actual, selected = min(
        candidates, key=lambda x: (abs(x[0] - target), -x[0], x[1].instrument_id)
    )
    selected_low = low_by_id[selected.instrument_id]
    data.update(
        instrument_id=selected.instrument_id,
        strike=selected.strike,
        actual_moneyness=decimal_text(actual),
        moneyness_error=decimal_text(actual - target),
        entry_option_high=selected.price,
        entry_option_low=selected_low.price,
    )
    if abs(actual - target) > MONEYNESS_TOLERANCE:
        reasons.append("moneyness_out_of_tolerance")
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    high_price, low_price = selected.price, selected_low.price
    if (
        high_price is None
        or low_price is None
        or not _numeric(high_price)
        or not _numeric(low_price)
        or not 0 <= low_price <= high_price
    ):
        reasons.append("invalid_selected_option_price")
    if close is None or not _numeric(close) or close <= 0:
        reasons.append("missing_expiry_close")
    else:
        data["expiry_underlying_proxy"] = close
    if reasons:
        return OutcomeCell(**data, exclusion_reasons=tuple(reasons))
    assert high_price is not None and low_price is not None and close is not None
    premium = (high_price + low_price) / 2
    payoff = max(close - selected.strike, 0) if kind == "CALL" else max(selected.strike - close, 0)
    points = premium - payoff
    ratio = points / proxy
    annual = ratio * 365 / actual_dte
    if not all(map(math.isfinite, (premium, payoff, points, ratio, annual))):
        raise SnapshotContractError("derived compensation is not finite.")
    data.update(
        entry_premium_proxy=premium,
        expiry_payoff_proxy=payoff,
        seller_compensation_points=points,
        seller_compensation_ratio=ratio,
        annualized_compensation_ratio=annual,
    )
    return OutcomeCell(**data)


def build_panel(
    request: MOOptionRiskPremiumRequest,
    index: IndexDailyHistoryResult,
    chains: Mapping[str, tuple[OptionChain, OptionChain]],
) -> tuple[tuple[OutcomeCell, ...], int]:
    """Build every expected cell, including exclusions, and count real expiries."""
    index_query = index_request(request)
    _validate_index(index_query, index)
    dates = tuple(row.trade_date for row in index.sample_observations)
    if set(chains) != set(dates):
        raise SnapshotContractError("MO Chain results do not cover the actual index trade dates.")
    closes = {row.trade_date: row.close for row in index.sample_observations}
    observable: dict[str, list[str]] = defaultdict(list)
    for trade_date in dates:
        high, low = chains[trade_date]
        _validate_chains(trade_date, high, low)
        for group in high.expiries:
            if request.start_expiry_date <= group.expiry_date <= request.end_expiry_date:
                observable[group.expiry_date].append(trade_date)
    if not observable:
        raise MOOptionRiskPremiumStudyError("no MO expiry was discovered in the requested range.")
    cells: list[OutcomeCell] = []
    for expiry in sorted(observable):
        candidates = [x for x in observable[expiry] if x < expiry]
        for dte in request.dte_targets:
            entry = (
                min(
                    candidates,
                    key=lambda x: (
                        abs((_date(expiry, "expiry") - _date(x, "entry")).days - dte),
                        -(_date(expiry, "expiry") - _date(x, "entry")).days,
                    ),
                )
                if candidates
                else None
            )
            entry_high: OptionChain | None
            entry_low: OptionChain | None
            entry_high, entry_low = chains[entry] if entry is not None else (None, None)
            for kind in ("CALL", "PUT"):
                for target in request.moneyness_targets:
                    cells.append(
                        _selected_cell(
                            expiry,
                            dte,
                            kind,
                            target,
                            entry,
                            entry_high,
                            entry_low,
                            closes.get(expiry),
                        )
                    )
    records = tuple(cells)
    if not any(not cell.exclusion_reasons for cell in records):
        raise MOOptionRiskPremiumStudyError(
            "the discovered expiry population has zero valid observations."
        )
    return records, len(observable)
