# Descriptive execution authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). It owns plan
validation/expansion, Job/Batch control, identity and complete result accounting.
Observation and conversion semantics belong to [OBSERVATION.md](OBSERVATION.md) and
[SAMPLE_CONVERSION.md](SAMPLE_CONVERSION.md); result association to
[STATISTICS_INTEGRATION.md](STATISTICS_INTEGRATION.md); numerical semantics to
[Statistics](../../market_statistics/CONTRACT.md); inputs to [UPSTREAM.md](../UPSTREAM.md).
Status: EXEC-01 authority frozen for the first case; runtime acceptance is tracked in
[Acceptance](ACCEPTANCE.md). ResearchPlan expansion and Batch remain unimplemented.

The independently consumable [Single Job contract](JOB_EXECUTION.md) owns the concrete
`execute_job(fixed_job, analysis_requests) -> JobResult` boundary, pure preflight,
immutable runtime records and stage-specific failure retention. This entry owns the
shared business identity and future Plan/Batch policy; the child cannot override them.

## ResearchPlan and preflight

```text
ResearchPlan
  metric: one versioned metric definition
  metric_parameters: one fixed explicit parameter set
  subjects: ordered non-empty sequence
  horizons: ordered non-empty sequence
  windows: ordered non-empty sequence of inclusive date pairs
  analysis_requests: ordered non-empty sequence of Research-owned AnalysisRequest
  on_job_failure: continue | stop
```

The single public [AnalysisRequest](RESULT_ASSOCIATION.md#public-operation-and-carriers)
encodes the existing ordered `(request_id, Statistics-owned StatisticalSpec)` vocabulary.
Future Executors reuse it; no competing request model is authorized. Local request
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

A Job's stable business identity is the structural tuple of case/metric definition
identity and version, canonical subject identity, all metric parameters, horizon with
its unit, and window bounds with their anchor/inclusion semantics. Parameter names are
compared in canonical name order; collection-valued parameters follow the case's defined
order/equality. For the first case this tuple is specified in its authority. An
implementation may use this tuple directly or a collision-safe deterministic encoding;
a hash alone must never silently merge unequal tuples.

Identity never depends on random values, execution time, list position or process ID.
StatisticalSpec is not part of observation identity. Each analysis occurrence is associated
using (job_identity, request_id, exact spec). Results retain the exact request/spec and
execution context, so changing a spec under the same request_id cannot silently overwrite
or reuse a previous result. JobResult instances belong to a particular execution, not a
global cache keyed solely by observation identity. No durable execution ID scheme is
required; execution time, if retained, is context and not business identity.

## Single Job delegation

EXEC-01 freezes the direct single Job operation under [JOB_EXECUTION.md](JOB_EXECUTION.md).
It binds only the published Index Trailing Return case, validates the entire fixed Job
and ordered non-empty request sequence before any upstream call, and reuses public
Preparation, Construction, Converter, Statistics and Association operations. No registry
or generic engine is authorized. All requests are required and run sequentially against
one projection; each actual compute result goes directly to its corresponding association.
Only Success/Failed are produced by this operation. Batch-only Skipped generation and
whole-plan expansion remain EXEC-02 scope.

The child contract owns the concrete carriers and all attempted/not-attempted and failure
rules, including complete ordered accounting and retained partial evidence. The existing
business identity above remains canonical. See its [reconciliation](JOB_EXECUTION.md#authority-reconciliation)
for how the existing component contracts are composed without changing their semantics.

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
