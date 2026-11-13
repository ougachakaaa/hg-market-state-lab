"""SQLite application integrity and configuration regression checks.

Portable path/alias, atomicity and crash checks live in test_online_sqlite_store.
"""

import hashlib
import json
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from market_backtesting.cases.futures_roll_long import (
    create_futures_roll_online_application,
    online,
    online_codec,
)
from market_backtesting.cases.futures_roll_long.online_codec import RESULT_LIMIT, json_bytes
from market_backtesting.cases.futures_roll_long.online_models import FuturesRollOnlineError
from public_input_fixtures import fake_services, request
from test_online_application import assert_error, completed


def mutate(path: Path, update: Any) -> None:
    root, run_id, name = path.parent.parent, path.parent.name, path.name
    table, column = (
        ("results", "payload")
        if name == "result.json"
        else ("runs", "metadata" if name == "request.json" else "state")
    )
    with sqlite3.connect(root / "runs.sqlite3") as connection:
        raw = json.loads(
            connection.execute(
                f"SELECT {column} FROM {table} WHERE run_id=?", (run_id,)
            ).fetchone()[0]
        )
        update(raw)
        connection.execute(
            f"UPDATE {table} SET {column}=? WHERE run_id=?", (json_bytes(raw, RESULT_LIMIT), run_id)
        )


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
    assert_error("corrupt", lambda: restarted.submit(request(), "alice"))
    assert restarted.preflight(request(), "alice").ready


@pytest.mark.parametrize("payload", [b'{"version":1,"version":1}', b"[]", b"not json"])
def test_corrupt_metadata_fails_without_repair(tmp_path: Path, payload: bytes) -> None:
    app, accepted = completed(tmp_path / "runs")
    with sqlite3.connect(tmp_path / "runs" / "runs.sqlite3") as connection:
        connection.execute("UPDATE runs SET metadata=?", (payload,))
    assert_error("corrupt", lambda: app.get_status(accepted.run_id, "alice"))
    with sqlite3.connect(tmp_path / "runs" / "runs.sqlite3") as connection:
        assert connection.execute("SELECT metadata FROM runs").fetchone()[0] == payload


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
    with sqlite3.connect(directory.parent / "runs.sqlite3") as connection:
        payload = connection.execute(
            "SELECT payload FROM results WHERE run_id=?", (accepted.run_id,)
        ).fetchone()[0]
        connection.execute(
            "UPDATE runs SET result_length=? WHERE run_id=?", (len(payload), accepted.run_id)
        )
    digest = hashlib.sha256(payload).hexdigest()
    mutate(directory / "state.json", lambda s: s.update(result_digest=digest))
    assert app.get_status(accepted.run_id, "alice").status == "COMPLETED"
    assert_error("corrupt", lambda: app.get_result(accepted.run_id, "alice"))
    # Reader permit releases after corrupt result.
    assert online._READ_PERMIT.acquire(blocking=False)
    online._READ_PERMIT.release()


@pytest.mark.parametrize("relative", [True, False])
def test_invalid_root_no_creation(tmp_path: Path, relative: bool) -> None:
    root = Path("relative-run-root") if relative else tmp_path / "new" / ".." / "escape"
    app = create_futures_roll_online_application(root=root, service=fake_services()[0])
    assert_error("unavailable", lambda: app.submit(request(), "alice"))
    assert not (tmp_path / "new").exists()


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
    assert_error("corrupt", lambda: restarted.submit(request(), "alice"))
    assert restarted.preflight(request(), "alice").ready


def test_oversized_owner_does_not_create_run(tmp_path: Path) -> None:
    app = create_futures_roll_online_application(root=tmp_path / "runs", service=fake_services()[0])
    assert_error("invalid_request", lambda: app.submit(request(), "x" * 16384))
    with sqlite3.connect(tmp_path / "runs" / "runs.sqlite3") as connection:
        assert connection.execute("SELECT count(*) FROM runs").fetchone() == (0,)


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
    monkeypatch.setattr(online, "FuturesRollSQLiteRunStore", InspectStore)
    create_futures_roll_online_application(service=fake_services()[0])
    expected = Path(online.__file__).resolve().parents[4] / ".runtime" / "futures_roll_long_online"
    assert roots == [expected]


def test_foreign_does_not_observe_corrupt_state(tmp_path: Path) -> None:
    app, accepted = completed(tmp_path / "runs")
    with sqlite3.connect(tmp_path / "runs" / "runs.sqlite3") as connection:
        connection.execute("UPDATE runs SET state=?", (b"broken state",))
    for method in (app.get_status, app.get_result):
        assert_error("run_not_found", lambda method=method: method(accepted.run_id, "bob"))


@pytest.mark.parametrize(
    "payload",
    [b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1,"a":2}', b"\xef\xbb\xbf{}", "{}".encode("utf-16")],
)
def test_strict_json_rejects_noncanonical_encodings(payload: bytes) -> None:
    with pytest.raises((ValueError, UnicodeError)):
        online_codec.strict_json(payload)
