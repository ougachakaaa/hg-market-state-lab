"""Create a readiness-only Run, perform actual G1 and preserve/retrieve its evidence."""

from __future__ import annotations

import argparse
import json
import math
import runpy
import sys
import tempfile
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parent
WORKBENCH = TASK_DIR.parents[2]
_checker = runpy.run_path(str(TASK_DIR / "check_backend.py"))
RunStore = runpy.run_path(str(WORKBENCH / "run_store.py"))["RunStore"]


def record_g1(root: Path, original_request: str, target: str, timeout: float) -> dict[str, Any]:
    task = json.loads((TASK_DIR.parent / "task.json").read_text(encoding="utf-8"))
    store = RunStore(root)
    manifest = store.create({
        "task": task, "original_request": original_request,
        "resolved_inputs": {"execution_scope": "G1 only; no Research execution",
                            "backend_target": target,
                            "timeout_seconds": timeout if math.isfinite(timeout) else str(timeout),
                            "research_inputs": "unresolved; not required for G1"},
        "workflow": ["Read backend OpenAPI", "Preserve raw G1 JSON",
                     "Record G1 and G2/G6 deferrals", "Read back and verify evidence"],
    })
    run_id = manifest["run_id"]
    result = _checker["check_backend"](target, timeout)
    with tempfile.TemporaryDirectory(prefix="historical-return-g1-") as directory:
        source = Path(directory) / "g1.json"
        source.write_text(_checker["json_text"](result) + "\n", encoding="utf-8")
        artifact = store.artifact(run_id, {"label": "raw G1 backend readiness JSON",
                                           "path": str(source)})["payload"]
    store.gate(run_id, {"gate_id": "G1", "status": result["status"],
                        "reason": result["reason"], "evidence": [artifact["artifact_id"]]})
    for gate_id, reason in (
        ("G2", "Authentication deferred in current MVP; loopback backend has no authentication."),
        ("G6", "Visualization implementation deferred in current MVP; no visualization performed."),
    ):
        store.gate(run_id, {"gate_id": gate_id, "status": "SKIPPED",
                            "reason": reason, "evidence": []})
    state = store.read(run_id)
    saved_artifact = state["artifacts"][0]["payload"]
    preserved = root.resolve() / run_id / saved_artifact["stored_path"]
    saved_result = json.loads(preserved.read_text(encoding="utf-8"))
    if (state["manifest"]["task"] != task or saved_result != result
            or state["gate_outcomes"][0]["payload"]["evidence"] != [artifact["artifact_id"]]):
        raise ValueError("G1 evidence round-trip verification failed")
    return {"run_id": run_id, "task_id": task["task_id"], "task_version": task["version"],
            "task_sha256": manifest["task_sha256"], "result": result,
            "run_directory": str(root.resolve() / run_id), "artifact": saved_artifact,
            "preserved_readiness_path": str(preserved), "evidence_verified": True,
            "gate_outcomes": [record["payload"] for record in state["gate_outcomes"]],
            "unexecuted_gates": ["G3", "G4", "G5"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _checker["add_arguments"](parser)
    parser.add_argument("--root", type=Path, default=WORKBENCH / ".runs")
    parser.add_argument("--original-request", required=True,
                        help="Describe the readiness-only user request; no research execution")
    args = parser.parse_args(argv)
    try:
        report = record_g1(args.root, args.original_request, args.base_url, args.timeout)
        print(_checker["json_text"](report))
        return _checker["exit_status"](report["result"])
    except (OSError, ValueError, TypeError) as error:
        print(f"G1 evidence recording failed: {type(error).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
