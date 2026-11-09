# Research Observation, conversion, association and execution usage

The stable human/agent entry is [USAGE.md](USAGE.md): the one admitted capability,
Python plan, HTTP discovery → preview → execute, evidence interpretation and operational limits.
This README retains component-level Python examples.
Deterministic HTTP acceptance, bounded real-market validation and current limits are
recorded in [Acceptance](descriptive/ACCEPTANCE.md); live HTTP remains unverified.

This is usage documentation. Contracts are owned by [the module authority](ARCHITECTURE.md)
and its [Observation boundary](descriptive/OBSERVATION.md).

From the repository root, install the root package with `poetry install --only-root`
after changing source registration. Run Python through `poetry run python`:

```python
from datetime import date

from market_research.descriptive.observation import DateWindow, ObservationJobSpec, observe

# Supply a full canonical index_code confirmed against public index metadata.
job = ObservationJobSpec(
    subject=verified_index_code,
    metric="trailing_cumulative_return_v1",
    metric_parameters={},
    horizon=2,
    historical_sample_window=DateWindow(date(2024, 1, 10), date(2024, 1, 16)),
)
result = observe(job)
```

Inspect `result.candidate_anchors`, `eligible_observations`, `unavailable_observations`
and `excluded_observations`. Each observation has a stable key and anchor; unavailable
observations retain endpoint dependencies and diagnostic reasons. Counts and ratios are
derived properties. `None` ratios mean Not Applicable for zero denominators.

`result.market_fact_coverage` separates `overall`, `warm_up` and `sample`, each with
expected/available/absent keys, counts and a ratio. Legal non-positive closes remain
available facts while causing business exclusions when both endpoints exist.

`result.provenance` retains canonical bytes, `input_fingerprint`, endpoint requirements
and `prepared_inputs`. The latter contains actual Calendar / Index requests, exact final
exports (including original coverage) and every preliminary Export / Ensure attempt.
The digest identifies the consumed v2 inputs; retained facts allow inspection.

For deterministic fixtures or independent pure use:

```python
from market_research.descriptive.cases.trailing_return import (
    construct_observations,
    prepare_inputs,
)

prepared = prepare_inputs(job, calendar_service=calendar_fake, index_service=index_fake)
result = construct_observations(job, prepared)
```

Preparation failures expose `stage`, `category`, `request` and obtained `evidence`;
`UpstreamFailure.__cause__` retains the public DataLake error. An incomplete Calendar
fails preparation; a validated partial Index Export can produce unavailable outcomes.
Construction makes no upstream calls. This API requires no Statistics, Converter or Executor.

Current status, validation evidence and limitations are in [Acceptance](descriptive/ACCEPTANCE.md).

The bounded isolated real-market validation is recorded in
[Acceptance](descriptive/ACCEPTANCE.md#real-market-validation-evidence) and uses fresh
isolated Dataset storage. Its [opt-in harness](tests/live_e2e_acceptance.py) runs only
when explicitly invoked; ordinary pytest remains deterministic. The historical
incompatible default Calendar cache was neither repaired nor changed.

## Pure scalar conversion and Statistics reuse

For an existing legal ObservationSet such as `result` above, the independent public
[converter](descriptive/SAMPLE_CONVERSION.md) performs no acquisition or statistics:

```python
from market_research.descriptive.conversion import (
    InvalidObservationSet,
    NoEligibleObservations,
    UnmappableSample,
    convert,
)
from market_statistics import IntervalCountSpec, QuantileSpec, compute

projection = convert(result)
sample = projection.numeric_sample
binding = projection.binding
assert binding.source_observation_reference is result
assert len(binding.ordered_observation_keys) == sample.sample_count == binding.eligible_count

quantile_result = compute(sample, QuantileSpec(points=[0, 0.5, 1]))
interval_result = compute(
    sample, IntervalCountSpec(edges=[-0.2, 0, 0.2], unit=sample.unit),
)
```

`SampleProjection` contains the Statistics NumericSample and Research SampleBinding.
The same binding and source serve both requests. `binding.unavailable_records` and
`binding.exclusion_reasons` are the complete original typed outcome records;
`coverage_context`, `business_provenance` and `sample_dependence_context` retain original
objects. Counts and observation/unavailable/excluded ratios are read-only source properties.
The exact fixed request, definition and Job identity are reachable through the source.

Conversion raises `InvalidObservationSet` for malformed sources, then
`NoEligibleObservations` for a valid source with no Eligible values, then
`UnmappableSample` for Statistics sample-construction rejection. All expose stage
`conversion`, category and readable exception text; translated failures retain their cause.
The caller retains the source and diagnostics when conversion fails. No JobResult or
business result association is produced. See the
[conversion contract](descriptive/SAMPLE_CONVERSION.md#deterministic-acceptance) and
[Acceptance](descriptive/ACCEPTANCE.md).

## Pure statistical result association

For the same `job`, ObservationSet `result` and `projection` above:

```python
from market_research.descriptive.association import AnalysisRequest, associate

request = AnalysisRequest("return_quantiles", QuantileSpec(points=[0, 0.5, 1]))
numerical_result = compute(projection.numeric_sample, request.spec)
evidence = associate(job, result, projection, request, numerical_result)
assert evidence.request is request
assert evidence.statistical_result is numerical_result
assert evidence.projection is projection
assert evidence.source_observation_reference is result
```

`ResearchAnalysisEvidence` is frozen; source question, keys, coverage, typed provenance
and dependence remain reachable through its original projection/binding/source.
`ResultAssociationFailure` reports stage/category, readable reason and attributable
Job/request identity; the caller retains the raw result when linkage fails.
Association validates source identity, exact request/result parameters, sample mapping,
units/counts and bounded result structure without conversion, computation or I/O.
A bare result has no sample identity: association cannot prove its hidden computation
origin or independently certify its mathematical payload. Use the actual corresponding
public compute result. This pure component does not execute Jobs or persist/cache evidence.
See the
[contract](descriptive/RESULT_ASSOCIATION.md) and [Acceptance](descriptive/ACCEPTANCE.md).

## Single Job execution

For the explicit fixed `job` above, the public executor performs preflight, preparation,
construction, conversion and every required analysis/association in declared order:

```python
from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.execution import execute_job
from market_statistics import IntervalCountSpec, QuantileSpec

job_result = execute_job(
    job,
    [
        AnalysisRequest("quantiles", QuantileSpec([0, 0.5, 1])),
        AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
    ],
)
```

Inspect `job_result.status`, ordered `analysis_outcomes` and `failures`. Each outcome
retains its original request/spec, raw result when returned, successful evidence or
attributable failure. All analyses share one projection. A failed analysis or association
does not prevent later requests; any required failure makes the Job Failed. Preparation,
construction or conversion failure returns all requests as not_attempted, retaining
obtained inputs, attempts and observations. InvalidPlan instead raises before I/O.
`input_attempts` exposes original preparation evidence. Skipped is reserved for Batch.

Run the independent deterministic example with public-service fakes, without market I/O:

```bash
poetry run python market_research/tests/job_execution_example.py
```

It asserts and prints both Success (two successful evidences, no failures) and Failed
(quantile failure followed by successful distribution evidence) with complete ordered
outcomes and retained source/projection. The [contract](descriptive/JOB_EXECUTION.md) and
[Acceptance](descriptive/ACCEPTANCE.md) record the exact scope.

## Batch execution

```python
from datetime import date
from market_research.descriptive.association import AnalysisRequest
from market_research.descriptive.execution import ResearchPlan, BatchResult, execute_batch
from market_research.descriptive.observation import DateWindow
from market_statistics import IntervalCountSpec, QuantileSpec

plan = ResearchPlan(
    metric="trailing_cumulative_return_v1",
    metric_parameters={},
    subjects=["000001.SH", "000300.SH"],
    horizons=[2, 5],
    windows=[
        DateWindow(date(2024, 1, 8), date(2024, 1, 9)),
        DateWindow(date(2024, 1, 9), date(2024, 1, 10)),
    ],
    analysis_requests=[
        AnalysisRequest("quantiles", QuantileSpec([0.1, 0.5, 0.9])),
        AnalysisRequest("distribution", IntervalCountSpec([-0.2, 0, 0.2], "decimal_ratio")),
    ],
    on_job_failure="continue",  # mandatory; alternatively "stop"
)
batch: BatchResult = execute_batch(plan)
```

Construction snapshots the input sequences and explicit empty parameters. execute_batch
revalidates the entire Plan and every expanded fixed Job before any input service or I/O.
This example expands in subjects → horizons → windows order to eight JobResults and
sixteen ordered AnalysisOutcomes. Each attempted Job independently calls execute_job.
Normal execution uses authorized DataLake services; the standalone example below supplies
synthetic public-service fakes instead, with no live metadata claim or cache access.

Inspect `batch.plan`, `batch.job_results`, derived `planned_count`, `success_count`,
`failed_count`, `skipped_count` and `status`. Continue executes every planned Job after
failures. Stop retains the first Failed Job's complete analysis outcomes and marks each
later Job Skipped with the failed identity, policy reason and not_attempted analyses.
Original raw results, Evidence, Coverage and Provenance remain reachable on each Job.
InvalidPlan raises before I/O; an unexpected Single Job contract violation propagates
instead of returning fabricated completion. No persistence, retry or cache is added.

Run the independent deterministic example from the repository root:

```bash
poetry run python market_research/tests/batch_execution_example.py
```

It asserts eight successful independent Jobs, then injects failure in Job two:
continue yields 7 Success / 1 Failed / 0 Skipped; stop yields 1 Success / 1 Failed /
6 Skipped. Each attempted Job still completes both required analysis attempts.
See the [Batch contract](descriptive/BATCH_EXECUTION.md) and
[Acceptance](descriptive/ACCEPTANCE.md).

## Futures Basis online Python application

The independent case facade exposes `FuturesBasisOnlineApplication`,
`OnlineServices`, `OnlineError` and `standard_report_request`. Create one application
instance per backend process. `submit(FuturesBasisRequest(...), owner_scope)` returns
the accepted `PENDING` snapshot immediately; `get_run(run_id, owner_scope)` returns
the persisted status, and `get_report(run_id, owner_scope)` reads the completed WP5
reader projection without running research. `OnlineError.kind` is the safe application
error for the HTTP adapter to map. The server selects `r01a_standard_v1`; callers
cannot supply statistical parameters.

The default store is `market_research/.runtime/futures_basis_online/` (Git ignored).
An absolute server-owned `LAB_FUTURES_BASIS_RUN_ROOT` can be supplied through the
repository root `.env` or process environment. Single-process operation is required;
no queue, cancellation, HTTP route or Publication admission is provided by this API.
See the [online authority](descriptive/cases/futures_basis/ONLINE_APPLICATION.md).
