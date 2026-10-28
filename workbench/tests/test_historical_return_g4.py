"""WB-04 deterministic planning acceptance, with public owner validation and no market I/O."""

import copy
import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from support import RunStore
from test_historical_return_g3 import G3, TASK_DIR, backend, ready

SCRIPT = TASK_DIR / "record_g4.py"
G4 = runpy.run_path(str(SCRIPT))
CANDIDATE = TASK_DIR / "examples" / "g4-candidate.json"


def candidate():
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


def discovered(root):
    with backend() as (target, _, _):
        run = ready(root, target)
        result = G3["record_g3"](root, run["run_id"])
        assert result["result"]["status"] == "PASS"
    return run["run_id"]


def attempt(root, run_id, value=None):
    return G4["record_g4"](root, run_id, candidate() if value is None else value)


def gate(root, run_id, gate_id, status, evidence=None, reason="synthetic subsequent failure"):
    return RunStore(root).gate(run_id, {"gate_id": gate_id, "status": status,
        "reason": reason, "evidence": evidence or []})


def test_full_history_public_python_plan_preview_and_immutable_same_run(tmp_path):
    run_id = discovered(tmp_path)
    store = RunStore(tmp_path)
    before = store.read(run_id)
    task_bytes = (TASK_DIR / "task.json").read_bytes()
    draft = candidate()
    original = copy.deepcopy(draft)
    report = attempt(tmp_path, run_id, draft)
    assert draft == original
    assert report["result"]["status"] == "PASS"
    assert report["evidence_verified"] is True
    frozen = report["frozen"]
    workflow, preview = frozen["workflow"], frozen["preview"]
    assert preview["planned_count"] == 1
    assert preview["analysis_attempt_count"] == 2
    assert preview["plan"]["windows"] == draft["research_plan"]["windows"]
    assert preview["plan"]["horizons"] == [21]  # No HTTP H20 cap applied to Python.
    assert workflow["original_objective"] == draft["original_objective"]
    assert workflow["resolved_inputs"]["research_plan"] == draft["research_plan"]
    assert workflow["research_plan"] == preview["plan"]
    assert workflow["preview"] == frozen["preview_artifact"]
    assert workflow["execution_authorization"]["status"] == "pending"
    assert workflow["known_readiness_gaps"]
    assert workflow["g5_executed"] is False
    after = RunStore(tmp_path).read(run_id)
    assert after["manifest"] == before["manifest"]
    assert after["records"][:len(before["records"])] == before["records"]
    assert (TASK_DIR / "task.json").read_bytes() == task_bytes
    assert not any(r["payload"]["gate_id"] == "G5" for r in after["gate_outcomes"])
    assert after["gate_outcomes"][-1]["payload"]["evidence"] == [
        frozen[k]["artifact_id"] for k in ("workflow_artifact", "preview_artifact",
                                          "attempt_artifact")]
    for r in after["artifacts"]:
        a = r["payload"]
        assert not Path(a["source_location"]).exists()
        assert hashlib.sha256((tmp_path / run_id / a["stored_path"]).read_bytes()).hexdigest() == (
            a["sha256"])
    # Fresh process can discover exact artifact and independently revalidate the public Preview.
    read = subprocess.run([sys.executable, str(SCRIPT), "--root", str(tmp_path),
                           "--run", run_id, "--read"], capture_output=True, text=True, timeout=20)
    assert read.returncode == 0, read.stderr
    assert json.loads(read.stdout) == frozen
    draft["research_plan"]["horizons"] = [5]
    with pytest.raises(ValueError, match="already frozen"):
        attempt(tmp_path, run_id, draft)
    assert store.read(run_id) == after


@pytest.mark.parametrize("problem", ["missing_g1", "g1_fail", "g2_fail", "g2_wrong_skip",
    "g2_pass", "g3_missing", "g3_fail", "g3_later_fail", "fake_evidence", "stale_g3",
    "g3_digest_mismatch", "g3_detail_mismatch", "g3_other_target", "g3_no_support"])
def test_prerequisites_fail_closed_before_plan_or_preview(tmp_path, problem):
    run_id = discovered(tmp_path)
    state = RunStore(tmp_path).read(run_id)
    if problem == "missing_g1":
        run_id = RunStore(tmp_path).create({"task": state["manifest"]["task"],
            "original_request": "Synthetic missing prerequisites", "resolved_inputs": {}})["run_id"]
    elif problem in ("g3_missing", "g3_fail"):
        with backend() as (target, _, _):
            run_id = ready(tmp_path, target)["run_id"]
        if problem == "g3_fail":
            gate(tmp_path, run_id, "G3", "FAIL")
    elif problem == "g2_wrong_skip":
        gate(tmp_path, run_id, "G2", "SKIPPED", reason="wrong reason")
    elif problem in ("g1_fail", "g2_fail", "g2_pass", "g3_later_fail"):
        which = {"g1_fail": "G1", "g2_fail": "G2", "g2_pass": "G2",
                 "g3_later_fail": "G3"}[problem]
        gate(tmp_path, run_id, which, "PASS" if problem == "g2_pass" else "FAIL",
             [state["artifacts"][0]["payload"]["artifact_id"]] if problem == "g2_pass" else [])
    elif problem == "stale_g3":
        gate(tmp_path, run_id, "G1", "PASS", state["gate_outcomes"][0]["payload"]["evidence"])
    else:
        g3 = next(r for r in state["gate_outcomes"] if r["payload"]["gate_id"] == "G3")
        _, saved = G4["artifact_json"](state, tmp_path, g3["payload"]["evidence"][0])
        if problem == "fake_evidence":
            saved = {}
        elif problem == "g3_digest_mismatch":
            saved["exchanges"][0]["response_sha256"] = "0" * 64
        elif problem == "g3_detail_mismatch":
            saved["capabilities"][0]["purpose"] = "modified after discovery"
        elif problem == "g3_other_target":
            saved["target"] = "http://127.0.0.1:1"
        else:
            saved["capabilities"] = []
        source = tmp_path / "unsuitable.json"
        source.write_text(json.dumps(saved), encoding="utf-8")
        a = RunStore(tmp_path).artifact(run_id, {"label": "unsuitable G3", "path": str(source)})
        gate(tmp_path, run_id, "G3", "PASS", [a["payload"]["artifact_id"]])
    # Even ResearchPlan construction is forbidden until prerequisites are satisfied.
    with patch.dict(G4["record_g4"].__globals__, {
            "ResearchPlan": lambda **kw: pytest.fail("must not construct plan"),
            "preview_plan": lambda p: pytest.fail("must not preview")}):
        report = attempt(tmp_path, run_id)
    assert report["result"]["status"] == "BLOCKED"
    assert report["result"]["workflow"] is None
    assert report["frozen"] is None


@pytest.mark.parametrize(("path", "value"), [
    (("research_plan", "subjects"), []),
    (("research_plan", "subjects"), ["000852"]),
    (("research_plan", "horizons"), [True]),
    (("research_plan", "horizons"), [0]),
    (("research_plan", "horizons"), []),
    (("research_plan", "windows"), []),
    (("research_plan", "metric_parameters"), {"made_up": 1}),
    (("research_plan", "on_job_failure"), "invented"),
    (("research_plan", "analysis_requests"), []),
    (("capability_id",), "undiscovered"),
    (("original_objective",), ""),
    (("input_resolution", "reference"), ""),
    (("execution_surface",), "http"),
    (("research_plan", "windows"), [{"start_date": "2026-10-28", "end_date": "2010-01-01"}]),
    (("research_plan", "windows"), [{"start_date": "20100101", "end_date": "2026-10-28"}]),
])
def test_invalid_or_missing_intent_has_no_defaults(tmp_path, path, value):
    run_id = discovered(tmp_path)
    draft = candidate()
    target = draft
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    report = attempt(tmp_path, run_id, draft)
    assert report["result"]["status"] == "FAIL"
    assert report["result"]["candidate"] == draft
    assert report["result"]["workflow"] is None
    if path == ("execution_surface",):
        assert "HTTP selection is rejected" in report["result"]["reason"]
        assert report["result"]["candidate"]["research_plan"]["windows"] == (
            candidate()["research_plan"]["windows"])


@pytest.mark.parametrize("field", sorted(G4["PLAN_FIELDS"]))
def test_every_plan_field_is_required(tmp_path, field):
    run_id = discovered(tmp_path)
    draft = candidate()
    del draft["research_plan"][field]
    assert attempt(tmp_path, run_id, draft)["result"]["status"] == "FAIL"


@pytest.mark.parametrize("spec", [
    {"method": "mean"}, {"method": "quantile"}, {"method": "quantile", "points": [0.5, 0.1]},
    {"method": "quantile", "points": [True]}, {"method": "quantile", "points": [-0.1]},
    {"method": "interval_count", "edges": [0, 0], "unit": "decimal_ratio"},
    {"method": "interval_count", "edges": [0, 1], "unit": "percent"},
    {"method": "interval_count", "edges": [0, 1]},
    {"method": "quantile", "points": [0.5], "extra": 1},
])
def test_public_statistical_validation_and_no_unsupported_method_defaults(tmp_path, spec):
    run_id = discovered(tmp_path)
    draft = candidate()
    draft["research_plan"]["analysis_requests"][0]["spec"] = spec
    result = attempt(tmp_path, run_id, draft)["result"]
    assert result["status"] == "FAIL"
    if spec == {"method": "quantile", "points": [-0.1]}:
        assert result["reason"].startswith("InvalidStatisticalSpec:")


def test_pure_public_preview_preserves_owner_expansion_and_has_no_market_cache_io(tmp_path,
                                                                              monkeypatch):
    import httpx

    import market_statistics
    from market_research.descriptive import execution
    from market_research.descriptive.cases import trailing_return
    from market_statistics import validate_spec

    run_id = discovered(tmp_path / "runs")
    public_preview = execution.preview_plan
    seen = []

    def forbidden(*args, **kwargs):
        raise AssertionError("No execution, preparation, acquisition, network or numerical compute")

    def observe(plan):
        for request in plan.analysis_requests:
            validate_spec(request.spec)
        result = public_preview(plan)
        seen.append(result)
        return result

    monkeypatch.setattr(execution, "execute_batch", forbidden)
    monkeypatch.setattr(execution, "execute_job", forbidden)
    monkeypatch.setattr(trailing_return, "prepare_inputs", forbidden)
    monkeypatch.setattr(httpx.Client, "request", forbidden)
    monkeypatch.setattr(market_statistics, "compute", forbidden)
    # Guard the aliases actually used by Research execution/preparation, not only facades.
    preparation = sys.modules["market_research.descriptive.cases.trailing_return.preparation"]
    monkeypatch.setattr(preparation, "create_calendar_service", forbidden)
    monkeypatch.setattr(preparation, "create_index_service", forbidden)
    monkeypatch.setattr(sys.modules["market_research.descriptive.execution.api"],
                        "prepare_inputs", forbidden)
    # Block opening any file outside intended Workbench evidence and authority reads.
    original_open = __import__("builtins").open

    def guarded_open(file, mode="r", *args, **kwargs):
        path = Path(file).resolve()
        if any(char in mode for char in "wax+"):
            assert path.is_relative_to(tmp_path), f"Unexpected write: {path}"
        if path.suffix in (".db", ".sqlite", ".sqlite3"):
            pytest.fail("Preview must not open market caches")
        return original_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)
    monkeypatch.setattr("sqlite3.connect", forbidden)
    # Temporary evidence files are inside the test workspace as well.
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    draft = candidate()
    draft["research_plan"]["subjects"] += ["000300.SH"]
    draft["research_plan"]["horizons"] += [5]
    draft["research_plan"]["windows"] += [{"start_date": "2020-01-01", "end_date": "2020-12-31"}]
    with patch.dict(G4["record_g4"].__globals__, {"preview_plan": observe}):
        report = attempt(tmp_path / "runs", run_id, draft)
    assert report["result"]["status"] == "PASS"
    assert report["frozen"]["preview"] == G4["preview_json"](seen[0])
    assert len(seen[0].jobs) == 8
    assert seen[0].analysis_attempt_count == 16
    assert sorted(p.name for p in tmp_path.iterdir()) == ["runs"]


def test_corruption_replacement_ambiguous_pass_and_latest_failure_rejected(tmp_path):
    run_id = discovered(tmp_path)
    report = attempt(tmp_path, run_id)
    frozen = report["frozen"]
    gate(tmp_path, run_id, "G4", "FAIL")
    with pytest.raises(ValueError, match="latest G4 PASS"):
        G4["read_frozen"](tmp_path, run_id)
    gate(tmp_path, run_id, "G4", "PASS", [frozen[k]["artifact_id"] for k in (
        "workflow_artifact", "preview_artifact", "attempt_artifact")])
    with pytest.raises(ValueError, match="Exactly one"):
        G4["read_frozen"](tmp_path, run_id)
    (tmp_path / run_id / frozen["workflow_artifact"]["stored_path"]).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="digest"):
        G4["read_frozen"](tmp_path, run_id)


def test_unrelated_artifacts_cannot_become_workflow_and_later_g3_fail_revokes_eligibility(tmp_path):
    run_id = discovered(tmp_path)
    attempt(tmp_path, run_id)
    gate(tmp_path, run_id, "G3", "FAIL")
    with pytest.raises(ValueError, match="Latest G3"):
        G4["read_frozen"](tmp_path, run_id)
    another = discovered(tmp_path)
    state = RunStore(tmp_path).read(another)
    unrelated = state["artifacts"][0]["payload"]["artifact_id"]
    gate(tmp_path, another, "G4", "PASS", [unrelated])
    with pytest.raises(ValueError, match="bind workflow"):
        G4["read_frozen"](tmp_path, another)


@pytest.mark.parametrize("changed", ["preview", "authorization", "candidate", "reference"])
def test_fresh_reader_rejects_semantically_mismatched_but_hash_valid_evidence(tmp_path, changed):
    run_id = discovered(tmp_path)
    store = RunStore(tmp_path)
    state = store.read(run_id)
    required = G4["prerequisites"](state, tmp_path)
    draft = candidate()
    workflow, preview = G4["freeze"](draft, state, required)
    if changed == "preview":
        preview["planned_count"] += 1
    if changed == "authorization":
        workflow["execution_authorization"]["status"] = "granted"
    pa = G4["save"](store, run_id, str(tmp_path), "actual Preview", preview)
    workflow["preview"] = G4["reference"](pa)
    wa = G4["save"](store, run_id, str(tmp_path), "workflow", workflow)
    if changed == "candidate":
        draft["research_plan"]["horizons"] = [5]
    report = {"schema_version": 1, "task_id": "historical_return_observation",
              "task_version": "1", "g5_executed": False, "reason_code": "workflow_frozen",
              "reason": "synthetic subsequent failure",
              "status": "PASS", "gate_id": "G4", "run_id": run_id,
              "prerequisites": required, "candidate": draft,
              "workflow": G4["reference"](wa), "preview": G4["reference"](pa)}
    if changed == "reference":
        report["workflow"]["sha256"] = "0" * 64
    ra = G4["save"](store, run_id, str(tmp_path), "attempt", report)
    gate(tmp_path, run_id, "G4", "PASS", [a["artifact_id"] for a in (wa, pa, ra)])
    store.read(run_id)  # All same-Run hashes and registrations are valid.
    with pytest.raises(ValueError, match="association mismatch"):
        G4["read_frozen"](tmp_path, run_id)


def test_http_selection_and_preview_failure_never_freeze_or_receive_defaults(tmp_path):
    run_id = discovered(tmp_path)
    draft = candidate()
    draft["execution_surface"] = "http"
    with patch.dict(G4["record_g4"].__globals__, {
            "preview_plan": lambda p: pytest.fail("HTTP must fail before preview")}):
        assert attempt(tmp_path, run_id, draft)["result"]["status"] == "FAIL"
    with patch.dict(G4["record_g4"].__globals__, {
            "preview_plan": lambda p: (_ for _ in ()).throw(ValueError("test preflight failure"))}):
        result = attempt(tmp_path, run_id)["result"]
    assert result["status"] == "FAIL"
    assert "test preflight failure" in result["reason"]
    assert result["preview"] is None and result["workflow"] is None


def test_task_mismatch_busy_and_concurrent_change_do_not_publish_pass(tmp_path):
    run_id = discovered(tmp_path)
    state = RunStore(tmp_path).read(run_id)
    task = copy.deepcopy(state["manifest"]["task"])
    task["version"] = "2"
    other = RunStore(tmp_path).create({"task": task, "original_request": "test",
                                      "resolved_inputs": {}})
    with pytest.raises(ValueError, match="Unsupported Task"):
        attempt(tmp_path, other["run_id"])
    lock = tmp_path / run_id / ".g4-writer"
    lock.mkdir()
    with pytest.raises(FileExistsError):
        attempt(tmp_path, run_id)
    lock.rmdir()
    real_preview = G4["preview_plan"]

    def concurrent(plan):
        preview = real_preview(plan)
        RunStore(tmp_path).event(run_id, {"operation": "concurrent change", "details": {}})
        return preview

    with patch.dict(G4["record_g4"].__globals__, {"preview_plan": concurrent}):
        with pytest.raises(ValueError, match="Run changed"):
            attempt(tmp_path, run_id)
    assert not lock.exists()
    assert all(r["payload"]["gate_id"] != "G4"
               for r in RunStore(tmp_path).read(run_id)["gate_outcomes"])


def test_cli_pass_fail_blocked_and_fresh_read(tmp_path):
    for status, code in (("PASS", 0), ("FAIL", 1), ("BLOCKED", 2)):
        run_id = discovered(tmp_path)
        value = candidate()
        if status == "FAIL":
            value["execution_surface"] = "http"
        if status == "BLOCKED":
            gate(tmp_path, run_id, "G3", "FAIL")
        path = tmp_path / "draft.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        command = [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--run", run_id]
        done = subprocess.run(command + ["--candidate", str(path)], capture_output=True,
                              text=True, timeout=20)
        assert done.returncode == code, done.stderr
        report = json.loads(done.stdout)
        assert report["result"]["status"] == status
        read = subprocess.run(command + ["--read"], capture_output=True, text=True, timeout=20)
        assert read.returncode == (0 if status == "PASS" else 1)
        assert "Traceback" not in read.stderr
