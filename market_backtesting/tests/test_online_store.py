"""POSIX store adversarial checks and actual atomic write/restart behavior."""

import hashlib
import json
import os
import stat
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long import (
    create_futures_roll_online_application,
    online,
    online_codec,
    online_store,
)
from market_backtesting.cases.futures_roll_long.online_codec import RESULT_LIMIT, json_bytes
from market_backtesting.cases.futures_roll_long.online_models import FuturesRollOnlineError
from market_backtesting.cases.futures_roll_long.online_store import FuturesRollRunStore
from public_input_fixtures import fake_services, request
from test_online_application import ControlledService, assert_error, completed, wait_terminal


def mutate(path: Path, update: Any) -> None:
    raw = json.loads(path.read_bytes())
    update(raw)
    path.write_bytes(json_bytes(raw, RESULT_LIMIT))


def test_recovery_pending_running_orphan_and_terminal_immutable(tmp_path: Path) -> None:
    root = tmp_path / "runs"
    store = FuturesRollRunStore(root)
    pending = store.create(request(), "alice")
    running = store.create(request(), "alice")
    store.transition(running.run_id, "RUNNING")
    # Real orphan bytes, never a successful result without terminal commit.
    (root / running.run_id / "result.json").write_bytes(b'{"orphan":true}')
    os.chmod(root / running.run_id / "result.json", 0o600)
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    for accepted in (pending, running):
        status = app.get_status(accepted.run_id, "alice")
        assert status.status == "INTERRUPTED"
        assert status.failure is not None
        assert status.failure.reason == "interrupted" and status.finished_at
        assert_error(
            "result_not_ready", lambda accepted=accepted: app.get_result(accepted.run_id, "alice")
        )
        assert_error(
            "corrupt", lambda accepted=accepted: store.transition(accepted.run_id, "RUNNING")
        )
    original = (root / running.run_id / "state.json").read_bytes()
    again = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert again.get_status(running.run_id, "alice").status == "INTERRUPTED"
    assert (root / running.run_id / "state.json").read_bytes() == original


@pytest.mark.parametrize("terminal", ["COMPLETED", "FAILED", "INTERRUPTED"])
def test_all_terminal_states_immutable(tmp_path: Path, terminal: str) -> None:
    app, accepted = completed(tmp_path / "runs")
    if terminal != "COMPLETED":
        # Construct via legal transitions in an independent persisted run.
        store = app._available()
        accepted = store.create(request(), "alice")
        from market_backtesting.cases.futures_roll_long.online_models import OnlineFailure

        category = "interrupted" if terminal == "INTERRUPTED" else "internal_failure"
        store.transition(
            accepted.run_id,
            terminal,  # type: ignore[arg-type]
            failure=OnlineFailure("execution", category, None, category),
        )
    store = app._available()
    for target in ("PENDING", "RUNNING", "COMPLETED", "FAILED", "INTERRUPTED"):
        assert_error("corrupt", lambda target=target: store.transition(accepted.run_id, target))
    restarted = create_futures_roll_online_application(
        root=tmp_path / "runs", service=fake_services()[0]
    )
    assert restarted.get_status(accepted.run_id, "alice").status == terminal


@pytest.mark.parametrize("object_name", ["root", "run", "result", "request", "state"])
def test_symlinks_rejected(tmp_path: Path, object_name: str) -> None:
    root = tmp_path / "runs"
    app, accepted = completed(root)
    path = {
        "root": root,
        "run": root / accepted.run_id,
        "result": root / accepted.run_id / "result.json",
        "request": root / accepted.run_id / "request.json",
        "state": root / accepted.run_id / "state.json",
    }[object_name]
    saved = path.with_name(path.name + "-saved")
    path.rename(saved)
    path.symlink_to(saved, target_is_directory=saved.is_dir())
    for operation in (app.get_status, app.get_result):
        assert_error("corrupt", lambda operation=operation: operation(accepted.run_id, "alice"))


@pytest.mark.parametrize("which", ["root", "run", "result", "request", "state"])
def test_unsafe_permissions(tmp_path: Path, which: str) -> None:
    root = tmp_path / "runs"
    app, accepted = completed(root)
    path = {
        "root": root,
        "run": root / accepted.run_id,
        "result": root / accepted.run_id / "result.json",
        "request": root / accepted.run_id / "request.json",
        "state": root / accepted.run_id / "state.json",
    }[which]
    original = stat.S_IMODE(path.stat().st_mode)
    path.chmod(original | 0o020)
    try:
        assert_error("corrupt", lambda: app.get_status(accepted.run_id, "alice"))
    finally:
        path.chmod(original)


def test_wrong_owner_and_created_modes(tmp_path: Path, monkeypatch: Any) -> None:
    root = tmp_path / "runs"
    app, accepted = completed(root)
    for path in (root, root / accepted.run_id):
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
    for name in ("request.json", "state.json", "result.json"):
        assert stat.S_IMODE((root / accepted.run_id / name).stat().st_mode) == 0o600
    uid = os.getuid()
    monkeypatch.setattr(online_store.os, "getuid", lambda: uid + 1)
    assert_error("corrupt", lambda: app.get_result(accepted.run_id, "alice"))


@pytest.mark.parametrize("kind", ["missing", "directory", "fifo", "hardlink", "oversized"])
def test_invalid_result_file(tmp_path: Path, kind: str) -> None:
    app, accepted = completed(tmp_path / "runs")
    path = tmp_path / "runs" / accepted.run_id / "result.json"
    if kind == "hardlink":
        os.link(path, tmp_path / "other")
    else:
        path.unlink()
        if kind == "directory":
            path.mkdir(mode=0o700)
        elif kind == "fifo":
            os.mkfifo(path, 0o600)
        elif kind == "oversized":
            with path.open("wb") as stream:
                stream.truncate(RESULT_LIMIT + 1)
            path.chmod(0o600)
    assert_error("corrupt", lambda: app.get_status(accepted.run_id, "alice"))
    assert_error("corrupt", lambda: app.get_result(accepted.run_id, "alice"))


def test_status_never_parses_result_or_checks_digest(tmp_path: Path, monkeypatch: Any) -> None:
    app, accepted = completed(tmp_path / "runs")
    result = tmp_path / "runs" / accepted.run_id / "result.json"
    result.write_bytes(b"invalid json and mismatched digest")
    assert app.get_status(accepted.run_id, "alice").status == "COMPLETED"
    assert_error("corrupt", lambda: app.get_result(accepted.run_id, "alice"))
    # A metadata-only read must not read any result bytes.
    original = online_store.read_bytes

    def checked(fd: int, name: str, limit: int) -> bytes:
        assert name != "result.json"
        return original(fd, name, limit)

    monkeypatch.setattr(online_store, "read_bytes", checked)
    assert app.get_status(accepted.run_id, "alice").status == "COMPLETED"


@pytest.mark.parametrize(
    "change",
    [
        lambda s: s.update(version=2),
        lambda s: s.update(version=True),
        lambda s: s.update(status="UNKNOWN"),
        lambda s: s.update(run_id="0" * 32),
        lambda s: s.update(result_digest=None),
        lambda s: s.update(finished_at=None),
        lambda s: s.update(extra="private"),
        lambda s: s.update(request_digest="0" * 64),
        lambda s: s.update(started_at="bad"),
    ],
)
def test_invalid_state_schema(tmp_path: Path, change: Any) -> None:
    app, accepted = completed(tmp_path / "runs")
    mutate(tmp_path / "runs" / accepted.run_id / "state.json", change)
    assert_error("corrupt", lambda: app.get_status(accepted.run_id, "alice"))
    restarted = create_futures_roll_online_application(
        root=tmp_path / "runs", service=fake_services()[0]
    )
    assert_error("unavailable", lambda: restarted.submit(request(), "alice"))
    assert restarted.preflight(request(), "alice").ready


@pytest.mark.parametrize("payload", [b'{"version":1,"version":1}', b"[]", b"not json"])
def test_corrupt_metadata_fails_without_repair(tmp_path: Path, payload: bytes) -> None:
    app, accepted = completed(tmp_path / "runs")
    path = tmp_path / "runs" / accepted.run_id / "request.json"
    path.write_bytes(payload)
    assert_error("corrupt", lambda: app.get_status(accepted.run_id, "alice"))
    assert path.read_bytes() == payload


@pytest.mark.parametrize(
    "change",
    [
        lambda r: r.update(profile="unknown"),
        lambda r: r.update(definition_version="unknown"),
        lambda r: r.update(status="partial"),
        lambda r: r.update(extra=1),
        lambda r: r["request"].update(strategy_profile="expiry_to_Q1_v1"),
        lambda r: r["daily"][0].update(daily_pnl=True),
        lambda r: r["views"]["returns"]["layers"][0]["layer"]["data"][0].update(y=9),
        lambda r: r["evidence"].update(input_fingerprint="bad"),
    ],
)
def test_complete_result_shape_even_with_recomputed_digest(tmp_path: Path, change: Any) -> None:
    app, accepted = completed(tmp_path / "runs")
    directory = tmp_path / "runs" / accepted.run_id
    mutate(directory / "result.json", change)
    digest = hashlib.sha256((directory / "result.json").read_bytes()).hexdigest()
    mutate(directory / "state.json", lambda s: s.update(result_digest=digest))
    assert app.get_status(accepted.run_id, "alice").status == "COMPLETED"
    assert_error("corrupt", lambda: app.get_result(accepted.run_id, "alice"))
    # Reader permit releases after corrupt result.
    assert online._READ_PERMIT.acquire(blocking=False)
    online._READ_PERMIT.release()


def test_unsupported_platform_before_tree_and_preflight_available(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(online, "supports_storage", lambda: False)
    root = tmp_path / "never-created"
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert not root.exists()
    assert app.preflight(request(), "alice").ready
    assert_error("unavailable", lambda: app.submit(request(), "alice"))


def test_native_windows_missing_dirfd_and_flags(monkeypatch: Any) -> None:
    with monkeypatch.context() as scoped:
        scoped.setattr(online_store.os, "name", "nt")
        assert not online_store.supports_storage()
    with monkeypatch.context() as scoped:
        scoped.setattr(online_store.os, "supports_dir_fd", set())
        assert not online_store.supports_storage()
    with monkeypatch.context() as scoped:
        scoped.delattr(online_store.os, "O_NOFOLLOW")
        assert not online_store.supports_storage()


@pytest.mark.parametrize("relative", [True, False])
def test_invalid_root_no_creation(tmp_path: Path, relative: bool) -> None:
    root = Path("relative-run-root") if relative else tmp_path / "new" / ".." / "escape"
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert_error("unavailable", lambda: app.submit(request(), "alice"))
    assert not (tmp_path / "new").exists()


def test_atomic_interruption_after_result_before_completed(
    tmp_path: Path, monkeypatch: Any
) -> None:
    root = tmp_path / "runs"
    store = FuturesRollRunStore(root)
    accepted = store.create(request(), "alice")
    store.transition(accepted.run_id, "RUNNING")
    from market_backtesting.cases.futures_roll_long import build_backtest_result

    payload = online_codec.encode_result(
        build_backtest_result(fake_services()[0].run(request())), request()
    )
    original = online_store.atomic_write

    def interrupted(fd: int, name: str, data: bytes) -> None:
        if name == "state.json":
            raise OSError("disk failure")
        original(fd, name, data)

    with monkeypatch.context() as scoped:
        scoped.setattr(online_store, "atomic_write", interrupted)
        with pytest.raises(OSError):
            store.publish(accepted.run_id, payload)
    assert (root / accepted.run_id / "result.json").read_bytes() == payload
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert app.get_status(accepted.run_id, "alice").status == "INTERRUPTED"
    assert_error("result_not_ready", lambda: app.get_result(accepted.run_id, "alice"))


def test_failed_atomic_replace_keeps_old_state(tmp_path: Path, monkeypatch: Any) -> None:
    store = FuturesRollRunStore(tmp_path / "runs")
    accepted = store.create(request(), "alice")
    path = tmp_path / "runs" / accepted.run_id / "state.json"
    original = path.read_bytes()

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise OSError("atomic replace failed")

    with monkeypatch.context() as scoped:
        scoped.setattr(online_store.os, "replace", fail)
        with pytest.raises(OSError):
            store.transition(accepted.run_id, "RUNNING")
    assert path.read_bytes() == original
    assert not list(path.parent.glob(".*"))


def test_unpersistable_worker_failure_is_unavailable_then_recovered(
    tmp_path: Path, monkeypatch: Any
) -> None:
    service = ControlledService(RuntimeError("private"))
    root = tmp_path / "runs"
    app = create_futures_roll_online_application(root=root, service=service)
    accepted = app.submit(request(), "alice")
    assert service.entered.wait(2)
    second = create_futures_roll_online_application(root=root, service=service)
    original = online_store.atomic_write

    def fail(*args: Any) -> Any:
        raise OSError("disk unavailable")

    with monkeypatch.context() as scoped:
        scoped.setattr(online_store, "atomic_write", fail)
        service.release.set()
        deadline = time.monotonic() + 5
        while online._ACTIVE is not None and time.monotonic() < deadline:
            time.sleep(0.005)
        assert online._ACTIVE is None
        assert_error("unavailable", lambda: app.get_status(accepted.run_id, "alice"))
        assert_error("unavailable", lambda: second.get_status(accepted.run_id, "alice"))
    assert online_store.atomic_write is original
    restarted = create_futures_roll_online_application(root=root, service=service)
    assert restarted.get_status(accepted.run_id, "alice").status == "INTERRUPTED"


def test_no_long_state_lock_during_publication(tmp_path: Path, monkeypatch: Any) -> None:
    entered, release = threading.Event(), threading.Event()
    original = online_store.atomic_write

    def blocked(fd: int, name: str, payload: bytes) -> None:
        if name == "result.json":
            entered.set()
            assert release.wait(5)
        original(fd, name, payload)

    monkeypatch.setattr(online_store, "atomic_write", blocked)
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    accepted = app.submit(request(), "alice")
    try:
        assert entered.wait(2)
        assert app.get_status(accepted.run_id, "alice").status == "RUNNING"
    finally:
        release.set()
        assert wait_terminal(app, accepted.run_id).status == "COMPLETED"


def test_real_size_bound_without_truncation(tmp_path: Path) -> None:
    from market_backtesting.cases.futures_roll_long import build_backtest_result

    result = build_backtest_result(fake_services()[0].run(request()))
    huge = replace(result, benchmark=replace(result.benchmark, index_name="x" * RESULT_LIMIT))
    with pytest.raises(FuturesRollOnlineError, match="result_too_large"):
        online_codec.encode_result(huge, request())


def test_metadata_request_corruption_is_isolated(tmp_path: Path) -> None:
    app, accepted = completed(tmp_path / "runs")
    mutate(
        tmp_path / "runs" / accepted.run_id / "request.json",
        lambda raw: raw["request"].update(product_code="bad"),
    )
    assert_error("corrupt", lambda: app.get_status(accepted.run_id, "alice"))
    restarted = create_futures_roll_online_application(
        root=tmp_path / "runs", service=fake_services()[0]
    )
    assert_error("unavailable", lambda: restarted.submit(request(), "alice"))
    assert restarted.preflight(request(), "alice").ready


def test_oversized_owner_does_not_create_run(tmp_path: Path) -> None:
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    assert_error("invalid_request", lambda: app.submit(request(), "x" * 16384))
    assert list((tmp_path / "runs").iterdir()) == []


def test_root_config_and_cwd_independent_default(tmp_path: Path, monkeypatch: Any) -> None:
    import lab_config

    root = tmp_path / "configured"
    env = tmp_path / ".env"
    env.write_text(f"LAB_BACKTESTING_RUN_ROOT={root}\n", encoding="utf-8")
    monkeypatch.setattr(lab_config, "ENV_FILE", env)
    monkeypatch.delenv(lab_config.LAB_BACKTESTING_RUN_ROOT_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    app = create_futures_roll_online_application(service=fake_services()[0])
    assert app._available().root == root
    assert root.is_dir()
    roots: list[Path] = []

    class InspectStore:
        def __init__(self, selected: Path) -> None:
            roots.append(selected)

        def recover(self, active: Any) -> None:
            pass

    monkeypatch.setattr(online, "backtesting_run_root", lambda: None)
    monkeypatch.setattr(online, "FuturesRollRunStore", InspectStore)
    create_futures_roll_online_application(service=fake_services()[0])
    expected = Path(online.__file__).resolve().parents[4] / ".runtime" / "futures_roll_long_online"
    assert roots == [expected]


def test_foreign_does_not_observe_corrupt_state(tmp_path: Path) -> None:
    app, accepted = completed(tmp_path / "runs")
    (tmp_path / "runs" / accepted.run_id / "state.json").write_bytes(b"broken state")
    for method in (app.get_status, app.get_result):
        assert_error("run_not_found", lambda method=method: method(accepted.run_id, "bob"))


@pytest.mark.parametrize(
    "payload",
    [b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1,"a":2}', b"\xef\xbb\xbf{}", "{}".encode("utf-16")],
)
def test_strict_json_rejects_noncanonical_encodings(payload: bytes) -> None:
    with pytest.raises((ValueError, UnicodeError)):
        online_codec.strict_json(payload)


def test_process_crash_after_result_write_real_restart(tmp_path: Path) -> None:
    import subprocess
    import sys

    code = """
import json, os, sys, threading
from pathlib import Path
sys.path.insert(0, sys.argv[2])
from public_input_fixtures import fake_services, request
from market_backtesting.cases.futures_roll_long import create_futures_roll_online_application
from market_backtesting.cases.futures_roll_long import online_store
original = online_store.atomic_write
def crash(fd, name, data):
    if name == "state.json" and json.loads(data)["status"] == "COMPLETED":
        os._exit(17)
    original(fd, name, data)
online_store.atomic_write = crash
app = create_futures_roll_online_application(root=Path(sys.argv[1]), service=fake_services()[0])
app.submit(request(), "alice")
threading.Event().wait(10)
os._exit(18)
"""
    root = tmp_path / "runs"
    child = subprocess.run(
        [sys.executable, "-c", code, str(root), str(Path(__file__).resolve().parent)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert child.returncode == 17, child.stderr
    (directory,) = root.iterdir()
    assert (directory / "result.json").is_file()
    assert json.loads((directory / "state.json").read_bytes())["status"] == "RUNNING"
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert app.get_status(directory.name, "alice").status == "INTERRUPTED"
    assert_error("result_not_ready", lambda: app.get_result(directory.name, "alice"))
