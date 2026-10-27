# EXEC-02 Batch implementation acceptance

This record contains implementation facts and local verification, not a second business
contract. The canonical boundary is [Batch execution](BATCH_EXECUTION.md), reached through
[Execution](EXECUTION.md); current readiness is in [Acceptance](ACCEPTANCE.md).
Verification date: 2026-10-27. No CI or live-market success is claimed.

## Baseline and commit sequence

Branch `reset/market-research-descriptive` started with a clean worktree at required
baseline `78b2a6ed3e3e87c718a142a032c90928acf8a345`. ASSOC-HARD-01 and EXEC-01 were
already completed in its history. No reset, overwritten work or upstream semantic
change was needed. Each scope was reviewed and committed before beginning the next:

1. `7207cde62c0fea53fbb765365d89ab08d859eb35` -
   `docs(research): freeze descriptive batch execution authority`.
2. `3745f6e84f0a930b328f682db04b15c1d5a2b5fb` -
   `feat(research): implement descriptive batch executor`.
3. The separate documentation commit containing this record -
   `docs(research): reconcile descriptive batch execution implementation`.

The authority commit moved Plan/Batch details into their narrow owner while retaining
shared business identity and navigation in Execution. Single Job and the case document
explicitly declared the case-owned immutable unit source before runtime changes.
Baseline gaps and unchanged component contracts are recorded in Batch's reconciliation.

## Public boundary and implementation evidence

```python
from market_research.descriptive.execution import ResearchPlan, BatchResult, execute_batch
# Existing execute_job, JobResult, AnalysisOutcome, FailureRecord and InvalidPlan remain.
```

[Plan values and preflight](../src/market_research/descriptive/execution/plan.py) snapshot
accepted sequences into tuples and explicit empty parameters into a read-only copy.
Constructor validation and execute_batch use pure complete preflight; every expanded
fixed Job passes the existing Single Job preflight before any attempted execution.
[Batch runtime](../src/market_research/descriptive/execution/batch.py) calls execute_job
for each attempted Job and retains its actual JobResult. It owns only sequential policy,
one minimal Skipped factory, bounded record checks and derived accounting properties.
The case public `DEFINITION` aliases the existing frozen construction definition; shared
Single Job preflight reads its unit. No new financial/numerical validation engine exists.
Facade exports use explicit aliases and direct facade tests, without `__all__`.

[Behavior tests](../tests/test_batch_execution.py) and
[Batch boundary tests](../tests/test_batch_boundaries.py) add 97 deterministic cases to
the existing 698 Research tests. Production component imports remain guarded by the
[existing boundary suite](../tests/test_conversion_boundaries.py). Evidence includes:

| Obligation | Actual evidence |
| --- | --- |
| 2 x 2 x 2 expansion / 16 analyses | Exact nested order, original public execute_job return objects, separate projections, unchanged original requests/results/evidence |
| Entire-plan preflight | Invalid late subject/H/window rejected; injected eighth case-specific validation failure rejects all eight with no execute_job or service creation; original exception chained |
| Public input legality | Constructor and execute_batch reject empty/wrong containers, generators, duplicates, noncanonical subjects, metric/version/parameters, bool/zero/negative/non-int H, timestamps/inverted/future windows, bad IDs/specs/units/policy; InvalidStatisticalSpec cause retained |
| Order and identity | Reordered dimensions reverse traversal without changing fixed structural identities; distinct overlapping windows execute independently; identical specs with distinct IDs both run |
| Continue | S/F/S retains all three original results; 3 = 2 + 1 + 0, partial_success; all attempted failures yield failed |
| Stop | S/F/Skipped yields 3 = 1 + 1 + 1; first failure yields 3 = 0 + 1 + 2; later jobs create no services or I/O |
| Failed Job completeness | First quantile failure still attempts and retains distribution success before Batch applies stop; association failure retains original raw result and other successful Evidence |
| Skipped invariants | Original fixed spec/identity, first failure trigger, readable policy reason, no inputs/projection/observations/failures, ordered not_attempted outcomes with no result/evidence/failure |
| Partial population retention | Failed association with a partial population retains raw result, successful Evidence, 4 candidates / 2 eligible / 2 unavailable, 50% observation coverage, 5/6 fact coverage, missing diagnostics, original prepared inputs and v2 fingerprint/provenance references |
| Early stage failure | Preparation failure retains original exception; all-unavailable input fails conversion retaining zero-eligible ObservationSet; every analysis not_attempted before later Skipped Jobs |
| Result consistency | Wrong count/order/identity/status, false Success, missing failures/results/evidence, reordered requests, malformed skipped context/trigger and non-tuple Batch storage rejected; no fabricated replacement result |
| Immutable and run-local | UserList/list/mapping changes after construction cannot alter accepted Plan; Plan and BatchResult frozen; separate runs retain distinct Job/Observation/projection objects |
| Dependency boundaries | Batch cannot import component execution operations, DataLake creation, Statistics compute/validation or private components; only execute_job does attempted work; Plan reuses shared pure preflight |
| Contract exceptions / cancellation | Unexpected executor exceptions, KeyboardInterrupt and SystemExit propagate instead of being turned into fake JobResults |

## Independent public API example

Executed outside pytest in the root Poetry environment:

```bash
poetry run python market_research/tests/batch_execution_example.py
```

The [standalone example](../tests/batch_execution_example.py) uses public Calendar/Index
fakes, real public preparation/construction/conversion/Statistics/association, a narrow
second-Job quantile failure injection and a wrapper recording actual execute_job returns.
Each Job receives its own synthetic services/prepared inputs. No live service, credentials,
network or default market cache is used. Synthetic sessions are 2024-01-01..2024-01-10;
they are a deterministic fake calendar, not a real exchange-calendar assertion. The two
explicit synthetic subject identities make no metadata/CSI1000 claim.

Input is subjects [000001.SH, 000300.SH], horizons [2, 5], and windows A =
2024-01-08..2024-01-09, B = 2024-01-09..2024-01-10. Actual expansion:

```text
000001.SH / 2 / A     000001.SH / 2 / B
000001.SH / 5 / A     000001.SH / 5 / B
000300.SH / 2 / A     000300.SH / 2 / B
000300.SH / 5 / A     000300.SH / 5 / B
```

Actual output, summarized from the executable JSON:

```text
success:  planned=8 success=8 failed=0 skipped=0 analyses=16 status=success
continue: planned=8 success=7 failed=1 skipped=0 analyses=16 status=partial_success
          [Success, Failed, Success, Success, Success, Success, Success, Success]
stop:     planned=8 success=1 failed=1 skipped=6 analyses=16 status=partial_success
          [Success, Failed, Skipped, Skipped, Skipped, Skipped, Skipped, Skipped]
```

The stop run makes four actual compute calls for two attempted Jobs; the six skipped
Jobs' twelve outcomes are not_attempted. The failed Job's distribution Evidence survives.
Every successful Evidence references its original request, raw result, projection and
ObservationSet; every attempted Batch entry is the exact JobResult returned by execute_job.

## Local verification and reconciliation

All commands ran from the repository root, using its single Poetry environment:

| Command | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | 795 passed |
| `poetry run pytest market_statistics/tests -q` | 171 passed |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | 19 passed |
| `poetry run ruff check market_research market_statistics` | Passed |
| `poetry run mypy market_research/src market_research/tests` | Passed; 42 source files |
| `poetry run pytest -q` | 2113 passed; one existing Starlette TestClient/httpx deprecation warning |
| `poetry check --lock` | Passed; no dependency/lock changes |
| `git diff --check` / `git diff --cached --check` | Passed; complete authority, implementation and reconciliation diffs reviewed before their respective commits |
| Standalone public Batch example above | All success, continue and stop assertions passed |

Initial checks found a fake row whose second subject code and symbol disagreed, formatting
issues and type-narrowing/test annotations; these were corrected before the implementation
commit. Existing public input validation rejected the malformed fake without relaxing
any market contract. No unresolved EXEC-02 implementation or semantic gap remains.

| Canonical concern | Runtime reconciliation |
| --- | --- |
| Plan values / Job identity | Immutable explicit snapshots; case validator supplies existing structural identity; no IDs/hashes/defaults added |
| Entire-plan preflight | All expanded jobs validated by the same Single Job pure preflight before execution |
| Expansion order | Subjects then horizons then windows; requests remain ordered analyses |
| Single Job reuse | Actual public execute_job called once per attempted Job; original return objects retained |
| Unit ownership | Existing case DEFINITION published read-only; both entry points reuse its exact unit through shared preflight |
| Continue / stop / Skipped | Sequential complete Job execution, first-failure trigger, one factory and honest unattempted outcomes |
| Count/status conservation | Derived from validated complete JobResult tuple; policy/count/order checks reject contradictions |
| Provenance retention | Original prepared evidence, source, projection, Coverage, StatisticalResult and ResearchAnalysisEvidence retained |
| Public dependency boundaries | Acquisition remains in case Preparation; Batch does no component execution; independent component contracts unchanged |

Current module/root navigation, usage and readiness now reflect EXEC-02. Historical
per-goal acceptance records retain their original scope. Observation formula/population,
Converter mapping, Association validation and Statistics numerical/opaque-unit semantics
have not changed. Persistence, result replay/cache, CLI/HTTP, new cases and report rendering
remain unimplemented/out of scope. Live Market E2E remains unperformed; the historical
Calendar-cache/metadata limitation is not rechecked, repaired or presented as current
live success. No user cache was changed. Stop at EXEC-02; no later Goal is started.

Verdict: **EXEC-02 Complete**.
