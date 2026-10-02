"""Owned public values; canonical observations/cffex_option_expiry_universe/IMPLEMENTATION.md."""

from dataclasses import dataclass
from datetime import date

from market_research.observations import ObservationInvalidRequestError


@dataclass(frozen=True)
class ExpiryUniverseRequest:
    product_code: str
    expiry_start_date: date
    expiry_end_date: date

    def __post_init__(self) -> None:
        if not isinstance(self.product_code, str) or self.product_code not in ("IO", "HO", "MO"):
            raise ObservationInvalidRequestError("product_code must be canonical IO, HO or MO")
        if type(self.expiry_start_date) is not date or type(self.expiry_end_date) is not date:
            raise ObservationInvalidRequestError("expiry window requires dates, not timestamps")
        if self.expiry_start_date > self.expiry_end_date:
            raise ObservationInvalidRequestError("expiry_start_date must be <= expiry_end_date")


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
class ExpiryUniverseArtifact:
    observation_identity: str
    product_code: str
    expiry_start_date: date
    expiry_end_date: date
    expiries: tuple[date, ...]
    complete: bool
    provenance: OptionsProvenance

    @property
    def semantic_identity(self) -> tuple[str, str, date, date]:
        return (
            self.observation_identity,
            self.product_code,
            self.expiry_start_date,
            self.expiry_end_date,
        )
