"""WB-06 isolated acceptance only. No live mode and no real execution consent.

Replays an Agent-authored candidate; this script is not a natural-language planner.
G1/G3 use the supplied backend. G5 uses only guarded public-service fixtures.
"""

import argparse
import copy
import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
from dataclasses import replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

from g5_fixtures import FIXTURES, G4, G5, execute, fresh_read, isolated_services
from support import RunStore

from market_research.descriptive import execution
from market_statistics import compute

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "workbench" / "tasks" / "historical_return_observation"
G1 = runpy.run_path(str(TASK / "runtime" / "record_g1.py"))
G3 = runpy.run_path(str(TASK / "runtime" / "record_g3.py"))
ORACLE = runpy.run_path(str(ROOT / "market_research" / "tests" / "live_e2e_acceptance.py"))


def save(root, run_id, label, value):
    with tempfile.TemporaryDirectory(prefix="wb06-evidence-") as folder:
        path = Path(folder) / "evidence.json"
        path.write_text(json.dumps(value, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        artifact = RunStore(root).artifact(run_id, {"label": label, "path": str(path)})["payload"]
    return G5["reference"](artifact)


def discover(root, target):
    result = G1["record_g1"](root, "WB-06 G1 readiness only; isolated acceptance follows; "
                              "no live authorization", target, 5)
    assert result["result"]["status"] == "PASS"
    run_id = result["run_id"]
    assert G3["record_g3"](root, run_id, 5)["result"]["status"] == "PASS"
    return run_id


def freeze(root, run_id, draft):
    state = RunStore(root).read(run_id)
    if not any(r["payload"]["gate_id"] == "G4" and r["payload"]["status"] == "PASS"
               for r in state["gate_outcomes"]):
        result = G4["record_g4"](root, run_id, draft)
        assert result["result"]["status"] == "PASS"
    frozen = G4["read_frozen"](root, run_id)
    done = subprocess.run([sys.executable, str(TASK / "runtime" / "record_g4.py"), "--root",
                           str(root),
                           "--run", run_id, "--read"], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == frozen
    assert frozen["workflow"]["research_plan"] == draft["research_plan"]
    assert frozen["preview"]["plan"] == draft["research_plan"]
    assert frozen["preview"]["planned_count"] == 1
    assert frozen["preview"]["analysis_attempt_count"] == 2
    return frozen


def fixture_services(draft, missing):
    """Dense artificial calendar; weekday choice is fixture data, not market inference."""
    plan = draft["research_plan"]
    code = plan["subjects"][0]
    end = date.fromisoformat(plan["windows"][0]["end_date"])
    sessions = tuple(d for d in FIXTURES["dates"](date(2009, 12, 1), end) if d.weekday() < 5)
    closes = {d: float(80 + ((7 * i) % 41)) for i, d in enumerate(sessions)}
    missing_day = date(2024, 1, 10)
    if missing:
        del closes[missing_day]
    cal = FIXTURES["CalendarFake"](sessions)
    idx = FIXTURES["IndexFake"](sessions, closes)
    idx.transform = lambda view: replace(view, records=tuple(
        replace(row, index_code=code, symbol=code.split(".")[0], name="中证1000",
                publisher="中证指数有限公司", category="规模指数") for row in view.records))
    if missing:
        # Public diagnostic identity must match this fixture's explicit index.
        original_ensure = idx.ensure

        def ensure(request):
            result = original_ensure(request)
            return replace(result, failures=tuple(
                replace(f, identity=(code, f.identity[1])) for f in result.failures))

        idx.ensure = ensure
    return cal, idx


def run_case(root, run_id, draft, *, missing=False):
    frozen = freeze(root, run_id, draft)
    before = RunStore(root).read(run_id)
    calls = computations = 0
    actual = None
    cal, idx = fixture_services(draft, missing)

    def invoke(plan):
        nonlocal calls, actual
        calls += 1
        assert G4["plain"](plan) == frozen["workflow"]["research_plan"]
        assert len(G5["intents"](RunStore(root).read(run_id))) == 1
        actual = execution.execute_batch(plan)
        return actual

    def calculate(sample, spec):
        nonlocal computations
        computations += 1
        return compute(sample, spec)

    # Existing simulated host refuses invocation outside its guarded fixture context.
    with (
        isolated_services(),
        patch("market_research.descriptive.cases.trailing_return.preparation.create_calendar_service",
              return_value=cal),
        patch("market_research.descriptive.cases.trailing_return.preparation.create_index_service",
              return_value=idx),
        patch("market_research.descriptive.execution.api.compute", side_effect=calculate),
    ):
        report = execute(root, run_id, invoke=invoke)
    assert calls == 1 and computations == 2 and actual is not None
    assert actual.status == "success" and report["result"]["status"] == "PASS"
    job = actual.job_results[0]
    # Independent published-Export oracle, using this job's full window instead of its
    # historical smoke-test window. It computes no Research/Statistics replacement output.
    with patch.dict(ORACLE["verify_job"].__globals__, {
            "WINDOW": job.fixed_job_spec.historical_sample_window}):
        oracle = ORACLE["verify_job"](job, actual.plan.analysis_requests)
    done, read = fresh_read(root, run_id)
    assert done.returncode == 0 and read["status"] == "PASS"
    assert read["batch_result"] == G5["OUTPUT"]["batch_json"](actual, actual.plan)
    after = RunStore(root).read(run_id)
    assert after["manifest"] == before["manifest"]
    assert after["records"][:len(before["records"])] == before["records"]
    obs = read["batch_result"]["job_results"][0]["observation_set"]
    summary = {
        "scenario": "injected_partial_facts" if missing else "complete_fixture",
        "synthetic_market_inputs": True, "real_user_consent": False,
        "run_id": run_id, "task_sha256": before["manifest"]["task_sha256"],
        "gates_at_completion": {r["payload"]["gate_id"]: r["payload"]["status"]
                                for r in after["gate_outcomes"]},
        "adapter_execution_context": read["execution_context"],
        "context_note": "live denotes ordinary adapter only; simulated host and fake services",
        "execute_batch_calls": calls, "statistics_calls": computations,
        "provider_calls": 0, "default_cache_access": False,
        "workflow_artifact": read["workflow_artifact"],
        "preview_artifact": frozen["preview_artifact"],
        "authorization_artifact": read["authorization"],
        "result_artifact": read["result_artifact"], "g5_report_artifact": read["report_artifact"],
        "plan": read["batch_result"]["plan"], "batch_status": actual.status,
        "job_status": job.status, "batch_counts": {k: read["batch_result"][k] for k in (
            "planned_count", "success_count", "failed_count", "skipped_count")},
        "population": {k: obs[k] for k in ("candidate_count", "eligible_count",
            "unavailable_count", "excluded_count", "observation_coverage")},
        "market_fact_coverage": {k: {field: obs["market_fact_coverage"][k][field]
            for field in ("expected_fact_units", "available_fact_units", "ratio")}
            for k in ("overall", "warm_up", "sample")},
        "input_profile": obs["provenance"]["input_profile"],
        "input_fingerprint": oracle["input_fingerprint"],
        "statistical_results": oracle["statistical_results"],
        "analysis_statuses": [o.status for o in job.analysis_outcomes],
        "independent_checks": oracle["independent_checks"],
        "association_checks": oracle["association_reference_checks"],
        "fresh_process_read_verified": True,
        "input_requests": {"calendar": G4["plain"](cal.calls), "index": G4["plain"](idx.calls)},
    }
    summary["inspection_artifact"] = save(root, run_id,
        "WB-06 independent output inspection", summary)
    # Expected injected failure is evidence of historical-read behavior, not a product defect.
    RunStore(root).gate(run_id, {"gate_id": "G3", "status": "FAIL", "evidence": [],
        "reason": "WB-06 expected injected later discovery failure; no production defect"})
    try:
        G4["read_frozen"](root, run_id)
    except ValueError:
        pass
    else:
        raise AssertionError("Current G4 eligibility must be revoked")
    history_before = RunStore(root).read(run_id)
    done, historical = fresh_read(root, run_id)
    assert done.returncode == 0 and historical["batch_result"] == read["batch_result"]
    assert RunStore(root).read(run_id) == history_before
    assert calls == 1
    summary["later_g3_failure"] = "expected test injection; current eligibility revoked"
    summary["historical_result_still_readable"] = True
    summary["history_check_artifact"] = save(root, run_id, "WB-06 historical read verification", {
        "expected_injected_g3_fail": True, "current_g4_ineligible": True,
        "fresh_process_g5_read": "PASS", "original_result_unchanged": True,
        "execute_batch_calls": calls})
    return summary


def no_consent(root, target, draft):
    run_id = discover(root, target)
    frozen = freeze(root, run_id, draft)
    with patch.object(execution, "execute_batch", side_effect=AssertionError("No consent")):
        result = G5["record_g5"](root, run_id, authorize=lambda challenge: None)
    state = RunStore(root).read(run_id)
    assert result["result"]["status"] == "BLOCKED" and not G5["intents"](state)
    return {"run_id": run_id, "status": result["result"]["status"],
            "reason": result["result"]["reason"], "workflow_artifact": frozen["workflow_artifact"],
            "intent_count": 0, "execute_batch_calls": 0, "real_user_consent": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--run", help="Already G1/G3-verified Run; never an executed Run")
    parser.add_argument("--root", type=Path, default=ROOT / "workbench" / ".runs")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    draft = json.loads(args.candidate.read_text(encoding="utf-8"))
    original = copy.deepcopy(draft)
    result = {"goal": "WB-06", "synthetic_only": True,
        "baseline": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "cases": [run_case(args.root, args.run or discover(args.root, args.base_url), draft),
                  run_case(args.root, discover(args.root, args.base_url), draft, missing=True)],
        "authorization_boundary": no_consent(args.root, args.base_url, draft),
        "live_full_history": "BLOCKED; operational budget and real consent not established"}
    assert draft == original
    args.output.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "runs": [c["run_id"] for c in result["cases"]],
                      "deterministic_e2e": "PASS", "live_full_history": "BLOCKED"}))


if __name__ == "__main__":
    main()
