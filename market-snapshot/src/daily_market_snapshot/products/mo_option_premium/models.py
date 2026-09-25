"""Canonical in-memory models of the MO Premium Plane backend."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OptionProduct(StrEnum):
    MO = "MO"


class PriceType(StrEnum):
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"


class OptionType(StrEnum):
    CALL = "call"
    PUT = "put"


class ReferenceBasis(StrEnum):
    UNDERLYING_SPOT = "underlying_spot"
    EXPIRY_FUTURES = "expiry_futures"


class ValueBasis(StrEnum):
    TOTAL = "total"
    TIME_VALUE = "time_value"


class TimeNormalization(StrEnum):
    UNANNUALIZED = "unannualized"
    ANNUALIZED = "annualized"


class MetricRepresentation(StrEnum):
    POINTS = "points"
    YIELD = "yield"


DEFAULT_PRICE_TYPE = PriceType.CLOSE


@dataclass(frozen=True)
class ObservationAnchor:
    as_of: str


@dataclass(frozen=True)
class UnderlyingReference:
    instrument_id: str
    price: float


@dataclass(frozen=True)
class FuturesReference:
    instrument_id: str
    price: float


@dataclass(frozen=True)
class OptionObservation:
    instrument_id: str
    option_type: OptionType
    expiry_date: str
    strike: float
    premium: float | None
    futures: FuturesReference | None


@dataclass(frozen=True)
class OptionMarketBasis:
    observation: ObservationAnchor
    option_product: OptionProduct
    price_type: PriceType
    underlying: UnderlyingReference
    options: tuple[OptionObservation, ...]


@dataclass(frozen=True)
class CalculationBasis:
    dte_basis: str = "inclusive_calendar_days"
    annualization_days: int = 365
    yield_denominator: str = "selected_reference_notional"
    contract_multiplier: float = 200.0


@dataclass(frozen=True)
class MetricValues:
    points: float | None
    yield_: float | None


@dataclass(frozen=True)
class TimeNormalizedMetrics:
    unannualized: MetricValues
    annualized: MetricValues


@dataclass(frozen=True)
class ValueMetrics:
    total: TimeNormalizedMetrics
    time_value: TimeNormalizedMetrics


@dataclass(frozen=True)
class PremiumMetrics:
    underlying_spot: ValueMetrics
    expiry_futures: ValueMetrics


@dataclass(frozen=True)
class PremiumPoint:
    observation: ObservationAnchor
    instrument_id: str
    option_product: OptionProduct
    option_type: OptionType
    expiry_date: str
    strike: float
    price_type: PriceType
    premium: float | None
    underlying: UnderlyingReference
    futures: FuturesReference | None
    calculation_basis: CalculationBasis
    dte: int
    metrics: PremiumMetrics


@dataclass(frozen=True)
class PremiumPlane:
    observation: ObservationAnchor
    option_product: OptionProduct
    price_type: PriceType
    underlying: UnderlyingReference
    calculation_basis: CalculationBasis
    points: tuple[PremiumPoint, ...]
