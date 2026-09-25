"""Pydantic DTOs for the MO Premium Plane HTTP projection."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, PlainValidator, WithJsonSchema

from ..models import OptionProduct, OptionType, PriceType

ISO_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def to_iso_date(value: object) -> date:
    if isinstance(value, str) and ISO_DATE_PATTERN.fullmatch(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise ValueError("as_of must be exactly YYYY-MM-DD")


IsoDate = Annotated[
    date,
    PlainValidator(to_iso_date),
    WithJsonSchema({"type": "string", "format": "date"}, mode="validation"),
]


class ObservationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["trade_date"] = "trade_date"
    value: str


class UnderlyingDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    price: float


class FuturesDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    price: float


class ExpiryDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expiry_date: str
    dte: int
    futures: FuturesDTO | None


class PremiumPointDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    expiry_date: str
    option_type: OptionType
    strike: float
    premium: float | None
    annualized_premium_points: float | None
    annualized_time_value_points: float | None
    annualized_seller_premium_yield: float | None


class PremiumPlaneResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: ObservationDTO
    option_product: OptionProduct
    price_type: PriceType
    underlying: UnderlyingDTO
    expiries: list[ExpiryDTO]
    points: list[PremiumPointDTO]
