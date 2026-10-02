"""Owned public values; canonical observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md."""

from dataclasses import dataclass
from datetime import date

from market_research.observations import ObservationInvalidRequestError


@dataclass(frozen=True)
class ExpiryDteChainRequest:
    product_code: str
    expiry_date: date
    target_dte: int

    def __post_init__(self) -> None:
        if not isinstance(self.product_code, str) or self.product_code not in ("IO", "HO", "MO"):
            raise ObservationInvalidRequestError("product_code must be canonical IO, HO or MO")
        if type(self.expiry_date) is not date:
            raise ObservationInvalidRequestError("expiry_date requires a date, not a timestamp")
        if type(self.target_dte) is not int or self.target_dte < 1:
            raise ObservationInvalidRequestError("target_dte must be a positive integer")


@dataclass(frozen=True)
class Window:
    start_date: date
    end_date: date


@dataclass(frozen=True)
class Coverage:
    requested_units: int
    successful_units: int
    missing_units: int
    pending_units: int
    failed_units: int
    complete: bool


@dataclass(frozen=True)
class OptionsScope:
    product_codes: tuple[str, ...]


@dataclass(frozen=True)
class OptionsProvenance:
    dataset: str
    view: str
    export_schema_version: int
    scope: OptionsScope
    window: Window
    coverage: Coverage


@dataclass(frozen=True)
class CalendarScope:
    exchange: str


@dataclass(frozen=True)
class CalendarProvenance:
    dataset: str
    view: str
    export_schema_version: int
    scope: CalendarScope
    window: Window
    coverage: Coverage


@dataclass(frozen=True)
class ExpiryDteChainRow:
    contract_code: str
    product_code: str
    symbol: str
    name: str
    exchange: str
    source_underlying_code: str
    underlying_index_code: str
    option_type: str
    exercise_type: str
    quote_unit: str
    settlement_month: str
    call_put: str
    list_date: date
    delist_date: date
    expiry: date
    last_exercise_date: date
    trade_date: date
    last_delivery_date: date | None
    per_unit: float
    opt_multiplier: float
    strike: float
    pre_settle: float
    pre_close: float | None
    close: float
    settle: float
    volume: float
    amount: float
    open_interest: float
    open: float | None
    high: float | None
    low: float | None


@dataclass(frozen=True)
class ExpiryDteChainArtifact:
    observation_identity: str
    product_code: str
    expiry_date: date
    target_dte: int
    ideal_calendar_date: date
    observation_date: date
    actual_dte: int
    rows: tuple[ExpiryDteChainRow, ...]
    calendar_provenance: tuple[CalendarProvenance, ...]
    options_provenance: OptionsProvenance
    complete: bool

    @property
    def semantic_identity(self) -> tuple[str, str, date, int]:
        return (
            self.observation_identity,
            self.product_code,
            self.expiry_date,
            self.target_dte,
        )
