"""Four bounded operations, delegating only to published Research APIs."""

from collections.abc import Callable, Coroutine
from threading import Lock
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from market_research.descriptive.capabilities import (
    CapabilityDescription,
    CapabilityNotFound,
    get_capability,
    list_capabilities,
)
from market_research.descriptive.execution import (
    InvalidPlan,
    ResearchPlan,
    execute_batch,
    preview_plan,
)
from market_research.descriptive.observation import InvalidObservationRequest
from market_statistics import InvalidStatisticalSpec

from .errors import ResearchApiError, ResearchErrorResponse, error_response
from .projection import batch_response, preview_response
from .requests import ExecuteBody, PlanBody, QuantileBody
from .schemas import BatchResponse, PreviewResponse

MAX_BODY_BYTES = 64 * 1024
_EXECUTION_GUARD = Lock()
RESEARCH_PATHS = frozenset({"/research/capabilities", "/research/preview", "/research/execute"})


def is_research_path(path: str) -> bool:
    return path in RESEARCH_PATHS or path.startswith("/research/capabilities/")


class ResearchRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def bounded(request: Request) -> Response:
            try:
                if request.method == "POST":
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > MAX_BODY_BYTES:
                            raise ResearchApiError(
                                "request_too_large", "Request body exceeds 64 KiB."
                            )
                        chunks.append(chunk)
                    request._body = b"".join(chunks)
                return await original(request)
            except (RequestValidationError, HTTPException) as exc:
                if isinstance(exc, HTTPException) and exc.status_code not in (400, 422):
                    raise
                return error_response(
                    ResearchApiError(
                        "invalid_request",
                        "Body must match the strict Research request schema.",
                    )
                )
            except ResearchApiError as exc:
                return error_response(exc)
            except InvalidPlan:
                return error_response(
                    ResearchApiError(
                        "invalid_request",
                        "Plan failed public Research preflight.",
                    )
                )
            except Exception:
                return error_response(
                    ResearchApiError(
                        "internal_error",
                        "Research HTTP execution could not be completed.",
                    )
                )

        return bounded


router = APIRouter(prefix="/research", tags=["Research"], route_class=ResearchRoute)
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ResearchErrorResponse,
        "description": "invalid_request or request_too_large; no I/O",
    },
    500: {"model": ResearchErrorResponse, "description": "internal_error; safe detail"},
}


@router.get(
    "/capabilities",
    operation_id="list_research_capabilities",
    responses={500: ERROR_RESPONSES[500]},
)
def capabilities() -> tuple[CapabilityDescription, ...]:
    """Read-only admitted capabilities. No service creation, market I/O or readiness probe."""
    return list_capabilities()


@router.get(
    "/capabilities/{id}",
    operation_id="get_research_capability",
    responses={
        404: {"model": ResearchErrorResponse, "description": "capability_not_found"},
        500: ERROR_RESPONSES[500],
    },
)
def capability(id: str) -> CapabilityDescription:
    try:
        return get_capability(id)
    except CapabilityNotFound as exc:
        raise ResearchApiError("capability_not_found", "Unknown Research capability.") from exc


def bounded_plan(body: PlanBody) -> ResearchPlan:
    if (
        len(body.subjects) * len(body.horizons) * len(body.windows) > 8
        or len(body.analysis_requests) > 4
        or any(h > 20 for h in body.horizons)
        or any((w.end_date - w.start_date).days + 1 > 93 for w in body.windows)
        or any(len(r.request_id) > 128 for r in body.analysis_requests)
        or any(
            len(r.spec.points if isinstance(r.spec, QuantileBody) else r.spec.edges) > 128
            for r in body.analysis_requests
        )
    ):
        raise ResearchApiError(
            "request_too_large", "Plan exceeds the published HTTP resource bounds."
        )
    try:
        return body.to_plan()
    except (InvalidPlan, InvalidStatisticalSpec, InvalidObservationRequest, ValueError) as exc:
        raise ResearchApiError(
            "invalid_request", "Plan failed public Research/Statistics preflight."
        ) from exc


@router.post("/preview", operation_id="preview_research_plan", responses=ERROR_RESPONSES)
def preview(body: PlanBody) -> PreviewResponse:
    """Entire-plan pure preflight and ordered expansion; never probes upstream availability."""
    return preview_response(preview_plan(bounded_plan(body)))


def _execute(body: ExecuteBody) -> BatchResponse:
    # The worker owns the lock for its complete lifetime, even if the caller disconnects.
    plan = bounded_plan(body)
    preview_plan(plan)
    if not _EXECUTION_GUARD.acquire(blocking=False):
        raise ResearchApiError("execution_busy", "A Research execution is already in flight.")
    try:
        return batch_response(execute_batch(plan))
    finally:
        _EXECUTION_GUARD.release()


@router.post(
    "/execute",
    operation_id="execute_research_plan",
    responses={
        **ERROR_RESPONSES,
        409: {"model": ResearchErrorResponse, "description": "execution_busy; no queue"},
    },
)
async def execute(body: ExecuteBody) -> BatchResponse:
    """One synchronous BatchResult, including failed/partial_success; may acquire/cache facts."""
    if body.acknowledge_acquisition is not True:
        raise ResearchApiError(
            "invalid_request",
            "acknowledge_acquisition must be explicitly true.",
            "acknowledge_acquisition",
        )
    return await run_in_threadpool(_execute, body)
