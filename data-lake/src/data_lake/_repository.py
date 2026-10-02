"""One rollback-journal SQLite, with read snapshots and per-unit write transactions."""

import hashlib
import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import closing, contextmanager
from dataclasses import astuple, dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import local
from uuid import uuid4

from ._domain import CachedUnit, ExecutionFailure, Instrument, Record, Status, Unit, UnitRecords
from ._serialization import canonical_json, record_hash
from .results import CoverageResult, OperationError

SCHEMA_VERSION = 3
BASIS_DDL = (
    "CREATE TABLE basis_snapshot (basis_id INTEGER PRIMARY KEY, "
    "content_hash TEXT NOT NULL UNIQUE, facts TEXT NOT NULL)",
    "CREATE TRIGGER immutable_basis BEFORE UPDATE ON basis_snapshot "
    "BEGIN SELECT RAISE(ABORT, 'Frozen basis is immutable'); END",
)
DDL = (
    ";\n".join(BASIS_DDL)
    + ";\n"
    + """
CREATE TABLE dataset_meta (
    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
    dataset_name TEXT NOT NULL, schema_version INTEGER NOT NULL,
    source_name TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE fetch_unit (
    unit_id INTEGER PRIMARY KEY, unit_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('pending', 'success', 'failed')),
    content_hash TEXT, record_count INTEGER CHECK(record_count >= 0),
    created_at TEXT NOT NULL, last_attempt_at TEXT NOT NULL, succeeded_at TEXT,
    error_code TEXT, error_message TEXT, basis TEXT,
    basis_id INTEGER REFERENCES basis_snapshot(basis_id),
    CHECK(status != 'success' OR
          (content_hash IS NOT NULL AND record_count IS NOT NULL AND succeeded_at IS NOT NULL
           AND error_code IS NULL AND error_message IS NULL))
);
CREATE TABLE instrument (
    instrument_id INTEGER PRIMARY KEY, instrument_key TEXT NOT NULL UNIQUE,
    source_code TEXT, instrument_type TEXT, symbol TEXT, exchange TEXT,
    name TEXT, valid_from TEXT, valid_to TEXT
);
CREATE TABLE records (
    record_id INTEGER PRIMARY KEY,
    fetch_unit_id INTEGER NOT NULL REFERENCES fetch_unit(unit_id),
    instrument_id INTEGER REFERENCES instrument(instrument_id), facts TEXT NOT NULL
);
CREATE INDEX records_unit ON records(fetch_unit_id);
"""
)
REQUIRED_COLUMNS = {
    "dataset_meta": {
        "singleton",
        "dataset_name",
        "schema_version",
        "source_name",
        "created_at",
        "updated_at",
    },
    "fetch_unit": {
        "unit_id",
        "unit_key",
        "status",
        "content_hash",
        "record_count",
        "created_at",
        "last_attempt_at",
        "succeeded_at",
        "error_code",
        "error_message",
        "basis",
    },
    "instrument": {
        "instrument_id",
        "instrument_key",
        "source_code",
        "instrument_type",
        "symbol",
        "exchange",
        "name",
        "valid_from",
        "valid_to",
    },
    "records": {"record_id", "fetch_unit_id", "instrument_id", "facts"},
}


def now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class Snapshot:
    coverage: CoverageResult
    successful: tuple[CachedUnit, ...]
    statuses: dict[str, Status]


class Repository:
    def __init__(self, path: Path, dataset: str, source: str) -> None:
        self.path = path
        self.dataset = dataset
        self.source = source
        self._sessions = local()

    def _validate(self, connection: sqlite3.Connection) -> None:
        for table, required in REQUIRED_COLUMNS.items():
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            if not required <= columns:
                raise OperationError("Dataset storage structure is incompatible")
        generation = self._identity(connection)
        if generation == 3:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(fetch_unit)")}
            basis_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(basis_snapshot)")
            }
            if (
                "basis_id" not in columns
                or not {"basis_id", "content_hash", "facts"} <= basis_columns
            ):
                raise OperationError("Dataset basis storage structure is incompatible")
            if connection.execute(
                "SELECT 1 FROM fetch_unit WHERE basis IS NOT NULL LIMIT 1"
            ).fetchone():
                raise OperationError("Dataset basis representation is inconsistent")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise OperationError("Dataset storage references are invalid")

    def _identity(self, connection: sqlite3.Connection) -> int:
        metadata = connection.execute("SELECT * FROM dataset_meta").fetchall()
        if len(metadata) != 1 or (
            metadata[0]["dataset_name"] != self.dataset
            or metadata[0]["source_name"] != self.source
            or metadata[0]["schema_version"] not in (2, SCHEMA_VERSION)
        ):
            raise OperationError("Dataset storage identity or generation is incompatible")
        return int(metadata[0]["schema_version"])

    def _upgrade(self, connection: sqlite3.Connection) -> None:
        # The caller holds BEGIN IMMEDIATE. A separate reader backs up the last
        # committed generation before any migration writes; backup never overwrites.
        backup = self.path.with_name(self.path.name + f".schema-2.{uuid4().hex}.backup")
        backup.touch(exist_ok=False)
        complete_backup = False
        try:
            with closing(
                sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
            ) as reader:
                with closing(sqlite3.connect(backup)) as destination:
                    reader.backup(destination)
            complete_backup = True
            for statement in BASIS_DDL:
                connection.execute(statement)
            connection.execute(
                "ALTER TABLE fetch_unit ADD COLUMN basis_id INTEGER "
                "REFERENCES basis_snapshot(basis_id)"
            )
            for row in connection.execute(
                "SELECT DISTINCT basis FROM fetch_unit WHERE basis IS NOT NULL"
            ).fetchall():
                original = row[0]
                value = json.loads(original)
                if not isinstance(value, dict):
                    raise OperationError("Frozen basis is invalid")
                encoded = canonical_json(value)
                basis_id = self._store_basis(connection, encoded)
                connection.execute(
                    "UPDATE fetch_unit SET basis_id=?, basis=NULL WHERE basis=?",
                    (basis_id, original),
                )
            connection.execute("UPDATE dataset_meta SET schema_version=?", (SCHEMA_VERSION,))
            self._validate(connection)
            connection.commit()
            connection.execute("BEGIN IMMEDIATE")
        except BaseException:
            connection.rollback()
            if not complete_backup:
                backup.unlink()
            raise

    @staticmethod
    def _store_basis(connection: sqlite3.Connection, encoded: str) -> int:
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        connection.execute(
            "INSERT INTO basis_snapshot(content_hash,facts) VALUES (?,?) "
            "ON CONFLICT(content_hash) DO NOTHING",
            (digest, encoded),
        )
        row = connection.execute(
            "SELECT basis_id,facts FROM basis_snapshot WHERE content_hash=?", (digest,)
        ).fetchone()
        if row is None or row["facts"] != encoded:
            raise OperationError("Frozen basis content conflicts with its identity")
        return int(row["basis_id"])

    @contextmanager
    def write_session(self) -> Iterator[None]:
        """Keep a thread-local connection, never a transaction across Source I/O."""
        if getattr(self._sessions, "connection", None) is not None:
            raise OperationError("Nested storage write sessions are unsupported")
        with self._connect(write=True) as connection:
            assert connection is not None
            connection.commit()
            self._sessions.connection = connection
            self._sessions.bases = {}
            try:
                yield
                connection.execute("BEGIN")
                self._validate(connection)
            finally:
                self._sessions.connection = None
                self._sessions.bases = {}

    @contextmanager
    def _connect(self, *, write: bool = False) -> Iterator[sqlite3.Connection | None]:
        active = getattr(self._sessions, "connection", None) if write else None
        if active is not None:
            try:
                active.execute("BEGIN IMMEDIATE")
                if self._identity(active) != SCHEMA_VERSION:
                    raise OperationError("Dataset storage generation changed during execution")
                yield active
                active.commit()
            except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as exc:
                raise OperationError("Dataset storage operation failed") from exc
            finally:
                active.rollback()
            return
        connection = None
        new = False
        initialized = False
        try:
            if not self.path.exists() and not write:
                yield None
                return
            if write:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation distinguishes a new cache from an invalid existing file.
                try:
                    self.path.touch(exist_ok=False)
                    new = True
                except FileExistsError:
                    new = False
                self._check_journal_mode()
                connection = sqlite3.connect(self.path)
            else:
                new = False
                self._check_journal_mode()
                connection = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            if new:
                # executescript otherwise commits implicitly; include BEGIN in the script.
                connection.executescript("BEGIN IMMEDIATE;\n" + DDL)
                timestamp = now()
                connection.execute(
                    "INSERT INTO dataset_meta VALUES (1, ?, ?, ?, ?, ?)",
                    (self.dataset, SCHEMA_VERSION, self.source, timestamp, timestamp),
                )
                connection.commit()
                initialized = True
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            self._validate(connection)
            if write and self._identity(connection) == 2:
                self._upgrade(connection)
            yield connection
            if write:
                connection.commit()
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as exc:
            raise OperationError("Dataset storage operation failed") from exc
        finally:
            try:
                if connection is not None:
                    connection.close()  # rolls back both failed writes and read transactions
                if new and not initialized:
                    self.path.unlink()
            except (sqlite3.Error, OSError) as exc:
                raise OperationError("Dataset storage cleanup failed") from exc

    def _check_journal_mode(self) -> None:
        # Even mode=ro can create WAL/SHM files. Inspect before SQLite opens the cache.
        # Header bytes 18 and 19 are the file write/read versions; 2 denotes WAL.
        with self.path.open("rb") as database:
            header = database.read(20)
        if header.startswith(b"SQLite format 3\x00") and 2 in header[18:20]:
            raise OperationError("Dataset storage uses unsupported WAL journal mode")

    def snapshot(self, units: Sequence[Unit]) -> Snapshot:
        statuses: dict[str, Status] = {}
        successful: list[CachedUnit] = []
        with self._connect() as connection:
            if connection is not None:
                generation = self._identity(connection)
                parsed_bases: dict[object, dict | None] = {}
                for unit in units:
                    row = connection.execute(
                        "SELECT * FROM fetch_unit WHERE unit_key = ?", (unit.key,)
                    ).fetchone()
                    if row is None:
                        continue
                    status = Status(row["status"])
                    statuses[unit.key] = status
                    if status != Status.SUCCESS:
                        continue
                    records: list[Record] = []
                    for record in connection.execute(
                        "SELECT r.facts, i.instrument_key FROM records r "
                        "LEFT JOIN instrument i USING(instrument_id) "
                        "WHERE r.fetch_unit_id = ? ORDER BY r.record_id",
                        (row["unit_id"],),
                    ):
                        fields = json.loads(record["facts"])
                        if not isinstance(fields, dict):
                            raise OperationError("Cached facts are invalid")
                        records.append(Record(fields, record["instrument_key"]))
                    if (
                        row["record_count"] != len(records)
                        or row["content_hash"] != record_hash(r.encode() for r in records)
                        or row["succeeded_at"] is None
                        or row["error_code"] is not None
                        or row["error_message"] is not None
                    ):
                        raise OperationError("Successful cache metadata is inconsistent")
                    instruments = tuple(
                        Instrument(**dict(instrument))
                        for instrument in connection.execute(
                            "SELECT DISTINCT i.instrument_key AS key, i.source_code, "
                            "i.instrument_type, i.symbol, i.exchange, i.name, i.valid_from, "
                            "i.valid_to FROM instrument i JOIN records r USING(instrument_id) "
                            "WHERE r.fetch_unit_id=? ORDER BY i.instrument_key",
                            (row["unit_id"],),
                        )
                    )
                    basis_key = row["basis_id"] if generation == 3 else row["basis"]
                    if basis_key not in parsed_bases:
                        if basis_key is None:
                            parsed_bases[basis_key] = None
                        else:
                            encoded_basis = basis_key
                            if generation == 3:
                                basis_row = connection.execute(
                                    "SELECT content_hash,facts FROM basis_snapshot "
                                    "WHERE basis_id=?",
                                    (basis_key,),
                                ).fetchone()
                                if (
                                    basis_row is None
                                    or hashlib.sha256(
                                        basis_row["facts"].encode("utf-8")
                                    ).hexdigest()
                                    != basis_row["content_hash"]
                                ):
                                    raise OperationError("Frozen basis content is inconsistent")
                                encoded_basis = basis_row["facts"]
                            parsed = json.loads(encoded_basis)
                            if not isinstance(parsed, dict):
                                raise OperationError("Frozen basis is invalid")
                            parsed_bases[basis_key] = parsed
                    successful.append(
                        CachedUnit(
                            unit,
                            tuple(records),
                            instruments,
                            parsed_bases[basis_key],
                        )
                    )
        counts = {status: list(statuses.values()).count(status) for status in Status}
        missing = len(units) - len(statuses)
        coverage = CoverageResult(
            len(units),
            counts[Status.SUCCESS],
            missing,
            counts[Status.PENDING],
            counts[Status.FAILED],
            len(successful) == len(units),
        )
        return Snapshot(coverage, tuple(successful), statuses)

    def successful_keys(self) -> tuple[str, ...]:
        """Internal metadata reuse seam; identity interpretation remains Dataset-owned."""
        with self._connect() as connection:
            if connection is None:
                return ()
            return tuple(
                row[0]
                for row in connection.execute(
                    "SELECT unit_key FROM fetch_unit WHERE status='success' ORDER BY unit_key"
                )
            )

    def pending(self, unit: Unit) -> None:
        with self._connect(write=True) as connection:
            assert connection is not None
            timestamp = now()
            connection.execute(
                "INSERT INTO fetch_unit(unit_key,status,created_at,last_attempt_at) "
                "VALUES (?, 'pending', ?, ?) ON CONFLICT(unit_key) DO UPDATE SET "
                "status='pending', last_attempt_at=excluded.last_attempt_at, "
                "succeeded_at=NULL, error_code=NULL, error_message=NULL",
                (unit.key, timestamp, timestamp),
            )
            connection.execute("UPDATE dataset_meta SET updated_at=?", (timestamp,))

    def failed(self, unit: Unit, failure: ExecutionFailure) -> None:
        with self._connect(write=True) as connection:
            assert connection is not None
            changed = connection.execute(
                "UPDATE fetch_unit SET status='failed', succeeded_at=NULL, "
                "error_code=?, error_message=? WHERE unit_key=? AND status='pending'",
                (failure.code, failure.reason, unit.key),
            )
            if changed.rowcount != 1:
                raise OperationError("Unit execution was not started")
            connection.execute("UPDATE dataset_meta SET updated_at=?", (now(),))

    def succeed(self, unit: Unit, normalized: UnitRecords) -> int:
        encoded = tuple(record.encode() for record in normalized.records)
        with self._connect(write=True) as connection:
            assert connection is not None
            row = connection.execute(
                "SELECT unit_id, status FROM fetch_unit WHERE unit_key=?", (unit.key,)
            ).fetchone()
            if row is None or row["status"] != Status.PENDING:
                raise OperationError("Unit execution was not started")
            connection.executemany(
                "INSERT INTO instrument(instrument_key,source_code,instrument_type,symbol,"
                "exchange,name,valid_from,valid_to) VALUES (?,?,?,?,?,?,?,?) "
                "ON CONFLICT(instrument_key) DO UPDATE SET source_code=excluded.source_code,"
                "instrument_type=excluded.instrument_type,symbol=excluded.symbol,"
                "exchange=excluded.exchange,name=excluded.name,valid_from=excluded.valid_from,"
                "valid_to=excluded.valid_to",
                (astuple(instrument) for instrument in normalized.instruments),
            )
            connection.execute("DELETE FROM records WHERE fetch_unit_id=?", (row["unit_id"],))
            instrument_ids: dict[str, int] = {}
            keys = sorted(
                {r.instrument_key for r in normalized.records if r.instrument_key is not None}
            )
            for offset in range(0, len(keys), 900):
                chunk = keys[offset : offset + 900]
                marks = ",".join("?" for _ in chunk)
                instrument_ids.update(
                    (item["instrument_key"], item["instrument_id"])
                    for item in connection.execute(
                        "SELECT instrument_key,instrument_id FROM instrument "
                        f"WHERE instrument_key IN ({marks})",
                        chunk,
                    )
                )
            if set(keys) != set(instrument_ids):
                raise OperationError("Record references an unknown local instrument")
            connection.executemany(
                "INSERT INTO records(fetch_unit_id,instrument_id,facts) VALUES (?,?,?)",
                (
                    (
                        row["unit_id"],
                        instrument_ids.get(record.instrument_key)
                        if record.instrument_key is not None
                        else None,
                        canonical_json(record.fields),
                    )
                    for record in normalized.records
                ),
            )
            basis_id = None
            if normalized.basis is not None:
                memo = getattr(self._sessions, "bases", {})
                cached = memo.get(id(normalized.basis))
                if cached is None:
                    basis_id = self._store_basis(connection, canonical_json(normalized.basis))
                    memo[id(normalized.basis)] = normalized.basis, basis_id
                else:
                    _, basis_id = cached
            timestamp = now()
            connection.execute(
                "UPDATE fetch_unit SET status='success', content_hash=?, "
                "record_count=?, succeeded_at=?, basis=NULL, basis_id=?, "
                "error_code=NULL, error_message=NULL "
                "WHERE unit_key=?",
                (
                    record_hash(encoded),
                    len(encoded),
                    timestamp,
                    basis_id,
                    unit.key,
                ),
            )
            connection.execute("UPDATE dataset_meta SET updated_at=?", (timestamp,))
        return len(encoded)
