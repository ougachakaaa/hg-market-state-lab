"""Daily delivery delegates solely to the public Calendar Spread facade."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from starlette.concurrency import run_in_threadpool

from market_research.descriptive.cases.futures_calendar_spread import (
    DailySpreadsResult,
    execute_daily_spreads,
    query_daily_spreads,
)

from .schemas import DailyErrorResponse, DailyRequest, DailyResponse
from .transport import CalendarSpreadRoute, execute

ROUTE_PATH = "/data/futures-calendar-spread"
router = APIRouter(tags=["Futures Calendar Spread"], route_class=CalendarSpreadRoute)


def get_daily_query() -> Callable[..., DailySpreadsResult]:
    return query_daily_spreads


def get_daily_execution() -> Callable[..., DailySpreadsResult]:
    return execute_daily_spreads


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
        lambda: project_daily(query(params.product_code, params.trade_date)),
    )


@router.post(
    ROUTE_PATH + "/query",
    operation_id="execute_futures_calendar_spread",
    response_model=DailyResponse,
    responses=responses(DailyErrorResponse),
)
async def daily_execution(
    body: DailyRequest,
    operation: Annotated[Callable[..., DailySpreadsResult], Depends(get_daily_execution)],
) -> Response:
    return await run_in_threadpool(
        execute,
        lambda: project_daily(operation(body.product_code, body.trade_date)),
    )


def project_daily(result: DailySpreadsResult) -> DailyResponse:
    reference = result.underlying_index
    # Explicit fields only: evidence and original provider failures stay in Research.
    dto = DailyResponse.model_validate({
        "case": result.case,
        "definition_version": result.definition_version,
        "request": result.request,
        "day": result.day,
        "accounting": result.accounting,
        "source_context": result.source_context,
        "underlying_index": {
            "index_code": reference.index_code,
            "trade_date": reference.trade_date,
            "close": reference.close,
            "availability": reference.availability,
            "reason_code": reference.reason_code,
            "failure_category": reference.failure_category,
        },
    })
    return dto
