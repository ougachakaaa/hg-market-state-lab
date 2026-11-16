"""Read-only historical query; no Research execute/Run lifecycle."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from starlette.concurrency import run_in_threadpool

from market_research.descriptive.cases.futures_calendar_spread import (
    HistoricalRelativeValueResult,
    query_historical_relative_value,
)
from ui_http.products.futures_calendar_spread.endpoint import responses
from ui_http.products.futures_calendar_spread.transport import (
    MAX_EDGES,
    MAX_WINDOW_DAYS,
    CalendarSpreadRoute,
    TransportError,
    execute,
)

from .projection import historical_response
from .schemas import HistoricalErrorResponse, HistoricalRequest, HistoricalResponse

ROUTE_PATH = "/research/calendar-spread-relative-value/query"
router = APIRouter(tags=["Calendar Spread Relative Value"], route_class=CalendarSpreadRoute)


def get_historical_query() -> Callable[..., HistoricalRelativeValueResult]:
    return query_historical_relative_value


@router.post(
    ROUTE_PATH,
    operation_id="query_calendar_spread_relative_value",
    response_model=HistoricalResponse,
    responses=responses(HistoricalErrorResponse),
)
async def historical(
    body: HistoricalRequest,
    query: Annotated[Callable[..., HistoricalRelativeValueResult], Depends(get_historical_query)],
) -> Response:
    if (body.evaluation_date - body.history_start).days + 1 > MAX_WINDOW_DAYS:
        raise TransportError("request_too_large", "history_start")
    if len(body.histogram_edges) > MAX_EDGES:
        raise TransportError("request_too_large", "histogram_edges")
    return await run_in_threadpool(
        execute,
        lambda: historical_response(
            query(
                body.product_code,
                body.history_start,
                body.evaluation_date,
                metric=body.metric,
                histogram_edges=(
                    body.histogram_edges if "histogram_edges" in body.model_fields_set else None
                ),
            )
        ),
    )
