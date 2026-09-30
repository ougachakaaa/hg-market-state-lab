"""Study request, canonical input identity, and public Snapshot queries."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from market_snapshot.products.index_daily_history import IndexDailyHistoryRequest
from market_snapshot.products.mo_option_chain.service import ChainQuery, OptionProduct, PriceType

STUDY_ID = "mo-option-risk-premium-baseline"
DEFAULT_DTE_TARGETS = (10, 20, 30, 40, 50, 60)
DEFAULT_MONEYNESS_TARGETS = tuple(Decimal(x) for x in ("0", "0.05", "0.10", "0.15", "0.20"))
DTE_TOLERANCE = 5
MONEYNESS_TOLERANCE = Decimal("0.025")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


class MOOptionRiskPremiumStudyError(ValueError):
    """A valid Study execution cannot produce complete evidence."""


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
