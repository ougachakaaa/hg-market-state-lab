"""Product-only FastAPI application used to publish the Premium contract."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from fastapi import FastAPI

from ui_http.auth._http import install_auth

from .endpoint import router


def contract_openapi(application: FastAPI) -> Callable[[], dict[str, Any]]:
    """Remove FastAPI's unused 422 response from the published contract."""
    build_openapi = application.openapi

    def openapi() -> dict[str, Any]:
        document: dict[str, Any] = deepcopy(build_openapi())
        for path in document["paths"].values():
            for operation in path.values():
                operation["responses"].pop("422", None)
        schemas = document["components"]["schemas"]
        if "HTTPValidationError" in schemas:
            schemas.pop("HTTPValidationError", None)
        return document

    return openapi


def create_app() -> FastAPI:
    application = FastAPI(
        title="hg-market-state-lab MO Premium Plane API",
        version="0.1.0",
        summary="Minimal HTTP delivery adapter for the MO Premium Plane contract.",
    )
    application.openapi = contract_openapi(application)  # type: ignore[method-assign]
    install_auth(application)
    application.include_router(router)
    return application


app = create_app()

__all__ = ["app", "create_app"]
