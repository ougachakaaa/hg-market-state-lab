"""MO Premium Plane HTTP error envelope and status mapping."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

ErrorParam = Literal["as_of", "option_product", "price_type"]
QUERY_PARAM_AS_OF: ErrorParam = "as_of"
QUERY_PARAM_OPTION_PRODUCT: ErrorParam = "option_product"
QUERY_PARAM_PRICE_TYPE: ErrorParam = "price_type"
CONTRACT_QUERY_PARAMS = frozenset(
    (QUERY_PARAM_AS_OF, QUERY_PARAM_OPTION_PRODUCT, QUERY_PARAM_PRICE_TYPE)
)
REQUIRED_QUERY_PARAMS: tuple[ErrorParam, ...] = (
    QUERY_PARAM_AS_OF,
    QUERY_PARAM_OPTION_PRODUCT,
)


class PremiumErrorKind(StrEnum):
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_QUERY = "unsupported_query"
    DATE_NOT_AVAILABLE = "date_not_available"
    PREMIUM_PLANE_UNAVAILABLE = "premium_plane_unavailable"


ERROR_STATUS: dict[PremiumErrorKind, int] = {
    PremiumErrorKind.INVALID_REQUEST: 400,
    PremiumErrorKind.UNSUPPORTED_QUERY: 400,
    PremiumErrorKind.DATE_NOT_AVAILABLE: 404,
    PremiumErrorKind.PREMIUM_PLANE_UNAVAILABLE: 503,
}


class PremiumErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: PremiumErrorKind
    detail: str
    param: Annotated[ErrorParam | None, Field(default=None)]


class PremiumErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: PremiumErrorBody


class PremiumApiError(Exception):
    def __init__(
        self, kind: PremiumErrorKind, detail: str, param: ErrorParam | None = None
    ) -> None:
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
        self.param = param

    @property
    def status_code(self) -> int:
        return ERROR_STATUS[self.kind]
