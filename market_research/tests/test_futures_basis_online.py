"""WP7 application acceptance with only synthetic public facts."""

import sqlite3
import threading
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

import lab_config
from futures_basis_observation_fixtures import REQUEST, Services
from market_research.descriptive.cases.futures_basis.online import (
    FuturesBasisOnlineApplication,
    OnlineError,
    OnlineServices,
    standard_report_request,
)
from market_research.descriptive.cases.futures_basis.report import compose_report
from market_statistics import CalculationFailure

# Terminal state is published before the worker's finally releases the process permit.
# Tests must join their own workers before another submit, storage mutation or teardown.
_workers: dict[tuple[int, str], threading.Thread] = {}


@pytest.fixture(autouse=True)
def join_execution_workers(monkeypatch):
    execute = FuturesBasisOnlineApplication._execute
    _workers.clear()

    def tracked_execute(self, run_id, request):
        _workers[id(self), run_id] = threading.current_thread()
        return execute(self, run_id, request)

    monkeypatch.setattr(FuturesBasisOnlineApplication, "_execute", tracked_execute)
    yield
    for worker in _workers.values():
        worker.join(timeout=2)
        assert not worker.is_alive(), "Synthetic execution leaked beyond its test"
    _workers.clear()


def application(root: Path, *, observe=None) -> FuturesBasisOnlineApplication:
    services = Services()
    kwargs = {"observe": observe} if observe is not None else {}
    return FuturesBasisOnlineApplication(
        root=root, services=OnlineServices(services, services, services), **kwargs
    )


def settled(app: FuturesBasisOnlineApplication, run_id: str) -> dict:
    for _ in range(100):
        state = app.get_run(run_id, "owner-a")
        if state["status"] in ("COMPLETED", "FAILED"):
            worker = _workers[id(app), run_id]
            worker.join(timeout=2)
            assert not worker.is_alive(), "Terminal publication preceded unfinished cleanup"
            return state
        time.sleep(0.02)
    pytest.fail("Synthetic run did not settle")


def error(kind: str, operation) -> None:
    with pytest.raises(OnlineError) as exc:
        operation()
    assert exc.value.kind == kind


def test_standard_profile_and_completed_reader_survive_restart(tmp_path):
    report_request = standard_report_request(REQUEST)
    assert report_request.quantile.points == (0, 0.25, 0.5, 0.75, 1)
    app = application(tmp_path)
    accepted = app.submit(REQUEST, "owner-a")
    run_id = accepted["run_id"]
    assert accepted["status"] == "PENDING" and len(run_id) == 32
    assert settled(app, run_id)["result_status"] == "complete"
    reader = app.get_report(run_id, "owner-a")
    assert reader["request"]["observation"]["product_code"] == "IM"
    assert reader["profile"] == "futures_basis_report_evidence_v1"
    app.observe = lambda *args, **kwargs: pytest.fail("Read recomputed observation")
    app.compose = lambda *args, **kwargs: pytest.fail("Read recomputed statistics")
    again = application(tmp_path)
    assert again.get_report(run_id, "owner-a") == reader
    error("run_not_found", lambda: again.get_run(run_id, "owner-b"))
    error("run_not_found", lambda: again.get_report(run_id, "owner-b"))
    error("run_not_found", lambda: again.get_run("../" + run_id, "owner-a"))


def test_worker_failure_is_classified_without_exception_text(tmp_path):
    def observe(*args, **kwargs):
        raise RuntimeError("provider token and /private/storage/path")

    app = application(tmp_path, observe=observe)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    state = settled(app, run_id)
    assert state["status"] == "FAILED"
    assert state["failure"] == {
        "stage": "execution",
        "category": "internal_failure",
        "dependency": None,
        "reason": "The execution could not finish.",
    }
    error("result_unavailable", lambda: app.get_report(run_id, "owner-a"))


def test_run_root_uses_repository_configuration_priority(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    from_file = tmp_path / "from-file"
    from_process = tmp_path / "from-process"
    env_file.write_text(f"LAB_FUTURES_BASIS_RUN_ROOT={from_file}\n", encoding="utf-8")
    monkeypatch.setattr(lab_config, "ENV_FILE", env_file)
    monkeypatch.delenv("LAB_FUTURES_BASIS_RUN_ROOT", raising=False)
    assert FuturesBasisOnlineApplication().root == from_file
    monkeypatch.setenv("LAB_FUTURES_BASIS_RUN_ROOT", str(from_process))
    assert FuturesBasisOnlineApplication().root == from_process


def test_partial_science_is_completed_and_original_failure_retained(tmp_path):
    def failing_method(source, request):
        with patch(
            "market_research.descriptive.cases.futures_basis.statistics.stats.compute",
            side_effect=CalculationFailure("mean", "synthetic method failure"),
        ):
            return compose_report(source, request)

    app = application(tmp_path)
    app.compose = failing_method
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    state = settled(app, run_id)
    assert state["status"] == "COMPLETED" and state["result_status"] == "partial"
    reader = app.get_report(run_id, "owner-a")
    assert reader["status"] == "partial"
    assert reader["distributions"][0]["methods"][0]["failure_category"] == "CalculationFailure"


def test_empty_samples_complete_and_report_size_bound(tmp_path, monkeypatch):
    services = Services()
    services.futures = replace(services.futures, records=())
    app = FuturesBasisOnlineApplication(
        root=tmp_path, services=OnlineServices(services, services, services)
    )
    finished = threading.Event()
    execute = app._execute

    def execute_and_signal(*args):
        try:
            execute(*args)
        finally:
            finished.set()

    monkeypatch.setattr(app, "_execute", execute_and_signal)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    assert settled(app, run_id)["result_status"] == "complete"
    assert app.get_report(run_id, "owner-a")["views"]["histograms"] == {}
    # Terminal publication precedes worker cleanup and release of the active permit.
    assert finished.wait(2)
    monkeypatch.setattr(
        "market_research.descriptive.cases.futures_basis.online.MAX_REPORT_BYTES", 100
    )
    oversized = app.submit(REQUEST, "owner-a")["run_id"]
    state = settled(app, oversized)
    assert state["status"] == "FAILED"
    assert state["failure"]["category"] == "result_too_large"
    error("result_unavailable", lambda: app.get_report(oversized, "owner-a"))


def test_simultaneous_submit_accepts_only_one(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    entered, release = threading.Event(), threading.Event()

    def observe(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        raise RuntimeError("synthetic")

    app = application(tmp_path, observe=observe)
    barrier = threading.Barrier(4)

    def submit():
        barrier.wait()
        try:
            return app.submit(REQUEST, "owner-a")
        except OnlineError as exc:
            return exc.kind

    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: submit(), range(4)))
        assert entered.wait(1)
        accepted = [result for result in results if isinstance(result, dict)]
        assert len(accepted) == 1 and results.count("run_busy") == 3
        assert len(list(tmp_path.iterdir())) == 1
    finally:
        release.set()
    settled(app, accepted[0]["run_id"])


def sql(app, statement, args=()):
    with sqlite3.connect(app.root / "runs.sqlite3") as c:
        return c.execute(statement, args).fetchall()


def test_recovery_excludes_active_and_terminal_admission(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def observe(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        raise RuntimeError("safe synthetic failure")

    app = application(tmp_path, observe=observe)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    try:
        assert entered.wait(2)
        again = application(tmp_path)
        assert again.get_run(run_id, "owner-a")["status"] == "RUNNING"
        error("run_busy", lambda: again.submit(REQUEST, "owner-a"))
        assert sql(app, "SELECT count(*) FROM runs") == [(1,)]
    finally:
        release.set()
    assert settled(app, run_id)["status"] == "FAILED"
    next_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, next_id)


def test_corruption_owner_and_bounded_reads(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online, online_sqlite_store

    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    assert online._READ_PERMIT.acquire(blocking=False)
    try:
        error("run_not_found", lambda: app.get_report(run_id, "foreign"))
        error("read_busy", lambda: app.get_report(run_id, "owner-a"))
        assert app.get_run(run_id, "owner-a")["result_available"]
    finally:
        online._READ_PERMIT.release()
    original = online_sqlite_store._decode

    def small_only(payload):
        assert len(payload) <= 8192
        return original(payload)

    with monkeypatch.context() as m:
        m.setattr(online_sqlite_store, "_decode", small_only)
        assert app.get_run(run_id, "owner-a")["result_available"]
    sql(app, "UPDATE results SET payload=zeroblob(?)", (32 * 1024 * 1024 + 1,))
    error("response_too_large", lambda: app.get_report(run_id, "owner-a"))
    error("corrupt", lambda: app.get_run(run_id, "owner-a"))
    error("run_not_found", lambda: app.get_run(run_id, "foreign"))


def test_foreign_identity_under_reader_contention(tmp_path, monkeypatch):
    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    entered, release = threading.Event(), threading.Event()
    original = app._store.read_report
    outcomes = []

    def blocked(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    monkeypatch.setattr(app._store, "read_report", blocked)
    reader = threading.Thread(target=lambda: outcomes.append(app.get_report(run_id, "owner-a")))
    reader.start()
    try:
        assert entered.wait(2)
        # Foreign identity is rejected before the permit is considered.
        error("run_not_found", lambda: app.get_report(run_id, "foreign"))
        error("run_not_found", lambda: app.get_report("0" * 32, "owner-a"))
        error("read_busy", lambda: app.get_report(run_id, "owner-a"))
        assert app.get_run(run_id, "owner-a")["status"] == "COMPLETED"
    finally:
        release.set()
        reader.join(5)
    assert len(outcomes) == 1


def test_application_has_no_private_store_sql():
    import inspect

    from market_research.descriptive.cases.futures_basis import online

    source = inspect.getsource(online)
    assert "_connection" not in source
    assert "SELECT " not in source


def test_completion_update_requires_single_row(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis.evidence import (
        json_bytes,
        scientific_payload,
    )
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )
    from market_research.descriptive.cases.futures_basis.service import observe_futures_basis

    services = Services()
    source = observe_futures_basis(
        REQUEST, calendar_service=services, futures_service=services, index_service=services
    )
    payload = json_bytes(
        scientific_payload(compose_report(source, standard_report_request(REQUEST)))[3]
    )
    store = FuturesBasisSQLiteRunStore(tmp_path)
    store.initialize()
    run_id = store.create(REQUEST, "owner-a")["run_id"]
    store.transition(run_id, "RUNNING")
    original = store._schema

    def ignore_completion(connection):
        original(connection)
        connection.execute(
            "CREATE TEMP TRIGGER IF NOT EXISTS skip_completion BEFORE UPDATE ON runs "
            "WHEN NEW.status='COMPLETED' BEGIN SELECT RAISE(IGNORE); END"
        )

    monkeypatch.setattr(store, "_schema", ignore_completion)
    error("corrupt", lambda: store.publish(run_id, payload, "complete"))
    assert store.status(run_id, "owner-a")["status"] == "RUNNING"
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT count(*) FROM results").fetchone() == (0,)


def test_recovery_treats_malformed_stored_identity_as_corrupt(tmp_path):
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )

    store = FuturesBasisSQLiteRunStore(tmp_path)
    store.initialize()
    with sqlite3.connect(store.path) as c:
        c.execute(
            "INSERT INTO runs VALUES (?,?,?,?,?,NULL,NULL,NULL)",
            ("BAD", "owner-a", b"{}", b"{}", "PENDING"),
        )
    error("corrupt", store.recover)


@pytest.mark.parametrize("version", [0, 2])
def test_existing_invalid_schema_is_not_initialized(tmp_path, version):
    with sqlite3.connect(tmp_path / "runs.sqlite3") as c:
        c.execute(f"PRAGMA user_version={version}")
    error("corrupt", lambda: application(tmp_path))


def test_atomic_commit_failure_and_failed_terminal_persistence(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online

    app = application(tmp_path)
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()

    def observe(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        raise RuntimeError("synthetic")

    app.observe = observe
    execute = app._execute

    def worker(*args):
        try:
            execute(*args)
        finally:
            finished.set()

    monkeypatch.setattr(app, "_execute", worker)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    assert entered.wait(2)

    def fail_commit(c):
        raise sqlite3.OperationalError("private storage details")

    monkeypatch.setattr(app._store, "_commit", fail_commit)
    release.set()
    assert finished.wait(5)
    error("unavailable", lambda: app.get_run(run_id, "owner-a"))
    error("unavailable", lambda: application(tmp_path))
    assert online._PROCESS_ACTIVE is None
    assert sql(app, "SELECT status FROM runs") == [("RUNNING",)]


def test_store_rollback_recovery_and_immutable_terminal(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )

    store = FuturesBasisSQLiteRunStore(tmp_path)
    store.initialize()
    run_id = store.create(REQUEST, "owner-a")["run_id"]
    store.transition(run_id, "RUNNING")
    store.recover()
    assert store.status(run_id, "owner-a")["status"] == "INTERRUPTED"
    error("corrupt", lambda: store.transition(run_id, "RUNNING"))
    assert store.read_report is not None


@pytest.mark.parametrize("after_commit", [False, True])
def test_real_process_exit_at_completion_commit(tmp_path, after_commit):
    import json
    import subprocess
    import sys

    from market_research.descriptive.cases.futures_basis.evidence import (
        json_bytes,
        scientific_payload,
    )
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )
    from market_research.descriptive.cases.futures_basis.service import observe_futures_basis

    services = Services()
    source = observe_futures_basis(
        REQUEST, calendar_service=services, futures_service=services, index_service=services
    )
    payload = json_bytes(
        scientific_payload(compose_report(source, standard_report_request(REQUEST)))[3]
    )
    payload_path = tmp_path / "fixture.json"
    payload_path.write_bytes(payload)
    store = FuturesBasisSQLiteRunStore(tmp_path)
    store.initialize()
    run_id = store.create(REQUEST, "owner-a")["run_id"]
    store.transition(run_id, "RUNNING")
    script = """
import sys, json, os
sys.path[:] = json.loads(sys.argv[1])
from pathlib import Path
from market_research.descriptive.cases.futures_basis import online_sqlite_store
FuturesBasisSQLiteRunStore = online_sqlite_store.FuturesBasisSQLiteRunStore
store = FuturesBasisSQLiteRunStore(Path(sys.argv[2]))
def commit(c):
    if sys.argv[4] == 'True': c.commit()
    os._exit(73)
store._commit = commit
store.publish(sys.argv[3], (store.root/'fixture.json').read_bytes(), 'complete')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            json.dumps(sys.path),
            str(tmp_path),
            run_id,
            str(after_commit),
        ],
        timeout=20,
    )
    assert result.returncode == 73
    store.recover()
    state = store.status(run_id, "owner-a")
    assert state["status"] == ("COMPLETED" if after_commit else "INTERRUPTED")
    if after_commit:
        assert store.read_report(run_id, "owner-a") == json.loads(payload)
    else:
        assert sql(type("App", (), {"root": tmp_path})(), "SELECT count(*) FROM results") == [(0,)]


def test_publish_commit_rollback_and_scientific_parity(tmp_path, monkeypatch):
    import json

    from market_research.descriptive.cases.futures_basis.evidence import (
        json_bytes,
        scientific_payload,
    )
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )
    from market_research.descriptive.cases.futures_basis.service import observe_futures_basis

    services = Services()
    source = observe_futures_basis(
        REQUEST, calendar_service=services, futures_service=services, index_service=services
    )
    expected = scientific_payload(compose_report(source, standard_report_request(REQUEST)))[3]
    payload = json_bytes(expected)
    store = FuturesBasisSQLiteRunStore(tmp_path)
    store.initialize()
    run_id = store.create(REQUEST, "owner-a")["run_id"]
    store.transition(run_id, "RUNNING")

    def failed_commit(c):
        raise sqlite3.OperationalError("synthetic")

    with monkeypatch.context() as m:
        m.setattr(store, "_commit", failed_commit)
        error("unavailable", lambda: store.publish(run_id, payload, "complete"))
    assert store.status(run_id, "owner-a")["status"] == "RUNNING"
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT count(*) FROM results").fetchone() == (0,)
    store.publish(run_id, payload, "complete")
    assert store.read_report(run_id, "owner-a") == json.loads(payload)
    error("corrupt", lambda: store.publish(run_id, payload, "complete"))
    app = application(tmp_path)
    online_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, online_id)
    assert app.get_report(online_id, "owner-a") == json.loads(payload)


def test_collision_and_legacy_files_ignored(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online_sqlite_store

    legacy = tmp_path / ("a" * 32)
    legacy.mkdir()
    (legacy / "state.json").write_bytes(b"unreadable legacy state")
    app = application(tmp_path)
    error("run_not_found", lambda: app.get_run("a" * 32, "owner-a"))
    store = app._store
    monkeypatch.setattr(online_sqlite_store.secrets, "token_hex", lambda _: "b" * 32)
    store.create(REQUEST, "owner-a")
    error("unavailable", lambda: store.create(REQUEST, "owner-a"))
    assert (legacy / "state.json").read_bytes() == b"unreadable legacy state"


@pytest.mark.parametrize("sidecar", ["-journal", "-wal", "-shm"])
def test_unsafe_sidecar_and_root_rejected(tmp_path, sidecar):
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )

    error("unavailable", lambda: application(Path("relative")))
    (tmp_path / ("runs.sqlite3" + sidecar)).mkdir()
    error("corrupt", lambda: FuturesBasisSQLiteRunStore(tmp_path).initialize())


@pytest.mark.parametrize("kind", ["missing", "wrong", "corrupt"])
def test_malformed_database_rejected_without_repair(tmp_path, kind):
    path = tmp_path / "runs.sqlite3"
    if kind == "corrupt":
        path.write_bytes(b"invalid database")
    else:
        with sqlite3.connect(path) as c:
            c.execute("PRAGMA user_version=1")
            if kind == "wrong":
                c.execute("CREATE TABLE runs (unexpected TEXT)")
    before = path.read_bytes()
    error("corrupt", lambda: application(tmp_path))
    assert path.read_bytes() == before


def test_invalid_request_no_run_and_read_does_not_initialize(tmp_path):
    from market_research.descriptive.cases.futures_basis import FuturesBasisRequest
    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )

    root = tmp_path / "absent"
    store = FuturesBasisSQLiteRunStore(root)
    error("run_not_found", lambda: store.status("a" * 32, "owner-a"))
    assert not root.exists()
    app = application(tmp_path)
    invalid = FuturesBasisRequest("XX", REQUEST.start_date, REQUEST.end_date)
    error("invalid_request", lambda: app.submit(invalid, "owner-a"))
    assert sql(app, "SELECT count(*) FROM runs") == [(0,)]


def test_symlink_and_hardlink_database_rejected(tmp_path):
    import os

    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )

    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "alias"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable to this OS account")
    error("unavailable", lambda: application(link))
    store = FuturesBasisSQLiteRunStore(target)
    store.initialize()
    os.link(store.path, tmp_path / "hardlink")
    error("corrupt", store.initialize)


def test_concurrent_construction_submission_preserves_active_run(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    entered, release = threading.Event(), threading.Event()

    def observe(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        raise RuntimeError("synthetic")

    app = application(tmp_path, observe=observe)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    try:
        assert entered.wait(2)
        barrier = threading.Barrier(4)

        def construct(_):
            barrier.wait()
            other = application(tmp_path)
            error("run_busy", lambda: other.submit(REQUEST, "owner-a"))
            return other.get_run(run_id, "owner-a")["status"]

        with ThreadPoolExecutor(max_workers=4) as pool:
            assert list(pool.map(construct, range(4))) == ["RUNNING"] * 4
        assert sql(app, "SELECT count(*) FROM runs") == [(1,)]
    finally:
        release.set()
    settled(app, run_id)


def test_database_hardlink_alias_rejected(tmp_path):
    import os

    from market_research.descriptive.cases.futures_basis.online_sqlite_store import (
        FuturesBasisSQLiteRunStore,
    )

    store = FuturesBasisSQLiteRunStore(tmp_path)
    store.initialize()
    os.link(store.path, tmp_path / "alias")
    error("corrupt", store.initialize)
