"""Execute one explicitly authorized frozen G4 workflow; preserve and read back evidence."""

from __future__ import annotations

import argparse
import copy
import runpy
import sys
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from market_research.descriptive import execution

TASK_DIR = Path(__file__).resolve().parent
G4 = runpy.run_path(str(TASK_DIR / "record_g4.py"))
OUTPUT = runpy.run_path(str(TASK_DIR / "g5_output.py"))
RunStore, JSON, LOAD = G4["RunStore"], G4["JSON"], G4["LOAD"]
reference, save = G4["reference"], G4["save"]
SURFACE = "market_research.descriptive.execution.execute_batch"
INTENT, COMPLETED = "G5 execution intent", "G5 execution completed"
SIDE_EFFECTS = ["market-data acquisition", "DataLake cache writes", "possible paid-data access"]


def challenge_for(frozen: dict) -> dict:
    workflow = frozen["workflow"]
    return {"run_id": frozen["run_id"], "task_id": workflow["task_id"],
            "task_version": workflow["task_version"], "task_sha256": workflow["task_sha256"],
            "original_objective": workflow["original_objective"],
            "workflow": frozen["workflow_artifact"], "preview": frozen["preview_artifact"],
            "execution_surface": SURFACE, "potential_side_effects": SIDE_EFFECTS.copy()}


def validate_authorization(value: Any, challenge: dict, context: str) -> dict:
    """Validate evidence; synthetic context is retained solely for historical reads."""
    if context not in ("live", "synthetic_test"):
        raise ValueError("Unknown execution context")
    a = G4["exact"](value, {"source_kind", "source_reference", "user_statement",
                          "approved_challenge", "resource_budget", "data_isolation"},
                    "authorization")
    allowed = ("user_message", "interactive_terminal") if context == "live" else (
        "synthetic_test",)
    if a["source_kind"] not in allowed or JSON(a["approved_challenge"]) != JSON(challenge):
        raise ValueError("Trustworthy authorization for this exact workflow is required")
    for name in ("source_reference", "user_statement", "resource_budget", "data_isolation"):
        G4["text"](a[name], name)
    if context == "live" and a["user_statement"] != approval_sentence(challenge):
        raise ValueError("The actual user must explicitly approve the full bound challenge")
    return LOAD(JSON(a).encode())


def approval_sentence(challenge: dict) -> str:
    return (f"AUTHORIZE G5 {challenge['workflow']['artifact_id']} "
            f"{challenge['workflow']['sha256']} via {challenge['execution_surface']} "
            f"for {challenge['original_objective']} including "
            + ", ".join(challenge["potential_side_effects"]))


def interactive_authorization(challenge: dict) -> dict | None:
    if not sys.stdin.isatty():
        return None
    print(JSON(challenge), file=sys.stderr)
    sentence = approval_sentence(challenge)
    print("Approve the displayed objective and Python invocation by typing exactly:\n" + sentence,
          file=sys.stderr)
    supplied = input()
    if supplied != sentence:
        return None
    print("Resource budget declaration (calls/cost/history; not enforced here):", file=sys.stderr)
    budget = input()
    print("Isolation declaration (verify owner-approved controls before long-history live use; "
          "not enforced here):", file=sys.stderr)
    isolation = input()
    return {"source_kind": "interactive_terminal",
            "source_reference": "current terminal interaction",
            "user_statement": supplied, "approved_challenge": challenge,
            "resource_budget": budget, "data_isolation": isolation}


def intents(state: dict) -> list[dict]:
    return [r for r in state["events"] if r["payload"]["operation"] == INTENT]


def report_base(run_id: str) -> dict:
    return {"schema_version": 1, "task_id": "historical_return_observation", "task_version": "1",
            "run_id": run_id, "gate_id": "G5", "workflow": None, "authorization": None,
            "intent_sequence": None, "attempt_id": None, "execution_context": None,
            "result": None, "completion_sequence": None, "execution_state": "not_invoked"}


def finish(store: Any, run_id: str, directory: str, report: dict) -> dict:
    artifact = save(store, run_id, directory, "G5 execution report", report)
    evidence = [report[k]["artifact_id"] for k in ("authorization", "result") if report[k]]
    evidence.append(artifact["artifact_id"])
    outcome = store.gate(run_id, {"gate_id": "G5", "status": report["status"],
        "reason": report["reason"], "evidence": evidence})
    return {"run_id": run_id, "result": report, "report_artifact": reference(artifact),
            "outcome": outcome}


def record_g5(root: Path, run_id: str, *,
              authorize: Callable[[dict], Any] = interactive_authorization) -> dict:
    """Live adapter. Authorizer must resolve genuine user approval in its trusted host context."""
    store = RunStore(root)
    before = store.read(run_id)
    G4["require_task"](before)
    lock = root.resolve() / run_id / ".g5-writer"
    lock.mkdir()
    try:
        before = store.read(run_id)
        report = report_base(run_id)
        with tempfile.TemporaryDirectory(prefix="historical-return-g5-") as directory:
            if intents(before):
                report.update(status="BLOCKED", reason="Prior execution intent requires operator "
                              "reconciliation; no further invocation",
                              execution_state="prior_intent")
                return finish(store, run_id, directory, report)
            try:
                frozen = G4["read_frozen"](root, run_id)
            except (ValueError, TypeError, KeyError, IndexError, StopIteration):
                report.update(status="BLOCKED", reason="Verified eligible frozen G4 required")
                return finish(store, run_id, directory, report)
            challenge = challenge_for(frozen)
            report.update(workflow=frozen["workflow_artifact"], execution_context="live")
            if frozen["workflow"]["resolved_inputs"]["provenance"][
                    "kind"] == "synthetic_test":
                report.update(status="BLOCKED", reason="Synthetic planning fixtures cannot be "
                              "executed through the live surface; create a real authorized Run")
                return finish(store, run_id, directory, report)
            plan = G4["plan_from_json"](frozen["workflow"]["research_plan"])
            if JSON(G4["preview_json"](execution.preview_plan(plan))) != JSON(frozen["preview"]):
                raise ValueError("Reconstructed plan/Preview mismatch")
            try:
                authorization = validate_authorization(authorize(copy.deepcopy(challenge)),
                                                       challenge, "live")
            except Exception:
                report.update(status="BLOCKED", reason="Explicit trustworthy user authorization "
                              "for this frozen workflow is missing or inappropriate")
                return finish(store, run_id, directory, report)
            if store.read(run_id) != before:
                raise ValueError("Run changed before execution; no invocation")
            auth = save(store, run_id, directory, "G5 authorization", authorization)
            report["authorization"] = reference(auth)
            current = store.read(run_id)
            if (current["records"][:-1] != before["records"]
                    or current["records"][-1]["payload"] != auth):
                raise ValueError("Run changed before intent; no invocation")
            attempt_id = uuid.uuid4().hex
            details = {"attempt_id": attempt_id, "execution_context": "live",
                       "challenge": challenge, "authorization": reference(auth)}
            intent = store.event(run_id, {"operation": INTENT, "details": details})
            report.update(intent_sequence=intent["sequence"], attempt_id=attempt_id)
            prefix = store.read(run_id)
            if prefix["records"] != current["records"] + [intent]:
                raise ValueError("Run changed at intent; reconciliation required")
            try:
                # The sole invocation, after durable authorization and intent.
                batch = execution.execute_batch(plan)
                output = OUTPUT["batch_json"](batch, plan)
                status = OUTPUT["validate_output"](output, frozen["preview"])
            except Exception:
                report.update(status="BLOCKED", reason="Invocation outcome uncertain; operator "
                              "reconciliation required; no automatic retry",
                              execution_state="uncertain")
            else:
                changed = store.read(run_id) != prefix
                result = save(store, run_id, directory, "G5 actual BatchResult", {
                    "schema_version": 1, **details, "batch_result": output})
                completed = store.event(run_id, {"operation": COMPLETED, "details": {
                    **details, "intent_sequence": intent["sequence"], "result": reference(result)}})
                report.update(status=status, reason=("All requested computations succeeded; "
                    "coverage is reported without a completeness claim" if status == "PASS" else
                    "Research Batch contains failed or skipped requested computations"),
                    execution_state="completed", result=reference(result),
                    completion_sequence=completed["sequence"])
                if changed:
                    report.update(status="BLOCKED", reason="Run changed during invocation; "
                                  "actual result preserved; operator reconciliation required")
            return finish(store, run_id, directory, report)
    finally:
        lock.rmdir()


def read_execution(root: Path, run_id: str) -> dict:
    store = RunStore(root)
    state = store.read(run_id)
    G4["require_task"](state)
    attempts = intents(state)
    result_gates = [r for r in state["gate_outcomes"] if r["payload"]["gate_id"] == "G5"
                    and r["payload"]["status"] in ("PASS", "FAIL")]
    if result_gates and not attempts:
        raise ValueError("G5 outcome without an execution intent")
    if not attempts:
        return {"run_id": run_id, "status": "BLOCKED", "execution_state": "not_invoked",
                "integrity_verified": True}
    if len(attempts) != 1:
        raise ValueError("Exactly one execution intent is permitted")
    intent = attempts[0]
    # Validate the exact operational state bound to this historical invocation.
    # RunStore has already checked the integrity of every currently committed record.
    prefix = {**state, **{key: [r for r in state[key] if r["sequence"] < intent["sequence"]]
                         for key in ("records", "gate_outcomes", "events", "artifacts")}}
    frozen = G4["_read_frozen"](prefix, root)
    d = intent["payload"]["details"]
    challenge = challenge_for(frozen)
    if JSON(d["challenge"]) != JSON(challenge) or intent["sequence"] <= frozen["g4_sequence"]:
        raise ValueError("Intent/frozen workflow association mismatch")
    auth_ref, auth = G4["artifact_json"](state, root, d["authorization"]["artifact_id"])
    validate_authorization(auth, challenge, d["execution_context"])
    auth_record = next(r for r in state["artifacts"] if r["payload"] == auth_ref)
    if reference(auth_ref) != d["authorization"] or auth_record["sequence"] >= intent["sequence"]:
        raise ValueError("Authorization/intent association mismatch")
    completions = [r for r in state["events"] if r["payload"]["operation"] == COMPLETED]
    if len(completions) > 1:
        raise ValueError("Ambiguous execution completion")
    if not completions:
        if result_gates:
            raise ValueError("G5 outcome without a completed invocation")
        return {"run_id": run_id, "status": "BLOCKED", "execution_state": "uncertain",
                "intent": intent, "authorization": reference(auth_ref), "integrity_verified": True}
    completed = completions[0]
    c = completed["payload"]["details"]
    result_ref, result = G4["artifact_json"](state, root, c["result"]["artifact_id"])
    result_record = next(r for r in state["artifacts"] if r["payload"] == result_ref)
    if (JSON(c) != JSON({**d, "intent_sequence": intent["sequence"],
                         "result": reference(result_ref)})
            or JSON(result) != JSON({"schema_version": 1, **d,
                                     "batch_result": result["batch_result"]})
            or not intent["sequence"] < result_record["sequence"] < completed["sequence"]):
        raise ValueError("Invocation/result linkage mismatch")
    status = OUTPUT["validate_output"](result["batch_result"], frozen["preview"])
    gates = result_gates
    if not gates:
        return {"run_id": run_id, "status": "BLOCKED", "execution_state": "unfinalized",
                "intent": intent, "authorization": reference(auth_ref),
                "result_artifact": reference(result_ref), "batch_result": result["batch_result"],
                "integrity_verified": True}
    if len(gates) != 1:
        raise ValueError("Ambiguous G5 outcome")
    gate = gates[0]
    ids = gate["payload"]["evidence"]
    if len(ids) != 3 or ids[:2] != [auth_ref["artifact_id"], result_ref["artifact_id"]]:
        raise ValueError("G5 outcome evidence linkage mismatch")
    report_ref, report = G4["artifact_json"](state, root, ids[2])
    expected = {**report_base(run_id), "workflow": challenge["workflow"],
                "authorization": reference(auth_ref), "intent_sequence": intent["sequence"],
                "attempt_id": d["attempt_id"], "execution_context": d["execution_context"],
                "result": reference(result_ref), "completion_sequence": completed["sequence"],
                "execution_state": "completed", "status": status,
                "reason": gate["payload"]["reason"]}
    report_record = next(r for r in state["artifacts"] if r["payload"] == report_ref)
    if (JSON(report) != JSON(expected) or gate["payload"]["status"] != status
            or not completed["sequence"] < report_record["sequence"] < gate["sequence"]):
        raise ValueError("G5 report/outcome association mismatch")
    return {"run_id": run_id, "status": status, "execution_state": "completed",
            "execution_context": d["execution_context"], "intent": intent,
            "authorization": reference(auth_ref), "workflow_artifact": challenge["workflow"],
            "result_artifact": reference(result_ref), "report_artifact": reference(report_ref),
            "batch_result": result["batch_result"], "integrity_verified": True}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=G4["WORKBENCH"] / ".runs")
    parser.add_argument("--run", required=True)
    parser.add_argument("--read", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = (read_execution(args.root, args.run) if args.read else
                  record_g5(args.root, args.run))
        print(JSON(result))
        status = result["status"] if args.read else result["result"]["status"]
        return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[status]
    except (OSError, ValueError, TypeError, KeyError, IndexError, StopIteration):
        print("G5 storage or evidence validation failed; inspect preserved Run; do not retry "
              "an existing intent", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
