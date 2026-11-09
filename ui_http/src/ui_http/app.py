"""Repository FastAPI composition root for owning-module product adapters.

This module composes the independent MO Option Chain, MO Premium Plane, Research
and Futures Basis Research adapters. It owns runtime wiring only; each product-local
bounded context keeps ownership of its router, query contract, DTOs and error envelope.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from copy import deepcopy
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ui_http.auth._http import install_auth

from .products.futures_basis_research.endpoint import (
    install_contract as install_futures_basis_contract,
)
from .products.futures_basis_research.endpoint import router as futures_basis_router
from .products.futures_basis_research.runtime import initialize as initialize_futures_basis
from .products.mo_option_chain.endpoint import router as chain_router
from .products.mo_option_chain.errors import (
    CONTRACT_QUERY_PARAMS as CHAIN_CONTRACT_QUERY_PARAMS,
)
from .products.mo_option_chain.errors import (
    QUERY_PARAM_OPTION_PRODUCT,
    QUERY_PARAM_PRICE_TYPE,
    QUERY_PARAM_TARGET_TRADE_DATE,
    ChainApiError,
    ChainErrorBody,
    ChainErrorKind,
    ChainErrorResponse,
)
from .products.mo_option_chain.errors import (
    REQUIRED_QUERY_PARAMS as CHAIN_REQUIRED_QUERY_PARAMS,
)
from .products.mo_option_premium.endpoint import ROUTE_PATH as PREMIUM_ROUTE_PATH
from .products.mo_option_premium.endpoint import router as premium_router
from .products.mo_option_premium.errors import (
    CONTRACT_QUERY_PARAMS as PREMIUM_CONTRACT_QUERY_PARAMS,
)
from .products.mo_option_premium.errors import (
    QUERY_PARAM_AS_OF,
    PremiumApiError,
    PremiumErrorBody,
    PremiumErrorKind,
    PremiumErrorResponse,
)
from .products.mo_option_premium.errors import (
    REQUIRED_QUERY_PARAMS as PREMIUM_REQUIRED_QUERY_PARAMS,
)
from .products.research.endpoint import is_research_path
from .products.research.endpoint import router as research_router
from .products.research.errors import ResearchApiError
from .products.research.errors import error_response as research_error_response
from .products.research_publication.endpoint import router as publication_router

TITLE = "hg-market-state-lab Market Snapshot API"
VERSION = "0.1.0"
VALIDATION_STATUS = "422"

CHAIN_VALIDATION_PARAMS: dict[str, str] = {
    QUERY_PARAM_TARGET_TRADE_DATE: QUERY_PARAM_TARGET_TRADE_DATE,
    QUERY_PARAM_OPTION_PRODUCT: QUERY_PARAM_OPTION_PRODUCT,
    QUERY_PARAM_PRICE_TYPE: QUERY_PARAM_PRICE_TYPE,
}
PREMIUM_VALIDATION_PARAMS: dict[str, str] = {
    QUERY_PARAM_AS_OF: QUERY_PARAM_AS_OF,
    QUERY_PARAM_OPTION_PRODUCT: QUERY_PARAM_OPTION_PRODUCT,
    QUERY_PARAM_PRICE_TYPE: QUERY_PARAM_PRICE_TYPE,
}


def contract_params(request: Request) -> tuple[frozenset[str], tuple[str, ...], dict[str, str]]:
    """Return the product-owned closed query contract for one composed route."""
    if request.url.path == PREMIUM_ROUTE_PATH:
        return (
            PREMIUM_CONTRACT_QUERY_PARAMS,
            PREMIUM_REQUIRED_QUERY_PARAMS,
            PREMIUM_VALIDATION_PARAMS,
        )
    return CHAIN_CONTRACT_QUERY_PARAMS, CHAIN_REQUIRED_QUERY_PARAMS, CHAIN_VALIDATION_PARAMS


def missing_param(request: Request) -> str | None:
    _, required, _ = contract_params(request)
    return next((param for param in required if param not in request.query_params), None)


def unexpected_param(request: Request) -> str | None:
    accepted, _, _ = contract_params(request)
    return next((name for name in request.query_params if name not in accepted), None)


def error_location(error: dict[str, object]) -> tuple[str, ...]:
    location = error.get("loc")
    if isinstance(location, list | tuple):
        return tuple(str(part) for part in location)
    return ()


def validation_param(request: Request, errors: list[dict[str, object]]) -> str | None:
    missing = missing_param(request)
    if missing is not None:
        return missing
    if unexpected_param(request) is not None:
        return None
    _, _, parameters = contract_params(request)
    for error in errors:
        for part in reversed(error_location(error)):
            if part in parameters:
                return parameters[part]
    return None


def validation_detail(request: Request, errors: list[dict[str, object]]) -> str:
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


def chain_error_response(error: ChainApiError) -> JSONResponse:
    body = ChainErrorResponse(
        error=ChainErrorBody(kind=error.kind, detail=error.detail, param=error.param)
    )
    return JSONResponse(status_code=error.status_code, content=body.model_dump(mode="json"))


def premium_error_response(error: PremiumApiError) -> JSONResponse:
    body = PremiumErrorResponse(
        error=PremiumErrorBody(kind=error.kind, detail=error.detail, param=error.param)
    )
    return JSONResponse(status_code=error.status_code, content=body.model_dump(mode="json"))


def contract_openapi(application: FastAPI) -> Callable[[], dict[str, Any]]:
    """Remove FastAPI's unused 422 response from every product operation."""
    build_openapi = application.openapi

    def openapi() -> dict[str, Any]:
        document: dict[str, Any] = deepcopy(build_openapi())
        for path in document["paths"].values():
            for operation in path.values():
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


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    initialize_futures_basis(application)
    yield


def create_app() -> FastAPI:
    """Build the repository runtime with independent product adapters."""
    application = FastAPI(
        lifespan=lifespan,
        title=TITLE,
        version=VERSION,
        summary="HTTP delivery runtime for market-snapshot products.",
    )
    application.openapi = contract_openapi(application)  # type: ignore[method-assign]

    @application.exception_handler(ChainApiError)
    async def handle_chain_api_error(_request: Request, exc: ChainApiError) -> JSONResponse:
        return chain_error_response(exc)

    @application.exception_handler(PremiumApiError)
    async def handle_premium_api_error(
        _request: Request, exc: PremiumApiError
    ) -> JSONResponse:
        return premium_error_response(exc)

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        if is_research_path(request.url.path):
            return research_error_response(ResearchApiError(
                "invalid_request", "Body must match the strict Research request schema.",
            ))
        errors = [dict(error) for error in exc.errors()]
        detail = validation_detail(request, errors)
        param = validation_param(request, errors)
        if request.url.path == PREMIUM_ROUTE_PATH:
            return premium_error_response(
                PremiumApiError(
                    PremiumErrorKind.INVALID_REQUEST,
                    detail,
                    param,  # type: ignore[arg-type]
                )
            )
        return chain_error_response(
            ChainApiError(
                ChainErrorKind.INVALID_REQUEST,
                detail,
                param,  # type: ignore[arg-type]
            )
        )

    install_auth(application, auth_routes=True)
    application.include_router(chain_router)
    application.include_router(premium_router)
    application.include_router(research_router)
    application.include_router(publication_router)
    application.include_router(futures_basis_router)
    install_futures_basis_contract(application)
    return application


app = create_app()

__all__ = ["app", "create_app"]
