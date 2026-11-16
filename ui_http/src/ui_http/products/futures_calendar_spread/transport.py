"""Bounded Calendar Spread transport, without business work or persistence."""

import json
import re
from collections.abc import Callable, Coroutine
from threading import BoundedSemaphore
from typing import Any

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError

from market_research.descriptive.cases.futures_calendar_spread import CalendarSpreadQueryError

from .schemas import DailyErrorResponse, ErrorBody, ErrorKind, Param, Wire

MAX_BODY_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_WINDOW_DAYS = 3660
MAX_EDGES = 128
_CAPACITY = BoundedSemaphore(2)
PATHS = frozenset(
    {
        "/data/futures-calendar-spread",
        "/research/calendar-spread-relative-value/query",
    }
)
PARAMS = frozenset(
    {
        "product_code",
        "trade_date",
        "history_start",
        "evaluation_date",
        "metric",
        "histogram_edges",
    }
)
ERRORS: dict[str, tuple[int, str]] = {
    "invalid_request": (400, "Invalid Calendar Spread request."),
    "incomplete_inputs": (409, "Required market data is incomplete."),
    "upstream_unavailable": (503, "Required market data is unavailable."),
    "input_contract_error": (502, "Market data did not match the required contract."),
    "slot_resolution_error": (422, "Contract slots could not be resolved."),
    "calculation_failure": (422, "Calendar Spread calculation failed."),
    "statistical_failure": (422, "Statistical analysis failed."),
    "internal_error": (500, "Calendar Spread request could not be completed."),
    "transport_busy": (503, "Calendar Spread delivery capacity is busy."),
    "request_too_large": (413, "Request exceeds Calendar Spread HTTP resource limits."),
    "response_too_large": (413, "Complete result exceeds Calendar Spread HTTP response limit."),
}


class TransportError(Exception):
    def __init__(self, kind: ErrorKind, param: Param | None = None):
        self.kind, self.param = kind, param


def error_response(kind: ErrorKind, param: Param | None = None) -> JSONResponse:
    status, detail = ERRORS[kind]
    dto = DailyErrorResponse(error=ErrorBody(kind=kind, detail=detail, param=param))
    return JSONResponse(
        dto.model_dump(mode="json"),
        status_code=status,
        headers={"Cache-Control": "no-store"},
    )


def validation_response(error: ValidationError | RequestValidationError) -> JSONResponse:
    from typing import cast

    param = next(
        (part for e in error.errors() for part in e["loc"] if part in PARAMS),
        None,
    )
    return error_response("invalid_request", cast(Param | None, param))


def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise TransportError("invalid_request", name if name in PARAMS else None)  # type: ignore[arg-type]
        result[name] = value
    return result


class CalendarSpreadRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def bounded(request: Request) -> Response:
            try:
                if request.method == "POST" and request.query_params:
                    raise TransportError("invalid_request")
                if request.method == "GET":
                    for name in request.query_params:
                        if name not in {"product_code", "trade_date"}:
                            raise TransportError("invalid_request")
                        if len(request.query_params.getlist(name)) != 1:
                            raise TransportError("invalid_request", name)  # type: ignore[arg-type]
                data = bytearray()
                async for chunk in request.stream():
                    if request.method == "GET" and chunk:
                        raise TransportError("invalid_request")
                    if len(data) + len(chunk) > MAX_BODY_BYTES:
                        raise TransportError("request_too_large")
                    data.extend(chunk)
                request._body = bytes(data)
                if request.method == "POST":
                    types = request.headers.getlist("content-type")
                    if (
                        len(types) != 1
                        or not re.fullmatch(
                            r'application/json\s*(?:;\s*charset\s*=\s*(?:utf-8|"utf-8")\s*)?',
                            types[0],
                            flags=re.IGNORECASE,
                        )
                        or "content-encoding" in request.headers
                    ):
                        raise TransportError("invalid_request")
                    # Explicit UTF-8; reject nonstandard JSON constants and duplicate
                    # keys before FastAPI can discard them.
                    json.loads(
                        bytes(data).decode("utf-8"),
                        object_pairs_hook=unique_keys,
                        parse_constant=lambda _: (_ for _ in ()).throw(
                            TransportError("invalid_request")
                        ),
                    )
                return await original(request)
            except TransportError as error:
                return error_response(error.kind, error.param)
            except (RequestValidationError, ValidationError) as error:
                return validation_response(error)
            except (ValueError, UnicodeError, RecursionError):
                return error_response("invalid_request")
            except Exception:
                return error_response("internal_error")

        return bounded


def execute(query_and_project: Callable[[], Wire]) -> Response:
    """Worker owns capacity through complete encoding, even after cancellation."""
    if not _CAPACITY.acquire(blocking=False):
        return error_response("transport_busy")
    try:
        try:
            dto = query_and_project()
            # Incremental encoding enforces the bound before allocating a complete
            # unbounded JSON string. Nothing is sent until validation/encoding end.
            payload = bytearray()
            for chunk in json.JSONEncoder(
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            ).iterencode(dto.model_dump(mode="json")):
                encoded = chunk.encode("utf-8")
                if len(payload) + len(encoded) > MAX_RESPONSE_BYTES:
                    raise TransportError("response_too_large")
                payload.extend(encoded)
            return Response(
                bytes(payload),
                media_type="application/json",
                headers={"Cache-Control": "no-store"},
            )
        except CalendarSpreadQueryError as error:
            from typing import cast

            kind = error.category if error.category in ERRORS else "internal_error"
            return error_response(cast(ErrorKind, kind))
        except TransportError as error:
            return error_response(error.kind, error.param)
        except Exception:
            return error_response("internal_error")
    finally:
        _CAPACITY.release()
