"""Pydantic DTOs of the MO Option Chain HTTP contract.

Authority: ``guides/mo-option-chain-http-contract.md`` (transport contract) over
``guides/mo-option-chain-read-contract.md`` (semantic response shape).

The DTOs are a faithful transport expression of the read model defined in
``services/mo_option_chain.py``: same fields, same names, same JSON shape, no
envelope and no extra field. They exist so the wire contract is code-generated,
validated and published as OpenAPI; they own no market semantics.

The closed value sets of the contract (option product, price type) are reused
from the application boundary instead of being re-declared here, so the request,
the read model and the response can never drift into two different value sets.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainValidator, WithJsonSchema

from ..services.mo_option_chain import OptionProduct, PriceType

__all__ = [
    "ExpiryGroupDTO",
    "FuturesRefDTO",
    "IsoDate",
    "OptionChainDTO",
    "OptionPointDTO",
    "OptionProduct",
    "PriceType",
    "UnderlyingRefDTO",
]

# The canonical target trade date representation of the query identity: exactly
# ``YYYY-MM-DD`` (``guides/mo-option-chain.md`` section 3). Anything else - a
# non-padded date, another separator, a compact date, an impossible date, a
# timestamp - is a request the contract does not accept.
ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def to_iso_date(value: object) -> date:
    """Accept exactly ``YYYY-MM-DD`` text and reject everything else.

    The validator is a plain validator on purpose: Pydantic's own date parsing
    accepts non-canonical input (``2026-9-7``, ``20260917``, a timestamp), which
    the query identity does not. Only canonical text is parsed, and every other
    value is reported as a request-validation error attributed to
    ``target_trade_date``, so the chain read boundary is never reached with a
    malformed query.
    """
    if isinstance(value, str) and ISO_DATE_PATTERN.fullmatch(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            # The shape is canonical but the date does not exist (month 13,
            # 30 February): still an invalid request, reported the same way.
            pass
    raise ValueError("target_trade_date must be exactly YYYY-MM-DD")


#: The request-side target trade date: strict ``YYYY-MM-DD`` in, canonical
#: ``YYYY-MM-DD`` out (the endpoint writes ``isoformat()`` into the query). The
#: JSON schema is declared explicitly, so the published contract still describes
#: the parameter as a date string even though a plain validator now owns parsing.
IsoDate = Annotated[
    date,
    PlainValidator(to_iso_date),
    WithJsonSchema({"type": "string", "format": "date"}, mode="validation"),
]

Strike = Annotated[float, Field(description="Option exercise price.")]
SelectedPrice = Annotated[
    float | None,
    Field(
        description=(
            "Selected price of the resolved price_type. null means the daily fact "
            "exists but the selected field has no Source fact; the contract is "
            "still present. A numeric 0 is data and is never replaced by null."
        )
    ),
]


class UnderlyingRefDTO(BaseModel):
    """The shared underlying reference of the chain."""

    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    price: Annotated[
        float,
        Field(
            description=(
                "Usable numeric underlying price under the same price_type as the "
                "options. A successful response never carries a null underlying."
            )
        ),
    ]


class FuturesRefDTO(BaseModel):
    """The IM futures reference when one expiry has a structural match."""

    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    price: float


class OptionPointDTO(BaseModel):
    """One option contract (one scatter point) of one expiry group."""

    model_config = ConfigDict(extra="forbid")

    instrument_id: Annotated[str, Field(description="Stable option instrument identity.")]
    strike: Strike
    price: SelectedPrice


class ExpiryGroupDTO(BaseModel):
    """One expiry of the chain, with its calls and puts already ordered."""

    model_config = ConfigDict(extra="forbid")

    expiry_date: Annotated[str, Field(description="Expiry date, YYYY-MM-DD.")]
    futures: Annotated[
        FuturesRefDTO | None,
        Field(description="Matched IM reference, or null when no active IM has this expiry."),
    ]
    calls: list[OptionPointDTO]
    puts: list[OptionPointDTO]


class OptionChainDTO(BaseModel):
    """The self-describing success response of ``GET /mo-option-chain``.

    Ordering, grouping and null semantics of this payload are owned by
    ``guides/mo-option-chain-read-contract.md``; this DTO only serializes them.
    """

    model_config = ConfigDict(extra="forbid")

    target_trade_date: Annotated[str, Field(description="Explicit target trade date, YYYY-MM-DD.")]
    option_product: OptionProduct
    price_type: Annotated[
        PriceType,
        Field(description="Resolved price_type used by every price in this response."),
    ]
    underlying: UnderlyingRefDTO
    expiries: list[ExpiryGroupDTO]
