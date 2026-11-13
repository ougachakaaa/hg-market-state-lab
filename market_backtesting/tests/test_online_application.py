"""Actual thread, WP3/WP4 pipeline, owner and concurrency acceptance."""

import sqlite3
import threading
import time
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long import (
    FuturesRollApplicationError,
    FuturesRollOnlineError,
    create_futures_roll_online_application,
    online,
)
from market_backtesting.cases.futures_roll_long.online_models import TERMINAL
from public_input_fixtures import fake_services, request


class ControlledService:
    def __init__(self, error: BaseException | None = None) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.error = error
        self.delegate = fake_services()[0]
        self.calls = 0
        self.worker_thread: int | None = None

    def run(self, req: Any) -> Any:
        self.calls += 1
        self.worker_thread = threading.get_ident()
        self.entered.set()
        if not self.release.wait(5):
            raise RuntimeError("test_worker_timeout")
        if self.error is not None:
            raise self.error
        return self.delegate.run(req)

    def preflight(self, req: Any) -> Any:
        return self.delegate.preflight(req)


def wait_terminal(app: Any, run_id: str, owner: str = "alice") -> Any:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        status = app.get_status(run_id, owner)
        if status.status in TERMINAL:
            # Terminal commit precedes worker finally; wait for guard release as well.
            with online._PROCESS_LOCK:
                if online._ACTIVE is None:
                    return status
        time.sleep(0.005)
    raise AssertionError("worker did not terminate")


def completed(root: Path, profile: str = "expiry_to_M1_v1") -> tuple[Any, Any]:
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    accepted = app.submit(request(profile), "alice")  # type: ignore[arg-type]
    assert wait_terminal(app, accepted.run_id).status == "COMPLETED"
    return app, accepted


def assert_error(category: str, operation: Any) -> None:
    with pytest.raises(FuturesRollOnlineError) as exc:
        operation()
    assert exc.value.category == category
    assert str(exc.value) == category


@pytest.mark.parametrize(
    "profile,pnl,target",
    [
        ("expiry_to_M1_v1", 22000, "IM2504.CFX"),
        ("expiry_to_Q1_v1", 19000, "IM2506.CFX"),
    ],
)
def test_real_thread_pipeline_and_oracle(
    tmp_path: Path, profile: str, pnl: int, target: str
) -> None:
    service = ControlledService()
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=service)
    accepted = app.submit(request(profile), "alice")  # type: ignore[arg-type]
    try:
        assert accepted.status == "PENDING"
        assert len(accepted.run_id) == 32 and int(accepted.run_id, 16) >= 0
        assert service.entered.wait(2)
        assert service.worker_thread != threading.get_ident()
        status = app.get_status(accepted.run_id, "alice")
        assert status.status == "RUNNING"
        assert status.started_at is not None
        assert_error("result_not_ready", lambda: app.get_result(accepted.run_id, "alice"))
        service.release.set()
        terminal = wait_terminal(app, accepted.run_id)
        assert terminal.status == "COMPLETED" and terminal.finished_at is not None
        result = app.get_result(accepted.run_id, "alice")
        from market_backtesting.cases.futures_roll_long import build_backtest_result
        from market_backtesting.cases.futures_roll_long.online_codec import encode_result

        oracle = build_backtest_result(service.delegate.run(accepted.request))
        assert result == oracle
        assert app._available().read_result(accepted.run_id, "alice") == encode_result(
            oracle, accepted.request
        )
        assert result.summary.total_pnl == pnl
        assert result.initial_notional.value == 1200000
        assert result.rolls[0].new_contract_code == target
        assert result.daily[2].pnl_contract_code == "IM2503.CFX"
        assert result.daily[-1].position_contract_code is None
        assert result.profile == "futures_roll_long_result_v1"
        assert result.views.returns.layers[0].layer.data[-1].y == result.summary.gross_return
        assert service.calls == 1
        restarted = create_futures_roll_online_application(root=tmp_path / "runs", service=service)
        assert restarted.get_result(accepted.run_id, "alice") == result
        assert service.calls == 1
        assert "owner_scope" not in asdict(terminal)
        assert "owner_scope" not in asdict(result)
    finally:
        service.release.set()
        wait_terminal(app, accepted.run_id)


def test_busy_cross_instance_no_directory_status_not_blocked(tmp_path: Path) -> None:
    service = ControlledService()
    app = create_futures_roll_online_application(root=tmp_path / "a", service=service)
    accepted = app.submit(request(), "alice")
    try:
        assert service.entered.wait(2)
        second = create_futures_roll_online_application(root=tmp_path / "b", service=service)
        same = create_futures_roll_online_application(root=tmp_path / "a", service=service)
        for other in (app, second, same):
            assert_error("run_busy", lambda other=other: other.submit(request(), "bob"))
        assert second._available().path.is_file()
        with sqlite3.connect(second._available().path) as connection:
            assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)
        assert len(list((tmp_path / "a").iterdir())) == 1
        assert same.get_status(accepted.run_id, "alice").status == "RUNNING"
        assert app.preflight(request(), "alice").ready
    finally:
        service.release.set()
        assert wait_terminal(app, accepted.run_id).status == "COMPLETED"
    next_run = second.submit(request(), "alice")
    assert wait_terminal(second, next_run.run_id).status == "COMPLETED"


@pytest.mark.parametrize(
    "error,stage,category,reason",
    [
        (
            RuntimeError("token=/private/provider"),
            "execution",
            "internal_failure",
            "internal_failure",
        ),
        (
            FuturesRollApplicationError(
                "incomplete_input",
                "final_export_incomplete",
                stage="export",
                dependency="calendar_sse",
            ),
            "export",
            "incomplete_input",
            "final_export_incomplete",
        ),
        (
            FuturesRollApplicationError("invalid_numeric", "daily_pnl", stage="replay"),
            "replay",
            "invalid_numeric",
            "daily_pnl",
        ),
    ],
)
def test_worker_failure_no_partial_and_guard_release(
    tmp_path: Path,
    error: BaseException,
    stage: str,
    category: str,
    reason: str,
) -> None:
    service = ControlledService(error)
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=service)
    accepted = app.submit(request(), "alice")
    service.release.set()
    state = wait_terminal(app, accepted.run_id)
    assert state.status == "FAILED"
    assert (state.failure.stage, state.failure.category, state.failure.reason) == (
        stage,
        category,
        reason,
    )
    assert "private" not in str(state) and "token" not in str(state)
    assert_error("result_not_ready", lambda: app.get_result(accepted.run_id, "alice"))
    assert not (tmp_path / "runs" / accepted.run_id / "result.json").exists()
    again = app.submit(request(), "alice")
    assert wait_terminal(app, again.run_id).status == "FAILED"


def test_ownership_missing_and_malformed_no_storage(tmp_path: Path, monkeypatch: Any) -> None:
    app, accepted = completed(tmp_path / "runs")
    for method in (app.get_status, app.get_result):
        for run_id, owner in ((accepted.run_id, "bob"), ("0" * 32, "bob")):
            assert_error(
                "run_not_found",
                lambda method=method, run_id=run_id, owner=owner: method(run_id, owner),
            )

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("malformed ID reached storage")

    monkeypatch.setattr(app, "_available", forbidden)
    for run_id in ("../escape", "A" * 32, "a" * 31, "a" * 33, "", "a/" * 16):
        for method in (app.get_status, app.get_result):
            assert_error(
                "run_not_found", lambda method=method, run_id=run_id: method(run_id, "alice")
            )


def test_single_full_reader_status_independent(tmp_path: Path, monkeypatch: Any) -> None:
    app, accepted = completed(tmp_path / "runs")
    entered, release = threading.Event(), threading.Event()
    original = online.decode_result
    outcomes: list[Any] = []

    def blocked(*args: Any) -> Any:
        entered.set()
        assert release.wait(5)
        return original(*args)

    monkeypatch.setattr(online, "decode_result", blocked)

    def read() -> None:
        outcomes.append(app.get_result(accepted.run_id, "alice"))

    thread = threading.Thread(target=read)
    thread.start()
    try:
        assert entered.wait(2)
        assert_error("read_busy", lambda: app.get_result(accepted.run_id, "alice"))
        assert_error("run_not_found", lambda: app.get_result(accepted.run_id, "bob"))
        assert app.get_status(accepted.run_id, "alice").status == "COMPLETED"
    finally:
        release.set()
        thread.join(5)
    assert len(outcomes) == 1
    assert app.get_result(accepted.run_id, "alice") == outcomes[0]


def test_invalid_request_owner_before_admission(tmp_path: Path) -> None:
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    with pytest.raises(FuturesRollApplicationError, match="invalid_product_code"):
        app.submit(replace(request(), product_code="OTHER"), "alice")  # type: ignore[arg-type]
    for operation in (app.submit, app.preflight):
        assert_error("invalid_request", lambda operation=operation: operation(request(), ""))
    with sqlite3.connect(app._available().path) as connection:
        assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)


def test_thread_start_failure(tmp_path: Path, monkeypatch: Any) -> None:
    def fail(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("private thread detail")

    monkeypatch.setattr(online.threading.Thread, "start", fail)
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    accepted = app.submit(request(), "alice")
    state = app.get_status(accepted.run_id, "alice")
    assert state.failure is not None
    assert state.status == "FAILED" and state.failure.category == "internal_failure"
    assert online._ACTIVE is None


@pytest.mark.parametrize(
    "failure,category",
    [
        (ValueError("private codec"), "serialization_failure"),
        (FuturesRollOnlineError("result_too_large"), "result_too_large"),
    ],
)
def test_serialization_failure_never_completes(
    tmp_path: Path,
    monkeypatch: Any,
    failure: Exception,
    category: str,
) -> None:
    def fail(*args: Any) -> Any:
        raise failure

    monkeypatch.setattr(online, "encode_result", fail)
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    accepted = app.submit(request(), "alice")
    state = wait_terminal(app, accepted.run_id)
    assert state.status == "FAILED" and state.failure.stage == "result_publication"
    assert state.failure.category == category
    assert_error("result_not_ready", lambda: app.get_result(accepted.run_id, "alice"))


@pytest.mark.parametrize("dependency", ["calendar_cffex", "calendar_sse", "futures", "index"])
def test_real_public_service_failure_projection(
    tmp_path: Path, dependency: str, monkeypatch: Any
) -> None:
    from data_lake import OperationError

    service, calendar, futures, index = fake_services()

    def failure(*args: Any) -> Any:
        raise OperationError("provider credential /private/file")

    if dependency == "calendar_sse":
        original = calendar.export

        def export(req: Any) -> Any:
            return failure(req) if req.exchange == "SSE" else original(req)

        monkeypatch.setattr(calendar, "export", export)
    else:
        selected = {"calendar_cffex": calendar, "futures": futures, "index": index}[dependency]
        monkeypatch.setattr(selected, "export", failure)
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=service)
    accepted = app.submit(request(), "alice")
    state = wait_terminal(app, accepted.run_id)
    assert state.status == "FAILED"
    assert asdict(state.failure) == dict(
        stage="export",
        category="upstream_operation",
        dependency=dependency,
        reason="operation_unavailable",
    )


@pytest.mark.parametrize(
    "category,reason",
    [
        ("invalid_result", "result_projection_mismatch"),
        ("invalid_evidence", "malformed_evidence"),
    ],
)
def test_wp4_failure_keeps_category_and_stage(
    tmp_path: Path,
    monkeypatch: Any,
    category: str,
    reason: str,
) -> None:
    from market_backtesting.cases.futures_roll_long import FuturesRollError

    def fail(*args: Any) -> Any:
        raise FuturesRollError(category, reason, detail="credential /private/path")

    monkeypatch.setattr(online, "validate_backtest_result", fail)
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    accepted = app.submit(request(), "alice")
    state = wait_terminal(app, accepted.run_id)
    assert state.status == "FAILED"
    assert asdict(state.failure) == dict(
        stage="result_validation", category=category, dependency=None, reason=reason
    )


def test_busy_admission_does_not_wait_for_metadata_creation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    service = ControlledService()
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=service)
    entered, release = threading.Event(), threading.Event()
    original = app._available().create
    accepted: list[Any] = []

    def blocked(*args: Any) -> Any:
        entered.set()
        assert release.wait(5)
        return original(*args)

    monkeypatch.setattr(app._available(), "create", blocked)
    thread = threading.Thread(target=lambda: accepted.append(app.submit(request(), "alice")))
    thread.start()
    try:
        assert entered.wait(2)
        assert_error("run_busy", lambda: app.submit(request(), "bob"))
        assert app._store is not None
        with sqlite3.connect(app._store.path) as connection:
            assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)
    finally:
        release.set()
        thread.join(5)
        service.release.set()
    assert len(accepted) == 1
    assert wait_terminal(app, accepted[0].run_id).status == "COMPLETED"


@pytest.mark.parametrize("terminal_failure", [False, True])
def test_failed_publication_commit_and_terminal_recovery(tmp_path, monkeypatch, terminal_failure):
    service = ControlledService()
    root = tmp_path / "runs"
    app = create_futures_roll_online_application(root=root, service=service)
    accepted = app.submit(request(), "alice")
    assert service.entered.wait(2)
    second = create_futures_roll_online_application(root=root, service=service)
    store = app._available()
    original = store._commit

    def fail(connection):
        status = connection.execute("SELECT status FROM runs").fetchone()[0]
        if status == "COMPLETED" or terminal_failure:
            raise sqlite3.OperationalError("private commit detail")
        original(connection)

    with monkeypatch.context() as patch:
        patch.setattr(store, "_commit", fail)
        service.release.set()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with online._PROCESS_LOCK:
                if online._ACTIVE is None:
                    break
            time.sleep(0.005)
        assert online._ACTIVE is None
        if terminal_failure:
            for instance in (app, second):
                assert_error(
                    "unavailable",
                    lambda instance=instance: instance.get_status(accepted.run_id, "alice"),
                )
        else:
            state = second.get_status(accepted.run_id, "alice")
            assert state.status == "FAILED"
            assert state.failure.category == "storage_failure"
            assert state.failure.stage == "result_publication"
        with sqlite3.connect(store.path) as connection:
            assert connection.execute("SELECT count(*) FROM results").fetchone() == (0,)
    restarted = create_futures_roll_online_application(root=root, service=service)
    assert restarted.get_status(accepted.run_id, "alice").status == (
        "INTERRUPTED" if terminal_failure else "FAILED"
    )


def test_unavailable_initialization_preflight_independent(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("private storage")

    monkeypatch.setattr(online.FuturesRollSQLiteRunStore, "recover", fail)
    root = tmp_path / "absent"
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert app.preflight(request(), "alice").ready
    assert not root.exists()
    assert_error("unavailable", lambda: app.submit(request(), "alice"))


def test_application_lock_contention_no_run(tmp_path):
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    with sqlite3.connect(app._available().path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        assert_error("unavailable", lambda: app.submit(request(), "alice"))
    assert online._ACTIVE is None
    with sqlite3.connect(app._available().path) as connection:
        assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)


def test_publication_validation_does_not_hold_process_lock(tmp_path, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = online.FuturesRollSQLiteRunStore._validate_payload

    def blocked(payload, req):
        entered.set()
        assert release.wait(5)
        original(payload, req)

    monkeypatch.setattr(
        online.FuturesRollSQLiteRunStore, "_validate_payload", staticmethod(blocked)
    )
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    accepted = app.submit(request(), "alice")
    try:
        assert entered.wait(2)
        assert app.get_status(accepted.run_id, "alice").status == "RUNNING"
    finally:
        release.set()
        assert wait_terminal(app, accepted.run_id).status == "COMPLETED"
