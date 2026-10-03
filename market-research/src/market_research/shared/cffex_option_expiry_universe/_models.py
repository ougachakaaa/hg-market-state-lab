"""Owned public values; canonical shared/cffex_option_expiry_universe/IMPLEMENTATION.md."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from ._errors import ExpiryUniverseInvalidRequestError


@dataclass(frozen=True)
class ExpiryUniverseRequest:
    product_code: str
    expiry_start_date: date
    expiry_end_date: date

    def __post_init__(self) -> None:
        if not isinstance(self.product_code, str) or self.product_code not in ("IO", "HO", "MO"):
            raise ExpiryUniverseInvalidRequestError("product_code must be canonical IO, HO or MO")
        if type(self.expiry_start_date) is not date or type(self.expiry_end_date) is not date:
            raise ExpiryUniverseInvalidRequestError("expiry window requires dates, not timestamps")
        if self.expiry_start_date > self.expiry_end_date:
            raise ExpiryUniverseInvalidRequestError("expiry_start_date must be <= expiry_end_date")
        if self.expiry_end_date > datetime.now(timezone(timedelta(hours=8))).date():
            raise ExpiryUniverseInvalidRequestError(
                "Window cannot extend beyond today in Asia/Shanghai"
            )


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
class ExpiryUniverseResult:
    product_code: str
    expiry_start_date: date
    expiry_end_date: date
    expiries: tuple[date, ...]
    complete: bool
    provenance: OptionsProvenance

    def __post_init__(self) -> None:
        # This public value also validates controlled collaborator returns in Study.
        ExpiryUniverseRequest(self.product_code, self.expiry_start_date, self.expiry_end_date)
        if (
            self.complete is not True
            or type(self.expiries) is not tuple
            or any(type(value) is not date for value in self.expiries)
            or self.expiries != tuple(sorted(set(self.expiries)))
            or any(
                not self.expiry_start_date <= value <= self.expiry_end_date
                for value in self.expiries
            )
        ):
            raise ValueError("Universe result must be complete with sorted unique in-range dates")
        context = self.provenance
        if (
            type(context) is not OptionsProvenance
            or type(context.scope) is not OptionsScope
            or type(context.window) is not Window
            or type(context.coverage) is not Coverage
        ):
            raise ValueError("Universe context must contain resolver-owned values")
        if (
            context.dataset != "tushare_equity_index_options"
            or context.view != "options_daily"
            or type(context.export_schema_version) is not int
            or context.export_schema_version != 2
            or type(context.scope.product_codes) is not tuple
            or context.scope.product_codes != (self.product_code,)
            or type(context.window.start_date) is not date
            or type(context.window.end_date) is not date
            or context.window.start_date != self.expiry_start_date
            or context.window.end_date != self.expiry_end_date
        ):
            raise ValueError("Invalid Universe Options context identity / scope / window")
        coverage = context.coverage
        counts = (
            coverage.requested_units,
            coverage.successful_units,
            coverage.missing_units,
            coverage.pending_units,
            coverage.failed_units,
        )
        if (
            any(type(value) is not int or value < 0 for value in counts)
            or coverage.complete is not True
            or counts[0] != counts[1]
            or any(counts[2:])
            or (bool(self.expiries) and counts[1] == 0)
        ):
            raise ValueError("Universe Options coverage must be coherent and complete")
