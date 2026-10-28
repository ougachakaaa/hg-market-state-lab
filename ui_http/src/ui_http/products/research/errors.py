"""Closed, safe Research-only transport error vocabulary."""

from typing import Literal

from fastapi.responses import JSONResponse

from .requests import WireModel

type ErrorKind = Literal[
    "invalid_request",
    "capability_not_found",
    "request_too_large",
    "execution_busy",
    "internal_error",
]


class ResearchErrorBody(WireModel):
    kind: ErrorKind
    detail: str
    param: str | None


class ResearchErrorResponse(WireModel):
    error: ResearchErrorBody


class ResearchApiError(Exception):
    def __init__(self, kind: ErrorKind, detail: str, param: str | None = None) -> None:
        self.kind, self.detail, self.param = kind, detail, param
        self.status_code = {
            "invalid_request": 400,
            "capability_not_found": 404,
            "request_too_large": 400,
            "execution_busy": 409,
            "internal_error": 500,
        }[kind]
        super().__init__(detail)


def error_response(error: ResearchApiError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=ResearchErrorResponse(
            error=ResearchErrorBody(kind=error.kind, detail=error.detail, param=error.param),
        ).model_dump(mode="json"),
    )
