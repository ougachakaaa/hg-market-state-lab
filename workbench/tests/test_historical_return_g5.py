"""Authorized G5 acceptance using actual public Research and Statistics with service fakes."""

import copy
import hashlib
import json
import subprocess
import sys
from unittest.mock import patch

import pytest
from g5_fixtures import (
    CODE,
    G4,
    G5,
    TASK_DIR,
    authorization,
    execute,
    fresh_read,
    frozen_run,
    isolated_services,
)
from support import RunStore
from test_historical_return_g4 import discovered, gate

from market_research.descriptive import execution
from market_statistics import CalculationFailure, compute


@pytest.fixture(autouse=True)
def no_default_services(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("No real service factory or default cache is permitted in WB-05")
    preparation = sys.modules["market_research.descriptive.cases.trailing_return.preparation"]
    monkeypatch.setattr(preparation, "create_calendar_service", forbidden)
    monkeypatch.setattr(preparation, "create_index_service", forbidden)
    monkeypatch.setattr("sqlite3.connect", forbidden)


def test_actual_success_exact_plan_one_call_durable_intent_and_fresh_read(tmp_path):
    run_id = frozen_run(tmp_path)
    before = RunStore(tmp_path).read(run_id)
    frozen = G4["read_frozen"](tmp_path, run_id)
    seen = []

    def invoke(plan):
        state = RunStore(tmp_path).read(run_id)
        assert len(G5["intents"](state)) == 1
        intent = G5["intents"](state)[0]["payload"]["details"]
        assert intent["challenge"]["workflow"] == frozen["workflow_artifact"]
        assert G4["plain"](plan) == frozen["workflow"]["research_plan"]
        batch = execution.execute_batch(plan)
        seen.append(batch)
        return batch

    with isolated_services():
        report = execute(tmp_path, run_id, invoke=invoke)
    assert report["result"]["status"] == "PASS" and len(seen) == 1
    done, read = fresh_read(tmp_path, run_id)
    assert done.returncode == 0 and read["integrity_verified"] is True
    output = read["batch_result"]
    assert output == G5["OUTPUT"]["batch_json"](seen[0], seen[0].plan)
    observation = output["job_results"][0]["observation_set"]
    assert observation["eligible_count"] == 3
    assert observation["candidate_count"] == 3
    assert observation["provenance"]["input_profile"] == "trailing_return_inputs_v2"
    import base64
    canonical = base64.b64decode(observation["provenance"]["canonical_input_bytes"]["value"])
    assert hashlib.sha256(canonical).hexdigest() == observation["provenance"]["input_fingerprint"]
    assert output["job_results"][0]["projection"]["numeric_sample"]["unit"] == "decimal_ratio"
    after = RunStore(tmp_path).read(run_id)
    assert after["manifest"] == before["manifest"]
    assert after["records"][:len(before["records"])] == before["records"]
    assert G4["read_frozen"](tmp_path, run_id) == frozen
    for r in after["artifacts"]:
        a = r["payload"]
        assert hashlib.sha256((tmp_path / run_id / a["stored_path"]).read_bytes()).hexdigest() == (
            a["sha256"])
    with patch.object(execution, "execute_batch", side_effect=AssertionError("no retry")):
        retry = execute(tmp_path, run_id)
    assert retry["result"]["status"] == "BLOCKED"
    assert G5["read_execution"](tmp_path, run_id)["status"] == "PASS"


@pytest.mark.parametrize("problem", ["missing_g4", "g4_fail", "g1_fail", "g2_fail", "g3_fail",
                                     "g4_later_fail", "ambiguous_g4", "workflow", "preview"])
def test_prerequisites_and_tampering_prevent_authorization_and_invocation(tmp_path, problem):
    run_id = discovered(tmp_path) if problem == "missing_g4" else frozen_run(tmp_path)
    if problem in ("g4_fail", "g4_later_fail", "g1_fail", "g2_fail", "g3_fail"):
        gate(tmp_path, run_id, problem[:2].upper(), "FAIL")
    elif problem == "ambiguous_g4":
        evidence = RunStore(tmp_path).read(run_id)["gate_outcomes"][-1]["payload"]["evidence"]
        gate(tmp_path, run_id, "G4", "PASS", evidence)
    elif problem in ("workflow", "preview"):
        frozen = G4["read_frozen"](tmp_path, run_id)
        artifact = frozen[problem + "_artifact"]
        (tmp_path / run_id / artifact["stored_path"]).write_bytes(b"altered")
    def forbidden(*args):
        pytest.fail("No authorization or invocation before prerequisites")
    if problem in ("workflow", "preview"):
        with pytest.raises(ValueError, match="digest"):
            execute(tmp_path, run_id, invoke=forbidden, authorize=forbidden)
    else:
        result = execute(tmp_path, run_id, invoke=forbidden, authorize=forbidden)
        assert result["result"]["status"] == "BLOCKED"


@pytest.mark.parametrize("problem", ["none", "empty", "other_workflow", "other_hash", "objective",
    "surface", "effects", "missing_reference", "missing_budget", "missing_isolation", "wrong_kind"])
def test_missing_or_inappropriate_authorization_blocks(tmp_path, problem):
    run_id = frozen_run(tmp_path)
    def authorize(challenge):
        if problem == "none":
            return None
        if problem == "empty":
            return {}
        a = authorization(challenge)
        changes = {"other_workflow": ("workflow", "artifact_id"),
                   "other_hash": ("workflow", "sha256")}
        if problem in changes:
            parent, key = changes[problem]
            a["approved_challenge"][parent][key] = "changed"
        elif problem in ("objective", "surface", "effects"):
            key = {"objective": "original_objective", "surface": "execution_surface",
                   "effects": "potential_side_effects"}[problem]
            a["approved_challenge"][key] = "changed"
        elif problem.startswith("missing_"):
            key = {"missing_reference": "source_reference", "missing_budget": "resource_budget",
                   "missing_isolation": "data_isolation"}[problem]
            a[key] = ""
        elif problem == "wrong_kind":
            a["source_kind"] = "agent_approval_file"
        return a
    result = execute(tmp_path, run_id, authorize=authorize,
                     invoke=lambda p: pytest.fail("unauthorized invocation"))
    assert result["result"]["status"] == "BLOCKED"
    assert not G5["intents"](RunStore(tmp_path).read(run_id))


def test_live_wrapper_rejects_synthetic_and_noninteractive_cli(tmp_path):
    run_id = frozen_run(tmp_path)
    with patch.object(execution, "execute_batch", side_effect=AssertionError("not authorized")):
        report = G5["record_g5"](tmp_path, run_id, authorize=authorization)
    assert report["result"]["status"] == "BLOCKED"
    done = subprocess.run([sys.executable, str(TASK_DIR / "record_g5.py"), "--root", str(tmp_path),
                           "--run", run_id], capture_output=True, text=True, timeout=20)
    assert done.returncode == 2 and json.loads(done.stdout)["result"]["status"] == "BLOCKED"
    assert not G5["intents"](RunStore(tmp_path).read(run_id))
    with pytest.raises(ValueError, match="Synthetic"):
        G5["_record_g5"](tmp_path, run_id, authorize=authorization,
                         invoke=execution.execute_batch, context="synthetic_test")


def test_live_authorization_requires_real_source_kind_and_verbatim_bound_statement(tmp_path):
    run_id = frozen_run(tmp_path)
    challenge = G5["challenge_for"](G4["read_frozen"](tmp_path, run_id))
    auth = authorization(challenge, "user_message")
    with pytest.raises(ValueError, match="explicitly approve"):
        G5["validate_authorization"](auth, challenge, "live")
    auth["user_statement"] = G5["approval_sentence"](challenge)
    assert G5["validate_authorization"](auth, challenge, "live") == auth
    auth["source_kind"] = "synthetic_test"
    with pytest.raises(ValueError, match="Trustworthy"):
        G5["validate_authorization"](auth, challenge, "live")


def test_live_wrapper_uses_trusted_host_callback_with_isolated_simulated_user(tmp_path):
    # Explicitly isolated test of the production path, never reusable consent for a real Run.
    run_id = discovered(tmp_path)
    from test_historical_return_g4 import candidate
    draft = candidate()
    draft["original_objective"] = (
        "Isolated simulated user request: compute index 000852.SH trailing returns with H=21 "
        "over 2010-01-01..2026-10-28, quartiles and the explicit decimal_ratio bins; "
        "use the full Python plan with continue policy and public-service fakes only.")
    draft["input_resolution"] = {"kind": "user_interaction",
                                  "reference": "isolated simulated user request"}
    G4["record_g4"](tmp_path, run_id, draft)
    def host(challenge):
        auth = authorization(challenge, "user_message")
        auth["user_statement"] = G5["approval_sentence"](challenge)
        return auth
    original = execution.execute_batch
    with (
        isolated_services(long=True),
        patch.object(execution, "execute_batch", wraps=original) as spy,
    ):
        report = G5["record_g5"](tmp_path, run_id, authorize=host)
    assert report["result"]["status"] == "PASS" and spy.call_count == 1


@pytest.mark.parametrize("empty", [False, True])
def test_partial_index_facts_preserve_actual_coverage_and_zero_eligible_failure(tmp_path, empty):
    run_id = frozen_run(tmp_path)
    with isolated_services(missing=True, empty=empty) as (_, idx):
        report = execute(tmp_path, run_id)
    expected = "FAIL" if empty else "PASS"
    assert report["result"]["status"] == expected
    done, read = fresh_read(tmp_path, run_id)
    assert done.returncode == (1 if empty else 0)
    job = read["batch_result"]["job_results"][0]
    obs = job["observation_set"]
    assert obs["candidate_count"] == 3
    assert obs["unavailable_count"] == (3 if empty else 2)
    assert obs["eligible_count"] == (0 if empty else 1)
    assert obs["market_fact_coverage"]["overall"]["ratio"] == (0 if empty else 4 / 5)
    assert obs["observation_coverage"] == (0 if empty else 1 / 3)
    assert [c[0] for c in idx.calls] == ["export", "ensure", "export"]
    if empty:
        assert job["failures"][0]["failure_category"] == "NoEligibleObservations"
        assert all(o["status"] == "not_attempted" for o in job["analysis_outcomes"])


@pytest.mark.parametrize("policy", ["continue", "stop"])
def test_failed_analysis_partial_batch_and_skips_never_false_pass(tmp_path, policy):
    run_id = frozen_run(tmp_path, subjects=[CODE, "000300.SH", "000852.SH"], policy=policy)
    calls = 0
    def calculate(sample, spec):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise CalculationFailure("quantile", "synthetic second Job failure")
        return compute(sample, spec)
    with isolated_services(), patch("market_research.descriptive.execution.api.compute",
                                    side_effect=calculate):
        report = execute(tmp_path, run_id)
    assert report["result"]["status"] == "FAIL"
    output = G5["read_execution"](tmp_path, run_id)["batch_result"]
    assert output["status"] == "partial_success"
    assert output["failed_count"] == 1
    assert output["success_count"] == (2 if policy == "continue" else 1)
    assert output["skipped_count"] == (0 if policy == "continue" else 1)
    assert calls == (6 if policy == "continue" else 4)
    assert [o["status"] for o in output["job_results"][1]["analysis_outcomes"]] == [
        "failed", "success"]
    assert output["job_results"][1]["observation_set"]["eligible_count"] == 3


@pytest.mark.parametrize("failure", ["exception", "keyboard", "unknown_result", "publication"])
def test_uncertain_attempt_never_retries_and_fresh_read_finds_intent(tmp_path, failure):
    run_id = frozen_run(tmp_path)
    calls = 0
    def invoke(plan):
        nonlocal calls
        calls += 1
        if failure == "keyboard":
            raise KeyboardInterrupt
        if failure == "exception":
            raise RuntimeError("SECRET_TOKEN must never be recorded")
        if failure == "unknown_result":
            return object()
        return execution.execute_batch(plan)
    original_save = G5["save"]
    def failing_save(store, rid, directory, name, value):
        if name == "G5 actual BatchResult":
            raise OSError("disk failure")
        return original_save(store, rid, directory, name, value)
    with isolated_services(), patch.dict(G5["_record_g5"].__globals__, {
            "save": failing_save if failure == "publication" else original_save}):
        if failure in ("keyboard", "publication"):
            with pytest.raises(KeyboardInterrupt if failure == "keyboard" else OSError):
                execute(tmp_path, run_id, invoke=invoke)
        else:
            assert execute(tmp_path, run_id, invoke=invoke)["result"]["status"] == "BLOCKED"
    assert calls == 1
    done, read = fresh_read(tmp_path, run_id)
    assert done.returncode == 2 and read["execution_state"] == "uncertain"
    assert execute(tmp_path, run_id, invoke=invoke)["result"]["status"] == "BLOCKED"
    assert calls == 1
    assert "SECRET_TOKEN" not in json.dumps(RunStore(tmp_path).read(run_id))
    for path in (tmp_path / run_id / "blobs").iterdir():
        assert b"SECRET_TOKEN" not in path.read_bytes()


def test_full_history_no_partition_or_truncation_one_public_batch_call(tmp_path):
    run_id = frozen_run(tmp_path, long=True)
    original = execution.execute_batch
    calls = []
    def invoke(plan):
        calls.append(plan)
        return original(plan)
    with isolated_services(long=True):
        assert execute(tmp_path, run_id, invoke=invoke)["result"]["status"] == "PASS"
    assert len(calls) == 1 and calls[0].horizons == (21,)
    window = calls[0].windows[0]
    assert window.start_date.isoformat() == "2010-01-01"
    assert window.end_date.isoformat() == "2026-10-28"
    read = G5["read_execution"](tmp_path, run_id)
    assert read["batch_result"]["planned_count"] == 1
    assert read["batch_result"]["plan"]["windows"][0]["start_date"] == "2010-01-01"


def test_output_projection_never_stringifies_unknown_objects_or_exception_text():
    class Unsafe:
        def __repr__(self):
            pytest.fail("No unsafe representation")
    output = G5["OUTPUT"]
    assert "omitted" in output["public_value"](Unsafe())
    from market_research.descriptive.cases.trailing_return import InputAttempt
    attempt = InputAttempt(Unsafe(), Unsafe(), {"password": "SECRET"}, RuntimeError("SECRET"))
    assert "SECRET" not in json.dumps(output["public_value"](attempt))
    assert output["public_value"](-0.0) == -0.0


def test_read_rejects_corrupt_result_and_forged_gate(tmp_path):
    run_id = frozen_run(tmp_path)
    with isolated_services():
        report = execute(tmp_path, run_id)
    read = G5["read_execution"](tmp_path, run_id)
    gate(tmp_path, run_id, "G5", "PASS", report["outcome"]["payload"]["evidence"])
    with pytest.raises(ValueError, match="Ambiguous"):
        G5["read_execution"](tmp_path, run_id)
    path = tmp_path / run_id / read["result_artifact"]["stored_path"]
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="digest"):
        G5["read_execution"](tmp_path, run_id)


def test_busy_and_authorization_time_concurrent_change_prevent_invocation(tmp_path):
    run_id = frozen_run(tmp_path)
    lock = tmp_path / run_id / ".g5-writer"
    lock.mkdir()
    with pytest.raises(FileExistsError):
        execute(tmp_path, run_id)
    lock.rmdir()
    def concurrent(challenge):
        RunStore(tmp_path).event(run_id, {"operation": "concurrent writer", "details": {}})
        return authorization(challenge)
    with pytest.raises(ValueError, match="Run changed"):
        execute(tmp_path, run_id, authorize=concurrent,
                invoke=lambda plan: pytest.fail("concurrent invocation"))
    assert not G5["intents"](RunStore(tmp_path).read(run_id))


def test_read_verifies_semantic_result_plan_and_accounting(tmp_path):
    run_id = frozen_run(tmp_path)
    with isolated_services():
        execute(tmp_path, run_id)
    read = G5["read_execution"](tmp_path, run_id)
    preview = G4["read_frozen"](tmp_path, run_id)["preview"]
    for key, value in (("success_count", 20), ("status", "failed"), ("plan", {})):
        changed = copy.deepcopy(read["batch_result"])
        changed[key] = value
        with pytest.raises(ValueError):
            G5["OUTPUT"]["validate_output"](changed, preview)
    changed = copy.deepcopy(read["batch_result"])
    changed["plan"]["analysis_requests"][0]["spec"]["points"][0] = False
    with pytest.raises(ValueError, match="linkage"):
        G5["OUTPUT"]["validate_output"](changed, preview)


def test_concurrent_change_during_invocation_preserves_actual_result_but_no_pass(tmp_path):
    run_id = frozen_run(tmp_path)
    calls = 0
    def invoke(plan):
        nonlocal calls
        calls += 1
        batch = execution.execute_batch(plan)
        RunStore(tmp_path).event(run_id, {"operation": "independent writer", "details": {}})
        return batch
    with isolated_services():
        report = execute(tmp_path, run_id, invoke=invoke)
    assert report["result"]["status"] == "BLOCKED"
    read = G5["read_execution"](tmp_path, run_id)
    assert read["execution_state"] == "unfinalized"
    assert read["batch_result"]["status"] == "success"
    assert execute(tmp_path, run_id, invoke=invoke)["result"]["status"] == "BLOCKED"
    assert calls == 1


def test_terminal_confirmation_binds_objective_hash_surface_side_effects_and_constraints(
        tmp_path, monkeypatch):
    run_id = frozen_run(tmp_path)
    challenge = G5["challenge_for"](G4["read_frozen"](tmp_path, run_id))
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    sentence = G5["approval_sentence"](challenge)
    with patch("builtins.input", side_effect=[sentence, "maximum 0 paid calls", "isolated cache"]):
        auth = G5["interactive_authorization"](challenge)
    assert G5["validate_authorization"](auth, challenge, "live") == auth
    with patch("builtins.input", return_value="yes"):
        assert G5["interactive_authorization"](challenge) is None


def test_malformed_public_export_is_retained_safely_as_actual_failed_batch(tmp_path):
    from dataclasses import replace
    run_id = frozen_run(tmp_path)
    with isolated_services() as (calendar, _):
        calendar.transform = lambda view: replace(view, scope={"private_token": "SECRET"})
        report = execute(tmp_path, run_id)
    assert report["result"]["status"] == "FAIL"
    read = G5["read_execution"](tmp_path, run_id)
    assert read["batch_result"]["job_results"][0]["failures"][0][
        "failure_category"] == "InvalidPublicInput"
    assert "SECRET" not in json.dumps(read)


def test_unexpected_job_exception_retains_classification_without_exception_text(tmp_path):
    run_id = frozen_run(tmp_path)
    with isolated_services(), patch("market_research.descriptive.execution.api.compute",
                                    side_effect=RuntimeError("PRIVATE_SECRET")):
        assert execute(tmp_path, run_id)["result"]["status"] == "FAIL"
    read = G5["read_execution"](tmp_path, run_id)
    assert read["batch_result"]["job_results"][0]["failures"][0][
        "failure_category"] == "ExecutionFailure"
    assert "PRIVATE_SECRET" not in json.dumps(read)
