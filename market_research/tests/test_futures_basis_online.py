"""WP7 application acceptance with only synthetic public facts."""

import json
import threading
import time
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

import lab_config
from futures_basis_observation_fixtures import REQUEST, Services
from market_research.descriptive.cases.futures_basis import FuturesBasisRequest
from market_research.descriptive.cases.futures_basis.inputs import InputPreparationError
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


@pytest.mark.parametrize(
    "invalid_case_request",
    [
        FuturesBasisRequest("XX", REQUEST.start_date, REQUEST.end_date),
        FuturesBasisRequest("IM", REQUEST.end_date, REQUEST.start_date),
        FuturesBasisRequest("IM", date(2020, 1, 1), date(2023, 1, 1)),
        FuturesBasisRequest("IM", REQUEST.start_date, date(2099, 1, 1)),
    ],
)
def test_invalid_requests_have_no_run_side_effect(tmp_path, invalid_case_request):
    app = application(tmp_path)
    error("invalid_request", lambda: app.submit(invalid_case_request, "owner-a"))
    assert list(tmp_path.iterdir()) == []


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


def test_busy_and_restart_interruption(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def observe(*args, **kwargs):
        entered.set()
        release.wait(2)
        raise RuntimeError("private path /tmp/secret")

    app = application(tmp_path, observe=observe)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    assert entered.wait(1)
    error("result_not_ready", lambda: app.get_report(run_id, "owner-a"))
    error("run_busy", lambda: app.submit(REQUEST, "owner-a"))
    assert len(list(tmp_path.iterdir())) == 1
    # A restarted process conservatively interrupts an abandoned running state.
    recovered = application(tmp_path)
    state = recovered.get_run(run_id, "owner-a")
    assert state["status"] == "INTERRUPTED"
    error("result_unavailable", lambda: recovered.get_report(run_id, "owner-a"))
    release.set()


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


def test_corrupt_digest_missing_report_and_symlink_fail_closed(tmp_path):
    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    run_dir = tmp_path / run_id
    report = run_dir / "report.json"
    report.write_bytes(report.read_bytes() + b" ")
    error("corrupt", lambda: app.get_report(run_id, "owner-a"))
    report.unlink()
    error("corrupt", lambda: app.get_report(run_id, "owner-a"))
    report.symlink_to(run_dir / "request.json")
    error("corrupt", lambda: app.get_report(run_id, "owner-a"))


def test_corrupt_state_and_foreign_request_do_not_leak(tmp_path):
    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    run_dir = tmp_path / run_id
    state = json.loads((run_dir / "state.json").read_text())
    state["status"] = "RUNNING"
    (run_dir / "state.json").write_text(json.dumps(state))
    error("run_not_found", lambda: app.get_run(run_id, "owner-b"))
    error("corrupt", lambda: app.get_run(run_id, "owner-a"))


def test_public_input_failure_and_pending_worker_failure(tmp_path):
    def observe(*args, **kwargs):
        raise InputPreparationError("upstream_operation", "futures", "/private/token")

    app = application(tmp_path, observe=observe)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    state = settled(app, run_id)
    assert state["failure"]["stage"] == "input_preparation"
    assert state["failure"]["dependency"] == "futures"
    assert "/private" not in json.dumps(state)

    with patch("threading.Thread.start", side_effect=RuntimeError("cannot start")):
        pending_id = app.submit(REQUEST, "owner-a")["run_id"]
    state = app.get_run(pending_id, "owner-a")
    assert state["status"] == "FAILED" and state["started_at"] is None


def test_invalid_storage_root_and_symlink_are_unavailable(tmp_path):
    error("unavailable", lambda: application(Path("relative/run/root")))
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(target, target_is_directory=True)
    error("unavailable", lambda: application(link))


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


def test_status_is_lightweight_even_with_reader_occupied(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online

    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    original_decode = online._decode

    def metadata_only(payload):
        assert len(payload) <= 8192, "Status parsed the report"
        return original_decode(payload)

    monkeypatch.setattr(online, "_decode", metadata_only)
    app._report = lambda *args: pytest.fail("Status called full reader")
    app.observe = app.compose = lambda *args: pytest.fail("Status executed Research")
    assert online._READ_PERMIT.acquire(blocking=False)
    try:
        for _ in range(3):
            assert app.get_run(run_id, "owner-a")["result_available"]
        error("read_busy", lambda: app.get_report(run_id, "owner-a"))
    finally:
        online._READ_PERMIT.release()


def test_stored_size_and_unknown_versions(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online

    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    report = tmp_path / run_id / "report.json"
    monkeypatch.setattr(online, "MAX_REPORT_BYTES", report.stat().st_size - 1)
    error("response_too_large", lambda: app.get_report(run_id, "owner-a"))
    error("corrupt", lambda: app.get_run(run_id, "owner-a"))
    monkeypatch.undo()
    state_path = tmp_path / run_id / "state.json"
    state = json.loads(state_path.read_text())
    state["version"] = 2
    state_path.write_text(json.dumps(state))
    error("unsupported_version", lambda: app.get_run(run_id, "owner-a"))


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


def test_atomic_publication_and_write_failure(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online

    app = application(tmp_path)
    original_write = online._write
    published, release = threading.Event(), threading.Event()

    def paused_write(fd, name, payload):
        original_write(fd, name, payload)
        if name == "report.json":
            published.set()
            assert release.wait(5)
            raise OnlineError("unavailable")

    monkeypatch.setattr(online, "_write", paused_write)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    try:
        assert published.wait(3)
        assert app.get_run(run_id, "owner-a")["result_available"] is False
        error("result_not_ready", lambda: app.get_report(run_id, "owner-a"))
    finally:
        release.set()
    assert settled(app, run_id)["status"] == "FAILED"
    assert not (tmp_path / run_id / "report.json").exists()


@pytest.mark.parametrize("status", ["PENDING", "RUNNING"])
def test_recover_abandoned_states_and_orphan_report(tmp_path, status):
    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    path = tmp_path / run_id / "state.json"
    state = json.loads(path.read_text())
    state.update(status=status, finished_at=None, result_status=None, result_digest=None)
    if status == "PENDING":
        state["started_at"] = None
    path.write_text(json.dumps(state))
    recovered = application(tmp_path)
    assert recovered.get_run(run_id, "owner-a")["status"] == "INTERRUPTED"
    error("result_unavailable", lambda: recovered.get_report(run_id, "owner-a"))


def test_nonregular_result_and_status_missing_result(tmp_path):
    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    path = tmp_path / run_id / "report.json"
    path.unlink()
    error("corrupt", lambda: app.get_run(run_id, "owner-a"))
    path.mkdir()
    error("corrupt", lambda: app.get_run(run_id, "owner-a"))
    error("corrupt", lambda: app.get_report(run_id, "owner-a"))


def test_concurrent_report_reader_and_payload_associations(tmp_path, monkeypatch):
    import hashlib
    from concurrent.futures import ThreadPoolExecutor

    app = application(tmp_path)
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    settled(app, run_id)
    entered, release = threading.Event(), threading.Event()
    original = app._report

    def blocked(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    monkeypatch.setattr(app, "_report", blocked)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(app.get_report, run_id, "owner-a")
        try:
            assert entered.wait(1)
            error("read_busy", lambda: app.get_report(run_id, "owner-a"))
            assert app.get_run(run_id, "owner-a")["result_available"]
        finally:
            release.set()
        assert future.result()["status"] == "complete"
    monkeypatch.undo()
    report_path = tmp_path / run_id / "report.json"
    state_path = tmp_path / run_id / "state.json"
    reader = json.loads(report_path.read_bytes())
    state = json.loads(state_path.read_bytes())
    for key, value, kind in [
        ("profile", "unknown_v2", "unsupported_version"),
        ("status", "partial", "corrupt"),
        ("fingerprint", "invalid", "corrupt"),
    ]:
        changed = dict(reader, **{key: value})
        payload = json.dumps(changed).encode()
        report_path.write_bytes(payload)
        state["result_digest"] = hashlib.sha256(payload).hexdigest()
        state_path.write_text(json.dumps(state))
        error(kind, lambda: app.get_report(run_id, "owner-a"))


def test_native_storage_capability_failure_is_side_effect_free(tmp_path, monkeypatch):
    from market_research.descriptive.cases.futures_basis import online

    monkeypatch.setattr(online, "_supports_storage", lambda: False)
    root = tmp_path / "unsupported"
    error("unavailable", lambda: application(root))
    assert not root.exists()
