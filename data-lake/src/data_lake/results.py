"""Shared semantic results; Dataset services own requests and export payloads."""

from dataclasses import dataclass


class InvalidRequestError(Exception):
    """Caller supplied an invalid semantic request."""


class OperationError(Exception):
    """The operation could not be executed, rather than returning incomplete coverage."""


@dataclass(frozen=True)
class CoverageResult:
    requested_units: int
    successful_units: int
    missing_units: int
    pending_units: int
    failed_units: int
    complete: bool


@dataclass(frozen=True)
class UnitFailure:
    identity: object
    reason: str


@dataclass(frozen=True)
class EnsureResult:
    requested_units: int
    already_successful_units: int
    attempted_units: int
    succeeded_units: int
    failed_units: int
    records_written: int
    complete: bool
    failures: tuple[UnitFailure, ...]


@dataclass(frozen=True)
class ExportEnvelope:
    """Dataset-owned views extend this header with their named payload fields."""

    dataset: str
    view: str
    export_schema_version: int
    scope: object
    window: object
    coverage: CoverageResult
