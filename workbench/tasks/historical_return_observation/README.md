# Historical Return Observation usage

Start at the [Task entry](ARCHITECTURE.md), then read [task.json](task.json) and the
[G1 contract](BACKEND_READY.md), [G3 contract](CAPABILITY_DISCOVERY.md) and
[G4 contract](WORKFLOW_PLANNING.md) and [G5 contract](AUTHORIZED_EXECUTION.md). This guide
is usage-only. WB-03/WB-04 implement version `1`'s approved discovery and planning
slices without changing its frozen definition. G1, G3, G4 and G5 are implemented; actual
market execution requires separate authorization and resolved research inputs.

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
research Task succeeded. This command leaves G3/G4/G5 unexecuted.

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

## G3 in the same Run

Use the `run_id` returned by `record_g1.py`, including a Run created before WB-03:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g3.py --run RUN_ID --timeout 2
```

Add `--root PATH` if that G1 Run uses a custom store. The target is derived exclusively
from preserved successful G1 evidence; changing backend origin requires a G1 check
for that origin. Latest G1 PASS and the Task's explicit G2 SKIPPED deferral are required.
The script appends the original list/detail bytes and verification JSON as one artifact,
then G3, and verifies them using a fresh reader. Previous records, frozen Task,
inputs and `manifest.workflow` remain unchanged. It creates no ResearchPlan or preview.

The report includes actual `capability_count`, `capability_ids`, complete inspected
`capabilities` (descriptions and published constraints), per-request errors and raw
base64 response bodies. `discovery_complete` and `task_readiness` are separate:
an empty valid catalog is complete discovery but G3 FAIL with the required ID missing.
Publication support never proves live provider/data readiness. PASS=0, FAIL=1,
BLOCKED=2; storage/unsupported Run failures exit 1. Timeout is per request, with no
retry or redirect. Repeat explicitly to append another independent attempt.

The existing `run_store.py read` command above retrieves G1 and G3 from the same Run.
`preserved_discovery_path` locates the artifact verified after temporary source removal.
See [WB-03 acceptance](DISCOVERY_ACCEPTANCE.md) for actual PASS/failure evidence and
the complete WB-03 changed-file/reconciliation record. That check leaves G4/G5 unexecuted.

## G4 Agent planning and persistence

Codex / DSH first reads the same Run's actual G3 capability descriptors, interprets
the original research goal and resolves every missing input through user interaction.
No guessed index, H, dates, statistical methods/parameters, units or failure policy.
Write a candidate using the exact shape of [the synthetic example](examples/g4-candidate.json).
This example explicitly requests `000852.SH`, H=21, inclusive 2010-01-01..2026-10-28,
trailing_cumulative_return_v1, empty metric parameters, quantile quartiles and explicit
decimal_ratio interval edges, with continue on failure. All values are test-only,
not defaults. The Agent selects Python because the complete historical window and H
exceed HTTP caps. The public Python preflight decides whether that plan is legal.

Direct Agent instruction example:

> Read the synthetic original_objective in examples/g4-candidate.json and the actual
> same-Run G3 descriptor. Confirm that this is the discovered supported index case,
> preserve all explicit inputs, and compose the complete public ResearchPlan shown
> there. Select public Python Preview for the full historical window. Freeze only
> planning and actual Preview into this Run; execution authorization stays pending.
> Report the exact frozen workflow identity/hash and remaining data-readiness gaps.

From repository root, substitute an existing Run with latest suitable G1/G3 PASS
and explicit G2 MVP SKIPPED; do not reuse a Run whose latest G3 failed:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g4.py --run RUN_ID --candidate workbench/tasks/historical_return_observation/examples/g4-candidate.json
poetry run python workbench/tasks/historical_return_observation/record_g4.py --run RUN_ID --read
```

Optional `--root PATH` selects the existing store. PASS=0, FAIL=1, BLOCKED=2; operational
errors exit 1. `--read` needs no draft and locates the exact accepted workflow, Preview
and attempt references through G4 PASS, verifies their hashes/associations and rechecks
the public pure Preview. It returns `integrity_verified`, not execution permission.
Store the returned `workflow_artifact.artifact_id` and `sha256` for future explicit G5
authorization. The mutable candidate and original manifest.workflow are not execution
authority. After PASS, a changed plan requires a new Run. Do not edit frozen evidence.

Only Python is supported by this recorder; HTTP selection is explicitly rejected,
including an oversized historical window, without a POST or request splitting.
Long-history Calendar, warm-up, Index facts and source/cache readiness remain unproven.
No research, acquisition, automatic partition/merge or G5 is performed. See
[WB-04 acceptance](PLANNING_ACCEPTANCE.md) for actual artifacts and verification.
Deterministic validation does not prove general natural-language planning quality;
interactive acceptance belongs to the final Workbench E2E Goal.

## G5 authorized Python execution and result delivery

First retrieve the exact accepted G4 with `record_g4.py --run RUN_ID --read`.
Use a real user-input workflow, not the synthetic example Run above. Preserve the
returned workflow artifact ID, SHA-256 and objective. Read
[the execution contract](AUTHORIZED_EXECUTION.md) before invoking.

In a human-controlled interactive terminal:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g5.py --run RUN_ID
poetry run python workbench/tasks/historical_return_observation/record_g5.py --run RUN_ID --read
poetry run python workbench/run_store.py read --run RUN_ID
```

Optional `--root PATH` selects the same store. The execution command displays the
full challenge and exact approval sentence, then asks for an explicit resource budget
and safe data/cache isolation description. An agent must never answer this human
prompt on the user's behalf. Noninteractive execution without a host authorizer blocks.
No generated JSON file grants permission, and Task approval alone grants no execution.

Codex / DSH may instead load `record_g5.py` with `runpy.run_path` and call
`record_g5(root, run_id, authorize=resolve_actual_user_approval)`. This callback must
show `approval_sentence(challenge)` to the user, resolve the actual reply in its trusted
session, and return the exact fields defined in the contract. `source_reference` must
locate that real reply, and `user_statement` must be its verbatim approval sentence.
Return `None` when there is no trustworthy approval. A callback that constructs its own
approval or reads an agent-authored approval file violates this boundary.

Approval is preserved separately; G4 bytes remain unchanged. The adapter records a
durable intent before the single public execute_batch call. Any existing intent blocks
another call. If interrupted, use `--read` and inspect the original Run; arrange operator
reconciliation. Never retry or delete the intent/lock automatically.

PASS=0 means every requested computation succeeded; FAIL=1 includes partial/failed
Batches with preserved successful analyses and failures. BLOCKED=2 means unmet
prerequisites, missing authorization or uncertain execution. Storage/evidence errors
exit 1. `--read` performs no execution. A completed result retains its original outcome
even after a blocked duplicate invocation; it is not permission for another execution.

The read report gives workflow, authorization, result and report artifact references.
Files are at `workbench/.runs/RUN_ID/blobs/ARTIFACT_ID` (or the explicit store root).
The result envelope's `batch_result` contains actual statistics, ordered Job/analysis
outcomes, populations, coverage, warm-up/dependence and public provenance. Public numeric
units remain decimal_ratio; incomplete facts are explicitly retained. Unsafe exception
objects/free text are omitted with markers. Research's legal partial-Index policy remains
unchanged; PASS does not mean 100% market coverage. A returned Batch with failed Jobs
is G5 FAIL even when the Python call completed normally.

Reproduce isolated acceptance, with zero paid-data access/default-cache changes:

```powershell
poetry run python workbench/tests/g5_execution_example.py
```

This uses explicitly synthetic authorization and public-service fakes in its test harness;
it cannot authorize the live adapter. See [WB-05 acceptance](EXECUTION_ACCEPTANCE.md)
for actual artifacts/checks. No full-history live readiness or WB-06 interactive
natural-language acceptance is claimed.
