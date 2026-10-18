"""Provider-neutral Source and Dataset-local Repository capabilities."""

from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from data_lake.domain import CachedUnit, ExecutionFailure, Status, Unit, UnitRecords
from data_lake.results import CoverageResult


@dataclass(frozen=True)
class Snapshot:
    coverage: CoverageResult
    successful: tuple[CachedUnit, ...]
    statuses: dict[str, Status]


class Source(Protocol):
    def fetch(self, units: tuple[Unit, ...]) -> Mapping[str, object]:
        """Return facts or safe failures by target identity; absent units are incomplete."""
        ...


class Repository(Protocol):
    @property
    def dataset(self) -> str: ...

    def snapshot(self, units: Sequence[Unit]) -> Snapshot: ...

    def successful_keys(self) -> tuple[str, ...]:
        """Expose identities for Dataset-owned, validated metadata reuse."""
        ...

    def write_session(self) -> AbstractContextManager[None]: ...

    def pending(self, unit: Unit) -> None: ...

    def failed(self, unit: Unit, failure: ExecutionFailure) -> None: ...

    def succeed(self, unit: Unit, normalized: UnitRecords) -> int: ...
