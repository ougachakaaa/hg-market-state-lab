# Research HTTP transport authority

This specializes [HTTP ownership](../../ARCHITECTURE.md), cataloged in
[HTTP_PRODUCTS](../../HTTP_PRODUCTS.md). Research owns the
[capability publication](../../../market_research/descriptive/RESEARCH_CAPABILITY.md),
Plan/Batch, observations and evidence. Statistics owns numerical rules. HTTP owns only
strict parsing, bounded synchronous invocation, wire projection and status/error mapping.
Usage belongs to [Research USAGE](../../../market_research/USAGE.md).

## Operations and dependency boundary

| Method/path | Stable operationId | 200 body |
| --- | --- | --- |
| GET /research/capabilities | list_research_capabilities | array of the one complete descriptor |
| GET /research/capabilities/{id} | get_research_capability | same descriptor |
| POST /research/preview | preview_research_plan | plan, ordered jobs, planned_count, analysis_attempt_count |
| POST /research/execute | execute_research_plan | structured Batch response below |

Compose these in the existing repository app/server. HTTP imports only Research public
capabilities, execution, association, observation and case facades plus Statistics root
Specs/results. No private Research plan/preflight import or direct DataLake dependency.
Discovery and preview create no DataLake service and perform zero market I/O. Neither
claims provider, credentials, cache readiness or availability. Unknown ID is typed 404.

## Strict request and normalized identity

Preview accepts exactly the eight explicit ResearchPlan fields: metric,
metric_parameters, subjects, horizons, windows, analysis_requests, on_job_failure.
Execute accepts those same top-level fields plus required
`acknowledge_acquisition: true`. False, missing acknowledgment and numeric 1 are invalid.
It acknowledges possible DataLake source-fact acquisition/cache writes; it is not an
authorization or authentication boundary. All nested models forbid extra fields.

Required method-discriminated specs are `{method:"quantile",points:[...]}` or
`{method:"interval_count",edges:[...],unit:"decimal_ratio"}`. No hidden method or
parameters. Transport rejects bool numeric coordinates/horizons, numeric strings,
timestamps, noncanonical date spellings, wrong container/scalar types and unknown tags.
Dates serialize YYYY-MM-DD. Construct original public Specs, AnalysisRequest, DateWindow
and ResearchPlan. Delegate numerical legality and entire-plan validation to their owners;
no parallel validator, Cartesian expansion or normalization of IDs/units/order.

Normalized plan echoes all fields, with binary64 spec coordinates. Each job summary has
fixed_job_spec and a named structural job_identity: metric, subject, metric_parameters,
horizon, horizon_unit, start_date, end_date, anchor_meaning, bounds. It preserves the
original tuple's components without a hash/run ID. Observation keys contain that identity
and anchor. Job array order is Research-owned expansion order.

## HTTP-only resource bounds and execution

Both POSTs reject before any I/O: more than 8 expanded jobs, 4 analyses per Job, 93
inclusive calendar days in any window, or H > 20 trading sessions. These are HTTP limits,
not Research invariants; no splitting. Additional wire resource bounds are 64 KiB request
body, 128 coordinates per spec and 128 characters per request_id. Oversize is typed
request_too_large. Body bytes are bounded before JSON parsing. Length multiplication
checks cardinality only; pure Research preflight still owns expansion/validation.

Execute performs pure preparation/preview first and calls public execute_batch exactly
once. A process-wide nonblocking in-flight guard permits one execution across composed
app instances; overlapping execution returns 409, without a queue or extra delegation.
Run synchronous execution and projection off the event loop; release guard only after
the worker actually finishes, including exceptional paths. Discovery remains responsive.
No retry, background submission, scheduler, cancellation/polling, distributed locking,
persistent run, result registry or result URL. Client disconnect is not cancellation.
Bounds limit plan/result cardinality, not a wall-clock deadline or provider availability;
case-owned backward Calendar discovery remains unchanged.

## Complete bounded wire evidence

200 means a BatchResult was produced, including failed and partial_success. Required
top-level fields are plan, status, planned_count, success_count, failed_count,
skipped_count, job_results and source_identity_limitation. No silent truncation.

Every Job contains fixed_job_spec, job_identity, status, skip_reason,
triggering_failed_job_identity, ordered analysis_outcomes, failures, input_attempts,
prepared_context, observation_set and projection (unavailable context is null).
Ordered outcomes retain exact request_id/spec, status, raw statistical_result or null,
associated boolean, failure or null and not_attempted_reason or null. A failed association
retains the original raw numerical result. Failures retain stage, category, request_id,
Job identity and a safe reason; HTTP never reruns failure classification.

Tagged quantile results retain method, estimator, ordered points_and_values,
sample_count and unit. Tagged interval_count retains edges, bins with both bounds and
inclusion flags/count/frequency, underflow/overflow counts/frequencies, sample_count/unit.
Successful numeric payloads are finite JSON numbers; zero and null remain distinct.
If a rejected raw numerical result contains NaN/infinity, retain that coordinate as
`{"kind":"non_finite","value":"nan|positive_infinity|negative_infinity"}` in the
same ordered result field. This explicitly tagged anomaly is legal only on failed raw
results, never successful results or NumericSample values; it avoids invalid JSON numbers
without discarding a returned association-failure result.

Observation projection includes definition, all candidate anchors and E/U/X counts,
ratios (null when inapplicable), every eligible key/anchor/value, every unavailable key,
missing dependency (role, required public fact, reason, input reference, diagnostics)
and present endpoint, every excluded key/reason/offending endpoint. Include overall,
warm-up and sample market coverage with expected/available/absent keys/counts/ratio;
sample dependence with every anchor/lookback span. Provenance includes original input
profile/fingerprint and endpoint requirements. Do not recompute fingerprints or results.

Projection contains NumericSample values/unit/count and ordered binding observation keys,
source_job_identity and source_input_fingerprint; binding coverage/provenance/dependence
reference the single containing observation_set rather than duplicating it per analysis.
`associated` references that Job's actual projection/source and is not origin attestation.

prepared_context lists final Calendar and Index public export summaries. Every InputAttempt
retains its actual tagged Calendar/Index request (scope and date bounds), preliminary/final
export summaries (dataset/view/schema, coverage and record_count), and Ensure counters plus
all failed unit identities. Absent attempts/results are null; malformed public evidence is
explicitly tagged invalid_public_shape, never serialized as an arbitrary object.

For safe delivery, exception-derived reason/not_attempted text and provider UnitFailure
diagnostic strings are replaced with explicit category/stage or unit-failure summaries;
count, identity and classification remain complete. Case-owned finite reason codes and
exclusion explanations remain. Original exception objects/chains/text, exact final and
preliminary Index/Calendar rows, canonical input bytes and richer PreparedInputs/Evidence
objects remain Python-only. No repr graphs, private paths, credentials, tracebacks or huge
duplicate exports. HTTP evidence identifies consumed source data but cannot reconstruct
the full exports, attest numerical origin, promise independence or establish prediction.

## Closed error map and OpenAPI

Envelope: `{"error":{"kind":"invalid_request","detail":"...","param":null}}`.
detail is safe explanatory text, never raw exception text; param is a declared field or
null. Unknown fields are rejected, never echoed into details. Research-scoped body
validation (including malformed JSON) must precede the sibling chain/premium handler.

| Status | kind | Meaning |
| --- | --- | --- |
| 400 | invalid_request | malformed/strict body, public constructor/InvalidPlan preflight failure; no I/O |
| 404 | capability_not_found | unsupported descriptor ID |
| 400 | request_too_large | HTTP-only bound; no I/O |
| 409 | execution_busy | process already executing; no extra execute_batch |
| 500 | internal_error | unexpected transport/runtime defect, safe detail |

Well-formed failed Job/Batch results remain 200 with structured partial evidence. OpenAPI
publishes concrete tagged request/result/evidence/error schemas, required fields, examples,
unique operation IDs and actual response statuses. Remove the unused framework 422 only
where its real 400 response is documented. MO routes, error schemas and generated per-feature
contracts retain their semantics; global composition tests add the four Research paths.

Default launch remains `poetry run lab serve backend`, 127.0.0.1:8011, no auth, CORS or
public deployment added. No frontend Research consumer is admitted: run sibling generation
and freshness checks but create no Research TypeScript artifacts. OpenAPI/local HTTP alone
does not connect a cloud agent; registered reachable tooling is required. No MCP, cloud
hosting, cache repair, historical-run retrieval or additional Research engine is introduced.
