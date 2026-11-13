"""W1-owned portable SQLite persistence."""

import hashlib
import secrets
import sqlite3
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import PROFILE_REPORT, json_bytes
from .inputs import DEFINITION_VERSION, FuturesBasisRequest
from .online_record import (
    ID_PATTERN,
    MAX_REPORT_BYTES,
    OnlineError,
    _decode,
    _failure_reason,
    _now,
    _request_data,
    _state,
    _validate_state,
    standard_report_request,
)
from .validation import validate_request

_SCHEMA = (
    "CREATE TABLE runs (run_id TEXT PRIMARY KEY, owner TEXT NOT NULL, "
    "metadata BLOB NOT NULL, state BLOB NOT NULL, status TEXT NOT NULL, "
    "result_length INTEGER, profile TEXT, scientific_status TEXT)",
    "CREATE TABLE results (run_id TEXT PRIMARY KEY REFERENCES runs(run_id), payload BLOB NOT NULL)",
)


class FuturesBasisSQLiteRunStore:
    def __init__(self, root: Path) -> None:
        if not root.is_absolute() or ".." in root.parts:
            raise OnlineError("unavailable")
        self.root = root
        self.path = root / "runs.sqlite3"
        self._identity: tuple[int, int] | None = None
        self._root_identity: tuple[int, int] | None = None

    def _paths(self, create: bool = False) -> None:
        for path in (*reversed(self.root.parents), self.root):
            try:
                info = path.lstat()
            except FileNotFoundError:
                if not create:
                    raise
                path.mkdir(mode=0o700)
                info = path.lstat()
            if (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
            ):
                raise OnlineError("unavailable")
        info = self.root.lstat()
        root_identity = (info.st_dev, info.st_ino)
        if not info.st_ino or (
            self._root_identity is not None and self._root_identity != root_identity
        ):
            raise OnlineError("corrupt")
        self._root_identity = root_identity
        for path in (self.path, *(Path(str(self.path) + s) for s in ("-journal", "-wal", "-shm"))):
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or getattr(info, "st_file_attributes", 0) & 0x400
                or info.st_nlink != 1
                or not info.st_ino
            ):
                raise OnlineError("corrupt")
        if self.path.exists():
            info = self.path.lstat()
            identity = (info.st_dev, info.st_ino)
            if self._identity is not None and self._identity != identity:
                raise OnlineError("corrupt")
            self._identity = identity

    @contextmanager
    def _connection(
        self, *, write: bool = False, initialize: bool = False
    ) -> Iterator[sqlite3.Connection]:
        connection = None
        try:
            self._paths(create=initialize)
            new = False
            if initialize:
                try:
                    with self.path.open("xb"):
                        pass
                    new = True
                except FileExistsError:
                    pass
                self._paths()
            if not self.path.exists():
                raise OnlineError("run_not_found")
            connection = sqlite3.connect(
                self.path.as_uri() + "?mode=rw", uri=True, timeout=1.0, isolation_level=None
            )
            self._paths()
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            if new:
                for statement in _SCHEMA:
                    connection.execute(statement)
                connection.execute("PRAGMA user_version=1")
            self._schema(connection)
            yield connection
            if write:
                self._paths()
                self._commit(connection)
            else:
                connection.rollback()
        except BaseException as exc:
            if connection is not None:
                try:
                    connection.rollback()
                except sqlite3.Error:
                    raise OnlineError("unavailable") from None
            if isinstance(exc, OnlineError):
                raise
            if isinstance(exc, sqlite3.Error):
                code = getattr(exc, "sqlite_errorcode", 0) & 255
                category = (
                    "corrupt"
                    if code
                    in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB, sqlite3.SQLITE_SCHEMA)
                    else "unavailable"
                )
                raise OnlineError(category) from None
            if isinstance(exc, FileNotFoundError):
                raise OnlineError("run_not_found" if not write else "unavailable") from None
            if isinstance(exc, OSError):
                raise OnlineError("unavailable") from None
            if isinstance(
                exc,
                ValueError | TypeError | KeyError | UnicodeError | OverflowError | RecursionError,
            ):
                raise OnlineError("corrupt") from None
            raise
        finally:
            if connection is not None:
                try:
                    connection.close()
                except sqlite3.Error:
                    raise OnlineError("unavailable") from None

    def _commit(self, connection: sqlite3.Connection) -> None:
        connection.commit()

    @staticmethod
    def _schema(connection: sqlite3.Connection) -> None:
        objects = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        if connection.execute("PRAGMA user_version").fetchone()[0] != 1 or objects != [
            (_SCHEMA[1],),
            (_SCHEMA[0],),
        ]:
            raise OnlineError("corrupt")

    def initialize(self) -> None:
        with self._connection(write=True, initialize=True):
            pass

    def create(self, request: FuturesBasisRequest, owner: str) -> dict[str, Any]:
        run_id, created = secrets.token_hex(16), _now()
        metadata = dict(
            version=1, request=_request_data(request), owner_scope=owner, created_at=created
        )
        encoded = json_bytes(metadata)
        if len(encoded) > 8192:
            raise OnlineError("invalid_request")
        with self._connection(write=True, initialize=True) as c:
            if c.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone():
                raise OnlineError("unavailable")
            c.execute(
                "INSERT INTO runs VALUES (?,?,?,?,?,NULL,NULL,NULL)",
                (run_id, owner, encoded, json_bytes(_state("PENDING", created)), "PENDING"),
            )
        return dict(
            run_id=run_id, status="PENDING", request=metadata["request"], created_at=created
        )

    @staticmethod
    def valid_id(run_id: str) -> None:
        if type(run_id) is not str or ID_PATTERN.fullmatch(run_id) is None:
            raise OnlineError("run_not_found")

    def _record(
        self, c: sqlite3.Connection, run_id: str, owner: str | None = None, full: bool = False
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        row = c.execute("SELECT owner FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or (owner is not None and row[0] != owner):
            raise OnlineError("run_not_found")
        bounds = c.execute(
            "SELECT typeof(metadata),length(metadata),typeof(state),length(state) "
            "FROM runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if any(
            kind != "blob" or type(size) is not int or not 0 < size <= 8192
            for kind, size in (bounds[:2], bounds[2:])
        ):
            raise OnlineError("corrupt")
        m, s, status, length, profile, science = c.execute(
            "SELECT metadata,state,status,result_length,profile,scientific_status FROM runs "
            "WHERE run_id=?",
            (run_id,),
        ).fetchone()
        m, s = _decode(m), _decode(s)
        if (
            not isinstance(m, dict)
            or set(m) != {"version", "request", "owner_scope", "created_at"}
            or m["owner_scope"] != row[0]
        ):
            raise OnlineError("corrupt")
        if type(m["version"]) is not int or m["version"] != 1:
            raise OnlineError("unsupported_version")
        req = m["request"]
        request = FuturesBasisRequest(
            req["product_code"],
            date.fromisoformat(req["start_date"]),
            date.fromisoformat(req["end_date"]),
            req["case"],
        )
        validate_request(request, check_today=False)
        if req != _request_data(request) or (request.end_date - request.start_date).days + 1 > 1096:
            raise OnlineError("corrupt")
        _validate_state(s)
        if s["created_at"] != m["created_at"] or s["status"] != status:
            raise OnlineError("corrupt")
        result = c.execute(
            "SELECT typeof(payload),length(payload) FROM results WHERE run_id=?", (run_id,)
        ).fetchone()
        if full and result and result[0] == "blob" and result[1] > MAX_REPORT_BYTES:
            raise OnlineError("response_too_large")
        if status == "COMPLETED":
            if (
                type(length) is not int
                or not 0 < length <= MAX_REPORT_BYTES
                or result != ("blob", length)
                or profile != PROFILE_REPORT
                or science != s["result_status"]
            ):
                raise OnlineError("corrupt")
        elif result is not None or any(x is not None for x in (length, profile, science)):
            raise OnlineError("corrupt")
        return m, s

    def status(self, run_id: str, owner: str) -> dict[str, Any]:
        self.valid_id(run_id)
        with self._connection() as c:
            m, s = self._record(c, run_id, owner)
        return dict(
            run_id=run_id,
            request=m["request"],
            **{k: v for k, v in s.items() if k not in {"version", "result_digest"}},
            result_available=s["status"] == "COMPLETED",
        )

    def _transition(
        self, c: sqlite3.Connection, run_id: str, status: str, failure: dict[str, Any] | None = None
    ) -> None:
        _, s = self._record(c, run_id)
        previous = s["status"]
        if status not in {
            "PENDING": {"RUNNING", "FAILED", "INTERRUPTED"},
            "RUNNING": {"FAILED", "INTERRUPTED"},
        }.get(previous, set()):
            raise OnlineError("corrupt")
        s.update(status=status, failure=failure)
        s["started_at" if status == "RUNNING" else "finished_at"] = _now()
        _validate_state(s)
        if (
            c.execute(
                "UPDATE runs SET state=?,status=? WHERE run_id=? AND status=?",
                (json_bytes(s), status, run_id, previous),
            ).rowcount
            != 1
        ):
            raise OnlineError("corrupt")

    def transition(self, run_id: str, status: str, failure: dict[str, Any] | None = None) -> None:
        with self._connection(write=True) as c:
            self._transition(c, run_id, status, failure)

    @staticmethod
    def validate_payload(payload: bytes, metadata: dict[str, Any], state: dict[str, Any]) -> Any:
        reader = _decode(payload)
        if not isinstance(reader, dict):
            raise OnlineError("corrupt")
        if reader.get("profile") != PROFILE_REPORT:
            raise OnlineError("unsupported_version")
        req = metadata["request"]
        request = FuturesBasisRequest(
            req["product_code"],
            date.fromisoformat(req["start_date"]),
            date.fromisoformat(req["end_date"]),
        )
        if (
            reader.get("request") != _decode(json_bytes(standard_report_request(request)))
            or reader.get("status") != state["result_status"]
            or reader.get("definition_version") != DEFINITION_VERSION
            or not isinstance(reader.get("fingerprint"), str)
            or len(reader["fingerprint"]) != 64
            or any(x not in "0123456789abcdef" for x in reader["fingerprint"])
            or json_bytes(reader) != payload
        ):
            raise OnlineError("corrupt")
        return reader

    def publish(self, run_id: str, payload: bytes, scientific_status: str) -> None:
        if len(payload) > MAX_REPORT_BYTES:
            raise OnlineError("result_too_large")
        with self._connection() as c:
            m, s = self._record(c, run_id)
        s.update(result_status=scientific_status)
        self.validate_payload(payload, m, s)
        with self._connection(write=True) as c:
            m, s = self._record(c, run_id)
            if s["status"] != "RUNNING":
                raise OnlineError("corrupt")
            s.update(
                status="COMPLETED",
                finished_at=_now(),
                result_status=scientific_status,
                result_digest=hashlib.sha256(payload).hexdigest(),
            )
            _validate_state(s)
            c.execute("INSERT INTO results VALUES (?,?)", (run_id, payload))
            c.execute(
                "UPDATE runs SET state=?,status='COMPLETED',result_length=?,profile=?,"
                "scientific_status=? WHERE run_id=? AND status='RUNNING'",
                (json_bytes(s), len(payload), PROFILE_REPORT, scientific_status, run_id),
            )

    def read_report(self, run_id: str, owner: str) -> dict[str, Any]:
        self.valid_id(run_id)
        with self._connection() as c:
            m, s = self._record(c, run_id, owner, full=True)
            if s["status"] != "COMPLETED":
                raise OnlineError(
                    "result_not_ready"
                    if s["status"] in {"PENDING", "RUNNING"}
                    else "result_unavailable"
                )
            payload = c.execute("SELECT payload FROM results WHERE run_id=?", (run_id,)).fetchone()[
                0
            ]
            if hashlib.sha256(payload).hexdigest() != s["result_digest"]:
                raise OnlineError("corrupt")
            return self.validate_payload(payload, m, s)

    def recover(self, active: tuple[str, str] | None = None) -> None:
        with self._connection(write=True, initialize=True) as c:
            for (run_id,) in c.execute("SELECT run_id FROM runs").fetchall():
                self.valid_id(run_id)
                _, s = self._record(c, run_id)
                if active != (str(self.root), run_id) and s["status"] in {"PENDING", "RUNNING"}:
                    self._transition(
                        c,
                        run_id,
                        "INTERRUPTED",
                        dict(
                            stage="execution",
                            category="interrupted",
                            dependency=None,
                            reason=_failure_reason("execution", "interrupted"),
                        ),
                    )
