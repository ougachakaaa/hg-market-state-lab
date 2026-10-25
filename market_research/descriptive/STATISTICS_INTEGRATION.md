# Descriptive Statistics integration authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). Research owns
conversion and business result association. Numerical types/methods/failures remain
exclusively in [Statistics CONTRACT.md](../../market_statistics/CONTRACT.md).
Status: Implementation Ready; converter and association are Expected Implementation Gaps.

## Conversion boundary

```text
convert(ObservationSet) -> SampleProjection
SampleProjection
  numeric_sample: Statistics NumericSample
  binding: Research SampleBinding

SampleBinding
  source_observation_reference
  ordered_observation_keys
  candidate_count
  eligible_count
  unavailable_count
  excluded_count
  unavailable_records
  exclusion_reasons
  coverage_context
  business_provenance
  sample_dependence_context
```

SampleProjection and SampleBinding are Research-owned semantic records, not Statistics
public types. Only `projection.numeric_sample` is passed to Statistics. There is no parallel
Research NumericSample or generic converter registry/framework.

For one Job's one scalar metric, verify the [ObservationSet](OBSERVATION.md) accounting
and map **all** eligible values, in the case's candidate order, preserving duplicates,
calculated numbers and exact unit. Each position in ordered_observation_keys identifies
the eligible observation at the same position in numeric_sample.values:

```text
len(numeric_sample.values) = eligible_count
len(ordered_observation_keys) = len(numeric_sample.values)
candidate_count = eligible_count + unavailable_count + excluded_count
```

The source reference resolves to the particular ObservationSet/fixed request and its
actual input fingerprint within the JobResult, not merely a subject/window label.
Exclusion reasons retain ordered excluded keys, codes and readable explanations;
unavailable_records retain ordered unavailable keys, anchors and every missing fact
identity/reason/evidence reference. coverage_context retains expected/available fact
units, original public CoverageResults, warm-up context and all ObservationSet ratios,
including Not Applicable. Counts derive from retained source outcome collections.
Business provenance retains observation definition, input references and the fixed Job.
Dependence context retains the case-declared anchor spacing, horizon and overlapping
lookback meaning; it is not an independence claim.

Conversion neither mutates observations nor acquires inputs, recalculates financial
formulas, changes units or adds a second eligibility screen. A value that cannot legally
map into the Statistics binary64 coordinate fails conversion; it is never filtered.
An invalid ObservationSet fails `InvalidObservationSet`; an otherwise unmappable scalar
or unit fails `UnmappableSample`; zero eligible observations fail `NoEligibleObservations`.
These Research categories report stage `conversion`. No NumericSample or successful
statistical result is fabricated for these cases. Numeric legality is inherited from
Statistics rather than redefined here; conversion validation does not replace compute-time
validation.

When zero eligible observations prevent a SampleProjection, JobResult still retains the
valid ObservationSet and its unavailable/excluded records, coverage and preparation
diagnostics. Statistics never receives missing markers or a fabricated empty sample and
does not clean market data or interpret its absence.

## Analysis and association

Call the synchronous public operation:

```text
compute(projection.numeric_sample, analysis_request.spec) -> StatisticalResult
associate(fixed_job, ObservationSet, SampleProjection, request, StatisticalResult)
    -> Research analysis evidence
```

All requests in the Job reuse the same immutable numerical sample and binding.
An association retains subject, metric/version/parameters, horizon, historical window,
observation provenance, SampleBinding, request_id, exact StatisticalSpec and StatisticalResult.
It validates result method/parameters, actual sample_count and unit against the request
and projection. A mismatch is `ResultAssociationFailure` at result_association, never a
new successful result. Research does not reimplement a statistic to verify or replace it.

Statistics errors retain their public category and readable reason under stage `analyze`,
plus Job/request identity. They do not authorize filtering, method substitution or
upstream fallback. [Execution](EXECUTION.md) owns continued attempts and aggregate status.
The Research stage name `analyze` and its analysis request/outcome vocabulary remain
Research-owned; the numerical operation is exclusively Statistics `compute`.
Failed jobs can retain successful numerical results and the binding as partial evidence.
Association failures preserve already returned raw Statistics results as traceable evidence
without claiming a valid completed business association.

A numerical result is not automatically a finding. Interpretation retains population,
subject, metric, horizon, window, actual inputs, method, unavailable/excluded outcomes,
fact and observation coverage and dependence
limitations. No reverse dependency from Statistics to Research or the input owners exists.

## Minimum acceptance obligations

Test all-eligible ordered mapping, equal-valued distinct keys, exact units, exclusions
retained without filtering twice, both count equalities, empty eligibility failure,
malformed sets/unmappable scalars, input immutability and no I/O. Verify only NumericSample
crosses the Statistics boundary; reuse it for multiple requests. Association tests cover every
retained business field, method/count/unit mismatches, preservation of Statistics error
categories and no recomputation. Cross-stage scenarios are in [EXECUTION.md](EXECUTION.md).
