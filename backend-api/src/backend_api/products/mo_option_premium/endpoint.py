"""Transport-only adapter for ``GET /mo-option-premium-plane``."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from market_snapshot.products.mo_option_premium import service

from .errors import (
    CONTRACT_QUERY_PARAMS,
    QUERY_PARAM_AS_OF,
    PremiumApiError,
    PremiumErrorKind,
    PremiumErrorResponse,
)
from .schemas import (
    ExpiryDTO,
    FuturesDTO,
    IsoDate,
    MetricDTO,
    ObservationDTO,
    PremiumMetricsDTO,
    PremiumPlaneResponse,
    PremiumPointDTO,
    TimeNormalizedMetricsDTO,
    UnderlyingDTO,
    ValueMetricsDTO,
)

ROUTE_PATH = "/mo-option-premium-plane"
router = APIRouter()


def get_premium_plane_provider() -> service.PremiumPlaneProvider:
    return service.read_premium_plane


def resolve_premium_query(
    request: Request,
    as_of: Annotated[IsoDate, Query(description="Trade-date observation, YYYY-MM-DD.")],
    option_product: Annotated[
        service.OptionProduct, Query(description="Option product; V1 supports MO only.")
    ],
    price_type: Annotated[
        service.PriceType, Query(description="Unified selected price semantics.")
    ] = service.DEFAULT_PRICE_TYPE,
) -> service.PremiumPlaneQuery:
    unexpected = next(
        (name for name in request.query_params if name not in CONTRACT_QUERY_PARAMS), None
    )
    if unexpected is not None:
        raise PremiumApiError(
            PremiumErrorKind.INVALID_REQUEST,
            f"unsupported query parameter {unexpected}",
        )
    return service.PremiumPlaneQuery(as_of.isoformat(), option_product, price_type)


ERROR_KINDS: dict[type[service.PremiumPlaneError], PremiumErrorKind] = {
    service.InvalidQueryError: PremiumErrorKind.INVALID_REQUEST,
    service.UnsupportedQueryError: PremiumErrorKind.UNSUPPORTED_QUERY,
    service.DateNotAvailableError: PremiumErrorKind.DATE_NOT_AVAILABLE,
    service.PremiumPlaneUnavailableError: PremiumErrorKind.PREMIUM_PLANE_UNAVAILABLE,
}


def project_plane(plane: service.PremiumPlane) -> PremiumPlaneResponse:
    """Losslessly normalize repeated Point context into the wire shape."""
    expiry_context: dict[str, ExpiryDTO] = {}
    for point in plane.points:
        futures = (
            FuturesDTO(
                instrument_id=point.futures.instrument_id,
                price=point.futures.price,
            )
            if point.futures is not None
            else None
        )
        context = ExpiryDTO(expiry_date=point.expiry_date, dte=point.dte, futures=futures)
        expiry_context.setdefault(point.expiry_date, context)
    return PremiumPlaneResponse(
        observation=ObservationDTO(value=plane.observation.as_of),
        option_product=plane.option_product,
        price_type=plane.price_type,
        underlying=UnderlyingDTO(
            instrument_id=plane.underlying.instrument_id,
            price=plane.underlying.price,
        ),
        expiries=[expiry_context[key] for key in sorted(expiry_context)],
        points=[
            PremiumPointDTO(
                instrument_id=point.instrument_id,
                expiry_date=point.expiry_date,
                option_type=point.option_type,
                strike=point.strike,
                premium=point.premium,
                metrics=_project_metrics(point.metrics),
            )
            for point in plane.points
        ],
    )


def _project_metrics(metrics: service.PremiumMetrics) -> PremiumMetricsDTO:
    return PremiumMetricsDTO(
        underlying_spot=_project_value_metrics(metrics.underlying_spot),
        expiry_futures=_project_value_metrics(metrics.expiry_futures),
    )


def _project_value_metrics(metrics: service.ValueMetrics) -> ValueMetricsDTO:
    return ValueMetricsDTO(
        total=_project_time_normalized_metrics(metrics.total),
        time_value=_project_time_normalized_metrics(metrics.time_value),
    )


def _project_time_normalized_metrics(
    metrics: service.TimeNormalizedMetrics,
) -> TimeNormalizedMetricsDTO:
    return TimeNormalizedMetricsDTO(
        unannualized=_project_metric(metrics.unannualized),
        annualized=_project_metric(metrics.annualized),
    )


def _project_metric(metric: service.MetricValues) -> MetricDTO:
    return MetricDTO(points=metric.points, yield_=metric.yield_)


async def read_plane(
    provider: Annotated[service.PremiumPlaneProvider, Depends(get_premium_plane_provider)],
    query: Annotated[service.PremiumPlaneQuery, Depends(resolve_premium_query)],
) -> PremiumPlaneResponse:
    result = provider(query)
    if result.error is not None:
        kind = next(
            (
                kind
                for error_type, kind in ERROR_KINDS.items()
                if isinstance(result.error, error_type)
            ),
            PremiumErrorKind.PREMIUM_PLANE_UNAVAILABLE,
        )
        param = (
            QUERY_PARAM_AS_OF
            if isinstance(result.error, service.DateNotAvailableError)
            else None
        )
        raise PremiumApiError(kind, str(result.error), param)
    assert result.plane is not None
    return project_plane(result.plane)


@router.get(
    ROUTE_PATH,
    operation_id="readMoOptionPremiumPlane",
    response_model=PremiumPlaneResponse,
    responses={
        400: {"model": PremiumErrorResponse, "description": "Invalid or unsupported request."},
        404: {"model": PremiumErrorResponse, "description": "Observation is unavailable."},
        503: {"model": PremiumErrorResponse, "description": "Plane cannot be produced."},
    },
)
async def read_mo_option_premium_plane(
    plane: Annotated[PremiumPlaneResponse, Depends(read_plane)],
) -> PremiumPlaneResponse:
    return plane
