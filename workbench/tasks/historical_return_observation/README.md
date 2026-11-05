# Historical Return Observation usage

Start at the [Task entry](ARCHITECTURE.md), then read [task.json](task.json) and the
[G1 contract](authority/BACKEND_READY.md),
[G3 contract](authority/CAPABILITY_DISCOVERY.md),
[G4 contract](authority/WORKFLOW_PLANNING.md) and
[G5 contract](authority/AUTHORIZED_EXECUTION.md). This guide is usage-only.

## Current status

The G1, G3, G4 and G5 recorders exist, and deterministic fixture acceptance remains
supported. A fresh live end-to-end path is currently blocked at G1: repository HTTP
authentication protects `/openapi.json` and all Research operations, while V1's anonymous
readiness and discovery contracts expect unauthenticated access. Existing Runs and the retained
historical results remain readable. See
[current operational compatibility](ARCHITECTURE.md#current-operational-compatibility)
and do not bypass authentication. The commands below document the V1 mechanisms; the
G3/G4/G5 steps require a compatible G1/G3 Run that cannot currently be created against
the authenticated backend.

## G1 backend readiness

From the repository root in its existing Poetry environment:

```powershell
# Read-only check. Prints one JSON object: PASS=0, FAIL=1, BLOCKED=2.
poetry run python workbench/tasks/historical_return_observation/runtime/check_backend.py

# Explicit target and timeout; this command does not start a server.
poetry run python workbench/tasks/historical_return_observation/runtime/check_backend.py --base-url http://127.0.0.1:8011 --timeout 2

# If the backend is stopped, explicitly start the official entry in a separate terminal.
poetry run lab serve backend
```

Reuse a compatible running backend. An occupied or incompatible port needs explicit
diagnosis; do not terminate or replace an existing user-owned process. A successful
`lab doctor` exit does not establish G1. The checker verifies the expected published API
contract and does not attest a process or checkout identity.

Against the current authenticated backend, anonymous `GET /openapi.json` returns 401.
The checker preserves that observation as a G1 FAIL with `http_status`; this is correct
V1 behavior, not a readiness success. Fixture PASS evidence is historical/deterministic
and does not prove current integration.

To create a readiness-only Run with the exact Task snapshot, preserve the raw machine
JSON, record G1 and the G2/G6 deferrals, and verify the stored evidence:

```powershell
poetry run python workbench/tasks/historical_return_observation/runtime/record_g1.py --original-request 'Verify G1 backend readiness only; no Research execution'
```

`--base-url`, `--timeout` and optional `--root PATH` are accepted. It prints the actual
`result`, `run_id`, `task_sha256`, `preserved_readiness_path`, artifact registration and
Gate outcomes. Its exit follows G1; evidence-storage errors exit nonzero.
`evidence_verified=true` means the same-Run frozen snapshot and preserved JSON were read
back after removal of the temporary source. It does not mean the full research Task
succeeded. This command leaves G3/G4/G5 unexecuted.

Retrieve with the public Run Store operation, replacing `RUN_ID` with the returned
identity (add `--root PATH` before `read` if a custom store was used):

```powershell
poetry run python workbench/run_store.py read --run RUN_ID
```

The raw preserved result is under `workbench/.runs/RUN_ID/blobs/ARTIFACT_ID`. Registration
includes byte size and SHA-256; `read` verifies integrity and same-Run ownership. Run
storage is ignored local state; fresh checkouts generate their own evidence.

The recorder loads `RunStore` and the checker with `runpy.run_path`, without an installed
package, and calls only existing create/artifact/gate/read operations. A cloud agent
still requires a registered reachable tool; local HTTP alone does not connect a cloud
session.

## G3 capability discovery

Use the `run_id` from a readiness Run whose latest G1 PASS is suitable, and whose G2 is
the exact V1 SKIPPED deferral:

```powershell
poetry run python workbench/tasks/historical_return_observation/runtime/record_g3.py --run RUN_ID --timeout 2
```

Add `--root PATH` if that Run uses a custom store. The target is derived exclusively from
preserved successful G1 evidence; changing backend origin requires a G1 check for that
origin. Latest G1 PASS and the Task's explicit G2 SKIPPED deferral are required. No fresh
Run can satisfy these prerequisites against the current authenticated backend; the
command is retained for compatible historical fixtures and future Task versions.

The script appends the original list/detail bytes and verification JSON as one artifact,
then G3, and verifies them with a fresh reader. Previous records, frozen Task, inputs and
`manifest.workflow` remain unchanged. It creates no ResearchPlan or preview. The report
includes actual `capability_count`, `capability_ids`, complete inspected `capabilities`,
per-request errors and raw base64 response bodies. `discovery_complete` and
`task_readiness` are separate: an empty valid catalog is complete discovery but G3 FAIL
because the required ID is missing. Publication support never proves live provider/data
readiness. PASS=0, FAIL=1, BLOCKED=2; storage or unsupported-Run failures exit 1. Timeout
is per request, with no retry or redirect. Repeat explicitly to append another attempt.

## G4 Agent planning and persistence

Codex / DSH reads the same Run's actual G3 descriptors, interprets the original research
goal and resolves every missing input through user interaction. Do not guess an index,
H, dates, statistical methods/parameters, units or failure policy. Write a candidate
using the exact shape of [the synthetic example](../../tests/fixtures/planning_candidate.json).
All values in that example are test-only, not defaults. The Agent selects Python because
the complete historical window and H exceed HTTP caps; the public Python preflight decides
whether the plan is legal.

From a Run with latest suitable G1/G3 PASS and explicit G2 SKIPPED:

```powershell
poetry run python workbench/tasks/historical_return_observation/runtime/record_g4.py --run RUN_ID --candidate workbench/tests/fixtures/planning_candidate.json
poetry run python workbench/tasks/historical_return_observation/runtime/record_g4.py --run RUN_ID --read
```

Optional `--root PATH` selects the existing store. PASS=0, FAIL=1, BLOCKED=2; operational
errors exit 1. `--read` needs no draft and locates the exact accepted workflow, Preview
and attempt references through G4 PASS, verifies their hashes/associations and rechecks
the public pure Preview. It returns `integrity_verified`, not execution permission. Store
the returned `workflow_artifact.artifact_id` and `sha256` for future explicit G5
authorization. The mutable candidate and original `manifest.workflow` are not execution
authority. After PASS, a changed plan requires a new Run. Do not edit frozen evidence.

Only Python is supported by this recorder; HTTP selection is explicitly rejected,
including an oversized historical window, without a POST or request splitting.
Long-history Calendar, warm-up, Index facts and source/cache readiness remain unproven.
No research, acquisition, automatic partition/merge or G5 is performed. Deterministic
validation does not prove general natural-language planning quality; interactive
interpretation remains an agent responsibility. A fresh G4 is currently blocked because
its G1/G3 prerequisites cannot pass against the authenticated backend.

## G5 authorized Python execution and result delivery

First retrieve the exact accepted G4 with `record_g4.py --run RUN_ID --read`. Use a real
user-input workflow, not the synthetic example Run. Preserve the returned workflow
artifact ID, SHA-256 and objective. Read the
[execution contract](authority/AUTHORIZED_EXECUTION.md) before invoking.

In a human-controlled interactive terminal:

```powershell
poetry run python workbench/tasks/historical_return_observation/runtime/record_g5.py --run RUN_ID
poetry run python workbench/tasks/historical_return_observation/runtime/record_g5.py --run RUN_ID --read
poetry run python workbench/run_store.py read --run RUN_ID
```

Optional `--root PATH` selects the same store. The execution command displays the full
challenge and exact approval sentence, then asks for an explicit resource budget and
data/cache isolation declaration. These strings enforce no controls. Before long-history
live acceptance, verify isolation and bounded acquisition through existing
owner-approved facilities; if controls cannot be verified, do not execute full history.
An agent must never answer this human prompt on the user's behalf. Noninteractive
execution without a host authorizer blocks. No generated JSON file grants permission,
and Task approval alone grants no execution.

Codex / DSH may instead load `record_g5.py` with `runpy.run_path` and call
`record_g5(root, run_id, authorize=resolve_actual_user_approval)`. This callback must
show `approval_sentence(challenge)` to the user, resolve the actual reply in its trusted
session, and return the exact fields defined in the contract. `source_reference` must
locate that real reply, and `user_statement` must be its verbatim approval sentence.
Return `None` when there is no trustworthy approval. A callback that constructs its own
approval or reads an agent-authored approval file violates this boundary.

Approval is preserved separately; G4 bytes remain unchanged. The adapter records a
durable intent before the single public `execute_batch` call. Any existing intent blocks
another call. If interrupted, use `--read` and inspect the original Run; arrange operator
reconciliation. Never retry or delete the intent/lock automatically.

PASS=0 means every requested computation succeeded; FAIL=1 includes partial/failed
Batches with preserved successful analyses and failures. BLOCKED=2 means unmet
prerequisites, missing authorization or uncertain execution. Storage/evidence errors
exit 1. `--read` performs no execution. A completed result retains its original outcome
even after a later G1/G3 failure or blocked duplicate invocation. Read validates evidence
bound to the historical intent; a new execution still requires current latest Gate
eligibility. A completed result is not permission for another execution.

The read report gives workflow, authorization, result and report artifact references.
Files are at `workbench/.runs/RUN_ID/blobs/ARTIFACT_ID` (or the explicit store root). The
result envelope's `batch_result` contains actual statistics, ordered Job/analysis
outcomes, populations, coverage, warm-up/dependence and public provenance. Numeric units
remain decimal_ratio; incomplete facts are explicitly retained. Unsafe exception
objects/free text are omitted with markers. Research's legal partial-Index policy remains
unchanged; PASS does not mean 100% market coverage. A returned Batch with failed Jobs is
G5 FAIL even when the Python call completed normally.

Reproduce isolated acceptance, with zero paid-data access/default-cache changes:

```powershell
poetry run python workbench/tests/g5_execution_example.py
```

This uses a simulated user interaction in the test harness and public-service fakes
through the ordinary adapter. Its fixture approval is test evidence only. Production has
no synthetic execution seam; historical synthetic Runs remain readable. Reported
`result_path` is relative to the selected Run store. No live readiness is implied. A
fresh G5 execution is currently blocked because its G4 prerequisites cannot pass against
the authenticated backend.

## Results and verification

Discover the [2026 four-index results](results/2026_four_index_returns/README.md) and
their scope and historical summary. Complete results and evidence are retained outside
the repository. Independent opt-in verification scripts live in
`workbench/tests/result_verification/`; the saved-result verifier reads local original
blobs and prohibits network and SQLite. Choose an output path outside the RunStore:

```powershell
poetry run python workbench/tests/result_verification/verify_saved.py --run RUN_ID --output OUTPUT_JSON
```

The cache verifier depends on the original external cache and local configuration; it
exercises only already-complete cache targets while denying Provider/network access. The
control harness is opt-in and requires a real trusted-host authorization for execution;
it is not another production runtime. Never reuse historical authorization. The retained
results are historical findings, not a claim of current backend compatibility.
