"""Produce two independent, synthetic Runs without touching business modules/data."""

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from support import SCRIPT, RunStore, synthetic_request


def demonstrate(root: Path) -> dict[str, Any]:
    store = RunStore(root)
    request = synthetic_request()
    original = json.dumps(request, sort_keys=True)
    blocked_request = copy.deepcopy(request)
    blocked_request["resolved_inputs"]["inspection_enabled"] = False
    manifests = [store.create(request), store.create(blocked_request)]
    assert manifests[0]["run_id"] != manifests[1]["run_id"]
    artifacts = []
    with tempfile.TemporaryDirectory(prefix="workbench-synthetic-") as directory:
        source = Path(directory) / "check.txt"
        source.write_text("synthetic evidence", encoding="utf-8")
        for manifest in manifests:
            run_id = manifest["run_id"]
            if manifest["resolved_inputs"]["inspection_enabled"]:
                observed = source.read_text(encoding="utf-8")
                assert observed == request["resolved_inputs"]["expected_text"]
                optional_matches = observed == "different optional expected text"
                assert not optional_matches
                store.event(run_id, {"operation": "inspect synthetic file",
                                     "details": {"observed": observed,
                                                 "optional_comparison_matches": optional_matches}})
            else:
                store.event(run_id, {"operation": "record supplied synthetic fixture",
                                     "details": {"inspection_enabled": False}})
            artifacts.append(store.artifact(run_id, {"label": "check output", "path": str(source)}))
    first, second = [manifest["run_id"] for manifest in manifests]
    evidence = [artifacts[0]["payload"]["artifact_id"]]
    store.gate(first, {"gate_id": "inspect", "status": "PASS",
                       "reason": "Read source and observed expected text", "evidence": evidence})
    store.gate(first, {"gate_id": "optional", "status": "FAIL",
                       "reason": "Attempted synthetic comparison did not match", "evidence": []})
    store.gate(second, {"gate_id": "inspect", "status": "BLOCKED",
                        "reason": "Synthetic inspection prerequisite is disabled",
                        "evidence": []})
    store.gate(second, {"gate_id": "optional", "status": "SKIPPED",
                        "reason": "Intentionally omitted in this synthetic Run", "evidence": []})
    states = [store.read(first), store.read(second)]
    assert json.dumps(request, sort_keys=True) == original
    assert states[0]["manifest"]["task"] == states[1]["manifest"]["task"] == request["task"]
    assert states[0]["manifest"]["task_sha256"] == states[1]["manifest"]["task_sha256"]
    summaries = []
    for state in states:
        run_id = state["manifest"]["run_id"]
        assert [r["sequence"] for r in state["records"]] == [1, 2, 3, 4]
        artifact = state["artifacts"][0]["payload"]
        preserved = root / run_id / artifact["stored_path"]
        assert preserved.read_text(encoding="utf-8") == "synthetic evidence"
        assert not Path(artifact["source_location"]).exists()
        summaries.append({"run_id": run_id, "directory": str(root / run_id),
                          "statuses": [r["payload"]["status"] for r in state["gate_outcomes"]],
                          "sequences": [r["sequence"] for r in state["records"]],
                          "artifact": str(preserved), "artifact_sha256": artifact["sha256"]})
    return {"task_id": request["task"]["task_id"], "version": request["task"]["version"],
            "task_sha256": manifests[0]["task_sha256"], "runs": summaries,
            "verified": "same Task, distinct Runs, all statuses, ordered records, retained bytes"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=SCRIPT.parent / ".runs")
    args = parser.parse_args()
    print(json.dumps(demonstrate(args.root.resolve()), indent=2))
