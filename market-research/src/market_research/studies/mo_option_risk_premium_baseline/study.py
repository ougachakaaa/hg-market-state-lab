"""Study-owned request, observation construction, aggregation, and provenance."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from statistics import mean, median
from typing import Any

from market_snapshot.products.index_daily_history import (
    IndexDailyHistoryRequest,
    IndexDailyHistoryResult,
)
from market_snapshot.products.mo_option_chain.service import (
    ChainQuery,
    OptionChain,
    OptionPoint,
    OptionProduct,
    PriceType,
)

STUDY_ID = "mo-option-risk-premium-baseline"
DEFAULT_DTE_TARGETS = (10, 20, 30, 40, 50, 60)
DEFAULT_MONEYNESS_TARGETS = tuple(Decimal(x) for x in ("0", "0.05", "0.10", "0.15", "0.20"))
DTE_TOLERANCE = 5
MONEYNESS_TOLERANCE = Decimal("0.025")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_MEASURES = (
    "entry_premium_proxy",
    "expiry_payoff_proxy",
    "seller_compensation_points",
    "seller_compensation_ratio",
    "annualized_compensation_ratio",
)
_COMPENSATION = (
    "seller_compensation_points",
    "seller_compensation_ratio",
    "annualized_compensation_ratio",
)


class MOOptionRiskPremiumStudyError(ValueError):
    """A valid Study execution cannot produce complete evidence."""


class SnapshotContractError(MOOptionRiskPremiumStudyError):
    """A supplied public Snapshot result contradicts its application contract."""


def _date(value: object, name: str) -> date:
    if not isinstance(value, str) or _ISO_DATE.fullmatch(value) is None:
        raise MOOptionRiskPremiumStudyError(f"{name} must be a valid YYYY-MM-DD date.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise MOOptionRiskPremiumStudyError(f"{name} must be a valid YYYY-MM-DD date.") from exc


def decimal_text(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    plain = format(value, "f")
    return plain.rstrip("0").rstrip(".") if "." in plain else plain


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, Decimal | int | float | str):
        raise MOOptionRiskPremiumStudyError("moneyness targets must be finite decimals >= 0.")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise MOOptionRiskPremiumStudyError(
            "moneyness targets must be finite decimals >= 0."
        ) from exc
    if not result.is_finite() or result < 0:
        raise MOOptionRiskPremiumStudyError("moneyness targets must be finite decimals >= 0.")
    return Decimal(decimal_text(result))


@dataclass(frozen=True)
class MOOptionRiskPremiumRequest:
    start_expiry_date: str
    end_expiry_date: str
    dte_targets: tuple[int, ...] = DEFAULT_DTE_TARGETS
    moneyness_targets: tuple[Decimal, ...] = DEFAULT_MONEYNESS_TARGETS

    def __post_init__(self) -> None:
        start = _date(self.start_expiry_date, "start_expiry_date")
        end = _date(self.end_expiry_date, "end_expiry_date")
        if start > end:
            raise MOOptionRiskPremiumStudyError(
                "start_expiry_date must not exceed end_expiry_date."
            )
        try:
            dtes = tuple(self.dte_targets)
            money = tuple(self.moneyness_targets)
        except TypeError as exc:
            raise MOOptionRiskPremiumStudyError("target sets must be non-empty.") from exc
        if not dtes or any(type(x) is not int or x <= 0 for x in dtes):
            raise MOOptionRiskPremiumStudyError("DTE targets must be non-empty positive integers.")
        if not money:
            raise MOOptionRiskPremiumStudyError("moneyness targets must be non-empty.")
        object.__setattr__(self, "dte_targets", tuple(sorted(set(dtes))))
        object.__setattr__(self, "moneyness_targets", tuple(sorted({_decimal(x) for x in money})))
        try:
            start - timedelta(days=max(dtes) + DTE_TOLERANCE)
        except (OverflowError, ValueError) as exc:
            raise MOOptionRiskPremiumStudyError("discovery start is outside the calendar.") from exc


def canonical_request(request: MOOptionRiskPremiumRequest) -> dict[str, object]:
    return {
        "start_expiry_date": request.start_expiry_date,
        "end_expiry_date": request.end_expiry_date,
        "dte_targets": list(request.dte_targets),
        "moneyness_targets": [decimal_text(x) for x in request.moneyness_targets],
    }


def _canonical_json(value: object, *, sort_keys: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
        sort_keys=sort_keys,
    )


def _digest(value: object, *, sort_keys: bool = False) -> str:
    return hashlib.sha256(_canonical_json(value, sort_keys=sort_keys).encode("utf-8")).hexdigest()


def run_key(request: MOOptionRiskPremiumRequest) -> str:
    return (
        f"{request.start_expiry_date}__{request.end_expiry_date}__"
        f"{_digest(canonical_request(request))}"
    )


def index_request(request: MOOptionRiskPremiumRequest) -> IndexDailyHistoryRequest:
    start = _date(request.start_expiry_date, "start_expiry_date")
    discovery_start = start - timedelta(days=max(request.dte_targets) + DTE_TOLERANCE)
    return IndexDailyHistoryRequest(
        ts_code="000852.SH",
        start_trade_date=discovery_start.isoformat(),
        end_trade_date=request.end_expiry_date,
        pre_start_observation_count=0,
    )


def chain_query(trade_date: str, price_type: PriceType) -> ChainQuery:
    return ChainQuery(trade_date, OptionProduct.MO, price_type)


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


@dataclass(frozen=True)
class StudyResult:
    request: MOOptionRiskPremiumRequest
    run_key: str
    cells: tuple[OutcomeCell, ...]
    summary: tuple[dict[str, Any], ...]
    provenance: dict[str, Any]
    expected_expiry_count: int


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


def _chain_facts(chain: OptionChain) -> dict[str, object]:
    return {
        "target_trade_date": chain.target_trade_date,
        "option_product": chain.option_product.value,
        "price_type": chain.price_type.value,
        "underlying": {
            "instrument_id": chain.underlying.instrument_id,
            "price": chain.underlying.price,
        },
        "expiries": [
            {
                "expiry_date": group.expiry_date,
                "calls": [
                    asdict(x)
                    for x in sorted(group.calls, key=lambda x: (x.strike, x.instrument_id))
                ],
                "puts": [
                    asdict(x) for x in sorted(group.puts, key=lambda x: (x.strike, x.instrument_id))
                ],
            }
            for group in sorted(chain.expiries, key=lambda x: x.expiry_date)
        ],
    }


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    left = math.floor(position)
    right = math.ceil(position)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def _summarize(
    cells: tuple[OutcomeCell, ...], request: MOOptionRiskPremiumRequest, expiry_count: int
) -> tuple[dict[str, Any], ...]:
    buckets: dict[tuple[int, str, str], list[OutcomeCell]] = defaultdict(list)
    for cell in cells:
        buckets[(cell.target_dte, cell.option_type, cell.moneyness_target)].append(cell)
    summary: list[dict[str, Any]] = []
    for dte in request.dte_targets:
        for kind in ("CALL", "PUT"):
            for target in request.moneyness_targets:
                name = decimal_text(target)
                group = buckets[(dte, kind, name)]
                valid = [cell for cell in group if not cell.exclusion_reasons]
                unique = len({cell.expiry_date for cell in valid})
                reasons = Counter(reason for cell in group for reason in cell.exclusion_reasons)
                record: dict[str, Any] = {
                    "target_dte": dte,
                    "option_type": kind,
                    "moneyness_target": name,
                    "sample_count": len(valid),
                    "unique_expiry_count": unique,
                    "expected_expiry_count": expiry_count,
                    "unique_expiry_coverage_count": unique,
                    "unique_expiry_coverage_ratio": unique / expiry_count,
                    "excluded_cell_count": len(group) - len(valid),
                    "reason_counts": dict(sorted(reasons.items())),
                    "defined_by": ["DteCompensationProfile", "MoneynessCompensationProfile"],
                }
                for field in _MEASURES:
                    values = [getattr(cell, field) for cell in valid]
                    numeric = [value for value in values if value is not None]
                    record[f"{field}_mean"] = mean(numeric) if numeric else None
                    record[f"{field}_median"] = median(numeric) if numeric else None
                    if field in _COMPENSATION:
                        record[f"{field}_min"] = min(numeric) if numeric else None
                        for label, p in (
                            ("p05", 0.05),
                            ("p25", 0.25),
                            ("p50", 0.5),
                            ("p75", 0.75),
                            ("p95", 0.95),
                        ):
                            record[f"{field}_{label}"] = (
                                record[f"{field}_median"]
                                if label == "p50"
                                else _quantile(numeric, p)
                                if numeric
                                else None
                            )
                points = [cell.seller_compensation_points for cell in valid]
                for label, predicate in (
                    ("positive", lambda x: x > 0),
                    ("negative", lambda x: x < 0),
                    ("zero", lambda x: x == 0),
                ):
                    record[f"{label}_frequency"] = (
                        sum(predicate(x) for x in points if x is not None) / len(valid)
                        if valid
                        else None
                    )
                summary.append(record)
    return tuple(summary)


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


def compute(
    request: MOOptionRiskPremiumRequest,
    index: IndexDailyHistoryResult,
    chains: Mapping[str, tuple[OptionChain, OptionChain]],
) -> StudyResult:
    """Build all expected observations and both Analysis views from public facts."""
    index_query = index_request(request)
    _validate_index(index_query, index)
    dates = tuple(row.trade_date for row in index.sample_observations)
    if set(chains) != set(dates):
        raise SnapshotContractError("MO Chain results do not cover the actual index trade dates.")
    closes = {row.trade_date: row.close for row in index.sample_observations}
    observable: dict[str, list[str]] = defaultdict(list)
    chain_facts: list[dict[str, object]] = []
    for trade_date in dates:
        high, low = chains[trade_date]
        _validate_chains(trade_date, high, low)
        for group in high.expiries:
            if request.start_expiry_date <= group.expiry_date <= request.end_expiry_date:
                observable[group.expiry_date].append(trade_date)
        chain_facts.extend((_chain_facts(high), _chain_facts(low)))
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
    index_facts = {
        "query": asdict(index_query),
        "sample_observations": [
            {"trade_date": row.trade_date, "close": row.close} for row in index.sample_observations
        ],
    }
    provenance = {
        "index_daily_history": {
            "query": asdict(index_query),
            "content_sha256": _digest(index_facts, sort_keys=True),
        },
        "mo_option_chain": {
            "queries": [
                asdict(chain_query(trade_date, kind))
                for trade_date in dates
                for kind in (PriceType.HIGH, PriceType.LOW)
            ],
            "content_sha256": _digest(chain_facts, sort_keys=True),
        },
    }
    provenance["observation_artifact_sha256"] = _digest(
        {
            "observation": "ExpiryDteOptionOutcome",
            "request": canonical_request(request),
            "upstream": provenance,
        },
        sort_keys=True,
    )
    return StudyResult(
        request,
        run_key(request),
        records,
        _summarize(records, request, len(observable)),
        provenance,
        len(observable),
    )
