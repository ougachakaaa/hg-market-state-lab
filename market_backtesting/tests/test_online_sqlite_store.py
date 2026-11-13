"""Independent SQLite persistence, transaction, process-crash and integrity checks."""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long.online_codec import (
    RESULT_LIMIT,
    encode_result,
    json_bytes,
)
from market_backtesting.cases.futures_roll_long.online_models import (
    FuturesRollOnlineError,
    OnlineFailure,
)
from market_backtesting.cases.futures_roll_long.online_sqlite_store import FuturesRollSQLiteRunStore
from market_backtesting.cases.futures_roll_long.result import build_backtest_result
from public_input_fixtures import fake_services, request


@pytest.fixture
def store(tmp_path: Path) -> FuturesRollSQLiteRunStore:
    return FuturesRollSQLiteRunStore(tmp_path / "runs")


@pytest.fixture
def payload() -> bytes:
    return encode_result(build_backtest_result(fake_services()[0].run(request())), request())


def error(category: str, operation: Any) -> None:
    with pytest.raises(FuturesRollOnlineError) as exc:
        operation()
    assert str(exc.value) == category


def sql(store: FuturesRollSQLiteRunStore, statement: str, args: tuple[Any, ...] = ()) -> None:
    with sqlite3.connect(store.path) as connection:
        connection.execute(statement, args)


def completed(store: FuturesRollSQLiteRunStore, payload: bytes) -> str:
    run_id = store.create(request(), "alice").run_id
    store.transition(run_id, "RUNNING")
    store.publish(run_id, payload)
    return run_id


def test_no_implicit_initialization_and_persistence(
    store: FuturesRollSQLiteRunStore, payload: bytes
) -> None:
    error("run_not_found", lambda: store.status("0" * 32, "alice"))
    assert not store.root.exists()
    store.initialize()
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
    run_id = completed(store, payload)
    reopened = FuturesRollSQLiteRunStore(store.root)
    assert reopened.status(run_id, "alice").status == "COMPLETED"
    assert reopened.read_result(run_id, "alice") == payload
    reopened.recover()
    assert reopened.read_result(run_id, "alice") == payload


@pytest.mark.parametrize(
    "kind", ["empty", "version0", "unknown", "missing", "incompatible", "corrupt"]
)
def test_bad_databases(store: FuturesRollSQLiteRunStore, kind: str) -> None:
    store.root.mkdir()
    if kind == "empty":
        store.path.touch()
    elif kind == "corrupt":
        store.path.write_bytes(b"not a SQLite database")
    else:
        sql(
            store,
            "PRAGMA user_version="
            + ("0" if kind == "version0" else "2" if kind == "unknown" else "1"),
        )
        if kind == "incompatible":
            sql(store, "CREATE TABLE runs (run_id TEXT)")
    before = store.path.read_bytes()
    error("corrupt", store.initialize)
    assert store.path.read_bytes() == before


def test_owner_first_malformed_and_collision(
    store: FuturesRollSQLiteRunStore, monkeypatch: Any
) -> None:
    accepted = store.create(request(), "alice")
    monkeypatch.setattr(
        "market_backtesting.cases.futures_roll_long.online_sqlite_store.secrets.token_hex",
        lambda _: accepted.run_id,
    )
    error("unavailable", lambda: store.create(request(), "bob"))
    sql(store, "UPDATE runs SET state=?", (b"broken",))
    error("run_not_found", lambda: store.status(accepted.run_id, "bob"))
    error("run_not_found", lambda: store.read_result(accepted.run_id, "bob"))
    error("corrupt", lambda: store.status(accepted.run_id, "alice"))
    for run_id in ("../escape", "A" * 32, "", "1" * 32):
        error("run_not_found", lambda run_id=run_id: store.status(run_id, "alice"))


@pytest.mark.parametrize("source", ["PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"])
@pytest.mark.parametrize("target", ["PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"])
def test_transition_matrix(
    store: FuturesRollSQLiteRunStore, payload: bytes, source: str, target: str
) -> None:
    run_id = store.create(request(), "alice").run_id
    failures = {
        "FAILED": OnlineFailure("execution", "internal_failure", None, "internal_failure"),
        "INTERRUPTED": OnlineFailure("execution", "interrupted", None, "interrupted"),
    }
    if source in {"RUNNING", "COMPLETED"}:
        store.transition(run_id, "RUNNING")
    if source == "COMPLETED":
        store.publish(run_id, payload)
    elif source in failures:
        store.transition(run_id, source, failure=failures[source])  # type: ignore[arg-type]
    legal = source in {"PENDING", "RUNNING"} and target in (
        {"RUNNING", "FAILED", "INTERRUPTED"} if source == "PENDING" else {"FAILED", "INTERRUPTED"}
    )

    def operation() -> None:
        store.transition(run_id, target, failure=failures.get(target))  # type: ignore[arg-type]

    if legal:
        operation()
        assert store.status(run_id, "alice").status == target
    else:
        error("corrupt", operation)
        assert store.status(run_id, "alice").status == source


def test_atomic_publish_and_commit_failure(
    store: FuturesRollSQLiteRunStore, payload: bytes, monkeypatch: Any
) -> None:
    run_id = store.create(request(), "alice").run_id
    error("corrupt", lambda: store.publish(run_id, payload))
    store.transition(run_id, "RUNNING")
    observer = FuturesRollSQLiteRunStore(store.root)

    def fail(connection: sqlite3.Connection) -> None:
        assert observer.status(run_id, "alice").status == "RUNNING"
        error("result_not_ready", lambda: observer.read_result(run_id, "alice"))
        raise sqlite3.OperationalError("private database path")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_commit", fail)
        error("unavailable", lambda: store.publish(run_id, payload))
    assert observer.status(run_id, "alice").status == "RUNNING"
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT count(*) FROM results").fetchone() == (0,)
    store.publish(run_id, payload)
    assert observer.read_result(run_id, "alice") == payload
    error("corrupt", lambda: store.publish(run_id, payload))


def test_recovery_atomic_active_exclusion(store: FuturesRollSQLiteRunStore, payload: bytes) -> None:
    done = completed(store, payload)
    pending = store.create(request(), "alice").run_id
    active = store.create(request(), "alice").run_id
    store.transition(active, "RUNNING")
    store.recover((str(store.root), active))
    assert store.status(pending, "alice").status == "INTERRUPTED"
    assert store.status(active, "alice").status == "RUNNING"
    store.recover()
    assert store.status(active, "alice").status == "INTERRUPTED"
    assert store.read_result(done, "alice") == payload
    bad = store.create(request(), "alice").run_id
    untouched = store.create(request(), "alice").run_id
    sql(store, "UPDATE runs SET state=? WHERE run_id=?", (b"{}", bad))
    error("corrupt", store.recover)
    assert store.status(untouched, "alice").status == "PENDING"


@pytest.mark.parametrize("after", [False, True])
def test_real_process_termination(
    store: FuturesRollSQLiteRunStore, payload: bytes, tmp_path: Path, after: bool
) -> None:
    run_id = store.create(request(), "alice").run_id
    store.transition(run_id, "RUNNING")
    payload_file = tmp_path / "payload.json"
    payload_file.write_bytes(payload)
    marker = tmp_path / "ready"
    script = """
import sys,time
from pathlib import Path
from market_backtesting.cases.futures_roll_long.online_sqlite_store import FuturesRollSQLiteRunStore
s=FuturesRollSQLiteRunStore(Path(sys.argv[1]))
def pause(c):
    if sys.argv[5] == 'True': c.commit()
    Path(sys.argv[4]).write_text('ready')
    while True: time.sleep(.01)
s._commit=pause
s.publish(sys.argv[2],Path(sys.argv[3]).read_bytes())
"""
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(store.root),
            run_id,
            str(payload_file),
            str(marker),
            str(after),
        ]
    )
    try:
        import time

        deadline = time.monotonic() + 15
        while not marker.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert marker.exists(), f"child failed: {process.poll()}"
    finally:
        process.kill()
        process.wait(timeout=10)
    reopened = FuturesRollSQLiteRunStore(store.root)
    reopened.recover()
    assert reopened.status(run_id, "alice").status == ("COMPLETED" if after else "INTERRUPTED")
    if after:
        assert reopened.read_result(run_id, "alice") == payload
    else:
        error("result_not_ready", lambda: reopened.read_result(run_id, "alice"))


@pytest.mark.parametrize(
    "kind",
    ["missing", "oversize", "length", "digest", "json", "canonical", "request", "profile", "text"],
)
def test_result_corruption(store: FuturesRollSQLiteRunStore, payload: bytes, kind: str) -> None:
    run_id = completed(store, payload)
    if kind == "missing":
        sql(store, "DELETE FROM results")
    elif kind == "oversize":
        sql(store, "UPDATE results SET payload=zeroblob(?)", (RESULT_LIMIT + 1,))
    elif kind == "length":
        sql(store, "UPDATE runs SET result_length=result_length+1")
    elif kind == "text":
        sql(store, "UPDATE results SET payload='text'")
    else:
        replacement = payload
        if kind == "digest":
            replacement = payload[:-1] + b" "
        elif kind == "json":
            replacement = b'{"a":1,"a":2}'
        elif kind == "canonical":
            replacement = b" " + payload
        elif kind in {"request", "profile"}:
            raw = json.loads(payload)
            if kind == "profile":
                raw["profile"] = "wrong"
            else:
                raw["request"]["product_code"] = "IF"
            replacement = json_bytes(raw, RESULT_LIMIT)
        sql(store, "UPDATE results SET payload=?", (replacement,))
        sql(store, "UPDATE runs SET result_length=?", (len(replacement),))
        if kind != "digest":
            with sqlite3.connect(store.path) as connection:
                state = json.loads(connection.execute("SELECT state FROM runs").fetchone()[0])
            state["result_digest"] = hashlib.sha256(replacement).hexdigest()
            sql(store, "UPDATE runs SET state=?", (json_bytes(state),))
    if kind in {"missing", "oversize", "length", "text"}:
        error("corrupt", lambda: store.status(run_id, "alice"))
    else:
        assert store.status(run_id, "alice").status == "COMPLETED"
    error("corrupt", lambda: store.read_result(run_id, "alice"))


def test_status_never_selects_blob(
    store: FuturesRollSQLiteRunStore, payload: bytes, monkeypatch: Any
) -> None:
    run_id = completed(store, payload)
    original = sqlite3.connect
    statements: list[str] = []

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        connection = original(*args, **kwargs)
        connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    assert store.status(run_id, "alice").status == "COMPLETED"
    assert any("length(payload)" in statement for statement in statements)
    assert not any(
        "SELECT payload" in statement or "SELECT *" in statement for statement in statements
    )


def test_lock_contention(store: FuturesRollSQLiteRunStore) -> None:
    store.initialize()
    with sqlite3.connect(store.path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        error("unavailable", lambda: store.create(request(), "alice"))
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)


@pytest.mark.parametrize("suffix", ["", "-journal", "-wal", "-shm"])
def test_hard_link_and_sidecar_rejection(
    store: FuturesRollSQLiteRunStore, tmp_path: Path, suffix: str
) -> None:
    store.initialize()
    destination = Path(str(store.path) + suffix)
    target = tmp_path / "external"
    if suffix:
        target.write_bytes(b"external")
        os.link(target, destination)
    else:
        os.link(destination, target)
    error("corrupt", store.initialize)


@pytest.mark.parametrize("kind", ["root", "ancestor", "db", "sidecar"])
def test_symlink_rejection(store: FuturesRollSQLiteRunStore, tmp_path: Path, kind: str) -> None:
    store.initialize()
    path = (
        store.root
        if kind == "root"
        else tmp_path
        if kind == "ancestor"
        else store.path
        if kind == "db"
        else Path(str(store.path) + "-journal")
    )
    target = path.with_name(path.name + "-target")
    if path.exists():
        path.rename(target)
    else:
        target.write_bytes(b"external")
    try:
        path.symlink_to(target, target_is_directory=target.is_dir())
    except OSError:
        if target.is_dir() and os.name == "nt":
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(path), str(target)],
                check=True,
                capture_output=True,
            )
        else:
            pytest.skip("symlink privilege unavailable")
    error("unavailable" if kind in {"root", "ancestor"} else "corrupt", store.initialize)


def test_root_validation(tmp_path: Path) -> None:
    for root in (Path("relative"), tmp_path / ".." / "escape"):
        error("unavailable", lambda root=root: FuturesRollSQLiteRunStore(root))


def test_publication_bound_and_invalid_failure(store: FuturesRollSQLiteRunStore) -> None:
    run_id = store.create(request(), "alice").run_id
    store.transition(run_id, "RUNNING")
    error("result_too_large", lambda: store.publish(run_id, b" " * (RESULT_LIMIT + 1)))
    error("corrupt", lambda: store.publish(run_id, b"{}"))
    error(
        "corrupt",
        lambda: store.transition(
            run_id, "FAILED", failure=OnlineFailure("execution", "internal_failure", None, "secret")
        ),
    )
    assert store.status(run_id, "alice").status == "RUNNING"


def test_statement_failure_rolls_back_creation(store: FuturesRollSQLiteRunStore) -> None:
    store.initialize()
    # A test-only trigger injected after schema verification causes the INSERT to fail.
    original = store._schema

    def fail_insert(connection: sqlite3.Connection) -> None:
        original(connection)
        connection.execute(
            "CREATE TEMP TRIGGER reject_insert BEFORE INSERT ON runs "
            "BEGIN SELECT RAISE(ABORT,'private'); END"
        )

    store._schema = fail_insert  # type: ignore[method-assign]
    error("unavailable", lambda: store.create(request(), "alice"))
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)


def test_rollback_failure_is_safe(store: FuturesRollSQLiteRunStore, monkeypatch: Any) -> None:
    store.initialize()
    original = sqlite3.connect

    class BrokenRollback(sqlite3.Connection):
        def rollback(self) -> None:
            raise sqlite3.OperationalError("private rollback path")

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        return original(*args, **kwargs, factory=BrokenRollback)

    monkeypatch.setattr(sqlite3, "connect", connect)

    def fail(connection: sqlite3.Connection) -> None:
        raise sqlite3.OperationalError("private commit path")

    monkeypatch.setattr(store, "_commit", fail)
    error("unavailable", lambda: store.create(request(), "alice"))
    with original(store.path) as connection:
        assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)


def test_initialization_failure_not_repaired(
    store: FuturesRollSQLiteRunStore, monkeypatch: Any
) -> None:
    def fail(connection: sqlite3.Connection) -> None:
        raise sqlite3.OperationalError("private")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_commit", fail)
        error("unavailable", store.initialize)
    error("corrupt", store.initialize)
    with sqlite3.connect(store.path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)


@pytest.mark.parametrize("owner", ["", None, 1])
def test_invalid_owner(store: FuturesRollSQLiteRunStore, owner: Any) -> None:
    run_id = store.create(request(), "alice").run_id
    error("invalid_request", lambda: store.status(run_id, owner))
    error("invalid_request", lambda: store.read_result(run_id, owner))


def test_legacy_ignored_and_database_replacement(store: FuturesRollSQLiteRunStore) -> None:
    legacy = store.root / ("1" * 32)
    legacy.mkdir(parents=True)
    (legacy / "request.json").write_bytes(b"legacy")
    store.recover()
    error("run_not_found", lambda: store.status(legacy.name, "alice"))
    assert (legacy / "request.json").read_bytes() == b"legacy"
    store.path.rename(store.path.with_suffix(".old"))
    store.path.touch()
    error("corrupt", store.initialize)


def test_snapshot_length_check_precedes_blob_load(
    store: FuturesRollSQLiteRunStore, payload: bytes, monkeypatch: Any
) -> None:
    run_id = completed(store, payload)
    sql(store, "UPDATE results SET payload=zeroblob(?)", (RESULT_LIMIT + 1,))
    original = sqlite3.connect
    reads: list[str] = []

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        connection = original(*args, **kwargs)
        connection.set_trace_callback(reads.append)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    error("corrupt", lambda: store.read_result(run_id, "alice"))
    assert not any("SELECT payload" in statement for statement in reads)


@pytest.mark.parametrize("column", ["metadata", "state"])
@pytest.mark.parametrize("value", [b"", "text", b"x" * (16 * 1024 + 1)])
def test_metadata_bounds_before_selection(store, monkeypatch, column, value):
    run_id = store.create(request(), "alice").run_id
    sql(store, f"UPDATE runs SET {column}=?", (value,))
    original = sqlite3.connect
    statements = []

    def connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        connection.set_trace_callback(statements.append)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)
    error("run_not_found", lambda: store.status(run_id, "bob"))
    error("corrupt", lambda: store.status(run_id, "alice"))
    error("corrupt", store.recover)
    assert any("length(metadata)" in statement for statement in statements)
    assert not any("SELECT metadata,state" in statement for statement in statements)
