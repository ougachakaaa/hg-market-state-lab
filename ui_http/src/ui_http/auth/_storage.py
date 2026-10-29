"""Auth-owned SQLite implementation. Consumers use the package public service."""

import os
import re
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from argon2 import extract_parameters
from argon2.exceptions import InvalidHashError
from argon2.low_level import Type

from ._models import AuthFailureKind, AuthServiceError, PendingUser, UserIdentity, UserStatus

_DDL = """CREATE TABLE users (
    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) = 36),
    username TEXT NOT NULL UNIQUE CHECK(
        length(username) BETWEEN 3 AND 64
        AND username GLOB '[a-z0-9]*'
        AND username NOT GLOB '*[^a-z0-9_.-]*'
    ),
    password_hash TEXT NOT NULL CHECK(password_hash LIKE '$argon2id$%'),
    status TEXT NOT NULL CHECK(status IN ('pending', 'active', 'rejected', 'disabled')),
    created_at TEXT NOT NULL
)"""
_SCHEMA_VERSION = 1


class UserStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._checked = False

    def _initialize(self) -> None:
        if self.path.exists():
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Publish a fully initialized empty DB without replacing a concurrent creator.
        # An existing empty/corrupt file must never be mistaken for a new database.
        descriptor, filename = tempfile.mkstemp(
            prefix=".auth-", suffix=".sqlite3", dir=self.path.parent
        )
        os.close(descriptor)
        temporary = Path(filename)
        try:
            with closing(sqlite3.connect(temporary)) as connection, connection:
                connection.execute(_DDL)
                connection.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
            try:
                os.link(temporary, self.path)
            except FileExistsError:
                pass
        finally:
            temporary.unlink()

    @contextmanager
    def _transaction(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        try:
            self._initialize()
            # rw prevents accidental recreation if the file disappears after initialization.
            uri = self.path.as_uri() + "?mode=rw"
            with closing(sqlite3.connect(uri, uri=True, timeout=10)) as connection:
                connection.row_factory = sqlite3.Row
                with connection:
                    connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                    self._validate_schema(connection)
                    if write or not self._checked:
                        if [row[0] for row in connection.execute("PRAGMA quick_check")] != ["ok"]:
                            raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE)
                        self._checked = True
                    yield connection
        except (sqlite3.Error, OSError, ValueError, TypeError, KeyError, InvalidHashError):
            raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE) from None

    @staticmethod
    def _validate_schema(connection: sqlite3.Connection) -> None:
        objects = {
            (row["type"], row["name"], row["tbl_name"], row["sql"])
            for row in connection.execute("SELECT type, name, tbl_name, sql FROM sqlite_schema")
        }
        expected = {
            ("table", "users", "users", _DDL),
            ("index", "sqlite_autoindex_users_1", "users", None),
            ("index", "sqlite_autoindex_users_2", "users", None),
        }
        if (
            connection.execute("PRAGMA user_version").fetchone()[0] != _SCHEMA_VERSION
            or objects != expected
        ):
            raise AuthServiceError(AuthFailureKind.OPERATIONAL_FAILURE)

    def insert(self, user_id: str, username: str, password_hash: str, created_at: str) -> None:
        with self._transaction(write=True) as connection:
            # Only the canonical username conflict is accepted; all other faults fail closed.
            connection.execute(
                "INSERT INTO users(id, username, password_hash, status, created_at) "
                "VALUES (?, ?, ?, 'pending', ?) ON CONFLICT(username) DO NOTHING",
                (user_id, username, password_hash, created_at),
            )

    @staticmethod
    def _identity(row: sqlite3.Row) -> UserIdentity:
        user_id = row["id"]
        if (
            str(UUID(user_id)) != user_id
            or re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}", row["username"]) is None
        ):
            raise ValueError("Invalid stored identity")
        return UserIdentity(user_id, row["username"], UserStatus(row["status"]))

    def list_pending(self) -> tuple[PendingUser, ...]:
        with self._transaction() as connection:
            result = []
            for row in connection.execute(
                "SELECT id, username, status, created_at FROM users "
                "WHERE status = 'pending' ORDER BY created_at, id"
            ):
                identity = self._identity(row)
                timestamp = datetime.fromisoformat(row["created_at"])
                if timestamp.utcoffset() != UTC.utcoffset(timestamp):
                    raise ValueError("Invalid stored timestamp")
                result.append(
                    PendingUser(
                        identity.id,
                        identity.username,
                        identity.status,
                        timestamp,
                    )
                )
            return tuple(result)

    def find(self, key: str, *, by_username: bool = False) -> tuple[UserIdentity, str] | None:
        column = "username" if by_username else "id"
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT id, username, status, password_hash, created_at FROM users "
                f"WHERE {column} = ?",
                (key,),
            ).fetchone()
            if row is None:
                return None
            parameters = extract_parameters(row["password_hash"])
            timestamp = datetime.fromisoformat(row["created_at"])
            if (
                parameters.type != Type.ID
                or parameters.memory_cost < 19456
                or parameters.time_cost < 2
                or parameters.parallelism < 1
                or parameters.salt_len < 16
                or timestamp.utcoffset() != UTC.utcoffset(timestamp)
            ):
                raise ValueError("Invalid stored credentials")
            return self._identity(row), row["password_hash"]

    def transition(self, user_id: str, source: UserStatus, target: UserStatus) -> UserIdentity:
        with self._transaction(write=True) as connection:
            row = connection.execute(
                "SELECT id, username, status FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if row is None:
                raise AuthServiceError(AuthFailureKind.NOT_FOUND)
            identity = self._identity(row)
            if identity.status == target:
                return identity
            if identity.status != source:
                raise AuthServiceError(AuthFailureKind.INVALID_TRANSITION)
            connection.execute("UPDATE users SET status = ? WHERE id = ?", (target, user_id))
            return UserIdentity(identity.id, identity.username, target)
