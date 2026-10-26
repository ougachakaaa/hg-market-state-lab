# Descriptive Statistics integration authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). Research owns
conversion and business result association. Numerical types/methods/failures remain
exclusively in [Statistics CONTRACT.md](../../market_statistics/CONTRACT.md).
Status: Implementation Ready; runtime readiness is tracked in [Acceptance](ACCEPTANCE.md).

## Conversion boundary

[Sample conversion](SAMPLE_CONVERSION.md) owns SampleProjection, SampleBinding,
convert, validation, conversion failures and conversion acceptance. Only the projected
NumericSample is submitted to Statistics. The retained binding provides exact source,
missing/excluded evidence, coverage and dependence context for association below.

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

Conversion obligations belong to [Sample conversion](SAMPLE_CONVERSION.md).
Association tests cover every retained business field, method/count/unit mismatches,
preservation of Statistics error categories and no recomputation. Cross-stage scenarios
are in [EXECUTION.md](EXECUTION.md).
