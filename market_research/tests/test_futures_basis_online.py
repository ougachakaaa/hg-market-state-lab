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
    run_id = app.submit(REQUEST, "owner-a")["run_id"]
    assert settled(app, run_id)["result_status"] == "complete"
    assert app.get_report(run_id, "owner-a")["views"]["histograms"] == {}
    monkeypatch.setattr(
        "market_research.descriptive.cases.futures_basis.online.MAX_REPORT_BYTES", 100
    )
    oversized = app.submit(REQUEST, "owner-a")["run_id"]
    state = settled(app, oversized)
    assert state["status"] == "FAILED"
    assert state["failure"]["category"] == "result_too_large"
    error("result_unavailable", lambda: app.get_report(oversized, "owner-a"))
