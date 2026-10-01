"""One rollback-journal SQLite, with read snapshots and per-unit write transactions."""

import json
import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import astuple, dataclass
from datetime import UTC, datetime
from pathlib import Path

from ._domain import CachedUnit, ExecutionFailure, Instrument, Record, Status, Unit, UnitRecords
from ._serialization import canonical_json, record_hash
from .results import ApplicationFailure, CoverageResult

SCHEMA_VERSION = 1
DDL = """
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
    error_code TEXT, error_message TEXT,
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

    def _validate(self, connection: sqlite3.Connection) -> None:
        for table, required in REQUIRED_COLUMNS.items():
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
            if not required <= columns:
                raise ApplicationFailure("Dataset storage structure is incompatible")
        metadata = connection.execute("SELECT * FROM dataset_meta").fetchall()
        if len(metadata) != 1 or (
            metadata[0]["dataset_name"],
            metadata[0]["schema_version"],
            metadata[0]["source_name"],
        ) != (self.dataset, SCHEMA_VERSION, self.source):
            raise ApplicationFailure("Dataset storage identity or generation is incompatible")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ApplicationFailure("Dataset storage references are invalid")

    @contextmanager
    def _connect(self, *, write: bool = False) -> Iterator[sqlite3.Connection | None]:
        connection = None
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
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            self._validate(connection)
            yield connection
            if write:
                connection.commit()
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError) as exc:
            raise ApplicationFailure("Dataset storage operation failed") from exc
        finally:
            if connection is not None:
                connection.close()  # rolls back both failed writes and read transactions

    def _check_journal_mode(self) -> None:
        # Even mode=ro can create WAL/SHM files. Inspect before SQLite opens the cache.
        # Header bytes 18 and 19 are the file write/read versions; 2 denotes WAL.
        with self.path.open("rb") as database:
            header = database.read(20)
        if header.startswith(b"SQLite format 3\x00") and 2 in header[18:20]:
            raise ApplicationFailure("Dataset storage uses unsupported WAL journal mode")

    def snapshot(self, units: Sequence[Unit]) -> Snapshot:
        statuses: dict[str, Status] = {}
        successful: list[CachedUnit] = []
        with self._connect() as connection:
            if connection is not None:
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
                            raise ApplicationFailure("Cached facts are invalid")
                        records.append(Record(fields, record["instrument_key"]))
                    if (
                        row["record_count"] != len(records)
                        or row["content_hash"] != record_hash(r.encode() for r in records)
                        or row["succeeded_at"] is None
                        or row["error_code"] is not None
                        or row["error_message"] is not None
                    ):
                        raise ApplicationFailure("Successful cache metadata is inconsistent")
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
                    successful.append(CachedUnit(unit, tuple(records), instruments))
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
                raise ApplicationFailure("Unit execution was not started")
            connection.execute("UPDATE dataset_meta SET updated_at=?", (now(),))

    def succeed(self, unit: Unit, normalized: UnitRecords) -> int:
        encoded = tuple(record.encode() for record in normalized.records)
        with self._connect(write=True) as connection:
            assert connection is not None
            row = connection.execute(
                "SELECT unit_id, status FROM fetch_unit WHERE unit_key=?", (unit.key,)
            ).fetchone()
            if row is None or row["status"] != Status.PENDING:
                raise ApplicationFailure("Unit execution was not started")
            for instrument in normalized.instruments:
                connection.execute(
                    "INSERT INTO instrument(instrument_key,source_code,instrument_type,symbol,"
                    "exchange,name,valid_from,valid_to) VALUES (?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(instrument_key) DO UPDATE SET source_code=excluded.source_code,"
                    "instrument_type=excluded.instrument_type,symbol=excluded.symbol,"
                    "exchange=excluded.exchange,name=excluded.name,valid_from=excluded.valid_from,"
                    "valid_to=excluded.valid_to",
                    astuple(instrument),
                )
            connection.execute("DELETE FROM records WHERE fetch_unit_id=?", (row["unit_id"],))
            for record in normalized.records:
                instrument_id = None
                if record.instrument_key is not None:
                    instrument = connection.execute(
                        "SELECT instrument_id FROM instrument WHERE instrument_key=?",
                        (record.instrument_key,),
                    ).fetchone()
                    if instrument is None:
                        raise ApplicationFailure("Record references an unknown local instrument")
                    instrument_id = instrument[0]
                connection.execute(
                    "INSERT INTO records(fetch_unit_id,instrument_id,facts) VALUES (?,?,?)",
                    (row["unit_id"], instrument_id, canonical_json(record.fields)),
                )
            timestamp = now()
            connection.execute(
                "UPDATE fetch_unit SET status='success', content_hash=?, "
                "record_count=?, succeeded_at=?, error_code=NULL, error_message=NULL "
                "WHERE unit_key=?",
                (record_hash(encoded), len(encoded), timestamp, unit.key),
            )
            connection.execute("UPDATE dataset_meta SET updated_at=?", (timestamp,))
        return len(encoded)
