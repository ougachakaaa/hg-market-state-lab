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

Acceptance instead calls the private test seam, with `source_kind=synthetic_test`,
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
The snapshot also retains authorization/report references and absolute output paths.
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
