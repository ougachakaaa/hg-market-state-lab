"""Internal values exchanged by Dataset collaborators and persistence."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from ._serialization import Json, canonical_json


class Status(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class Unit:
    identity: object

    @property
    def key(self) -> str:
        def encode(value: object) -> object:
            if type(value) is date:
                return value.isoformat()
            if isinstance(value, tuple):
                return [encode(item) for item in value]
            return value

        return canonical_json(encode(self.identity))


@dataclass(frozen=True)
class Instrument:
    key: str
    source_code: str | None = None
    instrument_type: str | None = None
    symbol: str | None = None
    exchange: str | None = None
    name: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


@dataclass(frozen=True)
class Record:
    fields: dict[str, Json]
    instrument_key: str | None = None

    def encode(self) -> str:
        return canonical_json({"fields": self.fields, "instrument_key": self.instrument_key})


@dataclass(frozen=True)
class UnitRecords:
    records: tuple[Record, ...]
    instruments: tuple[Instrument, ...] = ()
    basis: dict[str, Json] | None = None


@dataclass(frozen=True)
class CachedUnit:
    unit: Unit
    records: tuple[Record, ...]
    instruments: tuple[Instrument, ...] = ()
    basis: dict[str, Json] | None = None


class ExecutionFailure(Exception):
    """Explicit recoverable Source or completeness failure, safe to report publicly."""

    def __init__(self, reason: str, code: str = "unit_failure") -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code
