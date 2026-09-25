"""Canonical multidimensional Premium Point Preparation."""

from __future__ import annotations

import math
from datetime import date

from .models import (
    CalculationBasis,
    MetricValues,
    OptionMarketBasis,
    OptionObservation,
    OptionType,
    PremiumMetrics,
    PremiumPoint,
    TimeNormalizedMetrics,
    ValueMetrics,
)


class PointPreparationError(Exception):
    """A market basis cannot produce consistent analytical Points."""


def prepare_points(basis: OptionMarketBasis) -> tuple[PremiumPoint, ...]:
    """Calculate every coordinate in the authority-defined metric space."""
    if not math.isfinite(basis.underlying.price) or basis.underlying.price <= 0:
        raise PointPreparationError("underlying selected price must be strictly positive")
    try:
        observation_date = date.fromisoformat(basis.observation.as_of)
    except ValueError as exc:
        raise PointPreparationError("observation must be a valid trade date") from exc
    calculation_basis = CalculationBasis()
    points: list[PremiumPoint] = []
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
        metrics = _prepare_metrics(option, basis.underlying.price, calculation_basis, dte)
        futures_metrics = _prepare_metrics(
            option,
            None if option.futures is None else option.futures.price,
            calculation_basis,
            dte,
        )
        if any(
            metric is not None and not math.isfinite(metric)
            for metric in _metric_leaves(metrics) + _metric_leaves(futures_metrics)
        ):
            raise PointPreparationError(
                f"option {option.instrument_id} produces non-finite derived metrics"
            )
        points.append(
            PremiumPoint(
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
                metrics=PremiumMetrics(
                    underlying_spot=metrics,
                    expiry_futures=futures_metrics,
                ),
            )
        )
    return tuple(points)


def _prepare_metrics(
    option: OptionObservation,
    reference_price: float | None,
    calculation_basis: CalculationBasis,
    dte: int,
) -> ValueMetrics:
    total = option.premium
    time_value = (
        None
        if total is None or reference_price is None
        else total - _reference_intrinsic(option.option_type, reference_price, option.strike)
    )
    return ValueMetrics(
        total=_normalize(total, reference_price, calculation_basis, dte),
        time_value=_normalize(time_value, reference_price, calculation_basis, dte),
    )


def _reference_intrinsic(option_type: OptionType, reference_price: float, strike: float) -> float:
    if option_type is OptionType.CALL:
        return max(reference_price - strike, 0.0)
    return max(strike - reference_price, 0.0)


def _normalize(
    value: float | None,
    reference_price: float | None,
    calculation_basis: CalculationBasis,
    dte: int,
) -> TimeNormalizedMetrics:
    annualized = None if value is None else value * calculation_basis.annualization_days / dte
    return TimeNormalizedMetrics(
        unannualized=MetricValues(value, _yield(value, reference_price)),
        annualized=MetricValues(annualized, _yield(annualized, reference_price)),
    )


def _yield(value: float | None, reference_price: float | None) -> float | None:
    if value is None or reference_price is None or reference_price == 0.0:
        return None
    return value / reference_price


def _metric_leaves(metrics: ValueMetrics) -> tuple[float | None, ...]:
    return (
        metrics.total.unannualized.points,
        metrics.total.unannualized.yield_,
        metrics.total.annualized.points,
        metrics.total.annualized.yield_,
        metrics.time_value.unannualized.points,
        metrics.time_value.unannualized.yield_,
        metrics.time_value.annualized.points,
        metrics.time_value.annualized.yield_,
    )
