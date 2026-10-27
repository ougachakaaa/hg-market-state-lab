# Research Observation, conversion, association and Single Job usage

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

Verification commands and actual live-data status are in [Acceptance](descriptive/ACCEPTANCE.md).

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
business result association is produced. See [deterministic outputs and reconciliation](descriptive/CONVERSION_ACCEPTANCE.md).

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
[contract](descriptive/RESULT_ASSOCIATION.md) and
[deterministic acceptance](descriptive/ASSOCIATION_ACCEPTANCE.md).

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
outcomes and retained source/projection. The [contract](descriptive/JOB_EXECUTION.md)
and [actual acceptance](descriptive/JOB_EXECUTION_ACCEPTANCE.md) record the exact scope.
ResearchPlan and Batch execution remain unimplemented.
