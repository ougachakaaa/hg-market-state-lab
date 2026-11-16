"""Daily delivery delegates solely to the public Calendar Spread query."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from starlette.concurrency import run_in_threadpool

from market_research.descriptive.cases.futures_calendar_spread import (
    DailySpreadsResult,
    query_daily_spreads,
)

from .schemas import DailyErrorResponse, DailyRequest, DailyResponse
from .transport import CalendarSpreadRoute, execute

ROUTE_PATH = "/data/futures-calendar-spread"
router = APIRouter(tags=["Futures Calendar Spread"], route_class=CalendarSpreadRoute)


def get_daily_query() -> Callable[..., DailySpreadsResult]:
    return query_daily_spreads


def responses(model: type[DailyErrorResponse]) -> dict[int | str, dict[str, Any]]:
    return {status: {"model": model} for status in (400, 409, 413, 422, 500, 502, 503)}


@router.get(
    ROUTE_PATH,
    operation_id="query_futures_calendar_spread",
    response_model=DailyResponse,
    responses=responses(DailyErrorResponse),
)
async def daily(
    params: Annotated[DailyRequest, Query()],
    query: Annotated[Callable[..., DailySpreadsResult], Depends(get_daily_query)],
) -> Response:
    return await run_in_threadpool(
        execute,
        lambda: DailyResponse.model_validate(query(params.product_code, params.trade_date)),
    )
