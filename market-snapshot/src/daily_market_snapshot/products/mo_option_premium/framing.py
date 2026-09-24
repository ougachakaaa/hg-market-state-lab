"""Compatibility validation and sparse framing of Annualized Premium Points."""

from __future__ import annotations

from collections.abc import Sequence

from .models import AnnualizedPremiumPlane, AnnualizedPremiumPoint, OptionType


class PlaneFramingError(Exception):
    """Points cannot form one complete, compatible sparse Plane."""


def frame_plane(points: Sequence[AnnualizedPremiumPoint]) -> AnnualizedPremiumPlane:
    """Frame compatible real Points without recalculation or synthesis."""
    if not points:
        raise PlaneFramingError("a Premium Plane requires at least one real Point")
    first = points[0]
    shared = (
        first.observation,
        first.option_product,
        first.price_type,
        first.calculation_basis,
        first.underlying,
    )
    coordinates: set[tuple[str, float, OptionType]] = set()
    instruments: set[str] = set()
    expiry_context: dict[str, tuple[int, object]] = {}
    for point in points:
        if (
            point.observation,
            point.option_product,
            point.price_type,
            point.calculation_basis,
            point.underlying,
        ) != shared:
            raise PlaneFramingError("Points have incompatible shared analytical context")
        coordinate = (point.expiry_date, point.strike, point.option_type)
        if coordinate in coordinates:
            raise PlaneFramingError(f"duplicate analytical coordinate {coordinate}")
        if point.instrument_id in instruments:
            raise PlaneFramingError(f"duplicate option instrument {point.instrument_id}")
        coordinates.add(coordinate)
        instruments.add(point.instrument_id)
        context = (point.dte, point.futures)
        if point.expiry_date in expiry_context and expiry_context[point.expiry_date] != context:
            raise PlaneFramingError(
                f"expiry {point.expiry_date} has inconsistent DTE or futures reference"
            )
        expiry_context[point.expiry_date] = context
    side_order = {OptionType.CALL: 0, OptionType.PUT: 1}
    ordered = tuple(
        sorted(
            points,
            key=lambda point: (
                point.expiry_date,
                side_order[point.option_type],
                point.strike,
                point.instrument_id,
            ),
        )
    )
    return AnnualizedPremiumPlane(
        observation=first.observation,
        option_product=first.option_product,
        price_type=first.price_type,
        underlying=first.underlying,
        calculation_basis=first.calculation_basis,
        points=ordered,
    )
