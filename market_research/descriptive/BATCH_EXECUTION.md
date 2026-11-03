# Descriptive Batch execution contract

This contract specializes [Execution](EXECUTION.md). It owns EXEC-02 ResearchPlan,
entire-plan preflight, expansion, continue/stop, Skipped construction and BatchResult.
Attempted Job stages remain owned by [Single Job](JOB_EXECUTION.md). Only the published
Index Trailing Return case is supported; no case registry is introduced.

## Public API and immutable values

```python
from market_research.descriptive.execution import ResearchPlan, BatchResult, execute_batch
# execute_batch(plan: ResearchPlan) -> BatchResult
```

ResearchPlan is frozen with all eight explicit fields below. on_job_failure has no default.
The four sequence inputs accept collections.abc.Sequence, rejecting str, bytes,
bytearray, sets, mappings and generators. Snapshot declaration order into tuples; retain
original immutable AnalysisRequests and Statistics specs. DateWindow is the existing
public strict date-only value: datetime is illegal. The current case accepts only an
explicit empty parameter mapping; copy it into a read-only mapping without normalizing
or discarding values. No nested mutable parameter value can enter an accepted Plan.
Any future parameter semantics require case authority. Constructor validation raises
InvalidPlan for illegal inputs; execute_batch must independently revalidate all fields.

## ResearchPlan and preflight

```text
ResearchPlan
  metric: one versioned metric definition
  metric_parameters: one fixed explicit parameter set
  subjects: ordered non-empty sequence
  horizons: ordered non-empty sequence
  windows: ordered non-empty sequence of public date-only DateWindow
  analysis_requests: ordered non-empty sequence of Research-owned AnalysisRequest
  on_job_failure: continue | stop
```

The single public [AnalysisRequest](RESULT_ASSOCIATION.md#public-operation-and-carriers)
encodes the existing ordered `(request_id, Statistics-owned StatisticalSpec)` vocabulary.
Executors reuse it; no competing request model is authorized. Local request
construction validation and association-boundary rejection do not implement InvalidPlan:
plan/direct-job preflight owns that classification and ID uniqueness.
Executors pass each actual corresponding compute result directly to association; a bare
Statistics result carries no authenticated sample identity.

All listed analyses are required in V1; no optional-analysis policy exists.
Each horizon is a strictly positive integer, excluding bool. Each date is a date value,
not datetime or raw text; each window satisfies start <= end. Subject and metric
parameters must satisfy the selected case's contract, including canonical identities.
Collections are sequences, not scalar strings, sets or unordered maps. No hidden defaults
are supplied for dates, horizon, analysis parameters or on_job_failure.

Before **any** DataLake I/O, validate the entire plan's structure, semantic types,
non-emptiness, metric/case parameters, horizon/windows, duplicate elements, request
identities and standalone specs. Use the Statistics public `validate_spec`; do not copy its
algorithm-level validation. An IntervalCount unit must also match the case-declared
metric unit before I/O. Future market-window limits follow the selected upstream's
public request contract; do not silently truncate dates.

Exact duplicate subjects, horizons or windows are InvalidPlan, not silently deduplicated.
Different overlapping windows remain independent Jobs. request_id is a non-empty string,
unique within the plan's analysis_requests (therefore in each expanded Job); retain it
unchanged. Identical specs with different request_ids are legal distinct explicit
requests; duplicate IDs are invalid even with different specs. No method-level request
deduplication occurs. Invalid specs become InvalidPlan with the originating
InvalidStatisticalSpec context. InvalidPlan raises before execution and produces no
BatchResult or fake partially successful subset.

## Expansion and identity

```text
for subject in subjects:
    for horizon in horizons:
        for window in windows:
            yield ObservationJobSpec(subject, metric, metric_parameters, horizon, window)
```

This is the Cartesian product Subjects × Horizons × Windows in declared order.
Analysis requests are attached to each Job, not a fourth observation dimension.

## Batch execution and totals

V1 runs Jobs sequentially in expansion order, without automatic retries, concurrency,
scheduler, queue or persistent task state. on_job_failure is mandatory:

| Policy | Behavior after a Failed Job |
| --- | --- |
| continue | Execute the next independent Job. |
| stop | Finish recording the failed Job, including all its analysis attempts, then mark every later unattempted Job Skipped with the triggering failed Job identity. |

```text
execute_batch(ResearchPlan) -> BatchResult
BatchResult
  plan / on_job_failure
  job_results: every expanded Job, in expansion order
  planned_count / success_count / failed_count / skipped_count
  status: success | partial_success | failed

planned_count = success_count + failed_count + skipped_count
```

Counters derive from Job statuses. success means all Jobs Success (no skipped Jobs).
partial_success means at least one Success and at least one Failed. failed means zero
Success and at least one Failed. A non-empty valid plan cannot yield only Skipped Jobs:
the only skip trigger is an actual preceding failure. Skipped never hides failed attempts.
Batch owns no formulas, upstream fallback or silent population changes.

## Minimum deterministic acceptance

| Scenario | Required outcome |
| --- | --- |
| Two subjects × two horizons × two windows | Eight Jobs in exact nested-loop order; analyses do not multiply Jobs |
| Empty/wrong-type dimensions, bool/zero/negative horizon, inverted/timestamp dates, exact duplicates, bad policy/IDs/specs | InvalidPlan before any public input call |
| Different overlapping windows | Distinct Jobs, both retained |
| Reordered plan lists / changed analyses only | Same observation business identities, differing traversal/request associations as declared |
| One of two analyses fails | Both attempted in order; one failed outcome, one retained success; Job Failed |
| Preparation/construction/conversion fails | Job Failed at correct stage; all analyses not_attempted |
| Result mismatch/association failure | Job Failed at result_association, raw returned result retained; other requests attempted |
| Three Jobs S/F/S, continue | partial_success; planned 3 = success 2 + failed 1 + skipped 0 |
| Three Jobs S/F/(unattempted), stop | partial_success; 3 = 1 + 1 + 1; skip references second Job |
| First Job fails, stop | failed; remaining Jobs Skipped; zero successes |
| All Jobs succeed / all attempted Jobs fail with continue | success / failed respectively; complete ordered accounting |

## Complete preflight before execution

Validate plan type, all fields, non-empty sequence shapes, duplicates and explicit policy.
Expand all fixed ObservationJobSpecs in the nested order above, then validate **every**
expanded Job using the existing execution-owned pure Single Job preflight. Reuse case
public validate_job and Statistics public validate_spec; do not duplicate their rules.
IntervalCount compatibility reads the case public immutable DEFINITION.unit, the same
source used by construction. This validates all canonical subjects, exact metric/version
and case parameters, positive non-bool horizons, strict DateWindows including the case's
Asia/Shanghai current-date limit, request types/IDs/specs and exact units.

No service creation, export/ensure or execute_job may occur before all expanded Jobs
pass. If the eighth Job is illegal, the first seven must not execute. Never interleave
expansion and execution. InvalidPlan retains readable cause and applicable originating
exception chain; no partial BatchResult is returned. Single Job's own revalidation remains.
Two subjects x two horizons x two windows produce eight Jobs; two requests produce sixteen
AnalysisOutcomes, never sixteen Jobs. Different overlapping windows execute independently.

## Public Single Job composition

After full preflight, call `execute_job(fixed_job, plan.analysis_requests)` for each
attempted Job and retain its actual JobResult. Batch never executes preparation, producer,
Converter, Statistics or association itself. Each Job independently uses EXEC-01; no
implicit input/ObservationSet/projection sharing or cache across Jobs or runs is added.
Continue preserves all later results after failure. Stop waits for the entire failed Job,
including all required analysis attempts, before skipping later Jobs.

Only Batch policy creates Skipped through one minimal execution-owned construction
operation. Each skipped result retains the expanded fixed_job_spec and structural identity,
status Skipped, prepared_inputs/observation_set/projection None, failures (), explicit
skip_reason and triggering_failed_job_identity of the first actual Failed Job. Every
original request has an ordered not_attempted outcome with that policy reason, no raw
result, evidence or failure. execute_job still produces Success/Failed only. Skipped is
not a failed execution attempt; never fabricate InputPreparationFailure or Evidence.

## Result consistency and contract violations

BatchResult is frozen and retains plan and ordered tuple[JobResult, ...]. All counters
and status are read-only derived properties, without redundant stored counts. The retained
plan exposes on_job_failure. Always `len(job_results) = planned_count`, which must also
equal the complete expansion size. A non-empty valid Plan cannot produce only Skipped.

Runtime collection and direct BatchResult construction reject inconsistent accounting
with ValueError: wrong result type/count/order, fixed spec or identity; missing/reordered
original requests; illegal status; Success without all required successful raw results
and linked Evidence; Failed without a recorded failure; inconsistent analysis record
shapes; skipped input/results/failures; or policy/trigger inconsistent with the first
failure. Failure records retain the Job identity and attributable request, with ordered
outcome failures corresponding to Job failures. Check component references and existing
stage shapes, without revalidating Observation/Statistics mathematics. Original objects
and all partial raw results, Evidence, Coverage and Provenance remain reachable unchanged.

If execute_job unexpectedly raises after preflight, returns Skipped or violates its
contract, propagate/reject the problem. Never forge Failed results or completion to hide
it. Cancellation and process termination do not promise a complete BatchResult.
No concurrent/async batch, retry, scheduler, queue, persistence, replay, cache, CLI, HTTP,
report rendering, new case/numerical algorithm or Live Market E2E is introduced.

Deterministic acceptance additionally covers eighth-Job rejection before any I/O, all
container/duplicate/ID/spec/unit/policy failures, reordering and overlapping windows,
complete attempted analyses before stop, every skipped invariant/trigger, conservation,
retained partial raw results/Evidence/Coverage/Provenance, immutable snapshots and separate
run objects. Architecture checks forbid Batch from directly executing components.
Use public-service fakes/narrow patches and an independent public API example, never real
market/default caches. The Research test suite owns actual verification; it does not create
business semantics.
