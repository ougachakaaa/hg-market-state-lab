"""Pure calendar spread calculation under futures_calendar_spread_definition_v1."""

from dataclasses import dataclass
from datetime import date
from math import isfinite, log
from typing import Literal


@dataclass(frozen=True, slots=True)
class CalendarSpreadMetric:
    """An unrounded financial value with its business identity and unit."""

    value: float
    metric_id: Literal["signed_spread", "annualized_point_spread", "annualized_spread_ratio"]
    unit: Literal["index_points", "index_points_per_365_natural_days", "decimal_ratio"]


@dataclass(frozen=True, slots=True)
class CalendarSpreadResult:
    """All three metrics share one between-contract natural-day denominator."""

    signed_spread: CalendarSpreadMetric
    annualized_point_spread: CalendarSpreadMetric
    annualized_spread_ratio: CalendarSpreadMetric
    delta_days: int
    definition_version: Literal["futures_calendar_spread_definition_v1"] = (
        "futures_calendar_spread_definition_v1"
    )


class CalendarSpreadValidationError(ValueError):
    """An input is outside the financial capability's public contract."""


class CalendarSpreadCalculationError(ArithmeticError):
    """Legal inputs cannot produce finite metrics in the prescribed operation order."""


def _price(value: int | float, name: str) -> float:
    if type(value) not in (int, float):
        raise CalendarSpreadValidationError(f"{name} must be a built-in int or float")
    try:
        number = float(value)
    except OverflowError as exc:
        raise CalendarSpreadValidationError(f"{name} must fit finite binary64") from exc
    if not isfinite(number) or number <= 0.0:
        raise CalendarSpreadValidationError(f"{name} must be finite and positive")
    return number


def _finite(value: float) -> float:
    if not isfinite(value):
        raise CalendarSpreadCalculationError("non-finite calendar spread intermediate or result")
    return value


def compute_calendar_spread(
    near_close: int | float,
    far_close: int | float,
    near_last_trade_date: date,
    far_last_trade_date: date,
) -> CalendarSpreadResult:
    """Calculate signed, point-annualized and log-annualized calendar spreads.

    Only exact built-in int/float prices and date-only dates are accepted. Illegal
    inputs raise CalendarSpreadValidationError; valid-input numerical failures
    raise CalendarSpreadCalculationError. No I/O or presentation rounding occurs.
    """
    near = _price(near_close, "near_close")
    far = _price(far_close, "far_close")
    if type(near_last_trade_date) is not date or type(far_last_trade_date) is not date:
        raise CalendarSpreadValidationError("last trading dates must be exact datetime.date values")
    delta_days = (far_last_trade_date - near_last_trade_date).days
    if delta_days <= 0:
        raise CalendarSpreadValidationError(
            "far last trading date must follow near last trading date"
        )

    try:
        spread = _finite(near - far)
        point_numerator = _finite(spread * 365)
        point_spread = _finite(point_numerator / delta_days)
        price_ratio = _finite(near / far)
        log_ratio = _finite(log(price_ratio))
        ratio_numerator = _finite(365 * log_ratio)
        spread_ratio = _finite(ratio_numerator / delta_days)
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        raise CalendarSpreadCalculationError("calendar spread arithmetic failed") from exc

    return CalendarSpreadResult(
        signed_spread=CalendarSpreadMetric(spread, "signed_spread", "index_points"),
        annualized_point_spread=CalendarSpreadMetric(
            point_spread, "annualized_point_spread", "index_points_per_365_natural_days"
        ),
        annualized_spread_ratio=CalendarSpreadMetric(
            spread_ratio, "annualized_spread_ratio", "decimal_ratio"
        ),
        delta_days=delta_days,
    )
