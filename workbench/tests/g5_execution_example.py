"""Standalone isolated deterministic WB-05 execution; no providers or default user caches."""

import json
from pathlib import Path
from unittest.mock import patch

from g5_fixtures import CODE, G4, G5, execute, fresh_read, frozen_run, isolated_services
from support import RunStore

from market_research.descriptive import execution
from market_statistics import CalculationFailure, compute


def run(root, scenario):
    subjects = [CODE, "000300.SH"] if scenario == "partial_batch" else [CODE]
    run_id = frozen_run(root, subjects=subjects, long=scenario == "long_window")
    before = RunStore(root).read(run_id)
    frozen = G4["read_frozen"](root, run_id)
    calls = 0
    computations = 0
    actual = None

    def calculate(sample, spec):
        nonlocal computations
        computations += 1
        if scenario == "partial_batch" and computations == 3:
            raise CalculationFailure("quantile", "isolated deterministic required-analysis failure")
        return compute(sample, spec)

    def invoke(plan):
        nonlocal calls, actual
        calls += 1
        assert G4["plain"](plan) == frozen["workflow"]["research_plan"]
        assert len(G5["intents"](RunStore(root).read(run_id))) == 1
        actual = execution.execute_batch(plan)
        return actual

    with isolated_services(missing=scenario == "partial_facts", long=scenario == "long_window"), (
        patch("market_research.descriptive.execution.api.compute", side_effect=calculate)
    ):
        report = execute(root, run_id, invoke=invoke)
    assert calls == 1 and actual is not None
    done, read = fresh_read(root, run_id)
    assert done.returncode == (1 if scenario == "partial_batch" else 0)
    assert read["batch_result"] == G5["OUTPUT"]["batch_json"](actual, actual.plan)
    after = RunStore(root).read(run_id)
    assert after["manifest"] == before["manifest"]
    assert after["records"][:len(before["records"])] == before["records"]
    output = read["batch_result"]
    return {"scenario": scenario, "run_id": run_id, "g5_status": read["status"],
            "execution_context": read["execution_context"], "execute_batch_call_count": calls,
            "statistics_call_count": computations,
            "original_evidence_unchanged": True, "fresh_process_read_verified": True,
            "workflow_artifact": read["workflow_artifact"],
            "authorization_artifact": read["authorization"],
            "result_artifact": read["result_artifact"], "report_artifact": read["report_artifact"],
            "result_path": f"{run_id}/{read['result_artifact']['stored_path']}",
            "batch_status": output["status"],
            "counts": {k: output[k] for k in (
                "planned_count", "success_count", "failed_count", "skipped_count")},
            "plan": output["plan"], "jobs": [{
                "job_identity": job["job_identity"], "status": job["status"],
                "population": {k: job["observation_set"][k] for k in (
                    "candidate_count", "eligible_count", "unavailable_count", "excluded_count",
                    "observation_coverage")},
                "fact_coverage": {name: job["observation_set"]["market_fact_coverage"][name][
                    "ratio"]
                                  for name in ("overall", "warm_up", "sample")},
                "input_fingerprint": job["observation_set"]["provenance"]["input_fingerprint"],
                "analyses": [{k: o[k] for k in (
                    "request", "status", "statistical_result", "failure")}
                             for o in job["analysis_outcomes"]],
            } for job in output["job_results"]],
            "gate_sequence": report["outcome"]["sequence"]}


def main():
    root = Path(__file__).resolve().parents[1] / ".runs"
    result = {"synthetic_only": True, "live_readiness": "not_verified",
              "provider_calls": 0, "default_cache_access": False,
              "cases": [run(root, s) for s in (
                  "success", "partial_batch", "partial_facts", "long_window")]}
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
