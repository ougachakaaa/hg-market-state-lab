"""Minimal FastAPI application of the MO Option Chain HTTP delivery adapter.

Authority: ``guides/mo-option-chain-http-contract.md``. The application is a
delivery surface only: it exposes the HTTP contract, publishes it as OpenAPI and
turns a read failure into the contract's error envelope. It owns no market
semantics and it is not a general API platform (no auth, no versioning, no
schema registry, no second endpoint family).

Run it (the repository stays Poetry ``package-mode = false``, so the executable
shim supplies ``src/`` on the import path):

    poetry run python scripts/api.py
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .endpoint import ROUTE_PATH, router
from .errors import (
    CONTRACT_QUERY_PARAMS,
    QUERY_PARAM_OPTION_PRODUCT,
    QUERY_PARAM_PRICE_TYPE,
    QUERY_PARAM_TARGET_TRADE_DATE,
    REQUIRED_QUERY_PARAMS,
    ChainApiError,
    ChainErrorBody,
    ChainErrorKind,
    ChainErrorResponse,
)

TITLE = "hg-market-state-lab MO Option Chain API"
VERSION = "0.1.0"

# The status FastAPI documents by convention for a rejected request, and which
# this adapter answers with its own 400 error envelope instead.
VALIDATION_STATUS = "422"

# Request-validation locations that name a query parameter of the contract.
VALIDATION_PARAMS: dict[str, str] = {
    QUERY_PARAM_TARGET_TRADE_DATE: QUERY_PARAM_TARGET_TRADE_DATE,
    QUERY_PARAM_OPTION_PRODUCT: QUERY_PARAM_OPTION_PRODUCT,
    QUERY_PARAM_PRICE_TYPE: QUERY_PARAM_PRICE_TYPE,
}


def missing_param(request: Request) -> str | None:
    """The first required query parameter the request omitted."""
    for param in REQUIRED_QUERY_PARAMS:
        if param not in request.query_params:
            return param
    return None


def unexpected_param(request: Request) -> str | None:
    """The first query parameter the contract does not accept, if any.

    A parameter the contract does not declare has no ``error.param`` field to be
    attributed to, so it is reported by ``error.detail`` instead.
    """
    for name in request.query_params:
        if name not in CONTRACT_QUERY_PARAMS:
            return name
    return None


def error_location(error: dict[str, object]) -> tuple[str, ...]:
    """The normalized ``loc`` of one request-validation error."""
    location = error.get("loc")
    if isinstance(location, list | tuple):
        return tuple(str(part) for part in location)
    return ()


def validation_param(request: Request, errors: list[dict[str, object]]) -> str | None:
    """The query parameter a request-validation error is about.

    Only a parameter the contract declares can be named here: a parameter the
    contract does not accept has no contract field to attribute the failure to.
    """
    missing = missing_param(request)
    if missing is not None:
        return missing
    unexpected = unexpected_param(request)
    if unexpected is not None:
        return None
    for error in errors:
        for part in reversed(error_location(error)):
            if part in VALIDATION_PARAMS:
                return VALIDATION_PARAMS[part]
    return None


def validation_detail(request: Request, errors: list[dict[str, object]]) -> str:
    """A short human-readable summary of what made the request invalid."""
    missing = missing_param(request)
    if missing is not None:
        return f"missing required query parameter {missing}"
    unexpected = unexpected_param(request)
    if unexpected is not None:
        return f"unsupported query parameter {unexpected}"
    if not errors:
        return "invalid request"
    location = error_location(errors[0])
    name = location[-1] if location else "request"
    return f"invalid value for {name}: {errors[0].get('msg', 'invalid request')}"


def error_response(error: ChainApiError) -> JSONResponse:
    """Serialize one transport failure as the contract's error envelope."""
    body = ChainErrorResponse(
        error=ChainErrorBody(kind=error.kind, detail=error.detail, param=error.param)
    )
    return JSONResponse(status_code=error.status_code, content=body.model_dump(mode="json"))


def contract_openapi(application: FastAPI) -> Callable[[], dict[str, Any]]:
    """Build the OpenAPI generator that publishes exactly the contract.

    FastAPI documents a request-validation response (HTTP 422) for every
    operation with parameters. This adapter never produces it: a rejected request
    answers with the contract's own ``invalid_request`` envelope (HTTP 400). The
    published contract therefore drops that one entry, so the web UI sees the
    statuses the adapter can actually return and no second error shape.

    ``FastAPI.openapi`` is replaced, so the schema it builds is captured before
    the replacement to avoid calling the override recursively.
    """
    application.setup()
    build_openapi = application.openapi

    def openapi() -> dict[str, Any]:
        document: dict[str, Any] = deepcopy(build_openapi())
        operation = document["paths"][ROUTE_PATH]["get"]
        operation["responses"].pop(VALIDATION_STATUS, None)
        schemas = document["components"]["schemas"]
        if "HTTPValidationError" in schemas and not any(
            VALIDATION_STATUS in entry["responses"]
            for path in document["paths"].values()
            for entry in path.values()
        ):
            schemas.pop("HTTPValidationError", None)
        return document

    return openapi


def create_app() -> FastAPI:
    """Build the delivery adapter application."""
    application = FastAPI(
        title=TITLE,
        version=VERSION,
        summary="Minimal HTTP delivery adapter for the MO Option Chain read contract.",
    )
    application.openapi = contract_openapi(application)  # type: ignore[method-assign]

    @application.exception_handler(ChainApiError)
    async def handle_chain_api_error(_request: Request, exc: ChainApiError) -> JSONResponse:
        return error_response(exc)

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Report a rejected request as ``invalid_request`` (HTTP 400).

        The contract defines 400 for an invalid request and accepts exactly three
        query parameters, so an omitted required parameter, an unparsable value
        and an unknown parameter are all normalized here rather than exposed as
        FastAPI's own 422 error shape.
        """
        errors = [dict(error) for error in exc.errors()]
        return error_response(
            ChainApiError(
                ChainErrorKind.INVALID_REQUEST,
                validation_detail(request, errors),
                validation_param(request, errors),  # type: ignore[arg-type]
            )
        )

    application.include_router(router)
    return application


app = create_app()

__all__ = ["ROUTE_PATH", "app", "create_app"]
