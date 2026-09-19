"""Data Service ``mo-option-chain``: the application boundary of its read model.

Authority: ``guides/mo-option-chain.md`` (product identity, query identity,
invariants), ``guides/mo-option-chain-data.md`` (Source facts, Raw scope,
universe, completeness) and ``guides/mo-option-chain-read-contract.md``
(price / null / grouping / ordering / response / failure).

What this module owns:

* the read-model data types of the option-chain read contract;
* the query identity a caller resolves before any data preparation (section 3 of
  ``guides/mo-option-chain.md``);
* the failure categories of the read contract (section 11) as Python types, so a
  delivery surface can present a failure without knowing how the chain is built.

What this module deliberately does not do:

* it does not implement MO Option Chain Preparation, it does not read Raw
  Artifacts and it does not call the Tushare Source: the real read-model provider
  (``Capture -> Raw -> Preparation -> read model``) is still deferred, and only
  the boundary it will plug into is fixed here;
* it does not define HTTP semantics: status codes, the error envelope and the
  DTOs belong to the HTTP delivery adapter
  (``guides/mo-option-chain-http-contract.md``);
* it does not own ``option_product -> underlying`` mapping, universe, fallback or
  any other market semantics as data: those live in the Guides above.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

# The Data Service id, as declared in the static catalog
# (``guides/data-services.md`` section 2).
SERVICE_ID = "mo-option-chain"

SERVICE_DESCRIPTION = (
    "deterministic read model of the complete MO CSI1000 index option chain "
    "of one target trade date"
)

class OptionProduct(StrEnum):
    """The option products V1 can serve.

    Authority: ``guides/mo-option-chain.md`` sections 3 and 4. The single
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

    Authority: ``guides/mo-option-chain-read-contract.md`` section 1. ``settle``,
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
    (``guides/mo-option-chain.md`` section 3). ``price_type`` is always resolved
    before the query reaches a provider; an omitted value is never carried here.
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
class OptionPoint:
    """One option contract in one chain.

    ``expiry_date`` and the call / put grouping are expressed by the parent
    :class:`ExpiryGroup`; a point does not repeat them
    (``guides/mo-option-chain-read-contract.md`` section 6).

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
    a failure without a ``try`` / ``except`` chain, and an unwired provider is a
    value too (:data:`SERVICE_NOT_WIRED_RESULT`).
    """

    chain: OptionChain | None = None
    error: ChainReadError | None = None

    def __post_init__(self) -> None:
        if (self.chain is None) == (self.error is None):
            raise ValueError("a chain read result carries exactly one of chain / error")


class ServiceNotWiredError(ChainReadError):
    """The real MO Option Chain read-model provider is not wired yet.

    This is not a market-semantics failure: the Data Service
    ``Capture -> Raw -> Preparation -> read model`` implementation is still
    deferred (``guides/mo-option-chain-http-contract.md`` section 8). It exists so
    that "not wired yet" stays distinguishable from "the complete chain cannot be
    produced", and so that neither can masquerade as a successful empty chain.
    """

    kind = "service_not_wired"


# The result a provider returns while the real read-model implementation is
# deferred. The HTTP adapter maps it to its ``service_not_wired`` error kind.
SERVICE_NOT_WIRED_RESULT = ChainReadResult(
    error=ServiceNotWiredError("the mo-option-chain read model provider is not wired yet")
)


def read_chain_not_wired(_query: ChainQuery) -> ChainReadResult:
    """The V1 placeholder read-model provider: always reports "not wired yet".

    It carries no market data and no fallback: until the real provider replaces
    it, every request fails explicitly instead of inventing a chain.
    """
    return SERVICE_NOT_WIRED_RESULT


#: The application boundary the HTTP delivery adapter depends on: one resolved
#: query identity in, one :class:`ChainReadResult` out.
ChainReadProvider = Callable[[ChainQuery], ChainReadResult]
