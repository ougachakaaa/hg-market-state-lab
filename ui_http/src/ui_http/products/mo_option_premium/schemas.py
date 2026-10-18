"""Pydantic DTOs for the MO Premium Plane HTTP projection."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, PlainValidator, WithJsonSchema

from data_snapshot.products.mo_option_premium.service import (
    OptionProduct,
    OptionType,
    PriceType,
)

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


class MetricDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    points: float | None
    yield_: float | None = Field(
        validation_alias=AliasChoices("yield", "yield_"),
        serialization_alias="yield",
    )


class TimeNormalizedMetricsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unannualized: MetricDTO
    annualized: MetricDTO


class ValueMetricsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: TimeNormalizedMetricsDTO
    time_value: TimeNormalizedMetricsDTO


class PremiumMetricsDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    underlying_spot: ValueMetricsDTO
    expiry_futures: ValueMetricsDTO


class PremiumPointDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    instrument_id: str
    expiry_date: str
    option_type: OptionType
    strike: float
    premium: float | None
    metrics: PremiumMetricsDTO


class PremiumPlaneResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observation: ObservationDTO
    option_product: OptionProduct
    price_type: PriceType
    underlying: UnderlyingDTO
    expiries: list[ExpiryDTO]
    points: list[PremiumPointDTO]
