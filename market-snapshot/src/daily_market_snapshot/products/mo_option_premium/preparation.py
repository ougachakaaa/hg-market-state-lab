"""Canonical Annualized Premium Point Preparation."""

from __future__ import annotations

import math
from datetime import date

from .models import AnnualizedPremiumPoint, CalculationBasis, OptionMarketBasis


class PointPreparationError(Exception):
    """A market basis cannot produce consistent analytical Points."""


def prepare_points(basis: OptionMarketBasis) -> tuple[AnnualizedPremiumPoint, ...]:
    """Calculate DTE and both authority-defined annualized premium metrics."""
    if not math.isfinite(basis.underlying.price) or basis.underlying.price <= 0:
        raise PointPreparationError("underlying selected price must be strictly positive")
    try:
        observation_date = date.fromisoformat(basis.observation.as_of)
    except ValueError as exc:
        raise PointPreparationError("observation must be a valid trade date") from exc
    calculation_basis = CalculationBasis()
    points: list[AnnualizedPremiumPoint] = []
    seen_instruments: set[str] = set()
    for option in basis.options:
        if not option.instrument_id:
            raise PointPreparationError("option instrument identity must be present")
        if option.instrument_id in seen_instruments:
            raise PointPreparationError(f"duplicate option instrument {option.instrument_id}")
        seen_instruments.add(option.instrument_id)
        if not math.isfinite(option.strike):
            raise PointPreparationError(f"option {option.instrument_id} has invalid strike")
        if option.premium is not None and not math.isfinite(option.premium):
            raise PointPreparationError(f"option {option.instrument_id} has invalid premium")
        if option.futures is not None and (
            not option.futures.instrument_id or not math.isfinite(option.futures.price)
        ):
            raise PointPreparationError(
                f"option {option.instrument_id} has invalid futures reference"
            )
        try:
            expiry = date.fromisoformat(option.expiry_date)
        except ValueError as exc:
            raise PointPreparationError("expiry must be a valid date") from exc
        dte = (expiry - observation_date).days + 1
        if dte <= 0:
            raise PointPreparationError(f"post-expiry option {option.instrument_id}")
        annualized = None if option.premium is None else option.premium * 365 / dte
        seller_yield = None if annualized is None else annualized / basis.underlying.price
        if annualized is not None and not math.isfinite(annualized):
            raise PointPreparationError(
                f"option {option.instrument_id} produces non-finite derived metrics"
            )
        if seller_yield is not None and not math.isfinite(seller_yield):
            raise PointPreparationError(
                f"option {option.instrument_id} produces non-finite derived metrics"
            )
        points.append(
            AnnualizedPremiumPoint(
                observation=basis.observation,
                instrument_id=option.instrument_id,
                option_product=basis.option_product,
                option_type=option.option_type,
                expiry_date=option.expiry_date,
                strike=option.strike,
                price_type=basis.price_type,
                premium=option.premium,
                underlying=basis.underlying,
                futures=option.futures,
                calculation_basis=calculation_basis,
                dte=dte,
                annualized_premium_points=annualized,
                annualized_seller_premium_yield=seller_yield,
            )
        )
    return tuple(points)
