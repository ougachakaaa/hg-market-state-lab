"""The MO Option Chain HTTP endpoint: transport only.

Authority: ``products/mo_option_chain/http-contract.md``.

The endpoint resolves the request's query identity, asks the application boundary
(``data_snapshot.products.mo_option_chain.service``) for the read model, converts it to
the response DTO and maps a read failure to the error envelope plus its HTTP
status.

It owns no market semantics. It does not decide the option product's underlying,
the active contract universe, the selected price, the grouping or the ordering,
and it never fills, drops or substitutes a fact: all of that is owned by
``products/mo_option_chain/ARCHITECTURE.md`` and
``products/mo_option_chain/read-contract.md``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from data_snapshot.products.mo_option_chain import service

from .errors import (
    CONTRACT_QUERY_PARAMS,
    QUERY_PARAM_PRICE_TYPE,
    QUERY_PARAM_TARGET_TRADE_DATE,
    ChainApiError,
    ChainErrorKind,
    ChainErrorResponse,
    ErrorParam,
)
from .schemas import (
    ExpiryGroupDTO,
    FuturesRefDTO,
    IsoDate,
    OptionChainDTO,
    OptionPointDTO,
    UnderlyingRefDTO,
)

ROUTE_PATH = "/mo-option-chain"

router = APIRouter()


def get_chain_read_provider() -> service.ChainReadProvider:
    """Return the real application provider used by the default HTTP runtime."""
    return service.read_chain


def resolve_chain_query(
    request: Request,
    target_trade_date: Annotated[
        IsoDate,
        Query(
            description=(
                "Explicit target trade date, exactly YYYY-MM-DD. Not today / latest / "
                "current date; there is no fallback date."
            )
        ),
    ],
    option_product: Annotated[
        service.OptionProduct,
        Query(description="Option product. V1 supports MO only."),
    ],
    price_type: Annotated[
        service.PriceType,
        Query(description="Selected price semantics. Defaults to close when omitted."),
    ] = service.DEFAULT_PRICE_TYPE,
) -> service.ChainQuery:
    """Resolve the read query identity from the request.

    Only transport-level input shape is handled here: the date must already have
    passed the strict ``YYYY-MM-DD`` validation, an undeclared parameter is
    rejected, and the resolved identity (``target_trade_date + option_product +
    resolved price_type``) is handed on as the data product's canonical
    ``YYYY-MM-DD`` string. Whether a well-formed query can be served at all (for
    example a target date the Source has no facts for) is not a transport
    question and stays with the read model.
    """
    unexpected = next(
        (param for param in request.query_params if param not in CONTRACT_QUERY_PARAMS), None
    )
    if unexpected is not None:
        raise ChainApiError(
            ChainErrorKind.INVALID_REQUEST,
            f"unsupported query parameter {unexpected}",
        )
    return service.ChainQuery(
        target_trade_date=target_trade_date.isoformat(),
        option_product=option_product,
        price_type=price_type,
    )


#: Read failure category -> wire error kind (HTTP transport contract section 5).
CHAIN_ERROR_KINDS: dict[type[service.ChainReadError], ChainErrorKind] = {
    service.InvalidQueryError: ChainErrorKind.INVALID_REQUEST,
    service.UnsupportedQueryError: ChainErrorKind.UNSUPPORTED_QUERY,
    service.DateNotAvailableError: ChainErrorKind.DATE_NOT_AVAILABLE,
    service.OptionChainUnavailableError: ChainErrorKind.OPTION_CHAIN_UNAVAILABLE,
    service.ServiceNotWiredError: ChainErrorKind.SERVICE_NOT_WIRED,
}

# Which query parameter a read failure is attributed to, when the failure is
# about one input rather than about the chain as a whole.
READ_ERROR_PARAMS: dict[type[service.ChainReadError], ErrorParam] = {
    service.InvalidQueryError: QUERY_PARAM_TARGET_TRADE_DATE,
    service.UnsupportedQueryError: QUERY_PARAM_PRICE_TYPE,
    service.DateNotAvailableError: QUERY_PARAM_TARGET_TRADE_DATE,
}


def chain_error_kind(error: service.ChainReadError) -> ChainErrorKind:
    """The wire error kind of a read failure."""
    for error_type, kind in CHAIN_ERROR_KINDS.items():
        if isinstance(error, error_type):
            return kind
    raise ChainApiError(
        ChainErrorKind.OPTION_CHAIN_UNAVAILABLE,
        "the chain read model reported an unmapped failure",
    )


def chain_error_param(error: service.ChainReadError) -> ErrorParam | None:
    """The query parameter a read failure is attributed to, if any."""
    for error_type, param in READ_ERROR_PARAMS.items():
        if isinstance(error, error_type):
            return param
    return None


def to_chain_dto(chain: service.OptionChain) -> OptionChainDTO:
    """Convert the read model of one chain to the response DTO.

    The conversion is total and lossless: a ``None`` selected price stays
    ``None``, a ``0`` price stays ``0`` and no contract is added or removed, so
    the payload is the read contract's semantic response rather than a
    transport-invented variant of it.
    """
    return OptionChainDTO(
        target_trade_date=chain.target_trade_date,
        option_product=chain.option_product,
        price_type=chain.price_type,
        underlying=UnderlyingRefDTO(
            instrument_id=chain.underlying.instrument_id,
            price=chain.underlying.price,
        ),
        expiries=[
            ExpiryGroupDTO(
                expiry_date=group.expiry_date,
                futures=FuturesRefDTO(
                    instrument_id=group.futures.instrument_id,
                    price=group.futures.price,
                ) if group.futures is not None else None,
                calls=[to_point_dto(point) for point in group.calls],
                puts=[to_point_dto(point) for point in group.puts],
            )
            for group in chain.expiries
        ],
    )


def to_point_dto(point: service.OptionPoint) -> OptionPointDTO:
    """Convert one read-model option point to its DTO."""
    return OptionPointDTO(
        instrument_id=point.instrument_id,
        strike=point.strike,
        price=point.price,
    )


async def read_chain(
    provider: Annotated[service.ChainReadProvider, Depends(get_chain_read_provider)],
    query: Annotated[service.ChainQuery, Depends(resolve_chain_query)],
) -> OptionChainDTO:
    """Read one chain through the application boundary and serialize it.

    A failure of the boundary is reported as the corresponding error envelope and
    status; a successful read becomes the self-describing success response.
    """
    result = provider(query)
    if result.error is not None:
        raise ChainApiError(
            chain_error_kind(result.error),
            str(result.error),
            chain_error_param(result.error),
        )
    assert result.chain is not None
    return to_chain_dto(result.chain)


@router.get(
    ROUTE_PATH,
    operation_id="readMoOptionChain",
    summary="Read the MO CSI1000 option chain of one target trade date",
    response_model=OptionChainDTO,
    responses={
        400: {"model": ChainErrorResponse, "description": "Invalid or unsupported request."},
        404: {
            "model": ChainErrorResponse,
            "description": "The target trade date cannot be served by the Source.",
        },
        503: {
            "model": ChainErrorResponse,
            "description": "The complete chain cannot currently be produced.",
        },
    },
)
async def read_mo_option_chain(
    chain: Annotated[OptionChainDTO, Depends(read_chain)],
) -> OptionChainDTO:
    """``GET /mo-option-chain`` - the only MO Option Chain read surface of V1."""
    return chain
