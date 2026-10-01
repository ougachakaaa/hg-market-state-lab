"""Core invariants exercised through a minimal test-local Dataset service."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, asdict, dataclass
from pathlib import Path
from threading import Event

import pytest

import data_lake
import data_lake._repository as repository_module
from data_lake import (
    CoverageResult,
    EnsureResult,
    ExportEnvelope,
    InvalidRequestError,
    OperationError,
)
from data_lake._application import Core, Source
from data_lake._domain import (
    CachedUnit,
    ExecutionFailure,
    Instrument,
    Record,
    Unit,
    UnitRecords,
)
from data_lake._repository import Repository
from data_lake._runtime import database_path
from data_lake._serialization import canonical_json, record_hash


@dataclass(frozen=True)
class FakeView(ExportEnvelope):
    facts: tuple[dict[str, object], ...]


class FakeDataset:
    def __init__(self, root: Path, name: str = "fake") -> None:
        self.repository = Repository(database_path(name, root), name, "fake-source")
        self.responses: dict[str, object] = {}
        self.calls: list[tuple[Unit, ...]] = []
        self.preparations = 0
        self.credentials = True
        self.core = Core[tuple[str, ...], FakeView](
            self.repository,
            targets=self.targets,
            prepare_source=self.prepare,
            normalize=self.normalize,
            check_complete=self.check_complete,
            project=self.project,
        )

    def targets(self, request: tuple[str, ...]) -> tuple[Unit, ...]:
        if not isinstance(request, tuple) or not all(isinstance(item, str) for item in request):
            raise InvalidRequestError("Invalid fake request")
        return tuple(Unit(item) for item in request)

    def prepare(self) -> Source:
        self.preparations += 1
        if not self.credentials:
            raise OperationError("Fake credential is missing")
        return self

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        self.calls.append(units)
        return {
            unit.key: self.responses[str(unit.identity)]
            for unit in units
            if str(unit.identity) in self.responses
        }

    def normalize(self, unit: Unit, raw: object) -> UnitRecords:
        if isinstance(raw, BaseException):
            raise raw
        assert isinstance(raw, UnitRecords)
        return raw

    def check_complete(self, unit: Unit, normalized: UnitRecords) -> None:
        if any(record.fields.get("incomplete") for record in normalized.records):
            raise ExecutionFailure("Incomplete fake facts", "incomplete")

    def project(
        self, request: tuple[str, ...], coverage: CoverageResult, cached: tuple[CachedUnit, ...]
    ) -> FakeView:
        return FakeView(
            self.repository.dataset,
            "fake-facts",
            1,
            "fake-scope",
            request,
            coverage,
            tuple(dict(record.fields) for unit in cached for record in unit.records),
        )


def facts(value: int = 1) -> UnitRecords:
    return UnitRecords((Record({"value": value}),))


@pytest.fixture
def dataset(tmp_path: Path) -> FakeDataset:
    return FakeDataset(tmp_path / "cache")


def test_missing_reads_never_materialize_or_prepare_source(dataset: FakeDataset) -> None:
    dataset.credentials = False
    coverage = dataset.core.coverage(("a", "b"))
    assert coverage == CoverageResult(2, 0, 2, 0, 0, False)
    view = dataset.core.export(("a", "b"))
    assert view.coverage == coverage
    assert view.facts == ()
    assert dataset.preparations == 0 and dataset.calls == []
    assert not dataset.repository.path.parent.exists()


def test_empty_targets_are_complete_and_do_not_create_storage(dataset: FakeDataset) -> None:
    assert dataset.core.coverage(()).complete
    assert dataset.core.ensure(()) == EnsureResult(0, 0, 0, 0, 0, 0, True, ())
    assert dataset.core.export(()).facts == ()
    assert not dataset.repository.path.exists()


@pytest.mark.parametrize("stage", ["connect", "ddl", "metadata"])
def test_initialization_failure_cleans_new_database_and_allows_retry(
    dataset: FakeDataset, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    dataset.responses["a"] = facts()
    with monkeypatch.context() as injected:
        if stage == "connect":
            def reject_connection(*args: object, **kwargs: object) -> sqlite3.Connection:
                raise sqlite3.OperationalError("Injected connection failure")

            injected.setattr(sqlite3, "connect", reject_connection)
        else:
            fault = (
                "INVALID SQL;"
                if stage == "ddl"
                else "CREATE TRIGGER reject_metadata BEFORE INSERT ON dataset_meta "
                "BEGIN SELECT RAISE(ABORT, 'test'); END;"
            )
            injected.setattr(repository_module, "DDL", repository_module.DDL + fault)
        with pytest.raises(OperationError, match="storage operation failed"):
            dataset.core.ensure(("a",))
    assert list(dataset.repository.path.parent.iterdir()) == []
    assert dataset.calls == []
    assert dataset.core.coverage(("a",)).missing_units == 1
    assert dataset.core.ensure(("a",)) == EnsureResult(1, 0, 1, 1, 0, 1, True, ())


@pytest.mark.parametrize("failure", [RuntimeError, KeyboardInterrupt])
def test_initialization_exception_or_interrupt_cleans_new_database(
    dataset: FakeDataset, monkeypatch: pytest.MonkeyPatch, failure: type[BaseException]
) -> None:
    def interrupt_initialization() -> str:
        raise failure("Injected initialization interruption")

    with monkeypatch.context() as injected:
        injected.setattr(repository_module, "now", interrupt_initialization)
        expected = OperationError if failure is RuntimeError else KeyboardInterrupt
        with pytest.raises(expected):
            dataset.core.ensure(("a",))
    assert list(dataset.repository.path.parent.iterdir()) == []
    dataset.responses["a"] = facts()
    assert dataset.core.ensure(("a",)).complete


def test_failure_after_schema_commit_preserves_database_and_allows_retry(
    dataset: FakeDataset, monkeypatch: pytest.MonkeyPatch
) -> None:
    trigger = (
        "CREATE TRIGGER reject_unit BEFORE INSERT ON fetch_unit "
        "BEGIN SELECT RAISE(ABORT, 'test'); END;"
    )
    with monkeypatch.context() as injected:
        injected.setattr(repository_module, "DDL", repository_module.DDL + trigger)
        with pytest.raises(OperationError):
            dataset.core.ensure(("a",))
    assert dataset.repository.path.exists()
    assert dataset.core.coverage(("a",)) == CoverageResult(1, 0, 1, 0, 0, False)
    with sqlite3.connect(dataset.repository.path) as connection:
        assert connection.execute("SELECT count(*) FROM dataset_meta").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM records").fetchone()[0] == 0
        connection.execute("DROP TRIGGER reject_unit")
    dataset.responses["a"] = facts()
    assert dataset.core.ensure(("a",)).complete


def test_initialization_cleanup_failure_is_application_failure(
    dataset: FakeDataset, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_cleanup(path: Path, missing_ok: bool = False) -> None:
        raise PermissionError("Private storage path: " + str(path))

    with monkeypatch.context() as injected:
        injected.setattr(repository_module, "DDL", repository_module.DDL + "INVALID SQL;")
        injected.setattr(Path, "unlink", reject_cleanup)
        with pytest.raises(OperationError, match="storage cleanup failed") as error:
            dataset.core.ensure(("a",))
    assert str(dataset.repository.path) not in str(error.value)
    assert dataset.repository.path.exists()
    assert dataset.calls == []
    # Closing the failed connection rolled back DDL before the unlink failed.
    with sqlite3.connect(dataset.repository.path) as connection:
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == []


def test_four_states_and_counts_are_mutually_exclusive(dataset: FakeDataset) -> None:
    dataset.repository.pending(Unit("pending"))
    dataset.repository.pending(Unit("failed"))
    dataset.repository.failed(Unit("failed"), ExecutionFailure("failed"))
    dataset.responses["success"] = facts()
    dataset.core.ensure(("success",))
    coverage = dataset.core.coverage(("missing", "pending", "failed", "success", "success"))
    assert coverage == CoverageResult(4, 1, 1, 1, 1, False)
    assert (
        sum(
            (
                coverage.successful_units,
                coverage.missing_units,
                coverage.pending_units,
                coverage.failed_units,
            )
        )
        == coverage.requested_units
    )


def test_selection_retry_success_skip_and_committed_counts(dataset: FakeDataset) -> None:
    dataset.repository.pending(Unit("pending"))
    dataset.repository.pending(Unit("failed"))
    dataset.repository.failed(Unit("failed"), ExecutionFailure("previous attempt"))
    dataset.responses = {key: facts() for key in ("success", "pending", "failed", "missing")}
    assert dataset.core.ensure(("success",)).records_written == 1
    result = dataset.core.ensure(("success", "pending", "failed", "missing", "missing"))
    assert result == EnsureResult(4, 1, 3, 3, 0, 3, True, ())
    assert [u.identity for u in dataset.calls[-1]] == ["pending", "failed", "missing"]
    dataset.credentials = False
    before = dataset.repository.path.read_bytes()
    assert dataset.core.ensure(("success", "pending", "failed", "missing")) == (
        EnsureResult(4, 4, 0, 0, 0, 0, True, ())
    )
    assert dataset.preparations == 2
    assert dataset.repository.path.read_bytes() == before


def test_batch_success_does_not_imply_unit_success(dataset: FakeDataset) -> None:
    dataset.responses = {
        "a": facts(),
        "b": UnitRecords((Record({"incomplete": True}),)),
        "d": ExecutionFailure("Provider rejected this unit"),
        "e": UnitRecords(()),
    }
    result = dataset.core.ensure(("a", "b", "c", "d", "e"))
    assert (
        result.attempted_units,
        result.succeeded_units,
        result.failed_units,
        result.records_written,
        result.complete,
    ) == (5, 2, 3, 1, False)
    assert [failure.identity for failure in result.failures] == ["b", "c", "d"]
    assert len(dataset.calls) == 1
    assert dataset.core.coverage(("a", "b", "c", "d", "e")) == (
        CoverageResult(5, 2, 0, 0, 3, False)
    )
    dataset.responses.update({key: facts(2) for key in ("b", "c", "d")})
    retry = dataset.core.ensure(("a", "b", "c", "d", "e"))
    assert retry == EnsureResult(5, 2, 3, 3, 0, 3, True, ())


def test_recoverable_batch_failure_continues_next_batch(
    dataset: FakeDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fetch(units: tuple[Unit, ...]) -> dict[str, object]:
        if units[0].identity == "a":
            raise ExecutionFailure("Temporary provider failure", "provider")
        return {unit.key: facts() for unit in units}

    monkeypatch.setattr(dataset, "fetch", fetch)
    monkeypatch.setattr(dataset.core, "_batches", lambda units: (units[:2], units[2:]))
    result = dataset.core.ensure(("a", "b", "c"))
    assert (result.succeeded_units, result.failed_units, result.records_written) == (1, 2, 1)
    assert [failure.identity for failure in result.failures] == ["a", "b"]


def test_credential_failure_occurs_before_source_and_mutation(dataset: FakeDataset) -> None:
    dataset.credentials = False
    with pytest.raises(OperationError, match="credential"):
        dataset.core.ensure(("a",))
    assert dataset.calls == [] and not dataset.repository.path.parent.exists()


def test_unclassified_exception_is_application_failure_and_pending_is_retryable(
    dataset: FakeDataset,
) -> None:
    dataset.responses["a"] = RuntimeError("private provider transport detail")
    with pytest.raises(OperationError, match="could not be executed") as error:
        dataset.core.ensure(("a",))
    assert "private" not in str(error.value)
    assert dataset.core.coverage(("a",)) == CoverageResult(1, 0, 0, 1, 0, False)
    dataset.responses["a"] = facts()
    assert dataset.core.ensure(("a",)).complete


def test_interrupted_attempt_is_pending_and_can_retry(dataset: FakeDataset) -> None:
    dataset.responses["a"] = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        dataset.core.ensure(("a",))
    assert dataset.core.coverage(("a",)).pending_units == 1
    dataset.responses["a"] = facts()
    assert dataset.core.ensure(("a",)).complete


def test_atomic_rollback_restores_records_and_instruments(dataset: FakeDataset) -> None:
    unit = Unit("a")
    dataset.repository.pending(unit)
    dataset.repository.succeed(unit, facts(1))
    dataset.repository.pending(unit)
    bad = UnitRecords(
        (Record({"value": 2}, "new"), Record({"value": 3}, "unknown")), (Instrument("new", "NEW"),)
    )
    with pytest.raises(OperationError, match="unknown local instrument"):
        dataset.repository.succeed(unit, bad)
    with sqlite3.connect(dataset.repository.path) as connection:
        assert json.loads(connection.execute("SELECT facts FROM records").fetchone()[0]) == {
            "value": 1
        }
        assert connection.execute("SELECT count(*) FROM instrument").fetchone()[0] == 0
        assert connection.execute("SELECT status FROM fetch_unit").fetchone()[0] == "pending"
    assert dataset.core.export(("a",)).facts == ()
    dataset.responses["a"] = facts(2)
    assert dataset.core.ensure(("a",)).records_written == 1
    assert dataset.core.export(("a",)).facts == ({"value": 2},)


def test_sql_failure_cannot_leave_success(dataset: FakeDataset) -> None:
    dataset.repository.pending(Unit("a"))
    with sqlite3.connect(dataset.repository.path) as connection:
        connection.execute(
            "CREATE TRIGGER reject_success BEFORE UPDATE ON fetch_unit "
            "WHEN NEW.status='success' BEGIN SELECT RAISE(ABORT, 'test'); END"
        )
    dataset.responses["a"] = facts()
    with pytest.raises(OperationError):
        dataset.core.ensure(("a",))
    with sqlite3.connect(dataset.repository.path) as connection:
        assert connection.execute("SELECT count(*) FROM records").fetchone()[0] == 0
        assert connection.execute("SELECT status FROM fetch_unit").fetchone()[0] == "pending"


def test_export_uses_only_target_success_and_existing_reads_do_not_mutate(
    dataset: FakeDataset,
) -> None:
    dataset.responses = {"a": facts(1), "outside": facts(2)}
    dataset.core.ensure(("a", "outside"))
    dataset.repository.pending(Unit("pending"))
    dataset.repository.pending(Unit("failed"))
    dataset.repository.failed(Unit("failed"), ExecutionFailure("failure"))
    dataset.credentials = False
    path = dataset.repository.path
    before = (
        path.read_bytes(),
        path.stat().st_mtime_ns,
        sorted(p.name for p in path.parent.iterdir()),
        dataset.preparations,
    )
    target = ("a", "pending", "failed", "missing")
    view = dataset.core.export(target)
    assert view.facts == ({"value": 1},)
    assert view.coverage == dataset.core.coverage(target) == CoverageResult(4, 1, 1, 1, 1, False)
    assert before == (
        path.read_bytes(),
        path.stat().st_mtime_ns,
        sorted(p.name for p in path.parent.iterdir()),
        dataset.preparations,
    )


def test_projection_consumes_one_snapshot_even_if_writer_changes_cache(
    dataset: FakeDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset.responses["a"] = facts(1)
    dataset.core.ensure(("a",))
    original = dataset.project

    def project(
        request: tuple[str, ...], coverage: CoverageResult, cached: tuple[CachedUnit, ...]
    ) -> FakeView:
        dataset.repository.pending(Unit("a"))
        return original(request, coverage, cached)

    monkeypatch.setattr(dataset.core, "_project", project)
    view = dataset.core.export(("a",))
    assert view.coverage.complete and view.facts == ({"value": 1},)
    assert not dataset.core.coverage(("a",)).complete


def test_rollback_journal_snapshot_blocks_commit_until_read_finishes(
    dataset: FakeDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset.responses["a"] = facts()
    dataset.core.ensure(("a",))
    original = dataset.repository._validate
    updated = Event()
    committed = Event()

    def write() -> None:
        with sqlite3.connect(dataset.repository.path) as writer:
            writer.execute("UPDATE fetch_unit SET status='pending', succeeded_at=NULL")
            writer.execute("DELETE FROM records")
            updated.set()
        committed.set()

    with ThreadPoolExecutor(max_workers=1) as executor:
        writes = []

        def validate(connection: sqlite3.Connection) -> None:
            original(connection)  # pins the read transaction to the original cache state
            writes.append(executor.submit(write))
            assert updated.wait(timeout=5)
            assert not committed.is_set()

        monkeypatch.setattr(dataset.repository, "_validate", validate)
        view = dataset.core.export(("a",))
        assert view.coverage.complete and view.facts == ({"value": 1},)
        writes[0].result(timeout=5)
    assert committed.is_set()
    monkeypatch.setattr(dataset.repository, "_validate", original)
    assert dataset.core.coverage(("a",)).pending_units == 1


@pytest.mark.parametrize("operation", ["coverage", "export", "ensure", "write_connection"])
def test_wal_storage_is_rejected_before_connecting_or_mutating(
    dataset: FakeDataset,
    operation: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset.responses["a"] = facts()
    dataset.core.ensure(("a",))
    path = dataset.repository.path
    connection = sqlite3.connect(path)
    try:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    finally:
        connection.close()
    assert sorted(p.name for p in path.parent.iterdir()) == [path.name]
    before = (path.read_bytes(), path.stat().st_mtime_ns, dataset.preparations, len(dataset.calls))

    def unexpected_connect(*args: object, **kwargs: object) -> None:
        pytest.fail("WAL rejection must happen before SQLite connects")

    monkeypatch.setattr(sqlite3, "connect", unexpected_connect)
    with pytest.raises(OperationError, match="unsupported WAL"):
        if operation == "write_connection":
            dataset.repository.pending(Unit("b"))
        else:
            getattr(dataset.core, operation)(("a", "b"))
    assert before == (
        path.read_bytes(), path.stat().st_mtime_ns, dataset.preparations, len(dataset.calls)
    )
    assert sorted(p.name for p in path.parent.iterdir()) == [path.name]


def test_instrument_required_fields_are_left_to_dataset(dataset: FakeDataset) -> None:
    dataset.responses["a"] = UnitRecords(
        (Record({"value": 1}, "semantic-key"),), (Instrument("semantic-key"),)
    )
    assert dataset.core.ensure(("a",)).complete
    assert dataset.repository.snapshot((Unit("a"),)).successful[0].instruments == (
        Instrument("semantic-key"),
    )


def test_success_and_failure_require_started_unit(dataset: FakeDataset) -> None:
    unit = Unit("a")
    with pytest.raises(OperationError, match="not started"):
        dataset.repository.succeed(unit, facts())
    with pytest.raises(OperationError, match="not started"):
        dataset.repository.failed(unit, ExecutionFailure("Failure"))
    assert dataset.core.coverage(("a",)).missing_units == 1
    dataset.responses["a"] = facts()
    dataset.core.ensure(("a",))
    with pytest.raises(OperationError, match="not started"):
        dataset.repository.succeed(unit, facts(2))
    assert dataset.core.export(("a",)).facts == ({"value": 1},)


@pytest.mark.parametrize("operation", ["coverage", "ensure", "export"])
@pytest.mark.parametrize(
    "kind",
    [
        "empty",
        "corrupt",
        "wrong_identity",
        "wrong_schema",
        "missing_table",
        "bad_count",
        "bad_hash",
        "invalid_status",
    ],
)
def test_existing_invalid_storage_is_failure_not_missing(
    dataset: FakeDataset,
    operation: str,
    kind: str,
) -> None:
    if kind in ("empty", "corrupt"):
        dataset.repository.path.parent.mkdir()
        dataset.repository.path.write_bytes(b"" if kind == "empty" else b"not sqlite")
    else:
        dataset.responses["a"] = facts()
        dataset.core.ensure(("a",))
        with sqlite3.connect(dataset.repository.path) as connection:
            if kind == "wrong_identity":
                connection.execute("UPDATE dataset_meta SET dataset_name='other'")
            elif kind == "wrong_schema":
                connection.execute("UPDATE dataset_meta SET schema_version=99")
            elif kind == "missing_table":
                connection.execute("DROP TABLE records")
            elif kind == "bad_count":
                connection.execute("UPDATE fetch_unit SET record_count=999")
            elif kind == "bad_hash":
                connection.execute("UPDATE fetch_unit SET content_hash='bad'")
            elif kind == "invalid_status":
                connection.execute("PRAGMA ignore_check_constraints=ON")
                connection.execute("UPDATE fetch_unit SET status='unknown'")
    before = dataset.repository.path.read_bytes()
    with pytest.raises(OperationError):
        getattr(dataset.core, operation)(("a",))
    assert dataset.repository.path.read_bytes() == before


def test_dataset_isolation_and_local_instrument_references(tmp_path: Path) -> None:
    first, second = FakeDataset(tmp_path, "first"), FakeDataset(tmp_path, "second")
    first.responses["a"] = UnitRecords((Record({"value": 1}, "X"),), (Instrument("X", "X"),))
    second.responses["a"] = UnitRecords((Record({"value": 2}, "X"),), (Instrument("X", "X"),))
    first.core.ensure(("a",))
    assert second.core.coverage(("a",)).missing_units == 1
    second.core.ensure(("a",))
    assert first.repository.path != second.repository.path
    first.repository.path.unlink()
    assert second.core.export(("a",)).facts == ({"value": 2},)
    assert second.repository.snapshot((Unit("a"),)).successful[0].instruments == (
        Instrument("X", "X"),
    )
    with sqlite3.connect(second.repository.path) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert (
            connection.execute(
                "SELECT count(*) FROM records JOIN instrument USING(instrument_id)"
            ).fetchone()[0]
            == 1
        )


def test_hash_canonicalization_order_duplicates_and_semantic_instrument_key() -> None:
    first = Record({"b": 2, "a": 1}, "X")
    same = Record({"a": 1, "b": 2}, "X")
    other = Record({"a": 3})
    assert first.encode() == same.encode()
    assert record_hash([first.encode(), other.encode()]) == (
        record_hash([other.encode(), same.encode()])
    )
    assert record_hash([first.encode()]) != record_hash([first.encode(), first.encode()])
    assert record_hash([first.encode()]) != record_hash([Record(first.fields, "Y").encode()])
    assert Unit({"b": 2, "a": 1}).key == Unit({"a": 1, "b": 2}).key


def test_hash_is_independent_of_persistence_ids(tmp_path: Path) -> None:
    first, second = FakeDataset(tmp_path, "first"), FakeDataset(tmp_path, "second")
    second.responses["earlier"] = facts(99)
    second.core.ensure(("earlier",))
    hashes = []
    ids = []
    for dataset in (first, second):
        dataset.responses["a"] = facts(1)
        dataset.core.ensure(("a",))
        with sqlite3.connect(dataset.repository.path) as connection:
            unit_id, content_hash = connection.execute(
                "SELECT unit_id, content_hash FROM fetch_unit WHERE unit_key=?", (Unit("a").key,)
            ).fetchone()
            hashes.append(content_hash)
            ids.append(unit_id)
    assert ids[0] != ids[1] and hashes[0] == hashes[1]


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf"), {1: "non-string"}, ("tuple",), object()]
)
def test_noncanonical_values_are_rejected(value: object) -> None:
    with pytest.raises(ValueError):
        canonical_json(value)


def test_invalid_request_and_invalid_batch_plan_do_not_mutate(
    dataset: FakeDataset,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(InvalidRequestError):
        dataset.core.ensure("invalid")  # type: ignore[arg-type]
    monkeypatch.setattr(dataset.core, "_batches", lambda units: (units, units))
    with pytest.raises(OperationError, match="partition"):
        dataset.core.ensure(("a",))
    assert dataset.calls == [] and not dataset.repository.path.exists()


def test_public_facade_and_results_do_not_expose_persistence(dataset: FakeDataset) -> None:
    for name in (
        "CoverageResult",
        "EnsureResult",
        "UnitFailure",
        "ExportEnvelope",
        "InvalidRequestError",
        "OperationError",
    ):
        assert hasattr(data_lake, name)
    assert not hasattr(data_lake, "__all__")
    for name in ("Repository", "Core", "Source", "database_path"):
        assert not hasattr(data_lake, name)
    dataset.responses = {"a": facts(), "b": ExecutionFailure("Incomplete")}
    result = dataset.core.ensure(("a", "b"))
    public = json.dumps(asdict(result)) + json.dumps(asdict(dataset.core.export(("a", "b"))))
    for forbidden in (
        "unit_id",
        "record_id",
        "instrument_id",
        "sqlite",
        str(dataset.repository.path),
    ):
        assert forbidden not in public
    with pytest.raises(FrozenInstanceError):
        result.complete = True  # type: ignore[misc]
