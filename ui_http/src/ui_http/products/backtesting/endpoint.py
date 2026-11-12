"""Strict authenticated transport; W2 owns execution, results and classifications."""

import json
from collections.abc import Callable, Coroutine
from copy import deepcopy
from dataclasses import asdict
from datetime import date
from threading import BoundedSemaphore
from typing import Any

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from market_backtesting.cases.futures_roll_long import (
    FuturesRollApplicationError,
    FuturesRollOnlineError,
    FuturesRollRequest,
    OnlineRunStatus,
    validate_futures_roll_request,
)

from .runtime import application
from .schemas import (
    FuturesRollErrorResponse,
    FuturesRollPreflight,
    FuturesRollResultResponse,
    FuturesRollRun,
    FuturesRollRunAccepted,
    FuturesRollRunRequest,
)

MAX_BODY_BYTES = 4096
MAX_STATUS_BYTES = 64 * 1024
MAX_RESULT_BYTES = 32 * 1024 * 1024
_RESULT_DELIVERY_PERMIT = BoundedSemaphore(1)
ERRORS = {
    "invalid_request": (400, "Request must match the strict Futures Roll schema."),
    "request_too_large": (400, "Request body exceeds 4 KiB."),
    "run_not_found": (404, "Run not found."),
    "run_busy": (409, "A backtest is already running."),
    "result_not_ready": (409, "The run has not completed."),
    "corrupt": (409, "Stored run or result is corrupt."),
    "result_too_large": (413, "Stored result exceeds the 32 MiB bound."),
    "response_too_large": (413, "Result response exceeds the 32 MiB delivery bound."),
    "unavailable": (503, "Backtesting online application is unavailable."),
    "read_busy": (503, "Result reader capacity is occupied; retry manually."),
    "internal_error": (500, "Backtesting HTTP operation could not be completed."),
}
NO_STORE = {"Cache-Control": "no-store"}
CACHE_HEADER = {
    "Cache-Control": {
        "schema": {"type": "string", "const": "no-store"},
        "description": "Responses must not be cached.",
    }
}


class TransportError(Exception):
    def __init__(self, kind: str) -> None:
        self.kind = kind


def error_response(kind: str) -> Response:
    if kind not in ERRORS:
        kind = "internal_error"
    status, detail = ERRORS[kind]
    return Response(
        json.dumps({"error": {"kind": kind, "detail": detail, "param": None}}),
        status_code=status,
        media_type="application/json",
        headers=NO_STORE,
    )


class BacktestingRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def bounded(request: Request) -> Response:
            try:
                if request.query_params:
                    raise TransportError("invalid_request")
                return await original(request)
            except TransportError as exc:
                return error_response(exc.kind)
            except FuturesRollOnlineError as exc:
                return error_response(exc.category)
            except FuturesRollApplicationError as exc:
                return error_response(
                    "invalid_request" if exc.category == "invalid_request" else "internal_error"
                )
            except Exception:
                return error_response("internal_error")

        return bounded


router = APIRouter(
    prefix="/backtesting/futures-roll",
    tags=["Backtesting"],
    route_class=BacktestingRoute,
)


def responses(*kinds: str, success: int = 200) -> dict[int | str, dict[str, Any]]:
    result: dict[int | str, dict[str, Any]] = {success: {"headers": CACHE_HEADER}}
    for kind in ("invalid_request", *kinds, "internal_error"):
        status = ERRORS[kind][0]
        entry = result.setdefault(
            status,
            {
                "model": FuturesRollErrorResponse,
                "description": "",
                "headers": CACHE_HEADER,
            },
        )
        entry["description"] = ", ".join(filter(None, (entry["description"], kind)))
    return result


BODY_SCHEMA = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/FuturesRollRunRequest"},
            }
        },
    }
}
READ_ERRORS = ("run_not_found", "corrupt", "unavailable", "result_too_large")


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_key")
        value[key] = item
    return value


async def parse_request(request: Request) -> FuturesRollRequest:
    content_types = request.headers.getlist("content-type")
    encodings = request.headers.getlist("content-encoding")
    if (
        len(content_types) != 1
        or content_types[0].split(";", 1)[0].strip().lower() != "application/json"
        or (encodings and (len(encodings) != 1 or encodings[0].strip().lower() != "identity"))
    ):
        raise TransportError("invalid_request")
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY_BYTES:
            raise TransportError("request_too_large")
        raw.extend(chunk)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
        if type(value) is not dict or set(value) != {
            "product_code",
            "start_date",
            "end_date",
            "strategy_profile",
        }:
            raise ValueError("fields")
        if any(type(item) is not str for item in value.values()):
            raise ValueError("strings")
        for key in ("start_date", "end_date"):
            parsed = date.fromisoformat(value[key])
            if parsed.isoformat() != value[key]:
                raise ValueError("canonical_date")
            value[key] = parsed
        body = FuturesRollRunRequest.model_validate(value)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise TransportError("invalid_request") from None
    semantic = FuturesRollRequest(
        body.product_code,
        body.start_date,
        body.end_date,
        body.strategy_profile,
    )
    validate_futures_roll_request(semantic)
    return semantic


def json_date(value: Any) -> str:
    if type(value) is date:
        return value.isoformat()
    raise TypeError("unsupported_json_type")


def serialize(
    model: type[BaseModel],
    value: dict[str, Any],
    limit: int,
    status: int = 200,
) -> Response:
    payload = bytearray()
    encoder = json.JSONEncoder(
        allow_nan=False, ensure_ascii=True, separators=(",", ":"), default=json_date
    )
    for chunk in encoder.iterencode(value):
        encoded = chunk.encode("utf-8")
        if len(payload) + len(encoded) > limit:
            raise TransportError(
                "response_too_large" if model is FuturesRollResultResponse else "internal_error"
            )
        payload.extend(encoded)
    wire = bytes(payload)
    # Validate transport shape only. Financial validation remains entirely producer-owned.
    model.model_validate_json(wire)
    return Response(wire, status_code=status, media_type="application/json", headers=NO_STORE)


def status_value(status: OnlineRunStatus) -> dict[str, Any]:
    value = asdict(status)
    value["result_available"] = status.status == "COMPLETED"
    return value


@router.post(
    "/preflight",
    operation_id="preflight_futures_roll_backtest",
    response_model=FuturesRollPreflight,
    responses=responses("request_too_large", "unavailable"),
    openapi_extra=BODY_SCHEMA,
)
async def preflight(request: Request) -> Response:
    body = await parse_request(request)

    def assess() -> Response:
        result = application(request.app).preflight(body, request.state.auth_user.id)
        return serialize(
            FuturesRollPreflight, {**asdict(result), "ready": result.ready}, MAX_STATUS_BYTES
        )

    return await run_in_threadpool(assess)


@router.post(
    "/runs",
    operation_id="submit_futures_roll_backtest",
    status_code=202,
    response_model=FuturesRollRunAccepted,
    responses=responses("request_too_large", "run_busy", "unavailable", success=202),
    openapi_extra=BODY_SCHEMA,
)
async def submit(request: Request) -> Response:
    body = await parse_request(request)

    def admit() -> Response:
        accepted = application(request.app).submit(body, request.state.auth_user.id)
        value = {
            key: item
            for key, item in asdict(accepted).items()
            if key in {"run_id", "status", "request", "created_at"}
        }
        return serialize(FuturesRollRunAccepted, value, MAX_STATUS_BYTES, 202)

    return await run_in_threadpool(admit)


@router.get(
    "/runs/{run_id}",
    operation_id="get_futures_roll_backtest_run",
    response_model=FuturesRollRun,
    responses=responses(*READ_ERRORS),
)
def get_run(run_id: str, request: Request) -> Response:
    result = application(request.app).get_status(run_id, request.state.auth_user.id)
    return serialize(FuturesRollRun, status_value(result), MAX_STATUS_BYTES)


@router.get(
    "/runs/{run_id}/result",
    operation_id="get_futures_roll_backtest_result",
    response_model=FuturesRollResultResponse,
    responses=responses(*READ_ERRORS, "result_not_ready", "response_too_large", "read_busy"),
)
def get_result(run_id: str, request: Request) -> Response:
    app = application(request.app)
    owner = request.state.auth_user.id
    state = app.get_status(run_id, owner)
    if state.status != "COMPLETED":
        raise FuturesRollOnlineError("result_not_ready")
    if not _RESULT_DELIVERY_PERMIT.acquire(blocking=False):
        raise TransportError("read_busy")
    try:
        result = app.get_result(run_id, owner)
        if result.request != state.request:
            raise FuturesRollOnlineError("corrupt")
        return serialize(
            FuturesRollResultResponse,
            {
                "run_id": state.run_id,
                "request": asdict(state.request),
                "data": asdict(result),
            },
            MAX_RESULT_BYTES,
        )
    finally:
        _RESULT_DELIVERY_PERMIT.release()


def install_contract(app: FastAPI) -> None:
    build = app.openapi

    def openapi() -> dict[str, Any]:
        document = deepcopy(build())
        document["components"]["schemas"]["FuturesRollRunRequest"] = (
            FuturesRollRunRequest.model_json_schema()
        )
        for path, methods in document["paths"].items():
            if path.startswith("/backtesting/futures-roll/"):
                for operation in methods.values():
                    for response in operation["responses"].values():
                        response.setdefault("headers", {}).update(deepcopy(CACHE_HEADER))
        return document

    app.openapi = openapi  # type: ignore[method-assign]
