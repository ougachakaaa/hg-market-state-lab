"""Deterministic acceptance of the public WP1 financial boundary."""

import math
import socket
import sys
from dataclasses import FrozenInstanceError, fields
from datetime import date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from market_research.descriptive.cases.futures_calendar_spread import (
    CalendarSpreadCalculationError,
    CalendarSpreadMetric,
    CalendarSpreadResult,
    CalendarSpreadValidationError,
    compute_calendar_spread,
)

NEAR_DATE = date(2026, 11, 20)
FAR_DATE = date(2026, 12, 20)


def values(result: CalendarSpreadResult) -> tuple[float, float, float]:
    return (
        result.signed_spread.value,
        result.annualized_point_spread.value,
        result.annualized_spread_ratio.value,
    )


@pytest.mark.parametrize("near, far", [(110, 100), (90, 100), (100, 100)])
def test_positive_negative_and_equal_prices(near: int, far: int) -> None:
    result = compute_calendar_spread(near, far, NEAR_DATE, FAR_DATE)
    assert result.delta_days == 30
    assert values(result) == (near - far, (near - far) * 365 / 30, 365 * math.log(near / far) / 30)
    if near == far:
        assert values(result) == (0.0, 0.0, 0.0)
    else:
        assert all((value > 0) == (near > far) for value in values(result))


def test_identity_units_and_public_types() -> None:
    result = compute_calendar_spread(110.0, 100.0, NEAR_DATE, FAR_DATE)
    assert isinstance(result, CalendarSpreadResult)
    assert result.definition_version == "futures_calendar_spread_definition_v1"
    for name, unit in (
        ("signed_spread", "index_points"),
        ("annualized_point_spread", "index_points_per_365_natural_days"),
        ("annualized_spread_ratio", "decimal_ratio"),
    ):
        metric = getattr(result, name)
        assert isinstance(metric, CalendarSpreadMetric)
        assert metric.metric_id == name
        assert metric.unit == unit
        assert type(metric.value) is float


def test_logarithm_not_linear_and_no_presentation_rounding() -> None:
    result = compute_calendar_spread(110, 100, NEAR_DATE, FAR_DATE)
    ratio = result.annualized_spread_ratio.value
    assert ratio == 365 * math.log(1.1) / 30
    assert not math.isclose(ratio, 365 * (110 / 100 - 1) / 30)
    assert ratio != round(ratio, 2)
    assert result.annualized_point_spread.value != round(result.annualized_point_spread.value, 2)


@pytest.mark.parametrize(
    "near_date, far_date, days",
    [
        (date(2026, 12, 18), date(2027, 1, 15), 28),
        (date(2024, 2, 28), date(2024, 3, 1), 2),
        (date(2026, 11, 20), date(2026, 11, 21), 1),
        (date.min, date.max, (date.max - date.min).days),
    ],
)
def test_actual_last_trading_natural_day_spacing(
    near_date: date, far_date: date, days: int
) -> None:
    result = compute_calendar_spread(110, 100, near_date, far_date)
    assert result.delta_days == days
    assert result.annualized_point_spread.value == 10 * 365 / days
    assert result.annualized_spread_ratio.value == 365 * math.log(1.1) / days
    # A shifted pair with identical spacing gives the same result; there is no near DTE input.
    if far_date < date.max:
        assert (
            compute_calendar_spread(
                110, 100, near_date + timedelta(days=1), far_date + timedelta(days=1)
            )
            == result
        )


@pytest.mark.parametrize(
    "near, far",
    [
        (1e300, 1e300),
        (sys.float_info.max, sys.float_info.max),
        (1e-300, 2e-300),
        (math.ulp(0.0), math.ulp(0.0)),
        (1e305, 2e305),
        (1.0, sys.float_info.min),
    ],
)
def test_legal_extreme_values_remain_finite(near: float, far: float) -> None:
    result = compute_calendar_spread(near, far, NEAR_DATE, NEAR_DATE + timedelta(days=1))
    assert all(math.isfinite(value) for value in values(result))
    assert values(result) == (near - far, (near - far) * 365, 365 * math.log(near / far))


class FloatSubclass(float):
    pass


class IntSubclass(int):
    pass


class DateSubclass(date):
    pass


@pytest.mark.parametrize("field", ["near_close", "far_close"])
@pytest.mark.parametrize(
    "bad",
    [
        0,
        -1,
        0.0,
        -0.0,
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        False,
        "110",
        None,
        complex(1, 0),
        Decimal("110"),
        Fraction(110, 1),
        FloatSubclass(110),
        IntSubclass(110),
        10**400,
    ],
    ids=[
        "zero-int",
        "negative-int",
        "zero-float",
        "negative-zero",
        "negative-float",
        "nan",
        "inf",
        "negative-inf",
        "true",
        "false",
        "string",
        "none",
        "complex",
        "decimal",
        "fraction",
        "float-subclass",
        "int-subclass",
        "int-overflow",
    ],
)
def test_reject_illegal_prices(field: str, bad: object) -> None:
    inputs = dict(
        near_close=110, far_close=100, near_last_trade_date=NEAR_DATE, far_last_trade_date=FAR_DATE
    )
    inputs[field] = bad
    with pytest.raises(CalendarSpreadValidationError):
        compute_calendar_spread(**inputs)


@pytest.mark.parametrize("field", ["near_last_trade_date", "far_last_trade_date"])
@pytest.mark.parametrize(
    "bad",
    [datetime(2026, 11, 20), "2026-11-20", None, 20261120, DateSubclass(2026, 11, 20)],
)
def test_reject_non_date_only_values(field: str, bad: object) -> None:
    inputs = dict(
        near_close=110, far_close=100, near_last_trade_date=NEAR_DATE, far_last_trade_date=FAR_DATE
    )
    inputs[field] = bad
    with pytest.raises(CalendarSpreadValidationError):
        compute_calendar_spread(**inputs)


@pytest.mark.parametrize("far_date", [NEAR_DATE, NEAR_DATE - timedelta(days=1)])
def test_reject_nonpositive_day_spacing(far_date: date) -> None:
    with pytest.raises(CalendarSpreadValidationError):
        compute_calendar_spread(110, 100, NEAR_DATE, far_date)


@pytest.mark.parametrize(
    "near, far",
    [
        (1e306, 1.0),  # spread * 365 overflows even though division by 30 could rescue it.
        (1.0, 1e306),  # Negative point numerator also overflows.
        (1.0, math.ulp(0.0)),  # N/F overflows with a finite point calculation.
        (math.ulp(0.0), sys.float_info.max),  # N-F is finite; point multiplication fails.
        (math.ulp(0.0), 1e305),  # N/F underflows to zero after a finite point calculation.
    ],
)
def test_valid_input_calculation_failure(near: float, far: float) -> None:
    with pytest.raises(CalendarSpreadCalculationError):
        compute_calendar_spread(near, far, NEAR_DATE, FAR_DATE)


def test_undefined_log_preserves_cause() -> None:
    with pytest.raises(CalendarSpreadCalculationError) as failure:
        compute_calendar_spread(math.ulp(0.0), 1e305, NEAR_DATE, FAR_DATE)
    assert isinstance(failure.value.__cause__, ValueError)


def test_validate_all_inputs_before_financial_calculation() -> None:
    # These legal prices would cause overflow, but the illegal date is an input failure.
    with pytest.raises(CalendarSpreadValidationError):
        compute_calendar_spread(1e306, 1, NEAR_DATE, NEAR_DATE)


def test_immutable_deterministic_and_no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_network(*args: object, **kwargs: object) -> None:
        pytest.fail("financial computation attempted network access")

    monkeypatch.setattr(socket, "socket", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    inputs = (110, 100.0, NEAR_DATE, FAR_DATE)
    before = tuple(inputs)
    result = compute_calendar_spread(*inputs)
    assert all(compute_calendar_spread(*inputs) == result for _ in range(5))
    assert inputs == before
    for field in fields(result):
        with pytest.raises(FrozenInstanceError):
            setattr(result, field.name, None)
    for metric in (
        result.signed_spread,
        result.annualized_point_spread,
        result.annualized_spread_ratio,
    ):
        for field in fields(metric):
            with pytest.raises(FrozenInstanceError):
                setattr(metric, field.name, None)
    assert not hasattr(result, "__dict__")
    assert not hasattr(result.signed_spread, "__dict__")
