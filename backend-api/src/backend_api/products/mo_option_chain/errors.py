"""The HTTP error envelope, error kinds and status mapping of MO Option Chain.

Authority: ``products/mo_option_chain/http-contract.md`` sections 4 and 5, which
maps the semantic failure categories of ``products/mo_option_chain/read-contract.md``
section 11 onto transport.

This module owns only the transport representation of a failure: the envelope
shape, the closed set of error kinds and their HTTP status. It adds no failure
category of its own and carries no market fact.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

#: The query parameters the contract declares, as the ``error.param`` value type.
ErrorParam = Literal[
    "target_trade_date",
    "option_product",
    "price_type",
]

# The query parameter names the contract exposes. Used for the ``error.param``
# field so a client can attach a failure to the input it sent. They are annotated
# with the contract's parameter type so a caller of the adapter stays checked.
QUERY_PARAM_TARGET_TRADE_DATE: ErrorParam = "target_trade_date"
QUERY_PARAM_OPTION_PRODUCT: ErrorParam = "option_product"
QUERY_PARAM_PRICE_TYPE: ErrorParam = "price_type"

#: The query parameters the contract accepts. A request carrying anything else is
#: a request the contract does not accept (HTTP transport contract section 2).
CONTRACT_QUERY_PARAMS: frozenset[str] = frozenset(
    (QUERY_PARAM_TARGET_TRADE_DATE, QUERY_PARAM_OPTION_PRODUCT, QUERY_PARAM_PRICE_TYPE)
)

#: The query parameters the contract requires the caller to give explicitly.
REQUIRED_QUERY_PARAMS: tuple[ErrorParam, ...] = (
    QUERY_PARAM_TARGET_TRADE_DATE,
    QUERY_PARAM_OPTION_PRODUCT,
)


class ChainErrorKind(StrEnum):
    """Closed set of MO Option Chain error kinds.

    AUTHORITY: HTTP transport contract section 5. The set is closed: a delivery
    surface may not add, merge or reinterpret kinds.
    """

    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_QUERY = "unsupported_query"
    DATE_NOT_AVAILABLE = "date_not_available"
    OPTION_CHAIN_UNAVAILABLE = "option_chain_unavailable"
    SERVICE_NOT_WIRED = "service_not_wired"


#: Error kind -> HTTP status (HTTP transport contract section 5).
ERROR_STATUS: dict[ChainErrorKind, int] = {
    ChainErrorKind.INVALID_REQUEST: 400,
    ChainErrorKind.UNSUPPORTED_QUERY: 400,
    ChainErrorKind.DATE_NOT_AVAILABLE: 404,
    ChainErrorKind.OPTION_CHAIN_UNAVAILABLE: 503,
    ChainErrorKind.SERVICE_NOT_WIRED: 503,
}


class ChainErrorBody(BaseModel):
    """The single error object of every non-2xx response body."""

    model_config = ConfigDict(extra="forbid")

    kind: Annotated[ChainErrorKind, Field(description="Closed error kind; branch on this.")]
    detail: Annotated[
        str,
        Field(description="Human-readable explanation. Not a stable contract."),
    ]
    param: Annotated[
        ErrorParam | None,
        Field(
            default=None,
            description="Query parameter the failure is attributed to, when applicable.",
        ),
    ]


class ChainErrorResponse(BaseModel):
    """The error envelope: the full body of every non-2xx response."""

    model_config = ConfigDict(extra="forbid")

    error: ChainErrorBody


class ChainApiError(Exception):
    """A transport failure of the delivery adapter.

    It is raised only for transport-level outcomes. Semantic failures arrive as a
    :class:`~market_snapshot.products.mo_option_chain.service.ChainReadError` and are
    mapped by the adapter, never by this module.
    """

    def __init__(self, kind: ChainErrorKind, detail: str, param: ErrorParam | None = None) -> None:
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
        self.param = param

    @property
    def status_code(self) -> int:
        return ERROR_STATUS[self.kind]
