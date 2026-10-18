"""Private path / transaction primitives, with no Observation business schema."""

import sqlite3
from contextlib import closing
from pathlib import Path


def owned_path(context: str, filename: str) -> Path:
    root = Path(__file__).resolve().parents[5]
    return root / context / "output" / filename


def read_payload(path: Path, query: str, key: tuple[object, ...]) -> str | None:
    if not path.exists():
        return None
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        if db.execute("PRAGMA user_version").fetchone()[0] != 1:
            raise ValueError("Unsupported Observation SQLite schema")
        row = db.execute(query, key).fetchone()
        return None if row is None else row[0]


def publish_payload(
    path: Path,
    ddl: str,
    insert: str,
    query: str,
    key: tuple[object, ...],
    payload: str,
) -> str:
    """Commit one value, or return the concurrently published winner."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=30)) as db, db:
        db.execute("PRAGMA synchronous=FULL")
        db.execute("BEGIN IMMEDIATE")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            if db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                raise ValueError("Incompatible Observation SQLite schema")
            db.execute(ddl)
            db.execute("PRAGMA user_version=1")
        elif version != 1:
            raise ValueError("Unsupported Observation SQLite schema")
        # No overwrite: concurrent misses may compute twice, but publish one logical value.
        db.execute(insert, (*key, payload))
        row = db.execute(query, key).fetchone()
        if row is None:
            raise ValueError("Atomic publication produced no value")
        result: str = row[0]
    return result
