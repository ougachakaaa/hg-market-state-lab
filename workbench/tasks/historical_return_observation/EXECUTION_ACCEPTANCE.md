# WB-05 acceptance and reconciliation

Delivery: 2026-10-29, Asia/Shanghai. Baseline `develop` at required predecessor
`495e69893f98e6a6f1b6c5cdd6ed74bd9a7dc039`. Root Python 3.13.11.
The [request](EXECUTION_REQUEST.md), preserved with trailing whitespace normalized,
authorizes implementation and deterministic
acceptance only. No real market acquisition, credentials or default caches were used.

## Authority and implementation

The existing stable entry reaches the Task catalog, Task entry and new narrow
[execution contract](AUTHORIZED_EXECUTION.md). Workbench/Task architecture, catalog
and usage navigation now identify G5. `record_g5.py` implements the Task-local adapter;
`g5_output.py` projects actual public evidence safely. No business implementation,
shared recorder/contract, Task JSON, dependency, official CLI or HTTP contract changed.
`g5_fixtures.py`, `test_historical_return_g5.py` and `g5_execution_example.py` own
isolated tests/acceptance. [The snapshot](examples/g5-acceptance.json) records actual
delivery identities and numeric observations, not transferable execution approval.

Approved Task v1 SHA-256 remains
`2865ccf73e5736cb00eef383efad0732602e4e848f4b1ec5b53bef55a2b3cb19`.
G5 specializes its already approved separately authorized execution slice. All-required
computation success is distinguished from fact completeness under the published
missing-tolerant policy. WB-02/WB-04 implementation-state notes remain historical.
No Task semantic amendment or new version is required.

## Exact invocation and authorization

See [the usage procedure](README.md#g5-authorized-python-execution-and-result-delivery).
After genuine G1/G2/G3 and frozen G4, run from repository root:

```powershell
poetry run python workbench/tasks/historical_return_observation/record_g4.py --run RUN_ID --read
poetry run python workbench/tasks/historical_return_observation/record_g5.py --run RUN_ID
poetry run python workbench/tasks/historical_return_observation/record_g5.py --run RUN_ID --read
```

The human terminal displays the complete objective, workflow ID/SHA-256, Preview and
Python surface, and acquisition/cache/paid-data effects. Approval requires the displayed
exact sentence plus explicit budget and safe isolation description. Codex/DSH may use
the Python `record_g5(..., authorize=trusted_host_callback)` boundary to resolve the
same actual user reply from its session, with a genuine source reference. An arbitrary
approval JSON file, Task approval or synthetic authorization cannot grant live permission.
If the host cannot establish genuine consent, return None and G5 blocks. Local storage
verifies integrity, not the identity of a speaker; this is explicitly a trusted host duty.

At WB-05 delivery, acceptance called the private test seam, with
`source_kind=synthetic_test`,
explicit isolated invocation function, public Calendar/Index fakes and forbidden socket /
SQLite access during execution. The live wrapper rejects both synthetic authorizations
and frozen synthetic planning provenance. A separate temporary test simulates the trusted
host path with fakes; it does not provide a reusable real-user authorization record.

## Actual deterministic execution and same-Run delivery

Ran `poetry run python workbench/tests/g5_execution_example.py` successfully. The
standalone harness uses actual public Research preparation, observation, conversion,
Batch execution, Statistics compute and association. Only the public upstream services
are fakes. G1/G3 use the existing isolated loopback HTTP fixture. Nothing is served
persistently; no official backend process is started and no Research HTTP POST is sent.
Each case verifies exactly **one execute_batch call**, exact frozen Plan, durable
authorization/intent already present at invocation, original G1/G3/G4 evidence unchanged,
and an independent fresh-process read reproducing the complete output projection.

All artifacts below live in ignored `workbench/.runs/<run_id>/blobs/<artifact_id>`.
Their registration contains hashes and byte lengths; RunStore verifies the actual bytes.
The snapshot also retains authorization/report references. WB-05R changes only its
displayed output paths to store-relative paths; Run IDs, artifact references/hashes and
actual runtime evidence are retained. The private seam above is historical; the
WB-05R reconciliation below removes it from production.
The four Runs have G4 PASS at sequence 10, authorization artifact 11, intent 12,
actual result 13, completion 14, report 15 and G5 outcome 16. The frozen G4 still
records authorization pending; separate authorization evidence never edits it.

| Case | Run | Frozen workflow artifact | Actual result artifact | G5 |
| --- | --- | --- | --- | --- |
| Successful complete fixture | `4e66bd4669064d1e87076bd9589f8793` | `cf2220be32064f269391d334494a512d` | `b5f836849cb84ab18f497f56a25286b9` | PASS |
| Required analysis failure | `703ff8e4d4b445138f5059087cf317de` | `b4e1a28c9b6c4a8f86756366d1d5802d` | `61d00e1bf8464000b7d2113983aa175b` | FAIL |
| Legal partial Index facts | `3d227f4f583a4ca991e003a35736c310` | `b6d675b624e04fddb040e93e70104d5d` | `7acfb4dac03f4dd7b188b15997ee9271` | PASS with partial coverage |
| Complete long-window Plan | `067ffdceff39424b812bb3e7ebeb68fa` | `dbd63aaff71f4ab5968b28ce1091cb86` | `cf1e659fa73049739835500c01f12faa` | PASS on synthetic inputs |

Successful frozen workflow SHA-256:
`de0511fb4df667ff0bde8d5178696e57f5ce00e7d1af56db0540e96b2c5be89a`.
Successful result SHA-256:
`dad2f2b226f010e47766a2110b20e6a5a1ae505c1b5a877527766c87b96f7964`.
Partial-Batch workflow SHA-256:
`24c6899da97ac339598dd1b6b852e837f39ad9445491e5defc582603fbf988da`.
Partial-Batch result SHA-256:
`d0569803b51b410377369355f5e8194407fc9fe9518425d40871e6dc53e82b3b`.
All other exact SHA-256 values are in the snapshot, independently checked against blobs.

The short successful fixture uses `000001.SH`, H=2, inclusive 2024-01-10..2024-01-12,
three eligible observations, complete five-row Index facts including warm-up, quartiles
and explicit bins. Actual median is `0.058252427184465994` decimal_ratio; minimum
`0.05660377358490565`, maximum `0.06000000000000005`. Three values fall in `[0,0.1)`;
other bins and outside counts are zero. No presentation rounding enters preserved output.

The failed case requests two subjects with continue policy. Batch is partial_success:
planned 2, success 1, failed 1, skipped 0. The second Job's quantile raises public
CalculationFailure in the isolated test; its interval_count still succeeds. G5 is FAIL,
retaining both Jobs, all actual raw successful results, observations, input evidence and
failure classification. A completed Python invocation never creates a false PASS.

Partial-facts acceptance omits the 2024-01-10 Index row. Research performs export,
one ensure, final export against the fake. It preserves three candidates: E=1/U=2/X=0,
fact coverage 4/5, observation coverage 1/3, complete warm-up. Both analyses of the one
Eligible sample succeed, so G5 PASS makes no full-coverage claim. Separate tests cover
zero Eligible (conversion failure with all coverage retained), continue/stop, skipped
identities and all failed batches.

The long-window case preserves inclusive 2010-01-01..2026-10-28 with H=21 and one
unpartitioned Job. Its Calendar deliberately has a sparse synthetic open-session set;
five anchors are eligible. This proves full requested range/H reach the official Python
API unchanged, not live Calendar/Index completeness or historical statistical findings.

## Verification and remaining limits

All tooling ran from repository root:

| Command/check | Actual result |
| --- | --- |
| `poetry run pytest workbench/tests market_research/tests market_statistics/tests ui_http/tests ui_cli/tests data_snapshot/tests/test_authority_topology.py data_lake/tests/test_boundary.py -q` | 1530 passed, 93.13s; 39 G5 cases at that revision |
| `poetry run pytest workbench/tests/test_historical_return_g5.py -q` after final safe projection and strict JSON read-back | 41 passed, 23.50s |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` after documentation | 21 passed, 10.88s |
| `poetry run ruff check workbench` | Passed |
| `poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation` | Passed, 8 source files |
| `poetry run python workbench/tests/acceptance_example.py` | Existing synthetic storage example passed |
| `poetry run python workbench/tests/g5_execution_example.py` with final implementation | All four isolated Runs above passed their expected outcomes and fresh-process read-back |
| Final snapshot verification through current `read_execution` | All 16 artifact hashes, four outcomes and raw statistical outputs verified; approved Task bytes unchanged |

The combined suite emitted the existing Starlette httpx TestClient deprecation warning.
Final malformed-export handling additionally proves an actual InvalidPublicInput Batch
remains G5 FAIL with safe retained evidence, rather than becoming an uncertain transport
failure. An unexpected per-analysis exception retains ExecutionFailure classification
without leaking its original exception text.

Coverage includes missing/failed/latest/ambiguous G4; changed workflow/Preview bytes;
missing/wrong authorization objective/hash/surface/side effects/source/budget/isolation;
synthetic/live separation; exact Plan and one call; faithful numeric output; partial and
failed Batches; partial market coverage; safe exception projection; interruption/unknown
result/publication failure with no retry; duplicate intent; concurrent writes; preserved
original evidence; fresh process read; result corruption and false Gate outcomes;
2010-2026/H21 without HTTP caps or partitioning; no providers/default caches or G6.

No full-history live invocation occurred. Live canonical membership, Calendar including
warm-up, credentials/permissions, compatible cache state and actual Index availability
remain unverified for WB-06, together with interactive natural-language acceptance.
The adapter does not enforce provider budgets or redirect caches; the operator must
establish the declared safe execution environment through owner-approved mechanisms.
An intent without confirmed completion remains uncertain and permanently prevents a
second invocation in that Run. No reconciliation override, retry, scheduler, queue,
cache rebuild, new engine, numerical method, business policy or visualization was added.
Local hashes provide integrity, not cryptographic approval provenance or hostile-writer
protection. Publication retains the shared local hard-link/locking limitations.
Exception objects/free text are deliberately omitted; public failure classifications,
requests, counts and safe structural evidence remain locatable.

## WB-05R execution safety and historical read reconciliation

Reconciled 2026-10-29 (Asia/Shanghai), on `develop` from required baseline
`d179f717dcbeacbf6ef1a1a650d4c62fdae3575d`. This section records the current
implementation; the WB-05 results and private-seam description above remain historical.
Delivery followed authority reconciliation, minimal implementation, regression tests
and final review. WB-06 is not implemented or accepted.

The narrow [G5 authority](AUTHORIZED_EXECUTION.md) now distinguishes current execution
eligibility from historical evidence retrieval. `record_g4.read_frozen` still checks
all latest operational prerequisites. G5 read validates the entire store, derives the
committed prefix strictly before its sole stored intent, and applies the same G4
verifier to that prefix. The exact prerequisite sequences, workflow, Preview, approval,
intent, result, completion and report remain bound and verified. Later Gate failures
cannot revoke an intact historical result. No execution cutoff option was added.

The production `_record_g5(..., invoke=..., context=...)` seam and its callable-identity
guard were removed. The ordinary adapter always validates live authorization and invokes
the public `execution.execute_batch` once. Historical `synthetic_test` authorization is
accepted only when validating stored evidence, never by the execution entry. Tests now
simulate the host's user interaction and input provenance in the test directory;
public Calendar/Index service fakes still drive actual Research and Statistics.
Fault injection is confined to test monkeypatches. The simulated-host helper refuses
to reach Research unless its isolated service-fake context is active. It supplies no
real user consent.

Changed files are `AUTHORIZED_EXECUTION.md`, `WORKFLOW_PLANNING.md`, `record_g4.py`,
`record_g5.py`, `README.md`, this acceptance, `examples/g5-acceptance.json`, and
`workbench/tests/{g5_fixtures.py,g5_execution_example.py,test_historical_return_g5.py}`.
No business source, Research/Statistics meaning or calculations, Task JSON, shared
storage, dependencies, official CLI or HTTP contract changed. Root navigation already
reaches these narrow owners; no new authority layer or execution framework is needed.

Concrete new regressions in `test_historical_return_g5.py`:

- `test_completed_execution_survives_later_failed_gate_without_reinvocation`: four
  cases, later G1/G2/G3/G4 FAIL; exact original result in-process and fresh-process,
  unchanged store, no Research invocation, current G4 eligibility still rejected.
- `test_historical_read_fails_closed_on_corrupt_bound_evidence_after_later_g3_fail`:
  five cases, altered Workflow, Preview, authorization, Intent challenge or Result.
- `test_synthetic_authorization_cannot_invoke_public_api_through_wrappers`: direct
  and wrapped public function both remain uncalled with synthetic authorization.
- `test_synthetic_planning_cannot_be_promoted_by_live_style_authorization`: synthetic
  planning blocks before authorization or invocation.
- `test_simulated_host_harness_cannot_execute_without_active_service_fakes`: the
  simulated-host helper cannot call Research outside its isolated fake-service context.

Existing regressions continue to check latest failed/missing/ambiguous prerequisites,
exact frozen Plan and public API, actual numerical output, strict approval, corruption,
concurrency, failed/partial batches, uncertainty and one intent with no automatic retry.

| Verification | Actual result |
| --- | --- |
| `poetry run pytest workbench/tests market_research/tests market_statistics/tests data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py data_lake/tests/test_boundary.py -q` | 1270 passed in 85.54s; existing Starlette TestClient deprecation warning |
| G5 module within that final combined suite | 54 passing cases, including 13 added cases |
| `poetry run ruff check workbench` | Passed |
| `poetry run mypy workbench/run_store.py workbench/tasks/historical_return_observation` | Passed, 8 source files |
| `poetry run python workbench/tests/acceptance_example.py` | Passed; WB-01 synthetic storage acceptance |
| `poetry run python workbench/tests/g5_execution_example.py` | Four expected outcomes and fresh-process reads; one public Batch call per scenario; provider calls 0, default-cache access false |
| Original four WB-05 Runs above, read with execution/socket/SQLite access forbidden | PASS/FAIL/PASS/PASS; all 16 referenced artifact hashes and original statistical outputs verified; all 100 historical files unchanged |
| Baseline comparison of committed example and Task | Only four displayed result paths changed to store-relative paths; Run IDs, references, hashes, outputs and Task bytes unchanged |
| Final diff and documentation navigation | `git diff --check` passed; 42 local link targets verified |

New ignored example Runs, in success/partial-batch/partial-facts/long-window order:
`ce90389204e54f9fae5045fc191b41e3`, `c3b5e2cbe9904d70a7ddad0a96c62e06`,
`021b6649118044688ef22a8968766ce4`, `3f2aab8c64904ef2a3e5cf7c0ffc7e33`.
Their `execution_context=live` identifies the ordinary adapter exercised with service
fakes and a simulated host, not a real provider invocation or actual user authorization.
The committed snapshot remains the original WB-05 evidence; it was not regenerated.

`resource_budget` and `data_isolation` remain declarations, not resource controls.
Prompts and usage no longer imply that nonempty strings establish safe isolation.
Long-history live acceptance requires operator verification of isolation and bounded
acquisition through existing owner-approved facilities. If controls cannot be verified,
do not attempt full-history live execution. This reconciliation performed no real
provider call, paid acquisition or default-cache mutation. Live controls, real-market
readiness and separately approved WB-06 E2E acceptance remain unverified. Workbench
is not a security sandbox and cannot stop arbitrary Python callers bypassing the
official Agent workflow; trusted-host consent and local integrity limits remain.
