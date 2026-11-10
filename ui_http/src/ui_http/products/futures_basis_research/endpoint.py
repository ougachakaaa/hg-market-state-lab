"""Strict, bounded HTTP adaptation; all research and persistence stay with Research."""

import json
from collections.abc import Callable, Coroutine
from copy import deepcopy
from dataclasses import asdict
from datetime import date
from threading import BoundedSemaphore
from typing import Any

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool

from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest,
    OnlineError,
    RequestValidationError,
    preflight_inputs,
    validate_online_request,
)

from .runtime import application
from .schemas import (
    FuturesBasisErrorResponse,
    FuturesBasisPreflightResponse,
    FuturesBasisReportResponse,
    FuturesBasisRun,
    FuturesBasisRunAccepted,
    FuturesBasisRunRequest,
)

_REPORT_DELIVERY_PERMIT = BoundedSemaphore(1)
MAX_BODY_BYTES = 4 * 1024
MAX_RUN_BYTES = 64 * 1024
MAX_REPORT_BYTES = 32 * 1024 * 1024
ERRORS = {
    "invalid_request": (400, "Request must match the strict Futures Basis schema."),
    "request_too_large": (400, "Request body exceeds 4 KiB."),
    "run_busy": (409, "A Futures Basis run is active."),
    "run_not_found": (404, "Run not found."),
    "corrupt": (409, "Stored run or report is corrupt."),
    "unsupported_version": (409, "Stored run or report version is unsupported."),
    "result_not_ready": (409, "The run has not completed."),
    "result_unavailable": (409, "The run has no available result."),
    "response_too_large": (413, "Report exceeds the 32 MiB delivery bound."),
    "unavailable": (503, "Futures Basis run storage is unavailable."),
    "read_busy": (503, "Report reader capacity is occupied; retry manually."),
    "internal_error": (500, "Futures Basis HTTP operation could not be completed."),
}
NO_STORE = {"Cache-Control": "no-store"}
CACHE_HEADER = {
    "Cache-Control": {
        "schema": {"type": "string", "const": "no-store"},
        "description": "Responses must not be cached.",
    }
}


def error_response(kind: str) -> Response:
    status, detail = ERRORS.get(kind, ERRORS["internal_error"])
    if kind not in ERRORS:
        kind = "internal_error"
    return Response(
        json.dumps({"error": {"kind": kind, "detail": detail, "param": None}}),
        status_code=status,
        media_type="application/json",
        headers=NO_STORE,
    )


class FuturesBasisRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def bounded(request: Request) -> Response:
            try:
                if request.query_params:
                    raise OnlineError("invalid_request")
                return await original(request)
            except OnlineError as exc:
                return error_response(exc.kind)
            except Exception:
                return error_response("internal_error")

        return bounded


router = APIRouter(
    prefix="/research/futures-basis",
    tags=["Futures Basis Research"],
    route_class=FuturesBasisRoute,
)


def responses(*kinds: str, success: int = 200) -> dict[int | str, dict[str, Any]]:
    result: dict[int | str, dict[str, Any]] = {success: {"headers": CACHE_HEADER}}
    for kind in (*kinds, "internal_error"):
        status = ERRORS[kind][0]
        entry = result.setdefault(
            status, {"model": FuturesBasisErrorResponse, "description": "", "headers": CACHE_HEADER}
        )
        entry["description"] = ", ".join(filter(None, (entry["description"], kind)))
    return result


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


async def parse_request(request: Request) -> FuturesBasisRequest:
    if (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "application/json"
    ):
        raise OnlineError("invalid_request")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY_BYTES:
            raise OnlineError("request_too_large")
        raw.extend(chunk)
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
        if not isinstance(data, dict) or set(data) != {"product_code", "start_date", "end_date"}:
            raise ValueError
        if any(type(value) is not str for value in data.values()):
            raise ValueError
        for key in ("start_date", "end_date"):
            parsed = date.fromisoformat(data[key])
            if parsed.isoformat() != data[key]:
                raise ValueError
            data[key] = parsed
        body = FuturesBasisRunRequest.model_validate(data)
        return FuturesBasisRequest(body.product_code, body.start_date, body.end_date)
    except (ValueError, TypeError, UnicodeError, ValidationError, RecursionError):
        raise OnlineError("invalid_request") from None


def serialize(
    model: type[BaseModel], value: dict[str, Any], limit: int, status: int = 200
) -> Response:
    # JSON mode validates producer ISO dates without relaxing the strict request parser.
    payload = (
        model.model_validate_json(json.dumps(value, allow_nan=False)).model_dump_json().encode()
    )
    if len(payload) > limit:
        raise OnlineError(
            "response_too_large" if model is FuturesBasisReportResponse else "internal_error"
        )
    return Response(payload, status_code=status, media_type="application/json", headers=NO_STORE)


@router.post(
    "/preflight",
    operation_id="preflight_futures_basis_research",
    response_model=FuturesBasisPreflightResponse,
    responses=responses("invalid_request", "request_too_large"),
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/FuturesBasisRunRequest"}
                }
            },
        }
    },
)
async def preflight(request: Request) -> Response:
    body = await parse_request(request)
    try:
        validate_online_request(body)
    except RequestValidationError as exc:
        return serialize(
            FuturesBasisErrorResponse,
            {
                "error": {
                    "kind": "invalid_request",
                    "detail": str(exc),
                    "param": exc.param,
                }
            },
            MAX_RUN_BYTES,
            400,
        )
    assess = getattr(request.app.state, "futures_basis_preflight", preflight_inputs)
    result = await run_in_threadpool(assess, body)
    payload = asdict(result)
    payload["market_date"] = result.market_date.isoformat()
    return serialize(FuturesBasisPreflightResponse, payload, MAX_RUN_BYTES)


@router.post(
    "/runs",
    operation_id="submit_futures_basis_research_run",
    status_code=202,
    response_model=FuturesBasisRunAccepted,
    responses=responses(
        "invalid_request", "request_too_large", "run_busy", "unavailable", success=202
    ),
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/FuturesBasisRunRequest"}
                }
            },
        }
    },
)
async def submit_run(request: Request) -> Response:
    body = await parse_request(request)
    result = await run_in_threadpool(
        application(request.app).submit,
        body,
        request.state.auth_user.id,
    )
    return serialize(FuturesBasisRunAccepted, result, MAX_RUN_BYTES, 202)


@router.get(
    "/runs/{run_id}",
    operation_id="get_futures_basis_research_run",
    response_model=FuturesBasisRun,
    responses=responses(
        "invalid_request", "run_not_found", "corrupt", "unsupported_version", "unavailable"
    ),
)
def get_run(run_id: str, request: Request) -> Response:
    result = application(request.app).get_run(run_id, request.state.auth_user.id)
    return serialize(FuturesBasisRun, result, MAX_RUN_BYTES)


@router.get(
    "/runs/{run_id}/report",
    operation_id="get_futures_basis_research_report",
    response_model=FuturesBasisReportResponse,
    responses=responses(
        "invalid_request",
        "run_not_found",
        "result_not_ready",
        "result_unavailable",
        "corrupt",
        "unsupported_version",
        "response_too_large",
        "unavailable",
        "read_busy",
    ),
)
def get_report(run_id: str, request: Request) -> Response:
    if not _REPORT_DELIVERY_PERMIT.acquire(blocking=False):
        raise OnlineError("read_busy")
    try:
        app = application(request.app)
        owner = request.state.auth_user.id
        reader = app.get_report(run_id, owner)
        # Completed state is immutable; status lookup does not parse the report.
        run = app.get_run(run_id, owner)
        result = dict(
            run_id=run_id, request=run["request"], result_status=run["result_status"], data=reader
        )
        return serialize(FuturesBasisReportResponse, result, MAX_REPORT_BYTES)
    finally:
        _REPORT_DELIVERY_PERMIT.release()


def install_contract(app: FastAPI) -> None:
    build = app.openapi

    def openapi() -> dict[str, Any]:
        document = deepcopy(build())
        document["components"]["schemas"]["FuturesBasisRunRequest"] = (
            FuturesBasisRunRequest.model_json_schema()
        )
        for path, methods in document["paths"].items():
            if path.startswith("/research/futures-basis/"):
                for operation in methods.values():
                    for response in operation["responses"].values():
                        response.setdefault("headers", {}).update(deepcopy(CACHE_HEADER))
        return document

    app.openapi = openapi  # type: ignore[method-assign]
