"""Independent immutable Publication SQLite storage; no execution lifecycle."""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from ._paths import directories, regular, same
from .errors import (
    PublicationCollision,
    PublicationCorrupt,
    PublicationUnavailable,
    UnsupportedPublicationVersion,
    VerificationBudgetExceeded,
)

_SCHEMA = (
    (
        "CREATE TABLE publications (publication_id TEXT PRIMARY KEY, "
        "manifest BLOB NOT NULL, sha256 TEXT NOT NULL, "
        "size INTEGER NOT NULL, integrity BLOB NOT NULL)"
    ),
    (
        "CREATE TABLE records (publication_id TEXT NOT NULL REFERENCES "
        "publications(publication_id), kind TEXT NOT NULL, identity TEXT NOT NULL, "
        "payload BLOB NOT NULL, PRIMARY KEY(publication_id, kind, identity))"
    ),
)
# Serialize first initialization as well as visibility within this supported backend process.
_LOCK = threading.RLock()


class SQLiteStorage:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "publications.sqlite3"
        self._active: ContextVar[sqlite3.Connection | None] = ContextVar(
            "publication_connection", default=None
        )
        self._root_identity: tuple[int, int] | None = None
        self._file_identity: tuple[int, int] | None = None

    def _paths(self, create: bool = False) -> bool:
        if not directories(self.root, create=create):
            return False
        root_info = self.root.lstat()
        root_identity = (root_info.st_dev, root_info.st_ino)
        if self._root_identity is not None and self._root_identity != root_identity:
            raise PublicationCorrupt("publication root changed")
        self._root_identity = root_identity
        for suffix in ("-journal", "-wal", "-shm"):
            try:
                regular(Path(str(self.path) + suffix))
            except FileNotFoundError:
                pass
        try:
            info = regular(self.path)
            identity = (info.st_dev, info.st_ino)
            if self._file_identity is not None and self._file_identity != identity:
                raise PublicationCorrupt("publication database changed")
            self._file_identity = identity
        except FileNotFoundError:
            if self._file_identity is not None:
                raise PublicationCorrupt("publication database disappeared") from None
            return False
        return True

    @contextmanager
    def connection(self, *, write: bool = False) -> Iterator[sqlite3.Connection | None]:
        active = self._active.get()
        if active is not None and not write:
            yield active
            return
        with _LOCK:
            connection = None
            token = None
            try:
                exists = self._paths(create=write)
                if not exists and not write:
                    yield None
                    return
                new = False
                if not exists:
                    try:
                        with self.path.open("xb"):
                            pass
                        new = True
                    except FileExistsError:
                        pass
                before = regular(self.path)
                connection = sqlite3.connect(
                    self.path.as_uri() + "?mode=rw", uri=True, timeout=1.0, isolation_level=None
                )
                same(before, regular(self.path))
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("PRAGMA synchronous=FULL")
                connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                if new:
                    for sql in _SCHEMA:
                        connection.execute(sql)
                    connection.execute("PRAGMA user_version=1")
                    connection.commit()
                    connection.execute("BEGIN IMMEDIATE")
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                if version != 1:
                    if version == 0:
                        raise PublicationCorrupt("uninitialized existing database")
                    raise UnsupportedPublicationVersion("unsupported database version")
                actual = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name"
                ).fetchall()
                if actual != [(sql,) for sql in _SCHEMA]:
                    raise PublicationCorrupt("incompatible publication schema")
                if connection.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
                    raise PublicationCorrupt("unsupported publication journal mode")
                token = self._active.set(connection)
                yield connection
                self._paths()
                same(before, regular(self.path))
                if write:
                    self._commit(connection)
            except sqlite3.IntegrityError as exc:
                raise PublicationCollision("publication identity already exists") from exc
            except sqlite3.Error as exc:
                code = getattr(exc, "sqlite_errorcode", 0) & 255
                if code in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB, sqlite3.SQLITE_SCHEMA):
                    raise PublicationCorrupt("invalid publication database") from exc
                raise PublicationUnavailable("publication database unavailable") from exc
            except OSError as exc:
                raise PublicationUnavailable("publication storage unavailable") from exc
            finally:
                if token is not None:
                    self._active.reset(token)
                if connection is not None:
                    try:
                        connection.rollback()
                        connection.close()
                    except sqlite3.Error as exc:
                        raise PublicationUnavailable("cannot close publication database") from exc

    def _commit(self, connection: sqlite3.Connection) -> None:
        connection.commit()

    @staticmethod
    def blob(
        connection: sqlite3.Connection,
        pid: str,
        kind: str,
        identity: str,
        limit: int | None = None,
        expected_size: int | None = None,
    ) -> bytes:
        row = connection.execute(
            (
                "SELECT typeof(payload), length(payload) FROM records WHERE "
                "publication_id=? AND kind=? AND identity=?"
            ),
            (pid, kind, identity),
        ).fetchone()
        if row is None or row[0] != "blob":
            raise PublicationCorrupt("missing or malformed publication record")
        if limit is not None and row[1] > limit:
            raise VerificationBudgetExceeded("source verification capacity exceeded")
        if expected_size is not None and row[1] != expected_size:
            raise PublicationCorrupt("record size mismatch")
        return connection.execute(
            "SELECT payload FROM records WHERE publication_id=? AND kind=? AND identity=?",
            (pid, kind, identity),
        ).fetchone()[0]
