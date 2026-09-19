"""Pydantic DTOs of the MO Option Chain HTTP contract.

Authority: ``guides/mo-option-chain-http-contract.md`` (transport contract) over
``guides/mo-option-chain-read-contract.md`` (semantic response shape).

The DTOs are a faithful transport expression of the read model defined in
``services/mo_option_chain.py``: same fields, same names, same JSON shape, no
envelope and no extra field. They exist so the wire contract is code-generated,
validated and published as OpenAPI; they own no market semantics.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

# The only option product V1 supports. Declaring it as a literal keeps the
# contract closed in OpenAPI; a different value is a request the contract does
# not accept (HTTP transport contract section 5).
OptionProduct = Literal["MO"]

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
        str,
        Field(description="Resolved price_type used by every price in this response."),
    ]
    underlying: UnderlyingRefDTO
    expiries: list[ExpiryGroupDTO]
