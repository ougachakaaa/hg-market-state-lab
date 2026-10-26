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

## Analysis delegation

Call the synchronous public operation:

```text
compute(projection.numeric_sample, analysis_request.spec) -> StatisticalResult
associate(fixed_job, observation_set, projection, request, statistical_result)
    -> ResearchAnalysisEvidence
```

All requests in the Job reuse the same immutable numerical sample and binding.
The independently consumable [Result Association contract](RESULT_ASSOCIATION.md)
owns ASSOC-01: AnalysisRequest, ResearchAnalysisEvidence, associate, linkage validation,
failure semantics and deterministic acceptance. Conversion remains with its separate owner;
Research does not reimplement a statistic to verify or replace a result.

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

## ASSOC-01 authority reconciliation

The expanded association is an independently consumable bounded contract, so its fields,
validation and failure rules live below this integration entry in RESULT_ASSOCIATION.md.
This keeps conversion, association and orchestration details with unique owners.

| Existing boundary | Reconciled decision |
| --- | --- |
| Execution's ordered request_id/spec pairs | One public AnalysisRequest; plan uniqueness and InvalidPlan remain future preflight |
| Observation Job identity | Existing full structural tuple, accepting equivalent fixed Jobs; no new ID |
| Binding/source provenance | Exact source-object identity and original typed references, no copied context |
| Execution failure taxonomy | ResultAssociationFailure at result_association; caller retains raw results |
| Statistics numerical validation | Public validate_spec/NumericSample legality plus bounded linkage/shape/accounting checks; no recomputation or origin attestation |
| Architecture tests forbidding Association | Reconcile at runtime commit with precise public facade permissions and negative tests; Executor remains prohibited |
| Readiness | Authority only at this commit; implementation and factual acceptance recorded separately |
