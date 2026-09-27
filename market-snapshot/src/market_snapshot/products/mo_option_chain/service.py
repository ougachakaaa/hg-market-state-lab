"""Data Service ``mo-option-chain``: the application boundary of its read model.

Authority: ``products/mo_option_chain/ARCHITECTURE.md`` (product identity, query identity,
invariants), ``products/mo_option_chain/data.md`` (Source facts, Raw scope,
universe, completeness) and ``products/mo_option_chain/read-contract.md``
(price / null / grouping / ordering / response / failure).

What this module owns:

* the read-model data types of the option-chain read contract;
* the query identity a caller resolves before any data preparation (section 3 of
  ``products/mo_option_chain/ARCHITECTURE.md``);
* the failure categories of the read contract (section 11) as Python types;
* orchestration of the five Captures, goal-scoped Raw and Preparation.

What this module deliberately does not do:

* it does not define HTTP semantics: status codes, the error envelope and the
  DTOs belong to the HTTP delivery adapter
  (``products/mo_option_chain/http-contract.md``);
* it does not reimplement Capture endpoint queries or Preparation projections.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ... import artifacts
from ...capture import (
    im_futures_basic,
    im_futures_daily,
    index_daily,
    mo_option_basic,
    mo_option_daily,
)
from ...sources import tushare
from . import preparation

# Product identifier for its own request-scoped Raw artifacts.
SERVICE_ID = "mo-option-chain"
RAW_SUBDIR = "mo-option-chain"

SERVICE_DESCRIPTION = (
    "deterministic read model of the complete MO CSI1000 index option chain "
    "of one target trade date"
)


class OptionProduct(StrEnum):
    """The option products V1 can serve.

    Authority: ``products/mo_option_chain/ARCHITECTURE.md`` sections 3 and 4. The single
    executable source of truth for the product dimension: the HTTP request, the
    resolved query identity, the read model and the response DTO all use this
    type, so a future ``IO`` / ``HO`` extends one authoritative type instead of
    two that could drift.
    """

    MO = "MO"


#: The products V1 supports, derived from the authoritative type above.
SUPPORTED_OPTION_PRODUCTS: tuple[str, ...] = tuple(product.value for product in OptionProduct)

#: The product a caller gets when the contract resolves one without an explicit
#: choice; V1 has exactly one.
DEFAULT_OPTION_PRODUCT = OptionProduct.MO

# The date representation the query identity requires. The HTTP layer validates
# the caller's literal date string against it and passes the canonical
# ``YYYY-MM-DD`` string on; the data product owns the representation, not the
# transport layer.
TARGET_TRADE_DATE_FORMAT = "YYYY-MM-DD"


class PriceType(StrEnum):
    """The selected price semantics V1 supports.

    Authority: ``products/mo_option_chain/read-contract.md`` section 1. ``settle``,
    ``pre_close``, ``pre_settle`` and ``volume`` are deliberately absent.
    """

    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"


# The authority default when the caller omits ``price_type``.
DEFAULT_PRICE_TYPE = PriceType.CLOSE


class ChainReadError(Exception):
    """A ``mo-option-chain`` request that cannot be served as requested.

    Subclasses are the read contract's failure categories, so a delivery surface
    can map them without inspecting how the chain is produced.
    """

    #: The read-contract failure category this error reports.
    kind = "chain_read_error"


class InvalidQueryError(ChainReadError):
    """The query identity itself is not usable (bad date format, missing input)."""

    kind = "invalid_query"


class UnsupportedQueryError(ChainReadError):
    """The query identity is well formed but asks for something V1 does not support."""

    kind = "unsupported_query"


class DateNotAvailableError(ChainReadError):
    """``target_trade_date`` is valid but cannot be served by the Source.

    Either it is not a trading date, or the required option-chain Source facts do
    not exist for it. There is no fallback date, no nearest trading date and no
    silent date substitution.
    """

    kind = "date_not_available"


class OptionChainUnavailableError(ChainReadError):
    """The complete chain of a legal query cannot be produced.

    Covers the read contract's structural and completeness failures: the
    product-to-underlying mapping, the active contract universe, a missing daily
    row of an active contract, duplicate or inconsistent contract identity, a
    missing or malformed structural field, and an unavailable or malformed
    underlying selected price. The whole request fails; a partial chain is never
    returned.
    """

    kind = "option_chain_unavailable"


@dataclass(frozen=True)
class ChainQuery:
    """One resolved read query identity.

    ``target_trade_date + option_product + resolved price_type``
    (``products/mo_option_chain/ARCHITECTURE.md`` section 3).
    ``price_type`` is always resolved before the query reaches a provider; an
    omitted value is never carried here.
    """

    target_trade_date: str
    option_product: OptionProduct
    price_type: PriceType


@dataclass(frozen=True)
class UnderlyingRef:
    """The shared underlying reference of one chain."""

    instrument_id: str
    price: float


@dataclass(frozen=True)
class FuturesRef:
    """The IM futures reference when one MO expiry has a structural match."""

    instrument_id: str
    price: float


@dataclass(frozen=True)
class OptionPoint:
    """One option contract in one chain.

    ``expiry_date`` and the call / put grouping are expressed by the parent
    :class:`ExpiryGroup`; a point does not repeat them
    (``products/mo_option_chain/read-contract.md`` section 6).

    ``price`` is ``None`` when the selected ``price_type`` field has no Source
    fact for this contract. A numeric ``0`` is a legal fact and stays ``0``; it
    is never replaced by ``None``, and a ``None`` price is never dropped, zero
    filled or substituted (read contract section 3).
    """

    instrument_id: str
    strike: float
    price: float | None


@dataclass(frozen=True)
class ExpiryGroup:
    """One expiry of the chain: its calls and its puts, already ordered."""

    expiry_date: str
    futures: FuturesRef | None
    calls: tuple[OptionPoint, ...]
    puts: tuple[OptionPoint, ...]


@dataclass(frozen=True)
class OptionChain:
    """The read model of one request-scoped MO option chain.

    Self-describing (read contract section 9): it carries the resolved query
    identity and the underlying identity, so a successful response never depends
    on a client's local state to be interpretable.
    """

    target_trade_date: str
    option_product: OptionProduct
    price_type: PriceType
    underlying: UnderlyingRef
    expiries: tuple[ExpiryGroup, ...]


@dataclass(frozen=True)
class ChainReadResult:
    """What one read-model provider returns: a chain, or a read failure.

    The boundary is a value rather than an exception so a delivery surface maps
    a failure without a ``try`` / ``except`` chain.
    """

    chain: OptionChain | None = None
    error: ChainReadError | None = None

    def __post_init__(self) -> None:
        if (self.chain is None) == (self.error is None):
            raise ValueError("a chain read result carries exactly one of chain / error")


class ServiceNotWiredError(ChainReadError):
    """Bootstrap/test compatibility failure; the default provider is real."""

    kind = "service_not_wired"


# Kept for bootstrap/test compatibility; not the default runtime result.
SERVICE_NOT_WIRED_RESULT = ChainReadResult(
    error=ServiceNotWiredError("the mo-option-chain read model provider is not wired yet")
)


def read_chain_not_wired(_query: ChainQuery) -> ChainReadResult:
    """The optional bootstrap provider: always reports "not wired yet".

    It carries no market data and no fallback. The default runtime provider is
    :func:`read_chain`; this function remains for isolated compatibility tests.
    """
    return SERVICE_NOT_WIRED_RESULT


#: The application boundary the HTTP delivery adapter depends on: one resolved
#: query identity in, one :class:`ChainReadResult` out.
ChainReadProvider = Callable[[ChainQuery], ChainReadResult]


def query_error(query: ChainQuery) -> ChainReadError | None:
    """Validate a resolved application query before Source client creation."""
    try:
        tushare.to_tushare_date(query.target_trade_date)
    except tushare.TushareDateError as exc:
        return InvalidQueryError(str(exc))
    if query.option_product is not OptionProduct.MO or not isinstance(query.price_type, PriceType):
        return UnsupportedQueryError("unsupported option product or price type")
    return None


def to_read_model(query: ChainQuery, prepared: preparation.PreparedChain) -> OptionChain:
    """Wrap the prepared, already grouped facts in the application boundary types."""

    def points(rows: list[preparation.PreparedPoint]) -> tuple[OptionPoint, ...]:
        return tuple(OptionPoint(**row) for row in rows)

    return OptionChain(
        target_trade_date=query.target_trade_date,
        option_product=query.option_product,
        price_type=query.price_type,
        underlying=UnderlyingRef(
            instrument_id=prepared["underlying_instrument_id"],
            price=prepared["underlying_price"],
        ),
        expiries=tuple(
            ExpiryGroup(
                expiry_date=group["expiry_date"],
                futures=FuturesRef(**group["futures"]) if group["futures"] is not None else None,
                calls=points(group["calls"]),
                puts=points(group["puts"]),
            )
            for group in prepared["expiries"]
        ),
    )


def read_chain_with_api(
    api: tushare.TushareApi, query: ChainQuery, raw_root: Path | None = None
) -> ChainReadResult:
    """Run the real data path with an injected Source client (also used by tests)."""
    error = query_error(query)
    if error is not None:
        return ChainReadResult(error=error)

    raw_dir = (
        (artifacts.RAW_DIR if raw_root is None else raw_root)
        / RAW_SUBDIR
        / query.target_trade_date
    )
    try:
        index_facts = index_daily.collect_index_daily(
            query.target_trade_date,
            lambda **kwargs: index_daily.query_index_daily(api, **kwargs),
            index_codes=(preparation.UNDERLYING_ID,),
        )
    except index_daily.NoIndexDataError as exc:
        return ChainReadResult(error=DateNotAvailableError(str(exc)))
    except Exception as exc:
        # Tushare's client can raise a plain Exception for a Source API error.
        # Only an empty index observation is evidence for an unavailable date.
        return ChainReadResult(error=OptionChainUnavailableError(str(exc)))

    try:
        artifacts.write_raw_artifact(index_facts, raw_dir, index_daily.RAW_ARTIFACT)
        basic_facts = mo_option_basic.capture(api, query.target_trade_date)
        artifacts.write_raw_artifact(basic_facts, raw_dir, mo_option_basic.RAW_ARTIFACT)
        daily_facts = mo_option_daily.capture(api, query.target_trade_date, basic_facts)
        artifacts.write_raw_artifact(daily_facts, raw_dir, mo_option_daily.RAW_ARTIFACT)
        im_basic_facts = im_futures_basic.capture(api, query.target_trade_date)
        artifacts.write_raw_artifact(im_basic_facts, raw_dir, im_futures_basic.RAW_ARTIFACT)
        im_daily_facts = im_futures_daily.capture_target_date(
            api, query.target_trade_date, im_basic_facts
        )
        artifacts.write_raw_artifact(im_daily_facts, raw_dir, im_futures_daily.RAW_ARTIFACT)
    except Exception as exc:
        # The Source SDK raises plain Exception for API failures; no partial
        # chain can be published when any Capture or Raw write fails.
        return ChainReadResult(error=OptionChainUnavailableError(str(exc)))
    try:
        prepared = preparation.build_chain(query.target_trade_date, query.price_type.value, raw_dir)
    except preparation.PreparationError as exc:
        return ChainReadResult(error=OptionChainUnavailableError(str(exc)))
    return ChainReadResult(chain=to_read_model(query, prepared))


def read_chain(query: ChainQuery) -> ChainReadResult:
    """Production provider: create the configured Source client, then read a chain."""
    error = query_error(query)
    if error is not None:
        return ChainReadResult(error=error)
    try:
        api = tushare.create_tushare_api(tushare.get_tushare_token())
    except Exception as exc:
        # Client creation failures (including credentials) are service failures,
        # never evidence that the requested trade date is unavailable.
        return ChainReadResult(error=OptionChainUnavailableError(str(exc)))
    return read_chain_with_api(api, query)
