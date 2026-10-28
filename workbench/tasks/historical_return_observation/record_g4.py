"""Validate/freeze a Task-v1 Agent candidate, or read its exact accepted workflow."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import runpy
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any

from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.execution import ResearchPlan, preview_plan
from market_research.descriptive.observation import DateWindow
from market_statistics import IntervalCountSpec, QuantileSpec, StatisticalSpec

TASK_DIR = Path(__file__).resolve().parent
WORKBENCH = TASK_DIR.parents[1]
G3 = runpy.run_path(str(TASK_DIR / "check_capabilities.py"))
JSON = G3["G1"]["json_text"]
LOAD = G3["G1"]["_strict_json"]
RunStore = runpy.run_path(str(WORKBENCH / "run_store.py"))["RunStore"]
CAPABILITY = "trailing_cumulative_return_v1"
PLAN_FIELDS = {"metric", "metric_parameters", "subjects", "horizons", "windows",
               "analysis_requests", "on_job_failure"}
AUTHORIZATION = {
    "status": "pending",
    "required_before": "G5 execution of the exact frozen workflow artifact_id and sha256",
    "operations": ["Research execute_batch", "market-data acquisition",
                   "DataLake cache writes", "possible paid-data access"],
    "preview_grants_execution_authorization": False,
}
READINESS_GAPS = [
    "Canonical index syntax does not prove source membership.",
    "Historical SSE Calendar completeness and H-session warm-up are not probed.",
    "Full-window Index facts, credentials/permissions and compatible caches are not probed.",
    "Preview does not establish live availability or successful statistical results.",
    "G5 needs explicit user authorization for this exact frozen artifact identity/hash.",
]
OPERATIONS = [
    {"id": "authorize", "depends_on": [], "operation": "Obtain explicit G5 authorization"},
    {"id": "research", "depends_on": ["authorize"],
     "operation": "Delegate the complete plan once to public Research execute_batch",
     "delegated_order": ["prepare Calendar and Index inputs including warm-up",
                         "construct observations", "convert samples",
                         "compute requested Statistics and associate each result"],
     "requires_authorization": True},
    {"id": "retain", "depends_on": ["research"],
     "operation": "Preserve actual full results/failures and evidence in this Run"},
]
EXPECTED_OUTPUTS = [
    "Actual complete Batch/Job/analysis outcomes and statistical parameters/results/units",
    "Observation populations, coverage, warm-up, dependence and source provenance",
    "Same-Run result/evidence artifact identities, SHA-256 and locations; honest failures",
]
CASE_POLICY = {
    "authority": "market_research/descriptive/cases/trailing_return/ARCHITECTURE.md",
    "input_authority": "market_research/descriptive/cases/trailing_return/INPUTS.md",
    "source_binding": [
        {"dataset": "tushare_trade_calendar", "view": "calendar", "schema_version": 1,
         "calendar": "SSE"},
        {"dataset": "tushare_index_daily", "view": "index_daily", "schema_version": 1,
         "required_price": "close"},
    ],
    "input_policy": "descriptive_missing_tolerant_v1",
    "consumption": "Research Input Preparation alone consumes the bound DataLake public services; "
                   "export first, ensure an incomplete legal range once, final export proof",
    "calendar": "Complete Calendar including H preceding sessions is required; no shorter horizon",
    "missing_facts": "Legal partial Index exports are admissible; missing endpoints are "
                     "Unavailable, non-positive present endpoints Excluded; retain E/U/X coverage",
    "no_eligible_samples": "Conversion fails explicitly; no fabricated statistical result",
    "prohibitions": "No imputation, silent filtering, source fallback, date/horizon compression "
                    "or IID/causality/prediction/trading inference",
}


def plain(value: Any) -> Any:
    """Serialize public immutable carriers, preserving order and values."""
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, tuple | list):
        return [plain(v) for v in value]
    if type(value) is date:
        return value.isoformat()
    return value


def exact(value: Any, keys: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{name} requires exactly {', '.join(sorted(keys))}")
    return value


def text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be explicitly supplied as nonempty text")
    return value


def day(value: Any) -> date:
    if not isinstance(value, str):
        raise ValueError("Dates must be explicit YYYY-MM-DD strings")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Dates must be canonical YYYY-MM-DD strings")
    return parsed


def plan_from_json(value: Any) -> ResearchPlan:
    """Adapt explicit JSON to public types; owners validate all business/numerical rules."""
    p = exact(value, PLAN_FIELDS, "research_plan")
    for name in ("subjects", "horizons", "windows", "analysis_requests"):
        if not isinstance(p[name], list):
            raise ValueError(f"{name} must be an explicit ordered JSON array")
    windows = []
    for item in p["windows"]:
        w = exact(item, {"start_date", "end_date"}, "window")
        windows.append(DateWindow(day(w["start_date"]), day(w["end_date"])))
    analyses = []
    for item in p["analysis_requests"]:
        a = exact(item, {"request_id", "spec"}, "analysis request")
        s = a["spec"]
        if not isinstance(s, dict):
            raise ValueError("spec must be an explicit object")
        spec: StatisticalSpec
        if s.get("method") == "quantile":
            exact(s, {"method", "points"}, "quantile spec")
            spec = QuantileSpec(s["points"])
        elif s.get("method") == "interval_count":
            exact(s, {"method", "edges", "unit"}, "interval_count spec")
            spec = IntervalCountSpec(s["edges"], s["unit"])
        else:
            raise ValueError("Unsupported statistical method; no replacement is supplied")
        analyses.append(AnalysisRequest(a["request_id"], spec))
    return ResearchPlan(metric=p["metric"], metric_parameters=p["metric_parameters"],
                        subjects=p["subjects"], horizons=p["horizons"], windows=windows,
                        analysis_requests=analyses, on_job_failure=p["on_job_failure"])


def artifact_json(state: dict[str, Any], root: Path, artifact_id: str) -> tuple[dict, Any]:
    artifact = next(r["payload"] for r in state["artifacts"]
                    if r["payload"]["artifact_id"] == artifact_id)
    body = (root.resolve() / state["manifest"]["run_id"] / artifact["stored_path"]).read_bytes()
    return artifact, LOAD(body)


def prerequisites(state: dict[str, Any], root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"task_id": "historical_return_observation", "target": None}
    blocked = G3["_prerequisites"](state, root, result)
    if blocked:
        raise ValueError(G3["REASONS"][blocked])
    latest = {r["payload"]["gate_id"]: r for r in state["gate_outcomes"]}
    g3 = latest.get("G3")
    if not g3 or g3["payload"]["status"] != "PASS":
        raise ValueError("Latest G3 must PASS with preserved same-Run discovery evidence")
    for artifact_id in g3["payload"]["evidence"]:
        try:
            artifact, saved = artifact_json(state, root, artifact_id)
            if (saved["schema_version"] != 1 or saved["task_id"] != result["task_id"]
                    or saved["task_version"] != "1" or saved["gate_id"] != "G3"
                    or saved["status"] != "PASS" or saved["reason_code"] != "discovered"
                    or saved["target"] != result["target"]
                    or saved["prerequisites"] != result["prerequisites"]
                    or not saved["discovery_complete"] or not saved["task_readiness"]
                    or saved["missing_task_requirements"] != []
                    or g3["sequence"] <= max(result["prerequisites"]["g1_sequence"],
                                             result["prerequisites"]["g2_sequence"])):
                continue
            exchanges = saved["exchanges"]
            for e in exchanges:
                body = base64.b64decode(e["body_base64"], validate=True)
                if (e["error"] is not None or e["method"] != "GET"
                        or e["http_status"] != 200 or e["body_complete"] is not True
                        or e["content_type"].split(";", 1)[0].strip().lower()
                        != "application/json" or e["content_encoding"] not in ("", "identity")
                        or len(body) != e["response_bytes"] or len(body) > G3["MAX_BYTES"]
                        or hashlib.sha256(body).hexdigest() != e["response_sha256"]):
                    raise ValueError("Invalid preserved discovery exchange")
            catalog = G3["_validate"](exchanges[0], True)
            if catalog is None:
                continue
            ids = [d["id"] for d in catalog]
            if (len(set(ids)) != len(ids) or len(exchanges) != len(ids) + 1
                    or exchanges[0]["path"] != "/research/capabilities"
                    or saved["capability_ids"] != ids or saved["capability_count"] != len(ids)):
                continue
            details = []
            for id, e in zip(ids, exchanges[1:], strict=True):
                if e["path"] != "/research/capabilities/" + G3["quote"](id, safe=""):
                    raise ValueError("Discovery detail path mismatch")
                details.append(G3["_validate"](e, False))
            if JSON(details) != JSON(catalog) or JSON(details) != JSON(saved["capabilities"]):
                continue
            descriptor = next(d for d in details if d["id"] == CAPABILITY)
            if descriptor["status"] != "supported":
                continue
            return {**result["prerequisites"], "g3_sequence": g3["sequence"],
                    "g3_evidence": reference(artifact), "target": result["target"],
                    "capability": descriptor}
        except (ValueError, TypeError, KeyError, IndexError, StopIteration, AttributeError):
            continue
    raise ValueError("Latest G3 evidence is unsuitable, inconsistent or stale")


def reference(artifact: dict[str, Any]) -> dict[str, Any]:
    return {key: artifact[key] for key in ("artifact_id", "sha256", "stored_path")}


def require_task(state: dict[str, Any]) -> None:
    canonical = json.loads((TASK_DIR / "task.json").read_text(encoding="utf-8"))
    if JSON(state["manifest"]["task"]) != JSON(canonical):
        raise ValueError("Unsupported Task snapshot")


def preview_json(preview: Any) -> dict[str, Any]:
    return {**plain(preview), "planned_count": preview.planned_count,
            "analysis_attempt_count": preview.analysis_attempt_count,
            "expected_analyses_per_job": plain(preview.plan.analysis_requests)}


def freeze(candidate: Any, state: dict[str, Any], required: dict[str, Any]) -> tuple[dict, dict]:
    c = exact(candidate, {"schema_version", "original_objective", "input_resolution",
                         "capability_id", "execution_surface", "research_plan"}, "candidate")
    if type(c["schema_version"]) is not int or c["schema_version"] != 1:
        raise ValueError("Unsupported candidate schema")
    text(c["original_objective"], "original_objective")
    resolution = exact(c["input_resolution"], {"kind", "reference"}, "input_resolution")
    if resolution["kind"] not in ("explicit_user_request", "user_interaction", "synthetic_test"):
        raise ValueError("Explicit input resolution provenance is required")
    text(resolution["reference"], "input_resolution.reference")
    if c["capability_id"] != required["capability"]["id"]:
        raise ValueError("Select the actually discovered Task capability")
    if c["execution_surface"] != "python":
        raise ValueError("Only public Python Preview is supported; HTTP selection is rejected "
                         "without splitting, truncation or POST (93-day/H20 HTTP bounds apply)")
    if c["research_plan"].get("metric") != c["capability_id"]:
        raise ValueError("Plan metric must match the selected discovered capability")
    plan = plan_from_json(c["research_plan"])
    methods = {m["method"] for m in required["capability"]["analysis_methods"]}
    if any(a.spec.method not in methods for a in plan.analysis_requests):
        raise ValueError("Requested method was not discovered")
    preview = preview_json(preview_plan(plan))
    manifest = state["manifest"]
    workflow = {"schema_version": 1, "kind": "historical_return_workflow",
        "run_id": manifest["run_id"], "task_id": "historical_return_observation",
        "task_version": "1", "task_sha256": manifest["task_sha256"],
        "original_objective": c["original_objective"],
        "resolved_inputs": {"research_plan": c["research_plan"], "provenance": resolution},
        "capability_id": c["capability_id"], "prerequisites": required,
        "execution_surface": {"kind": "python",
            "preview": "market_research.descriptive.execution.preview_plan",
            "future_execution": "market_research.descriptive.execution.execute_batch"},
        "research_plan": preview["plan"], "planned_operations": plain(OPERATIONS),
        "case_policy": plain(CASE_POLICY),
        "execution_authorization": plain(AUTHORIZATION),
        "expected_outputs": plain(EXPECTED_OUTPUTS),
        "limits": {"python": "Public semantic preflight; no HTTP caps or partitioning",
                   "http": "Not selected; 93 days/window, H20, 8 jobs, 4 analyses/job, "
                           "128 coordinates/spec, 128 request_id characters, 64 KiB body",
                   "research": required["capability"]},
        "known_readiness_gaps": plain(READINESS_GAPS), "g5_executed": False}
    return workflow, preview


def save(store: Any, run_id: str, directory: str, name: str, value: Any) -> dict[str, Any]:
    path = Path(directory) / (name + ".json")
    path.write_text(JSON(value) + "\n", encoding="utf-8")
    return store.artifact(run_id, {"label": name, "path": str(path)})["payload"]


def record_g4(root: Path, run_id: str, candidate: Any) -> dict[str, Any]:
    store = RunStore(root)
    before = store.read(run_id)
    require_task(before)
    lock = root.resolve() / run_id / ".g4-writer"
    lock.mkdir()
    try:
        before = store.read(run_id)
        if any(r["payload"]["gate_id"] == "G4" and r["payload"]["status"] == "PASS"
               for r in before["gate_outcomes"]):
            raise ValueError("A workflow is already frozen; changed planning requires a new Run")
        # Detach the candidate before checking or persisting it, including finite JSON checks.
        candidate = LOAD(JSON(candidate).encode())
        result: dict[str, Any] = {"schema_version": 1, "task_id": "historical_return_observation",
            "task_version": "1", "gate_id": "G4", "run_id": run_id, "candidate": candidate,
            "prerequisites": None, "workflow": None, "preview": None, "g5_executed": False}
        workflow = preview = None
        try:
            required = prerequisites(before, root)
        except ValueError as error:
            result.update(status="BLOCKED", reason_code="prerequisites_required", reason=str(error))
        else:
            result["prerequisites"] = required
            try:
                workflow, preview = freeze(candidate, before, required)
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
                result.update(status="FAIL", reason_code="candidate_invalid",
                              reason=f"{type(error).__name__}: {error}")
            else:
                result.update(status="PASS", reason_code="workflow_frozen",
                              reason="Explicit full-window plan validated; pure Preview frozen; "
                                     "G5 authorization pending and live readiness unproven")
        if store.read(run_id) != before:
            raise ValueError("Run changed during planning; explicitly recheck")
        with tempfile.TemporaryDirectory(prefix="historical-return-g4-") as directory:
            artifacts = []
            if workflow is not None and preview is not None:
                preview_artifact = save(store, run_id, directory, "G4 actual pure Preview", preview)
                workflow["preview"] = reference(preview_artifact)
                workflow_artifact = save(store, run_id, directory, "G4 frozen workflow", workflow)
                result.update(workflow=reference(workflow_artifact),
                              preview=reference(preview_artifact))
                artifacts = [workflow_artifact, preview_artifact]
            report_artifact = save(store, run_id, directory, "G4 planning attempt", result)
            artifacts.append(report_artifact)
            current = store.read(run_id)
            # Only our artifact registrations may have appeared since planning began.
            suffix = current["records"][len(before["records"]):]
            if (current["manifest"] != before["manifest"]
                    or current["records"][:len(before["records"])] != before["records"]
                    or len(suffix) != len(artifacts)
                    or {r["payload"]["artifact_id"] for r in suffix if r["kind"] == "artifact"}
                    != {a["artifact_id"] for a in artifacts}):
                raise ValueError("Run changed during finalization; no G4 outcome published")
            store.gate(run_id, {"gate_id": "G4", "status": result["status"],
                               "reason": result["reason"],
                               "evidence": [a["artifact_id"] for a in artifacts]})
        after = RunStore(root).read(run_id)
        if (after["manifest"] != before["manifest"]
                or after["records"][:len(before["records"])] != before["records"]):
            raise ValueError("G4 history verification failed")
        _, saved = artifact_json(after, root, report_artifact["artifact_id"])
        if JSON(saved) != JSON(result):
            raise ValueError("G4 report round-trip failed")
        verified = read_frozen(root, run_id) if result["status"] == "PASS" else None
        return {"run_id": run_id, "result": result, "frozen": verified,
                "attempt_artifact": reference(report_artifact), "evidence_verified": True,
                "manifest_unchanged": True, "previous_records_unchanged": True,
                "gate_outcomes": after["gate_outcomes"]}
    finally:
        lock.rmdir()


def read_frozen(root: Path, run_id: str) -> dict[str, Any]:
    state = RunStore(root).read(run_id)
    require_task(state)
    gates = [r for r in state["gate_outcomes"] if r["payload"]["gate_id"] == "G4"]
    passes = [r for r in gates if r["payload"]["status"] == "PASS"]
    if len(passes) != 1 or gates[-1] != passes[0]:
        raise ValueError("Exactly one accepted latest G4 PASS is required")
    outcome = passes[0]
    ids = outcome["payload"]["evidence"]
    if len(ids) != 3:
        raise ValueError("G4 PASS must bind workflow, Preview and attempt report")
    (wa, workflow), (pa, preview), (ra, report) = [artifact_json(state, root, id) for id in ids]
    exact(report, {"schema_version", "task_id", "task_version", "gate_id", "run_id",
                   "candidate", "prerequisites", "workflow", "preview", "g5_executed",
                   "status", "reason_code", "reason"}, "G4 attempt report")
    required = prerequisites(state, root)
    expected, expected_preview = freeze(report["candidate"], state, required)
    expected["preview"] = reference(pa)
    if (type(report["schema_version"]) is not int or report["schema_version"] != 1
            or report["task_id"] != "historical_return_observation"
            or report["task_version"] != "1" or report["g5_executed"] is not False
            or report["reason_code"] != "workflow_frozen"
            or report["status"] != "PASS" or report["gate_id"] != "G4"
            or report["run_id"] != run_id or report["prerequisites"] != required
            or report["workflow"] != reference(wa) or report["preview"] != reference(pa)
            or JSON(workflow) != JSON(expected) or JSON(preview) != JSON(expected_preview)
            or report["reason"] != outcome["payload"]["reason"]
            or required["g3_sequence"] >= outcome["sequence"]):
        raise ValueError("Frozen workflow/Preview/report/prerequisite association mismatch")
    return {"run_id": run_id, "g4_sequence": outcome["sequence"],
            "workflow_artifact": reference(wa), "preview_artifact": reference(pa),
            "attempt_artifact": reference(ra), "workflow": workflow, "preview": preview,
            "integrity_verified": True,
            "execution_authorization": plain(workflow["execution_authorization"]),
            "g5_executed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=WORKBENCH / ".runs")
    parser.add_argument("--run", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--candidate", type=Path)
    mode.add_argument("--read", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.read:
            print(JSON(read_frozen(args.root, args.run)))
            return 0
        report = record_g4(args.root, args.run, LOAD(args.candidate.read_bytes()))
        print(JSON(report))
        return G3["G1"]["exit_status"](report["result"])
    except (OSError, ValueError, TypeError) as error:
        print(f"G4 failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
