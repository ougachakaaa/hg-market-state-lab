"""Exercise the Application against neutral ports without a SQLite repository."""

from collections.abc import Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass

from data_lake.application import Core
from data_lake.domain import CachedUnit, ExecutionFailure, Record, Status, Unit, UnitRecords
from data_lake.ports import Repository, Snapshot
from data_lake.results import CoverageResult, ExportEnvelope


class MemoryRepository:
    dataset = "fake"

    def __init__(self) -> None:
        self.statuses: dict[str, Status] = {}
        self.facts: dict[str, CachedUnit] = {}
        self.mutations: list[str] = []

    def snapshot(self, units: Sequence[Unit]) -> Snapshot:
        statuses = {
            unit.key: self.statuses[unit.key] for unit in units if unit.key in self.statuses
        }
        successful = tuple(
            self.facts[unit.key] for unit in units if statuses.get(unit.key) == Status.SUCCESS
        )
        return Snapshot(
            CoverageResult(
                len(units),
                len(successful),
                len(units) - len(statuses),
                list(statuses.values()).count(Status.PENDING),
                list(statuses.values()).count(Status.FAILED),
                len(successful) == len(units),
            ),
            successful,
            statuses,
        )

    def successful_keys(self) -> tuple[str, ...]:
        return tuple(key for key, status in self.statuses.items() if status == Status.SUCCESS)

    def write_session(self) -> AbstractContextManager[None]:
        return nullcontext()

    def pending(self, unit: Unit) -> None:
        self.mutations.append(unit.key)
        self.statuses[unit.key] = Status.PENDING

    def failed(self, unit: Unit, failure: ExecutionFailure) -> None:
        assert self.statuses[unit.key] == Status.PENDING
        self.statuses[unit.key] = Status.FAILED

    def succeed(self, unit: Unit, normalized: UnitRecords) -> int:
        assert self.statuses[unit.key] == Status.PENDING
        self.facts[unit.key] = CachedUnit(
            unit, normalized.records, normalized.instruments, normalized.basis
        )
        self.statuses[unit.key] = Status.SUCCESS
        return len(normalized.records)


class MemorySource:
    def __init__(self) -> None:
        self.calls: list[tuple[Unit, ...]] = []
        self.responses: dict[str, object] = {}

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        self.calls.append(units)
        return {unit.key: self.responses[unit.key] for unit in units if unit.key in self.responses}


@dataclass(frozen=True)
class View(ExportEnvelope):
    records: tuple[Record, ...]


def test_application_accepts_repository_port_and_preserves_lifecycle() -> None:
    repository: Repository = MemoryRepository()
    source = MemorySource()
    preparations: list[bool] = []
    units = (Unit("a"), Unit("b"))

    def prepare() -> MemorySource:
        preparations.append(True)
        return source

    def normalize(unit: Unit, raw: object) -> UnitRecords:
        assert isinstance(raw, UnitRecords)
        return raw

    def validate(unit: Unit, facts: UnitRecords) -> None:
        if len(facts.records) != 1:
            raise ExecutionFailure("Expected one record")

    core = Core[tuple[Unit, ...], View](
        repository,
        targets=lambda request: request,
        prepare_source=prepare,
        normalize=normalize,
        check_complete=validate,
        project=lambda request, coverage, cached: View(
            "fake",
            "facts",
            1,
            "scope",
            request,
            coverage,
            tuple(record for item in cached for record in item.records),
        ),
    )
    assert core.coverage(units) == CoverageResult(2, 0, 2, 0, 0, False)
    assert core.export(units).records == ()
    assert not preparations

    source.responses[units[0].key] = UnitRecords((Record({"value": 1}),))
    first = core.ensure(units)
    assert (first.succeeded_units, first.failed_units, first.records_written) == (1, 1, 1)
    assert first.failures[0].identity == "b"

    source.responses[units[1].key] = UnitRecords((Record({"value": 2}),))
    second = core.ensure(units)
    assert second.complete and second.already_successful_units == second.attempted_units == 1
    assert source.calls == [units, (units[1],)]
    assert core.ensure(units).attempted_units == 0
    view = core.export(units)
    assert view.coverage == core.coverage(units) == CoverageResult(2, 2, 0, 0, 0, True)
    assert tuple(record.fields for record in view.records) == ({"value": 1}, {"value": 2})
    assert len(preparations) == 2
