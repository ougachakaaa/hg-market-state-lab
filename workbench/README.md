# Workbench usage

Start agents at [AGENTS.md](AGENTS.md). [Architecture](ARCHITECTURE.md) routes to the
canonical Task / Run / Gate / storage contracts. This guide supplies usage only.
Approved Tasks enter through the [Task catalog](tasks/README.md). The WB-01
acceptance fixture below remains synthetic. For WB-02 readiness, WB-03 discovery, WB-04
planning/persistence and actual Run evidence, use the
[Historical Return Observation guide](tasks/historical_return_observation/README.md).

From repository root, using the existing Python 3.13 environment:

```powershell
poetry run python workbench/run_store.py --help
poetry run python workbench/run_store.py create --input create.json
poetry run python workbench/run_store.py artifact --run RUN_ID --input artifact.json
poetry run python workbench/run_store.py gate --run RUN_ID --input gate.json
poetry run python workbench/run_store.py event --run RUN_ID --input event.json
poetry run python workbench/run_store.py read --run RUN_ID
```

`RUN_ID` is the `run_id` returned by create. Every successful command prints JSON;
errors go to stderr and exit nonzero. Add `--root PATH` **before** the operation to
use another store. The default is ignored `workbench/.runs/`, regardless of cwd.
These are script operations, not `lab` commands.

`create.json` contains `task`, `original_request`, `resolved_inputs`, and optional
`workflow`. Use a versioned Task approved by the user, following the
[Task snapshot schema](contracts/TASK.md). For tests only, a complete minimal example is:

```json
{
  "task": {
    "task_id": "synthetic-file-check",
    "version": "1",
    "approval": {"kind": "synthetic", "reference": "Test fixture only; no business approval"},
    "goal": "Exercise generic evidence storage",
    "scope": "Synthetic local files only",
    "required_inputs": [],
    "allowed_capabilities": ["Read a synthetic local file"],
    "planning_constraints": [],
    "expected_outputs": ["Preserved evidence"],
    "acceptance_criteria": ["Evidence is retrievable"],
    "gates": [{"gate_id": "inspect", "criteria": "File contains expected text", "depends_on": []}]
  },
  "original_request": "Test generic storage",
  "resolved_inputs": {}
}
```

Register an existing local output/check file with `artifact.json`:

```json
{"label": "inspection output", "path": "path/to/check.txt"}
```

The recorder copies its bytes and returns `payload.artifact_id`, `stored_path`,
original location, digest and size. Use that ID in `gate.json`:

```json
{"gate_id": "inspect", "status": "PASS", "reason": "Expected text observed", "evidence": ["ARTIFACT_ID"]}
```

PASS requires actual supporting evidence. The executor must check its relevance
against the Task's criteria. FAIL, BLOCKED and SKIPPED require explicit reasons and
may use an empty evidence array; their [meanings](contracts/GATE.md) differ.
Registering evidence from another Run is rejected. Rechecking appends an attempt.

Record an actual operation with `event.json`:

```json
{"operation": "inspect synthetic file", "details": {"observed": "expected text"}}
```

Read returns the frozen manifest, all ordered records and filtered Gate/event/artifact
histories. Join the store root, Run ID and artifact `stored_path` to locate the
preserved output; the original file can be removed without losing the copy. Do not
edit these files in place. [Storage authority](contracts/STORAGE.md) defines crash,
locking, corruption and filesystem limits.

For in-process use without packaging, load this standalone script with standard-library
`runpy.run_path("workbench/run_store.py")`, obtain `RunStore` from the returned mapping,
and call `create(request)`, `artifact(run_id, request)`, `gate(run_id, outcome)`,
`event(run_id, event)` or `read(run_id)`. The CLI uses the same methods.

Run the independently reproducible acceptance example:

```powershell
poetry run python workbench/tests/acceptance_example.py
```

It creates one synthetic Task version and two distinct Runs, checks all four Gate
statuses, preserves evidence after temporary source removal and prints identities,
locations and verification results. It writes only ignored Workbench evidence.
Recorded delivery checks and known limits are in [WB-01 acceptance](ACCEPTANCE.md).
