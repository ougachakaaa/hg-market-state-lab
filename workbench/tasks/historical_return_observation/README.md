# Historical Return Observation usage

Start at the [Task entry](ARCHITECTURE.md), then read [task.json](task.json) and the
[G1 contract](BACKEND_READY.md). This guide is usage-only. Version `1` approves
Task design and G1 acceptance; actual market execution requires separate authorization
and resolved research inputs. Only G1 is implemented.

From the repository root in its existing Poetry environment:

```powershell
# Read-only check. Prints one JSON object: PASS=0, FAIL=1, BLOCKED=2.
poetry run python workbench/tasks/historical_return_observation/check_backend.py

# Explicit target and timeout; this command does not start a server.
poetry run python workbench/tasks/historical_return_observation/check_backend.py --base-url http://127.0.0.1:8011 --timeout 2

# If the backend is stopped, explicitly start the official entry in a separate terminal.
poetry run lab serve backend
```

Reuse a compatible running backend. An occupied/incompatible port needs explicit
diagnosis; do not terminate or replace an existing user-owned process. A successful
`lab doctor` exit does not establish G1. The checker verifies the expected published
API contract and does not attest a process or checkout identity.

To create an actual readiness-only Run with an exact Task snapshot, check G1, preserve
raw machine JSON, record G1 and G2/G6 deferrals, and verify the stored evidence:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g1.py --original-request 'Verify G1 backend readiness only; no Research execution'
```

`--base-url`, `--timeout` and optional `--root PATH` are accepted by this script too.
It prints the actual `result`, `run_id`, `task_sha256`, `preserved_readiness_path`,
artifact registration and Gate outcomes. Its exit follows G1; evidence-storage errors
exit nonzero. `evidence_verified=true` means the same-Run frozen snapshot and preserved
JSON were read back after removal of the temporary source. It does not mean the full
research Task succeeded. G3/G4/G5 remain unexecuted, with no fabricated outcomes.

Retrieve using the existing public Run Store operation, replacing RUN_ID with the
returned identity (add `--root PATH` before `read` if a custom store was used):

```powershell
poetry run python workbench/run_store.py read --run RUN_ID
```

The raw preserved result is under `workbench/.runs/RUN_ID/blobs/ARTIFACT_ID`. Registration
includes byte size and SHA-256; `read` verifies integrity and same-Run ownership.
Run storage is ignored local state. Fresh checkouts must rerun the check to generate
their own evidence; [acceptance](ACCEPTANCE.md) records this delivery's actual examples.

This script demonstration uses `runpy.run_path` to load `RunStore` and the Task checker
without creating an installed package. It calls only existing `create`, `artifact`,
`gate`, and `read` operations. The raw checker can also be used independently by an
external Codex / DSH agent with local tool access. A cloud agent still requires a
registered reachable tool; local HTTP alone does not provide that connection.

For full historical research such as 2010-2026, retain exact requested dates but stop
at the current implementation boundary. HTTP cannot accept one such window. Python
has different constraints, not proven long-history availability. Future G4/G5 must
resolve the complete legal surface and live data, preserve/freeze the workflow and
obtain execution authorization. No partitioning, merging or market execution is added.
