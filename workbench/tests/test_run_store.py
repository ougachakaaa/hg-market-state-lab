import copy
import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import pytest
from acceptance_example import demonstrate
from support import SCRIPT, RunStore, _script, synthetic_request


def test_two_runs_round_trip_and_preserved_evidence(tmp_path):
    result = demonstrate(tmp_path)
    assert result["runs"][0]["statuses"] == ["PASS", "FAIL"]
    assert result["runs"][1]["statuses"] == ["BLOCKED", "SKIPPED"]
    assert result["runs"][0]["run_id"] != result["runs"][1]["run_id"]
    first = RunStore(tmp_path).read(result["runs"][0]["run_id"])
    assert first["manifest"]["original_request"] == synthetic_request()["original_request"]
    assert first["manifest"]["resolved_inputs"] == synthetic_request()["resolved_inputs"]
    assert first["manifest"]["workflow"] == synthetic_request()["workflow"]


def test_snapshot_detaches_mutable_caller_and_multiple_versions(tmp_path):
    store = RunStore(tmp_path)
    request = synthetic_request()
    original = copy.deepcopy(request)
    first = store.create(request)
    request["task"]["version"] = "2"
    request["task"]["gates"][0]["criteria"] = "Different criteria"
    second = store.create(request)
    first["task"]["goal"] = "caller mutation"
    saved = store.read(first["run_id"])["manifest"]
    assert saved["task"] == original["task"]
    assert store.read(second["run_id"])["manifest"]["task"] == request["task"]
    assert saved["task_sha256"] != second["task_sha256"]


@pytest.mark.parametrize("status", ["FAIL", "BLOCKED", "SKIPPED"])
def test_nonpass_requires_reason(tmp_path, status):
    store = RunStore(tmp_path)
    run_id = store.create(synthetic_request())["run_id"]
    with pytest.raises(ValueError, match="reason"):
        store.gate(run_id, {"gate_id": "inspect", "status": status, "reason": " ", "evidence": []})
    assert store.read(run_id)["records"] == []


def test_pass_requires_same_run_preserved_evidence_and_rechecks_append(tmp_path):
    store = RunStore(tmp_path / "store")
    first, second = [store.create(synthetic_request())["run_id"] for _ in range(2)]
    outcome = {"gate_id": "inspect", "status": "PASS", "reason": "", "evidence": []}
    with pytest.raises(ValueError, match="PASS requires"):
        store.gate(first, outcome)
    source = tmp_path / "check.txt"
    source.write_text("checked", encoding="utf-8")
    artifact = store.artifact(first, {"label": "proof", "path": str(source)})["payload"]
    outcome["evidence"] = [artifact["artifact_id"]]
    with pytest.raises(ValueError, match="this Run"):
        store.gate(second, outcome)
    store.gate(first, outcome)
    store.gate(first, {"gate_id": "inspect", "status": "FAIL",
                       "reason": "Subsequent check failed", "evidence": outcome["evidence"]})
    state = store.read(first)
    assert [r["payload"]["status"] for r in state["gate_outcomes"]] == ["PASS", "FAIL"]
    source.write_text("changed", encoding="utf-8")
    assert (store.root / first / artifact["stored_path"]).read_text(encoding="utf-8") == "checked"


@pytest.mark.parametrize("change", ["missing-version", "missing-scope", "bad-approval", "duplicate",
                                    "unknown-dependency", "cycle", "nonfinite", "nonstring-key"])
def test_invalid_task_has_no_side_effects(tmp_path, change):
    request = synthetic_request()
    task = request["task"]
    if change == "missing-version":
        del task["version"]
    elif change == "missing-scope":
        del task["scope"]
    elif change == "bad-approval":
        task["approval"]["kind"] = "agent_inferred"
    elif change == "duplicate":
        task["gates"].append(task["gates"][0])
    elif change == "unknown-dependency":
        task["gates"][0]["depends_on"] = ["unknown"]
    elif change == "cycle":
        task["gates"][0]["depends_on"] = ["optional"]
    elif change == "nonfinite":
        request["resolved_inputs"]["bad"] = float("nan")
    else:
        request["resolved_inputs"][1] = "not a string key"
    store = RunStore(tmp_path / "unused")
    with pytest.raises(ValueError):
        store.create(request)
    assert not store.root.exists()


@pytest.mark.parametrize("gate_id,status", [("unknown", "PASS"), ("inspect", "pass"),
                                           ("inspect", "SUCCESS"), ("inspect", [])])
def test_unknown_gate_and_status_rejected(tmp_path, gate_id, status):
    store = RunStore(tmp_path)
    run_id = store.create(synthetic_request())["run_id"]
    with pytest.raises(ValueError):
        store.gate(run_id, {"gate_id": gate_id, "status": status, "reason": "why", "evidence": []})
    assert not (tmp_path / run_id / ".writer").exists()


def test_empty_gates_and_optional_workflow_are_valid(tmp_path):
    request = synthetic_request()
    request["task"]["gates"] = []
    del request["workflow"]
    store = RunStore(tmp_path)
    manifest = store.create(request)
    assert store.read(manifest["run_id"])["manifest"]["workflow"] is None


def test_busy_writer_and_collision_preserve_existing_bytes(tmp_path):
    store = RunStore(tmp_path)
    manifest = store.create(synthetic_request())
    run_id = manifest["run_id"]
    manifest_path = tmp_path / run_id / "manifest.json"
    before = manifest_path.read_bytes()
    fake_uuid = type("FixedUUID", (), {"hex": run_id})()
    with patch.object(_script["uuid"], "uuid4", return_value=fake_uuid):
        with pytest.raises(FileExistsError):
            store.create(synthetic_request())
    lock = tmp_path / run_id / ".writer"
    lock.mkdir()
    with pytest.raises(FileExistsError):
        store.event(run_id, {"operation": "attempt", "details": {}})
    assert lock.is_dir()
    assert manifest_path.read_bytes() == before
    assert store.read(run_id)["records"] == []


def test_publication_is_exclusive_and_failed_publish_leaves_no_record(tmp_path):
    publish = _script["_publish"]
    path = tmp_path / "immutable"
    publish(path, b"original")
    with pytest.raises(FileExistsError):
        publish(path, b"replacement")
    assert path.read_bytes() == b"original"
    store = RunStore(tmp_path / "store")
    run_id = store.create(synthetic_request())["run_id"]
    with patch.object(os, "link", side_effect=OSError("injected publication failure")):
        with pytest.raises(OSError, match="injected"):
            store.event(run_id, {"operation": "attempt", "details": {}})
    assert store.read(run_id)["records"] == []
    assert list((store.root / run_id / "records").iterdir()) == []
    store.event(run_id, {"operation": "retry", "details": {}})
    assert store.read(run_id)["records"][0]["sequence"] == 1


def test_reader_sees_committed_prefix_and_concurrent_writer_is_busy(tmp_path):
    store = RunStore(tmp_path / "store")
    run_id = store.create(synthetic_request())["run_id"]
    store.event(run_id, {"operation": "first", "details": {}})
    publishing = threading.Event()
    resume = threading.Event()
    real_link = os.link

    def paused_link(source, destination):
        # At this point the temporary file is complete, but not committed.
        assert json.loads(Path(source).read_text(encoding="utf-8"))["sequence"] == 2
        publishing.set()
        assert resume.wait(timeout=10)
        return real_link(source, destination)

    with ThreadPoolExecutor(max_workers=1) as executor:
        with patch.object(os, "link", side_effect=paused_link):
            future = executor.submit(store.event, run_id, {"operation": "second", "details": {}})
            try:
                assert publishing.wait(timeout=10)
                assert len(store.read(run_id)["records"]) == 1
                with pytest.raises(FileExistsError):
                    store.event(run_id, {"operation": "competing", "details": {}})
            finally:
                resume.set()
            assert future.result(timeout=10)["sequence"] == 2
    assert [r["payload"]["operation"] for r in store.read(run_id)["events"]] == ["first", "second"]


def test_artifact_collision_cannot_replace_evidence(tmp_path):
    store = RunStore(tmp_path / "store")
    run_id = store.create(synthetic_request())["run_id"]
    source = tmp_path / "source"
    source.write_bytes(b"original")
    artifact = store.artifact(run_id, {"label": "proof", "path": str(source)})["payload"]
    source.write_bytes(b"replacement")
    fixed = type("FixedUUID", (), {"hex": artifact["artifact_id"]})()
    with patch.object(_script["uuid"], "uuid4", return_value=fixed):
        with pytest.raises(FileExistsError):
            store.artifact(run_id, {"label": "replacement", "path": str(source)})
    state = store.read(run_id)
    assert len(state["artifacts"]) == 1
    assert (store.root / run_id / artifact["stored_path"]).read_bytes() == b"original"


def test_missing_artifact_and_invalid_event_do_not_append(tmp_path):
    store = RunStore(tmp_path / "store")
    run_id = store.create(synthetic_request())["run_id"]
    with pytest.raises(FileNotFoundError):
        store.artifact(run_id, {"label": "missing", "path": str(tmp_path / "absent")})
    with pytest.raises(ValueError):
        store.event(run_id, {"operation": "", "details": {}})
    with pytest.raises(ValueError):
        store.event(run_id, {"operation": "x", "details": {"bad": object()}})
    assert store.read(run_id)["records"] == []


@pytest.mark.parametrize("corruption", ["identity", "snapshot", "sequence", "missing-record",
                                      "blob", "gate-evidence", "record-kind", "format"])
def test_corruption_is_explicit_and_read_does_not_repair(tmp_path, corruption):
    result = demonstrate(tmp_path)
    run_id = result["runs"][0]["run_id"]
    run = tmp_path / run_id
    if corruption in {"identity", "snapshot", "format"}:
        path = run / "manifest.json"
    elif corruption == "blob":
        path = Path(result["runs"][0]["artifact"])
    else:
        path = run / "records" / "00000003.json"
    if corruption == "blob":
        path.write_bytes(b"corrupt")
    elif corruption == "missing-record":
        path.unlink()
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        if corruption == "identity":
            data["run_id"] = "0" * 32
        elif corruption == "snapshot":
            data["task"]["version"] = "wrong version"
        elif corruption == "sequence":
            data["sequence"] = 9
        elif corruption == "gate-evidence":
            data["payload"]["evidence"] = ["0" * 32]
        elif corruption == "record-kind":
            data["kind"] = "unknown"
        else:
            data["format_version"] = 2
        path.write_text(json.dumps(data), encoding="utf-8")
    snapshot = {str(p): p.read_bytes() for p in run.rglob("*") if p.is_file()}
    with pytest.raises(ValueError):
        RunStore(tmp_path).read(run_id)
    assert snapshot == {str(p): p.read_bytes() for p in run.rglob("*") if p.is_file()}


@pytest.mark.parametrize("run_id", ["../escape", "", "a" * 31, "A" * 32, "C:\\escape"])
def test_run_path_traversal_rejected(tmp_path, run_id):
    store = RunStore(tmp_path)
    with pytest.raises(ValueError):
        store.read(run_id)
    with pytest.raises(ValueError):
        store.event(run_id, {"operation": "x", "details": {}})


def test_aliased_record_is_rejected(tmp_path):
    store = RunStore(tmp_path)
    run_id = store.create(synthetic_request())["run_id"]
    store.event(run_id, {"operation": "x", "details": {}})
    path = tmp_path / run_id / "records" / "00000001.json"
    target = tmp_path / "aliased.json"
    target.write_bytes(path.read_bytes())
    path.unlink()
    try:
        path.symlink_to(target)
    except OSError:
        if sys.platform != "win32":
            pytest.skip("OS user lacks symlink permission")
        # Windows directory junctions need no symlink privilege.
        import _winapi

        path.parent.rmdir()  # Empty test-only directory, no recursive removal.
        _winapi.CreateJunction(str(tmp_path), str(path.parent))
    with pytest.raises(ValueError, match="symlinks|escapes"):
        store.read(run_id)


def test_cli_all_operations_and_errors(tmp_path):
    root = tmp_path / "store"
    payload = tmp_path / "input.json"

    def invoke(operation, data=None, run_id=None):
        command = [sys.executable, str(SCRIPT), "--root", str(root), operation]
        if run_id is not None:
            command += ["--run", run_id]
        if data is not None:
            payload.write_text(json.dumps(data), encoding="utf-8")
            command += ["--input", str(payload)]
        return subprocess.run(command, capture_output=True, text=True, cwd=tmp_path, check=False)

    created = invoke("create", synthetic_request())
    assert created.returncode == 0, created.stderr
    run_id = json.loads(created.stdout)["run_id"]
    source = tmp_path / "source.txt"
    source.write_text("evidence", encoding="utf-8")
    registered = invoke("artifact", {"label": "proof", "path": str(source)}, run_id)
    assert registered.returncode == 0, registered.stderr
    artifact_id = json.loads(registered.stdout)["payload"]["artifact_id"]
    event = invoke("event", {"operation": "read file", "details": {"count": 1}}, run_id)
    assert event.returncode == 0, event.stderr
    outcome = {"gate_id": "inspect", "status": "PASS", "reason": "checked",
               "evidence": [artifact_id]}
    assert invoke("gate", outcome, run_id).returncode == 0
    saved = invoke("read", run_id=run_id)
    assert saved.returncode == 0, saved.stderr
    assert len(json.loads(saved.stdout)["records"]) == 3
    outcome["evidence"] = []
    failed = invoke("gate", outcome, run_id)
    assert failed.returncode == 1
    assert "PASS requires" in failed.stderr
    assert failed.stdout == ""
    payload.write_text('{"task": null, "task": null}', encoding="utf-8")
    duplicate = subprocess.run([sys.executable, str(SCRIPT), "create", "--input", str(payload)],
                               capture_output=True, text=True, check=False)
    assert duplicate.returncode == 1
    assert "duplicate JSON key" in duplicate.stderr
