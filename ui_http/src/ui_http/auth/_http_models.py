"""Auth transport values, independent of every business product's error enum."""

from typing import Any, Literal

from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

ErrorKind = Literal[
    "invalid_request",
    "authentication_required",
    "invalid_credentials",
    "origin_forbidden",
    "rate_limited",
    "internal_error",
]
DETAILS: dict[ErrorKind, tuple[int, str]] = {
    "invalid_request": (400, "Invalid authentication request."),
    "authentication_required": (401, "Authentication required."),
    "invalid_credentials": (401, "Invalid username or password."),
    "origin_forbidden": (403, "Same-origin request required."),
    "rate_limited": (429, "Too many requests."),
    "internal_error": (500, "Authentication service unavailable."),
}


class AuthErrorBody(BaseModel):
    kind: ErrorKind
    detail: str
    param: None = None


class AuthErrorResponse(BaseModel):
    error: AuthErrorBody


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    username: str = Field(max_length=64)
    password: str = Field(min_length=12, max_length=128, repr=False)


class ActiveIdentity(BaseModel):
    id: str
    username: str
    status: Literal["active"] = "active"


class Accepted(BaseModel):
    message: Literal["Registration request accepted."] = "Registration request accepted."


class AuthHttpError(Exception):
    def __init__(self, kind: ErrorKind, retry: int | None = None) -> None:
        self.kind, self.retry = kind, retry
        super().__init__(DETAILS[kind][1])

    def response(self) -> JSONResponse:
        status, detail = DETAILS[self.kind]
        headers = {"Cache-Control": "no-store"}
        if self.retry is not None:
            headers["Retry-After"] = str(self.retry)
        return JSONResponse(
            status_code=status,
            headers=headers,
            content={
                "error": {"kind": self.kind, "detail": detail, "param": None},
            },
        )


ACCESS_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": AuthErrorResponse, "description": detail}
    for kind, (status, detail) in DETAILS.items()
    if kind in {"authentication_required", "origin_forbidden", "internal_error"}
}
