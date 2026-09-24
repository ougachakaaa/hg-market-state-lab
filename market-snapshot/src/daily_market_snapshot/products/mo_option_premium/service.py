"""Request orchestration and result boundary of MO Premium Plane."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ... import artifacts
from ...capture import (
    im_futures_basic,
    im_futures_daily,
    index_daily,
    mo_option_basic,
    mo_option_daily,
)
from ...sources import tushare
from . import basis, framing, preparation
from .models import DEFAULT_PRICE_TYPE, AnnualizedPremiumPlane, OptionProduct, PriceType


class PremiumPlaneError(Exception):
    """A Premium Plane request cannot be served as requested."""

    kind = "premium_plane_error"


class InvalidQueryError(PremiumPlaneError):
    kind = "invalid_query"


class UnsupportedQueryError(PremiumPlaneError):
    kind = "unsupported_query"


class DateNotAvailableError(PremiumPlaneError):
    kind = "date_not_available"


class PremiumPlaneUnavailableError(PremiumPlaneError):
    kind = "premium_plane_unavailable"


@dataclass(frozen=True)
class PremiumPlaneQuery:
    as_of: str
    option_product: OptionProduct
    price_type: PriceType = DEFAULT_PRICE_TYPE


@dataclass(frozen=True)
class PremiumPlaneResult:
    plane: AnnualizedPremiumPlane | None = None
    error: PremiumPlaneError | None = None

    def __post_init__(self) -> None:
        if (self.plane is None) == (self.error is None):
            raise ValueError("a Premium Plane result carries exactly one of plane / error")


PremiumPlaneProvider = Callable[[PremiumPlaneQuery], PremiumPlaneResult]


def query_error(query: PremiumPlaneQuery) -> PremiumPlaneError | None:
    try:
        tushare.to_tushare_date(query.as_of)
    except tushare.TushareDateError as exc:
        return InvalidQueryError(str(exc))
    if query.option_product is not OptionProduct.MO or not isinstance(query.price_type, PriceType):
        return UnsupportedQueryError("unsupported option product or price type")
    return None


def read_premium_plane_with_api(
    api: tushare.TushareApi,
    query: PremiumPlaneQuery,
    raw_root: Path | None = None,
) -> PremiumPlaneResult:
    """Execute the canonical request stages against an injected Source client."""
    error = query_error(query)
    if error is not None:
        return PremiumPlaneResult(error=error)
    raw_dir = (
        artifacts.mo_option_premium_raw_dir(query.as_of)
        if raw_root is None
        else raw_root / artifacts.MO_OPTION_PREMIUM_RAW_SUBDIR / query.as_of
    )

    # This one Capture is the complete observation admission probe: only a
    # successful Raw write followed by zero exact rows means date unavailable.
    try:
        index_facts = index_daily.capture_observation(api, query.as_of, basis.UNDERLYING_ID)
        artifacts.write_raw_artifact(index_facts, raw_dir, index_daily.RAW_ARTIFACT)
    except Exception as exc:
        return PremiumPlaneResult(error=PremiumPlaneUnavailableError(str(exc)))
    exact_observations = [
        row
        for row in index_facts
        if row.get("ts_code") == basis.UNDERLYING_ID and row.get("trade_date") == query.as_of
    ]
    if not exact_observations:
        return PremiumPlaneResult(
            error=DateNotAvailableError(
                f"no {basis.UNDERLYING_ID} observation for as_of={query.as_of}"
            )
        )

    try:
        option_basic_facts = mo_option_basic.capture(api, query.as_of)
        artifacts.write_raw_artifact(
            option_basic_facts, raw_dir, mo_option_basic.RAW_ARTIFACT
        )
        option_daily_facts = mo_option_daily.capture(api, query.as_of, option_basic_facts)
        artifacts.write_raw_artifact(
            option_daily_facts, raw_dir, mo_option_daily.RAW_ARTIFACT
        )
        futures_basic_facts = im_futures_basic.capture(api, query.as_of)
        artifacts.write_raw_artifact(
            futures_basic_facts, raw_dir, im_futures_basic.RAW_ARTIFACT
        )
        futures_daily_facts = im_futures_daily.capture_target_date(
            api, query.as_of, futures_basic_facts
        )
        artifacts.write_raw_artifact(
            futures_daily_facts, raw_dir, im_futures_daily.RAW_ARTIFACT
        )
    except Exception as exc:
        return PremiumPlaneResult(error=PremiumPlaneUnavailableError(str(exc)))

    try:
        market_basis = basis.construct_basis(
            query.as_of, query.option_product, query.price_type, raw_dir
        )
        points = preparation.prepare_points(market_basis)
        plane = framing.frame_plane(points)
    except (
        basis.BasisConstructionError,
        preparation.PointPreparationError,
        framing.PlaneFramingError,
    ) as exc:
        return PremiumPlaneResult(error=PremiumPlaneUnavailableError(str(exc)))
    return PremiumPlaneResult(plane=plane)


def read_premium_plane(query: PremiumPlaneQuery) -> PremiumPlaneResult:
    """Production provider used by the HTTP adapter."""
    error = query_error(query)
    if error is not None:
        return PremiumPlaneResult(error=error)
    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
    except Exception as exc:
        return PremiumPlaneResult(error=PremiumPlaneUnavailableError(str(exc)))
    return read_premium_plane_with_api(api, query)


__all__ = [
    "DEFAULT_PRICE_TYPE",
    "DateNotAvailableError",
    "InvalidQueryError",
    "OptionProduct",
    "PremiumPlaneError",
    "PremiumPlaneProvider",
    "PremiumPlaneQuery",
    "PremiumPlaneResult",
    "PremiumPlaneUnavailableError",
    "PriceType",
    "UnsupportedQueryError",
    "read_premium_plane",
    "read_premium_plane_with_api",
]
