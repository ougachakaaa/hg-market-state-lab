"""Synthetic fixtures shared by tests and the standalone acceptance example."""

import runpy
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve().parents[1] / "run_store.py"
_script = runpy.run_path(str(SCRIPT))
RunStore = _script["RunStore"]


def synthetic_request() -> dict[str, Any]:
    return {
        "task": {
            "task_id": "synthetic-file-check",
            "version": "1",
            "approval": {"kind": "synthetic", "reference": "WB-01 test only; no business approval"},
            "goal": "Exercise generic evidence storage",
            "scope": "Synthetic local files only",
            "required_inputs": ["Synthetic check text", "Inspection enabled flag"],
            "allowed_capabilities": ["Read synthetic local files"],
            "planning_constraints": ["No business operations"],
            "expected_outputs": ["Preserved evidence"],
            "acceptance_criteria": ["Independent Run evidence is retrievable"],
            "gates": [
                {"gate_id": "inspect",
                 "criteria": "With inspection enabled, expected text is present",
                 "depends_on": []},
                {"gate_id": "optional", "criteria": "Optional test check succeeds",
                 "depends_on": ["inspect"]},
            ],
        },
        "original_request": "Validate the synthetic file recorder",
        "resolved_inputs": {"expected_text": "synthetic evidence", "inspection_enabled": True},
        "workflow": [{"operation": "inspect synthetic file"}],
    }
