"""Shared IM-basis predictor and empirical quantile semantics."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from market_snapshot.products.csi1000_im_basis_history import (
    CSI1000IMBasisHistoryResult,
    IMBasisObservation,
)

SLOTS = ("M0", "M1", "Q1", "Q2")
NON_FRONT_SLOTS = ("M1", "Q1", "Q2")


class ResearchInputError(ValueError):
    """A Snapshot public result violates the required semantic contract."""


@dataclass(frozen=True)
class DailyIMBasis:
    trade_date: str
    underlying_close: float
    annualized_basis_by_slot: dict[str, float]
    non_front_mean_basis: float


def linear_quantile(values: Sequence[float], probability: float) -> float:
    """Empirical quantile with linear interpolation (NumPy method='linear')."""
    if not values:
        raise ResearchInputError("an empirical quantile needs a non-empty sample.")
    if not 0 <= probability <= 1:
        raise ValueError("probability must be between 0 and 1.")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def daily_im_basis(result: CSI1000IMBasisHistoryResult) -> tuple[DailyIMBasis, ...]:
    """Validate the public panel and calculate its shared daily predictor."""
    grouped: dict[str, list[IMBasisObservation]] = {}
    for observation in result.observations:
        grouped.setdefault(observation.trade_date, []).append(observation)
    if not grouped:
        raise ResearchInputError("Snapshot result has no observations.")

    daily: list[DailyIMBasis] = []
    for trade_date in sorted(grouped):
        by_slot: dict[str, IMBasisObservation] = {}
        underlying_values: set[float] = set()
        for observation in grouped[trade_date]:
            slot = observation.contract_slot
            if slot in by_slot:
                raise ResearchInputError(f"duplicate {slot} observation on {trade_date}.")
            if slot not in SLOTS:
                raise ResearchInputError(f"unknown contract slot {slot!r} on {trade_date}.")
            if not math.isfinite(observation.annualized_basis_pct):
                raise ResearchInputError(f"non-finite basis on {trade_date}.")
            if not math.isfinite(observation.underlying_close) or observation.underlying_close == 0:
                raise ResearchInputError(f"unusable underlying close on {trade_date}.")
            by_slot[slot] = observation
            underlying_values.add(observation.underlying_close)
        if set(by_slot) != set(SLOTS):
            raise ResearchInputError(f"incomplete IM slot panel on {trade_date}.")
        if len(underlying_values) != 1:
            raise ResearchInputError(f"inconsistent underlying close on {trade_date}.")
        basis_by_slot = {slot: by_slot[slot].annualized_basis_pct for slot in SLOTS}
        predictor = math.fsum(basis_by_slot[slot] for slot in NON_FRONT_SLOTS) / 3
        daily.append(
            DailyIMBasis(
                trade_date=trade_date,
                underlying_close=underlying_values.pop(),
                annualized_basis_by_slot=basis_by_slot,
                non_front_mean_basis=predictor,
            )
        )
    return tuple(daily)
