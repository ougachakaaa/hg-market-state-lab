"""Independent Daily futures–spot calculation; no I/O or pair population changes."""

from dataclasses import dataclass
from datetime import date
from math import isfinite, log
from typing import Literal

from data_lake.datasets.tushare_equity_index_futures import FuturesDailyRow
from market_research.descriptive.cases.futures_basis import DailyUniverseEvidence, Slot

from .daily_index import DailyUnderlyingIndexEvidence, DailyUnderlyingIndexReference
from .inputs import PreparedCalendarSpreadInputs
from .observations import CalendarSpreadDay, ExpiryStage

SPOT_DEFINITION = "daily_futures_spot_definition_v1"
SLOTS: tuple[Slot, ...] = ("M0", "M1", "Q1", "Q2")
SpotOutcome = Literal["valid", "not_applicable", "excluded", "error"]
SpotReason = Literal[
    "no_active_contract",
    "index_reference_unavailable",
    "nonpositive_close",
    "expiry_day",
    "calculation_failure",
]


@dataclass(frozen=True, slots=True)
class DailyFuturesSpotComparison:
    product_code: str
    trade_date: date
    slot: Slot
    futures: FuturesDailyRow | None
    underlying_index: DailyUnderlyingIndexReference
    remaining_days: int | None
    expiry_stage: ExpiryStage | None
    signed_spread: float | None
    annualized_point_spread: float | None
    annualized_spread_ratio: float | None
    outcome: SpotOutcome
    reason: SpotReason | None
    failure_category: str | None
    source_evidence: DailyUniverseEvidence
    reference_evidence: DailyUnderlyingIndexEvidence
    calculation_exception: Exception | None = None
    definition_version: Literal["daily_futures_spot_definition_v1"] = SPOT_DEFINITION


def _price(value: object) -> float:
    if type(value) not in (int, float):
        raise ValueError("Expected finite binary64 Close")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError("Expected finite binary64 Close") from exc
    if not isfinite(number):
        raise ValueError("Expected finite binary64 Close")
    return number


def _finite(value: float) -> float:
    if not isfinite(value):
        raise ArithmeticError("Nonfinite futures–spot intermediate")
    return value


def construct_daily_spot_comparisons(
    day: CalendarSpreadDay,
    prepared: PreparedCalendarSpreadInputs,
    reference: DailyUnderlyingIndexReference,
    evidence: DailyUnderlyingIndexEvidence,
) -> tuple[DailyFuturesSpotComparison, ...]:
    """Reuse validated daily inputs; isolate only new numerical failures per Slot."""
    if day.status == "closed":
        return ()
    if day.resolution is None:
        raise ValueError("Missing Daily Slot resolution")
    if reference.trade_date != day.trade_date:
        raise ValueError("Mismatched reference date")
    by_code = {
        row.contract_code: row
        for row in prepared.futures_export.records
        if row.trade_date == day.trade_date
    }
    mappings = {mapping.slot: mapping.contract for mapping in day.resolution.mappings}
    results = []
    for slot in SLOTS:
        contract = mappings[slot]
        row = None if contract is None else by_code[contract.contract_code]
        dte = None if row is None else (row.delist_date - day.trade_date).days
        if dte is not None and dte < 0:
            raise ValueError("Negative remaining contract life")
        stage: ExpiryStage | None = (
            None if dte is None else "0_7" if dte <= 7 else "8_21" if dte <= 21 else "22_plus"
        )
        spread = point = ratio = None
        category = None
        exception = None
        outcome: SpotOutcome = "not_applicable"
        reason: SpotReason | None
        if row is None:
            reason = "no_active_contract"
        else:
            if row.underlying_index_code != reference.index_code:
                raise ValueError("Mismatched underlying identity")
            f = _price(row.close)
            if reference.availability != "available":
                reason = "index_reference_unavailable"
                category = reference.failure_category
            else:
                s = _price(reference.close)
                if f <= 0 or s <= 0:
                    outcome, reason = "excluded", "nonpositive_close"
                else:
                    try:
                        spread = _finite(f - s)
                        if dte == 0:
                            reason = "expiry_day"
                        else:
                            assert dte is not None
                            point = _finite(_finite(spread * 365) / dte)
                            price_ratio = _finite(f / s)
                            ratio = _finite(_finite(365 * _finite(log(price_ratio))) / dte)
                            outcome, reason = "valid", None
                    except (ArithmeticError, ValueError) as exc:
                        spread = point = ratio = None
                        outcome, reason = "error", "calculation_failure"
                        category, exception = "calculation_failure", exc
        results.append(
            DailyFuturesSpotComparison(
                prepared.request.product_code,
                day.trade_date,
                slot,
                row,
                reference,
                dte,
                stage,
                spread,
                point,
                ratio,
                outcome,
                reason,
                category,
                day.resolution.evidence,
                evidence,
                exception,
            )
        )
    return tuple(results)
