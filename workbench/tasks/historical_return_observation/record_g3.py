"""Append actual G3 discovery evidence/outcome to an existing Historical Return Run."""

from __future__ import annotations

import argparse
import json
import runpy
import sys
import tempfile
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parent
WORKBENCH = TASK_DIR.parents[1]
CHECK = runpy.run_path(str(TASK_DIR / "check_capabilities.py"))
RunStore = runpy.run_path(str(WORKBENCH / "run_store.py"))["RunStore"]


def record_g3(root: Path, run_id: str, timeout: float = 2) -> dict[str, Any]:
    store = RunStore(root)
    before = store.read(run_id)
    task = json.loads((TASK_DIR / "task.json").read_text(encoding="utf-8"))
    if before["manifest"]["task"] != task:
        raise ValueError("Unsupported Task snapshot")
    result = CHECK["check_capabilities"](before, root, timeout)
    if store.read(run_id) != before:
        raise ValueError("Run changed during discovery; explicitly recheck")
    with tempfile.TemporaryDirectory(prefix="historical-return-g3-") as directory:
        source = Path(directory) / "g3.json"
        source.write_text(CHECK["G1"]["json_text"](result) + "\n", encoding="utf-8")
        artifact = store.artifact(run_id, {"label": "raw G3 capability discovery JSON",
                                           "path": str(source)})["payload"]
    outcome = store.gate(run_id, {"gate_id": "G3", "status": result["status"],
        "reason": result["reason"], "evidence": [artifact["artifact_id"]]})
    # Fresh reader verifies digest/ownership after original evidence source removal.
    after = RunStore(root).read(run_id)
    preserved = root.resolve() / run_id / artifact["stored_path"]
    saved = CHECK["G1"]["_strict_json"](preserved.read_bytes())
    prefix_length = len(before["records"])
    if (after["manifest"] != before["manifest"] or saved != result
            or after["records"][:prefix_length] != before["records"]
            or outcome not in after["gate_outcomes"]
            or artifact not in [r["payload"] for r in after["artifacts"]]):
        raise ValueError("G3 evidence round-trip verification failed")
    return {"run_id": run_id, "task_sha256": after["manifest"]["task_sha256"],
        "result": result, "artifact": artifact, "preserved_discovery_path": str(preserved),
        "evidence_verified": True, "manifest_unchanged": True, "previous_records_unchanged": True,
        "gate_outcomes": [r["payload"] for r in after["gate_outcomes"]],
        "unexecuted_gates": [g for g in ("G4", "G5") if not any(
            r["payload"]["gate_id"] == g for r in after["gate_outcomes"])]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=WORKBENCH / ".runs")
    parser.add_argument("--run", required=True, help="Existing Run created by G1")
    parser.add_argument("--timeout", type=float, default=2, help="Seconds per request, 0 < t <= 30")
    args = parser.parse_args(argv)
    try:
        report = record_g3(args.root, args.run, args.timeout)
        print(CHECK["G1"]["json_text"](report))
        return CHECK["G1"]["exit_status"](report["result"])
    except (OSError, ValueError, TypeError) as error:
        print(f"G3 evidence recording failed: {type(error).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
