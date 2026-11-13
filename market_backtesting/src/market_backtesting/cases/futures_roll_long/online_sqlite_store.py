"""W2-private portable SQLite persistence; application admission remains caller-owned."""

import hashlib
import secrets
import sqlite3
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from .application_models import FuturesRollApplicationError, FuturesRollRequest
from .failures import FuturesRollError
from .online_codec import (
    METADATA_LIMIT,
    RESULT_LIMIT,
    decode_request,
    decode_result,
    json_bytes,
    strict_json,
)
from .online_models import FuturesRollOnlineError, OnlineFailure, OnlineRunStatus, RunState
from .online_record import now, valid_id, validate_state

_SCHEMA = (
    "CREATE TABLE runs (run_id TEXT PRIMARY KEY, owner TEXT NOT NULL, "
    "metadata BLOB NOT NULL, state BLOB NOT NULL, status TEXT NOT NULL, "
    "result_length INTEGER, profile TEXT, scientific_status TEXT)",
    "CREATE TABLE results (run_id TEXT PRIMARY KEY REFERENCES runs(run_id), payload BLOB NOT NULL)",
)


class FuturesRollSQLiteRunStore:
    """No initialization on construction/read; no connections escape this boundary.

    One backend process is supported. Callers serialize admission and recovery and
    supply the actual active run. Controlled ancestors/ACLs are an operator obligation;
    portable identity checks cannot defeat hostile concurrent path replacement.
    """

    def __init__(self, root: Path) -> None:
        if not root.is_absolute() or ".." in root.parts:
            raise FuturesRollOnlineError("unavailable")
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
                raise FuturesRollOnlineError("unavailable")
        info = self.root.lstat()
        root_identity = (info.st_dev, info.st_ino)
        if not info.st_ino or (
            self._root_identity is not None and self._root_identity != root_identity
        ):
            raise FuturesRollOnlineError("corrupt")
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
                raise FuturesRollOnlineError("corrupt")
        if self.path.exists():
            info = self.path.lstat()
            identity = (info.st_dev, info.st_ino)
            if self._identity is not None and self._identity != identity:
                raise FuturesRollOnlineError("corrupt")
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
                raise FuturesRollOnlineError("run_not_found")
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
                    raise FuturesRollOnlineError("unavailable") from None
            if isinstance(exc, FuturesRollOnlineError):
                raise
            if isinstance(exc, sqlite3.Error):
                code = getattr(exc, "sqlite_errorcode", 0) & 255
                category = (
                    "corrupt"
                    if code
                    in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB, sqlite3.SQLITE_SCHEMA)
                    else "unavailable"
                )
                raise FuturesRollOnlineError(category) from None
            if isinstance(exc, FileNotFoundError):
                raise FuturesRollOnlineError(
                    "run_not_found" if not write else "unavailable"
                ) from None
            if isinstance(exc, OSError):
                raise FuturesRollOnlineError("unavailable") from None
            if isinstance(
                exc,
                ValueError | TypeError | OverflowError | RecursionError | FuturesRollError,
            ):
                raise FuturesRollOnlineError("corrupt") from None
            raise
        finally:
            if connection is not None:
                try:
                    connection.close()
                except sqlite3.Error:
                    raise FuturesRollOnlineError("unavailable") from None

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
            raise FuturesRollOnlineError("corrupt")

    def initialize(self) -> None:
        with self._connection(write=True, initialize=True):
            pass

    def create(self, request: FuturesRollRequest, owner: str) -> OnlineRunStatus:
        if type(owner) is not str or not owner:
            raise FuturesRollOnlineError("invalid_request")
        run_id, created = secrets.token_hex(16), now()
        metadata = dict(
            version=1, run_id=run_id, request=asdict(request), owner_scope=owner, created_at=created
        )
        try:
            encoded = json_bytes(metadata)
            decode_request(strict_json(encoded)["request"])
        except (ValueError, TypeError, FuturesRollOnlineError, FuturesRollApplicationError):
            raise FuturesRollOnlineError("invalid_request") from None
        state = dict(
            version=1,
            run_id=run_id,
            request_digest=hashlib.sha256(encoded).hexdigest(),
            status="PENDING",
            created_at=created,
            started_at=None,
            finished_at=None,
            failure=None,
            result_digest=None,
        )
        with self._connection(write=True, initialize=True) as connection:
            if connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone():
                raise FuturesRollOnlineError("unavailable")
            connection.execute(
                "INSERT INTO runs VALUES (?,?,?,?,?,NULL,NULL,NULL)",
                (run_id, owner, encoded, json_bytes(state), "PENDING"),
            )
        return OnlineRunStatus(run_id, "PENDING", request, created)

    def _record(
        self, connection: sqlite3.Connection, run_id: str, owner: str | None = None
    ) -> tuple[dict[str, Any], dict[str, Any], FuturesRollRequest]:
        row = connection.execute("SELECT owner FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None or (owner is not None and row[0] != owner):
            raise FuturesRollOnlineError("run_not_found")
        bounds = connection.execute(
            "SELECT typeof(metadata),length(metadata),typeof(state),length(state) "
            "FROM runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        if bounds is None or any(
            kind != "blob" or type(size) is not int or not 0 < size <= METADATA_LIMIT
            for kind, size in (bounds[:2], bounds[2:])
        ):
            raise ValueError("metadata_size")
        row = connection.execute(
            "SELECT metadata,state,status,result_length,profile,scientific_status "
            "FROM runs WHERE run_id=?",
            (run_id,),
        ).fetchone()
        metadata_bytes, state_bytes, status, length, profile, scientific = row
        if (
            type(metadata_bytes) is not bytes
            or type(state_bytes) is not bytes
            or max(len(metadata_bytes), len(state_bytes)) > METADATA_LIMIT
        ):
            raise ValueError("metadata_size")
        metadata, state = strict_json(metadata_bytes), strict_json(state_bytes)
        if (
            type(metadata) is not dict
            or set(metadata) != {"version", "run_id", "request", "owner_scope", "created_at"}
            or type(metadata["version"]) is not int
            or metadata["version"] != 1
            or metadata["run_id"] != run_id
            or type(metadata["owner_scope"]) is not str
            or not metadata["owner_scope"]
        ):
            raise ValueError("metadata_identity")
        if (
            metadata["owner_scope"]
            != connection.execute("SELECT owner FROM runs WHERE run_id=?", (run_id,)).fetchone()[0]
        ):
            raise ValueError("owner_identity")
        request = decode_request(metadata["request"])
        validate_state(state, run_id, metadata)
        if state["status"] != status:
            raise ValueError("state_identity")
        result = connection.execute(
            "SELECT typeof(payload),length(payload) FROM results WHERE run_id=?", (run_id,)
        ).fetchone()
        if status == "COMPLETED":
            if (
                type(length) is not int
                or not 0 < length <= RESULT_LIMIT
                or result != ("blob", length)
                or profile != "futures_roll_long_result_v1"
                or scientific != "complete"
            ):
                raise ValueError("result_metadata")
        elif result is not None or any(
            value is not None for value in (length, profile, scientific)
        ):
            raise ValueError("unexpected_result")
        return metadata, state, request

    @staticmethod
    def _status(run_id: str, state: dict[str, Any], request: FuturesRollRequest) -> OnlineRunStatus:
        return OnlineRunStatus(
            run_id,
            cast(RunState, state["status"]),
            request,
            state["created_at"],
            state["started_at"],
            state["finished_at"],
            OnlineFailure(**state["failure"]) if state["failure"] else None,
        )

    def status(self, run_id: str, owner: str) -> OnlineRunStatus:
        valid_id(run_id)
        if type(owner) is not str or not owner:
            raise FuturesRollOnlineError("invalid_request")
        with self._connection() as connection:
            _, state, request = self._record(connection, run_id, owner)
            return self._status(run_id, state, request)

    def _transition(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        status: RunState,
        failure: OnlineFailure | None = None,
    ) -> None:
        metadata, state, _ = self._record(connection, run_id)
        previous = state["status"]
        if status not in {
            "PENDING": {"RUNNING", "FAILED", "INTERRUPTED"},
            "RUNNING": {"FAILED", "INTERRUPTED"},
        }.get(previous, set()):
            raise FuturesRollOnlineError("corrupt")
        state["status"], state["failure"] = status, asdict(failure) if failure else None
        if status == "RUNNING":
            state["started_at"] = now()
        else:
            state["finished_at"] = now()
        validate_state(state, run_id, metadata)
        if (
            connection.execute(
                "UPDATE runs SET state=?,status=? WHERE run_id=? AND status=?",
                (json_bytes(state), status, run_id, previous),
            ).rowcount
            != 1
        ):
            raise FuturesRollOnlineError("corrupt")

    def transition(
        self, run_id: str, status: RunState, *, failure: OnlineFailure | None = None
    ) -> None:
        valid_id(run_id)
        with self._connection(write=True) as connection:
            self._transition(connection, run_id, status, failure)

    @staticmethod
    def _validate_payload(payload: bytes, request: FuturesRollRequest) -> None:
        try:
            decode_result(payload, request)
            if json_bytes(strict_json(payload), RESULT_LIMIT) != payload:
                raise ValueError("canonical_json")
        except (
            ValueError,
            TypeError,
            OverflowError,
            RecursionError,
            FuturesRollError,
            FuturesRollOnlineError,
        ):
            raise FuturesRollOnlineError("corrupt") from None

    def publish(self, run_id: str, payload: bytes) -> None:
        valid_id(run_id)
        if type(payload) is not bytes:
            raise FuturesRollOnlineError("corrupt")
        if len(payload) > RESULT_LIMIT:
            raise FuturesRollOnlineError("result_too_large")
        with self._connection() as connection:
            _, _, request = self._record(connection, run_id)
        self._validate_payload(payload, request)
        with self._connection(write=True) as connection:
            metadata, state, current_request = self._record(connection, run_id)
            if state["status"] != "RUNNING" or current_request != request:
                raise FuturesRollOnlineError("corrupt")
            state.update(
                status="COMPLETED",
                finished_at=now(),
                result_digest=hashlib.sha256(payload).hexdigest(),
            )
            validate_state(state, run_id, metadata)
            connection.execute("INSERT INTO results VALUES (?,?)", (run_id, payload))
            if (
                connection.execute(
                    "UPDATE runs SET state=?,status='COMPLETED',result_length=?,"
                    "profile='futures_roll_long_result_v1',scientific_status='complete' "
                    "WHERE run_id=? AND status='RUNNING'",
                    (json_bytes(state), len(payload), run_id),
                ).rowcount
                != 1
            ):
                raise FuturesRollOnlineError("corrupt")

    def read_result(self, run_id: str, owner: str) -> bytes:
        valid_id(run_id)
        if type(owner) is not str or not owner:
            raise FuturesRollOnlineError("invalid_request")
        with self._connection() as connection:
            _, state, request = self._record(connection, run_id, owner)
            if state["status"] != "COMPLETED":
                raise FuturesRollOnlineError("result_not_ready")
            payload = connection.execute(
                "SELECT payload FROM results WHERE run_id=?", (run_id,)
            ).fetchone()[0]
            if hashlib.sha256(payload).hexdigest() != state["result_digest"]:
                raise ValueError("result_digest")
            self._validate_payload(payload, request)
            return cast(bytes, payload)

    def recover(self, active: tuple[str, str] | None = None) -> None:
        with self._connection(write=True, initialize=True) as connection:
            ids = connection.execute("SELECT run_id FROM runs").fetchall()
            for (run_id,) in ids:
                try:
                    valid_id(run_id)
                except FuturesRollOnlineError:
                    raise FuturesRollOnlineError("corrupt") from None
                _, state, _ = self._record(connection, run_id)
                if active == (str(self.root), run_id):
                    continue
                if state["status"] in {"PENDING", "RUNNING"}:
                    self._transition(
                        connection,
                        run_id,
                        "INTERRUPTED",
                        OnlineFailure("execution", "interrupted", None, "interrupted"),
                    )
