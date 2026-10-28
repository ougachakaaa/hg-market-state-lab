# WB-04 acceptance and reconciliation

Delivery date: 2026-10-29 (Asia/Shanghai); acceptance began 2026-10-28.
Baseline: `develop`, predecessor
`9d06542f711a42412d40b1e20c6e7e473be73a96`. Root runtime: Python 3.13.11.
Approval is the [WB-04 Goal](PLANNING_REQUEST.md), preserved with trailing whitespace
normalized. This records actual acceptance, not business semantics or live readiness.

## Authority and implementation

The stable root entry reaches Workbench, the Task catalog, Task entry and new narrow
[G4 contract](WORKFLOW_PLANNING.md). That document owns candidate serialization,
prerequisite verification, frozen artifact association, read-back, outcomes and the
authorization reconciliation. Workbench architecture, Task catalog/entry, G3 navigation
and Workbench/Task usage guides now route to the implemented planning slice.

Added: `PLANNING_REQUEST.md`, `WORKFLOW_PLANNING.md`, this acceptance record,
`record_g4.py`, `workbench/tests/test_historical_return_g4.py`, and the candidate/actual
JSON examples below. `examples/.gitattributes` disables newline conversion for byte-exact
G4 JSON SHA-256 verification across platforms. No specialized schema or operation detail
was placed in the top-level architecture. Existing shared Task/Run/Gate/Storage contracts, generic
RunStore, G1/G3 scripts, approved `task.json`, dependencies, business/HTTP/CLI code
and generated contracts remain unchanged.

The Task-specific script adapts complete Agent-authored JSON to public DateWindow,
AnalysisRequest, Statistics specs and ResearchPlan, then calls public preview_plan.
It implements neither natural-language reasoning nor a statistical algorithm. It
revalidates preserved G3 list/detail exchanges, public descriptor types, same-target
G1 evidence, explicit deferred G2 and latest record associations before planning.
Failed prerequisites block even plan construction. Frozen workflows identify source
binding/missing-data policy, operations/dependencies, expected outputs and pending
execution authorization without granting upstream access to Workbench.

## Agent usage and actual full-history Preview

See [usage](README.md#g4-agent-planning-and-persistence) for the direct Codex / DSH
planning instruction and [fully specified synthetic request](examples/g4-candidate.json).
The Agent must read actual G3 evidence, faithfully resolve the original objective and
ask for any missing input before constructing that candidate. The fixture values are
explicit test inputs, never user defaults or execution approval.

Final actual invocation, from repository root after G1 and G3 in the same Run:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g4.py --run fe7d4c9a5c014a248101aff15195ba4a --candidate workbench/tasks/historical_return_observation/examples/g4-candidate.json
poetry run python workbench/tasks/historical_return_observation/record_g4.py --run fe7d4c9a5c014a248101aff15195ba4a --read
poetry run python workbench/run_store.py read --run fe7d4c9a5c014a248101aff15195ba4a
```

All three exited 0. The fresh G4 reader locates the accepted artifact through G4 PASS,
checks all hashes/associations and independently repeats pure public validation/Preview.
It consumes no mutable draft and makes no HTTP request. PASS=0, FAIL=1, BLOCKED=2;
storage/unsupported Run errors exit 1.

Validated request: canonical index `000852.SH`, H=21 trading sessions, inclusive
2010-01-01 through 2026-10-28 ending-session anchors, explicit
`trailing_cumulative_return_v1`, `{}` parameters, `on_job_failure=continue`.
Required analyses: `quartiles` with points `[0,0.25,0.5,0.75,1]`; `explicit-bins`
with edges `[-0.2,-0.1,0,0.1,0.2]`, unit `decimal_ratio`.
Actual [Preview](examples/g4-preview.json) reports **1 Job, 2 expected analysis attempts**,
retaining the complete dates, H and original order. No statistical values were computed.

Supported recorder surface: **public Python ResearchPlan/preview_plan only**, selected
after successful public preflight. Python inherits no HTTP caps. This example exceeds
both HTTP's 93-day window and H20 bounds. HTTP selection, even for a bounded candidate,
is explicitly unsupported by this recorder and fails before Preview/POST. The owner
still publishes bounded HTTP Preview for external consumers. No splitting, merging,
truncation, replacement metric or long-history acquisition was implemented.

## Same-Run immutable evidence

Final Run: `fe7d4c9a5c014a248101aff15195ba4a`, in ignored `workbench/.runs/`.
Task v1 frozen SHA-256 remains:

```text
2865ccf73e5736cb00eef383efad0732602e4e848f4b1ec5b53bef55a2b3cb19
```

| Sequence | Record |
| --- | --- |
| 1 | G1 artifact `0b405c3604ff4b4fa97d8950c7e42c03` |
| 2 | G1 PASS, referencing sequence 1 |
| 3 | G2 SKIPPED, exact authorized MVP authentication deferral |
| 4 | G6 SKIPPED, visualization deferred; no visualization performed |
| 5 | G3 artifact `d9b1d15b6ee240d3bb7207f0510a7b4e` |
| 6 | G3 PASS, referencing sequence 5 and preserving G1/G2 associations |
| 7 | Actual Preview artifact `9ce5f354b6634187b41c59fc55eb74b6` |
| 8 | Frozen workflow artifact `d0828edae9644b85a9b7c2d1ecf462de` |
| 9 | G4 attempt artifact `77f9de4db6ce4cecbb2abf84d2758da5` |
| 10 | G4 PASS, evidence ordered as workflow, Preview, attempt |

Authoritative workflow location:
`workbench/.runs/fe7d4c9a5c014a248101aff15195ba4a/blobs/d0828edae9644b85a9b7c2d1ecf462de`.
Its identity and SHA-256 for future explicit authorization are:

```text
artifact_id: d0828edae9644b85a9b7c2d1ecf462de
sha256: 5fa7f59b03ea87c3cf600bc075739dbc47abdc4d105c8338185e740a193ca3c4
```

The workflow binds Preview identity/hash and exact G1/G2/G3 records. Gate and attempt
bind the workflow identity/hash. The manifest's preliminary G1 operational steps and
unresolved G1 research inputs were not repurposed or edited. Fresh reads verify original
manifest and record prefix unchanged and preserved bytes after temporary sources vanish.
No G5 outcome exists. After PASS a new plan requires a new Run.

Committed byte-exact historical snapshots (not transferable evidence for future Runs):

| Snapshot | Bytes | SHA-256 |
| --- | --- | --- |
| [G1](examples/g4-g1.json) | 1294 | `5ac7c2c23afad19e9540d8aae746a2d7fc1880099a18334f44b119ca460e1eb1` |
| [G3](examples/g4-g3.json) | 11130 | `a354f316888f74d37d36eee5dda5e2a4a20635a1339f8b8c17c9da1f18f00387` |
| [Preview](examples/g4-preview.json) | 1166 | `41edcf3ee60ab65eef069924b0f9277451a1c9629aab9e3db976a9a508dfc1ed` |
| [Workflow](examples/g4-workflow.json) | 11299 | `5fa7f59b03ea87c3cf600bc075739dbc47abdc4d105c8338185e740a193ca3c4` |
| [G4 PASS attempt](examples/g4-pass.json) | 5277 | `ed9f1f5b1b80a4be7b1283517c14407e2191cfa8f9273bb3a88e0a0a1cf30cf2` |

## Failed/blocked acceptance and side effects

Negative Run `330b67ffff844ae29d2c4808b235efc1` first obtained actual same-Run G1/G3
PASS. Submitting the complete 2010-2026 candidate with `execution_surface=http`
produced [G4 FAIL](examples/g4-fail.json), outcome sequence 8, preserving the candidate
and explicit surface-rejection reason. It did not shorten or split the window.
After stopping the owned backend, actual G3 with `--timeout 0.5` failed and appended
sequence 10. A subsequent valid Python G4 candidate produced
[G4 BLOCKED](examples/g4-blocked.json), sequence 12: latest G3 must PASS. Sequence 6's
older G3 PASS did not authorize planning. Neither negative attempt preserved a fake
Preview or frozen workflow. Both raw G4 attempts remain same-Run artifacts.

Initial pure-Preview smoke Run `525ddd86310c43c5b962a3331346ec01` was finalized before
the review added the explicit case-policy snapshot. Its accepted evidence was left
untouched; the final complete delivery uses the new Run above.

The official backend was started only on an unoccupied 8011. Final smoke process PID
3848 logged exactly GET `/openapi.json`, GET `/research/capabilities`, GET
`/research/capabilities/trailing_cumulative_return_v1`, all 200. Stopped only the owned
process after acceptance and confirmed no remaining listener. No HTTP Preview or Execute
POST, provider call, credential resolution, DataLake service/acquisition or cache mutation
was required. Automated acceptance guards actual Research preparation/service-creation
aliases, execution, HTTP calls, numerical compute and SQLite connection creation; it
permits writes only to temporary Workbench evidence.

## Executed verification

All commands ran from repository root:

| Command | Result |
| --- | --- |
| `poetry run pytest workbench/tests market_research/tests market_statistics/tests ui_http/tests ui_cli/tests data_snapshot/tests/test_authority_topology.py data_lake/tests/test_boundary.py -q` | **1491 passed**, 61.46s; includes 56 G4 acceptance cases |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` after final documentation | 21 passed, 10.83s |
| `poetry run ruff check workbench` | Passed |
| `poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation` | Passed, 6 source files |
| `poetry run python workbench/tests/acceptance_example.py` | Existing synthetic two-Run example passed |
| Actual G1/G3/G4 and both fresh-read commands above | Passed; artifacts/manifest/history verified |
| Actual oversized HTTP G4 and latest-failed-G3 G4 | FAIL and BLOCKED as expected; no Preview or execution |
| `git diff --check` and complete staged diff review | Passed before commit; staged example bytes independently matched preserved artifact hashes |

The suite emitted the existing Starlette httpx TestClient deprecation warning.
G4 tests cover missing/failed/stale prerequisites, latest-attempt precedence, unsuitable
or inconsistent G3 bytes/descriptors/target, every missing plan field, invalid codes/H/
windows/parameters/policy, unsupported methods, public statistical validation, full-window
Python and HTTP rejection, public Job expansion order/counts, no market/cache side effects,
same-Run hashes/associations, fresh process retrieval, immutable snapshots, replacement
refusal, corruption, ambiguous PASS, hash-valid but semantically mismatched artifacts,
busy/concurrent changes and CLI statuses. Shared storage and owner suites also pass.

## Reconciliation and remaining G5 blockers

Task v1 requires authorization **before research execution**, expressly allows pure G4
Preview, and separately requires G5 execution authorization. Its prospective G4 phrase
"resolved research inputs and authorization" is reconciled as a required explicit
authorization disposition. Here that disposition is **pending**, with future operations
listed and the exact artifact identity/hash available. No approved amendment is needed;
`task.json` and historical snapshots remain unchanged. G2/G6 remain explicit deferrals.

Full-history Preview legality establishes neither source membership nor complete SSE
Calendar, H-session warm-up, Index fact availability, permissions/credentials or compatible
cache readiness. G5 must obtain explicit authorization for the exact frozen artifact and
resolve those live concerns through the existing public Research boundary. Existing
missing-tolerant Index policy, strict Calendar proof, coverage and overlapping-lookback
dependence remain unchanged. No long-history execution/data acquisition was attempted,
and no result availability or completed research is claimed. G5 itself is unimplemented.

Storage remains local append-only integrity evidence, not hostile-writer attestation.
G4 finalization requires quiescent other writers; multi-record publication is not a
transaction. Read-back fails closed on stale prerequisites or ambiguous associations.
Deterministic validation plus this explicit synthetic Agent example do not prove general
natural-language planning quality. Interactive acceptance belongs to the final Workbench
E2E Goal, along with actual separately authorized execution and eventual output retention.
