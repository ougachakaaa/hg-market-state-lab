# EXEC-01 Single Job implementation acceptance

This is implementation evidence, not a second execution authority. The canonical
boundary is [JOB_EXECUTION.md](JOB_EXECUTION.md), reached through [Execution](EXECUTION.md).
Current readiness is in [ACCEPTANCE.md](ACCEPTANCE.md). Verification date: 2026-10-27.

## Baseline and commit sequence

Branch `reset/market-research-descriptive` started clean at ASSOC-HARD-01 acceptance
`c78e01d6d1ee7e2b24d90b82af8cf4059a7df917`, inheriting the requested
`6172196f2f62f2b2dfb4d07819634c84b64a33e3` (verified with git merge-base --is-ancestor).
Work was completed sequentially, with each diff reviewed and committed before the next:

1. `050fd9062e0ea944ea4dbb3b63606f04b5b80dec` —
   `docs(research): freeze single job execution authority`.
2. `bdcad82934f888ac266dd13112b035127d02dcd1` —
   `feat(research): implement single job executor`.
3. The separate documentation commit containing this record —
   `docs(research): reconcile single job executor implementation`.

The authority commit split the independently consumable Single Job contract from the
Plan/Batch entry. Identity remains owned by Execution and the case. The case's minimal
public validator reuses its existing validator and identity builder; no market rule,
unit conversion, financial formula or numerical method was reimplemented.

## Delivered public boundary and evidence

```python
from market_research.descriptive.execution import (
    InvalidPlan, FailureRecord, AnalysisOutcome, JobResult, execute_job,
)
from market_research.descriptive.association import AnalysisRequest
from market_statistics import QuantileSpec, IntervalCountSpec

job_result = execute_job(
    fixed_job,
    [
        AnalysisRequest("quantiles", QuantileSpec([0, 0.5, 1])),
        AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
    ],
)
```

The [runtime](../src/market_research/descriptive/execution/api.py) uses public facades
only. [Frozen records](../src/market_research/descriptive/execution/models.py) retain
original component references. The [case validator](../src/market_research/descriptive/cases/trailing_return/validation.py)
performs no service creation and returns the existing structural identity.
No duplicate AnalysisRequest or `__all__` was added.

[Deterministic tests](../tests/test_job_execution.py) pass 97 cases. The architectural
boundary tests add 18 rejection cases and enforce precise permitted public symbols,
including no component-to-Executor dependency. Coverage includes:

| Obligation | Actual evidence |
| --- | --- |
| Complete Job and both numerical methods | Success; real public compute results and both valid evidences; exact source, projection, sample, spec, request and raw-result references |
| Legal partial and excluded populations | Missing diagnostics, all Unavailable/Excluded records, fact/observation coverage, typed provenance and fingerprint retained; eligible samples can still yield Success |
| Preflight before I/O | Corrupt/wrong Job types, subject/version/parameters/H/date/window, bad sequence types/emptiness, IDs, specs and exact units rejected as InvalidPlan; no upstream calls; every exact spec validated before preparation |
| Preparation | Public InvalidRequestError/OperationError retained through original UpstreamFailure and exception chain; original request and three obtained InputAttempts retained; all analyses not_attempted |
| Construction | Original prepared inputs/attempts survive formula/accounting failure or pure input-validation failure; actual stage is observation_construction |
| Conversion | Exact source retained for invalid/mapping failures; unavailable/excluded/mixed/empty populations fail NoEligibleObservations; no compute/empty sample |
| Ordered partial failure | First compute/association failure does not block later success; association failure retains actual raw result; last required failure cannot be hidden by earlier success |
| Accounting and purity | One construction/conversion, one compute per attempted request, no deduplication/cache/retry; same specs with distinct exact IDs remain distinct; ordered attributable failures and one outcome per request |
| Unexpected exceptions / cancellation | RuntimeError classified ExecutionFailure at each actual stage with original cause; KeyboardInterrupt, SystemExit and asyncio cancellation propagate at preflight and all runtime stages |
| Immutable inputs and execution scope | Original parameters preserved, frozen result/outcome/failure/sample, tuple results, separate runs produce separate objects with equal business identity; execute_job never returns Skipped |

## Independent public API runs

Executed outside pytest, from the root Poetry environment:

```bash
poetry run python market_research/tests/job_execution_example.py
```

The [executable example](../tests/job_execution_example.py) uses existing public-contract
Calendar/Index fakes, the actual public preparation/construction/conversion/association
and numerical operations. Only the preparation operation's service binding and one
injected compute failure are patched. No live market services or default caches are used.
The fixture has explicit synthetic index identity `000001.SH`, H=2, sample window
2024-01-10..2024-01-12 and closes [100,110,121,110,121] on D0..D4.
It makes no CSI1000 metadata claim.

Observed successful run:

```text
JobResult status = Success
ObservationSet = retained; SampleProjection = retained
sample = (0.20999999999999996, 0.0, 0.0), unit = decimal_ratio
quantiles: success + raw QuantileResult + ResearchAnalysisEvidence
distribution: success + raw IntervalCountResult + ResearchAnalysisEvidence
failures = ()
```

The deterministic handoff test additionally asserts real Quantile pairs
((0,0), (0.5,0), (1,0.20999999999999996)), Interval bin counts (0,2) and overflow 1.
Both evidences reference the same projection and their actual corresponding raw result.

Observed injected partial failure:

```text
JobResult status = Failed
ObservationSet = retained; SampleProjection = retained
quantiles: failed, no fabricated raw result or Evidence
distribution: success + raw IntervalCountResult + ResearchAnalysisEvidence
failures = (analyze / CalculationFailure / request_id=quantiles,)
```

Separate association-injection tests retain the first raw result after association
failure and the second successful evidence, returning a complete Failed JobResult.

## Verification and reconciliation

All requested commands ran in the repository root's unique Poetry environment:

| Command | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | 698 passed |
| `poetry run pytest market_statistics/tests -q` | 171 passed |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | 19 passed |
| `poetry run ruff check market_research market_statistics` | Passed |
| `poetry run mypy market_research/src market_research/tests` | Passed; 37 source files |
| `poetry run pytest -q` | 2016 passed; one existing Starlette TestClient/httpx deprecation warning |
| `poetry check --lock` | Passed; no dependency or lock change |
| `git diff --check` / `git diff --cached --check` | Passed; complete diffs reviewed before commits |
| Independent public API example above | Success and partial failure assertions passed |

Initial implementation checks found one unused test import, Ruff formatting issues and
a test-helper optional-type narrowing issue; all were fixed before the implementation
commit. During documentation reconciliation, topology briefly failed because the new
acceptance file was not yet written; the completed documentation was checked again.

The public API composes the frozen authority without runtime semantic drift. The
Construction call can revalidate public inputs and raise an existing preparation error
type: its original category is retained while failure_stage records the actual call,
as frozen before implementation. Case validation/identity, Observation derivation,
Converter mapping, Statistics numerics and Association checks are reused unchanged.
Execution consumes only authorized public facades; acquisition remains in Preparation.

Current readiness entries and usage navigation now point to Single Job implementation;
prior per-goal acceptance documents retain their historical scope/status. No unresolved
EXEC-01 semantic or implementation gap remains. ResearchPlan, Batch/stop/continue and
actual Skipped generation remain unimplemented EXEC-02 scope. Persistence, cache/replay,
CLI, HTTP and live-data acceptance remain outside this goal. The historical Calendar
cache/live metadata limitation was not rechecked or repaired; no current live-data
success is claimed. No automatic EXEC-02 continuation.

Verdict: **EXEC-01 Complete**.
