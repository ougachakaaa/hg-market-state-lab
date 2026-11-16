# Research — Calendar Spread Historical Relative Value HTTP contract

Status: WP5 implemented; acceptance is recorded in the
[case Roadmap](../../../market_research/descriptive/cases/futures_calendar_spread/ROADMAP.md).
Specializes [HTTP ownership](../../ARCHITECTURE.md). Query/result, sample policy and
failure classification belong to [Research](../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md),
with numerical semantics under [Relative value](../../../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md).

## Issue #13 delivery status

The original WP5 read-only POST remains the current implementation until Issue #13
WP2. This contract now explicitly authorizes the execution-semantic change below;
[reconciliation](../../../market_research/descriptive/cases/futures_calendar_spread/AUTO_PREPARATION_RECONCILIATION.md)
records the undelivered target without rewriting historical acceptance.

## Operation and body

`POST /research/calendar-spread-relative-value/query`, operationId
`query_calendar_spread_relative_value`, accepts no query parameters and a closed
JSON body with required `product_code`, `history_start`, `evaluation_date` and
optional `metric`, `histogram_edges`. Content type is application/json, optionally
with charset. Reject duplicate/unknown fields, malformed JSON and coercible types
as 400 invalid_request. Optional fields may be omitted, not supplied as null.

Dates are canonical YYYY-MM-DD. Product and metric are canonical business enum
values; Research owns validation, strict history_start<evaluation_date, the future
date limit and default `annualized_spread_ratio`. histogram_edges is an ordered
array of finite JSON numbers; Statistics public validation owns boundary legality.
No horizon, strategy, owner, run_id, arbitrary formulas or statistical estimator
override is accepted.

This POST is a synchronous user-initiated analytical execution. It invokes only
the case facade's `execute_historical_relative_value`; its Input Preparation may
conditionally Ensure legal incomplete Calendar/Futures caches and requires complete
final Exports. Path, HTTP operationId, request body and successful Result shape stay
unchanged; request.operation remains `query_historical_relative_value`, identifying
the analysis rather than acquisition permission. Execution source_context follows
[Query Results](../../../market_research/descriptive/cases/futures_calendar_spread/QUERY_RESULTS.md).
The read-only Python `query_historical_relative_value` remains available separately;
this HTTP entry no longer promises read-only cache access. It creates no durable
execution identity. It is independent of `/research/execute`, capability
discovery, Plan/Batch, Publication and Futures Basis online Runs.

## Result and errors

200 projects the complete business Result: case/definition/request, current Daily
projection, six pairs' per-stage/all-stages distributions, matching-stage and
all-stages assessments, metric/unit, actual sample dates/counts, numerical method
parameters/results, histogram outside counts when requested, candidate accounting,
availability reasons and source/interpretation limitations. Do not send full
upstream Exports, credentials or private paths. Null, zero, ordering and full
finite precision survive serialization; percentages stay fractions in [0,1].

Empty/small historical groups and unavailable current observations remain 200
business outcomes, retaining their distinct reasons. No synthetic neutral rank,
all-stage fallback or transport-level financial/statistical recomputation.

Use the same error envelope and shared category/status projection as
[Daily HTTP](../futures_calendar_spread/http-contract.md), including the optional
reason_code projection, and adding `statistical_failure` → 422 / statistical_failure. Illegal statistical request
parameters are Research `invalid_request` → 400, not execution failures.
Do not expose the default framework 422 validation body.

## Access and consumer boundaries

Apply [existing Auth](../../AUTHENTICATION.md), including its POST same-origin
policy, before product processing. Responses are no-store. HTTP imports neither
DataLake nor private Statistics algorithms; Research returns business-associated
numerical results. The [Web consumer](../../../ui_web/src/features/calendar_spread_relative_value/ARCHITECTURE.md)
owns generated OpenAPI/TypeScript at WP6. Demo later captures this formal 200 Result;
it never calls the Python facade directly. Runtime resource limits may constrain
transport delivery but must never truncate samples or silently change populations.

## WP5 transport bounds and projection

The [shared Calendar Spread transport bounds](../futures_calendar_spread/http-contract.md#wp5-transport-bounds-and-projection)
own the shared two-worker process capacity, 16 KiB streamed body limit, UTF-8 JSON
parsing, 32 MiB complete-response limit, threadpool execution, safe errors and
atomic serialization. This Research product additionally limits the inclusive
window to 3660 natural dates and histogram_edges to 128 entries; excess returns
413 `request_too_large` with the relevant field in param before business execution.
These are transport bounds, without truncation or changes to business populations.

HistoricalRequest, HistoricalResponse and HistoricalErrorResponse are the
product-owned typed DTOs in `schemas.py`, published by composed `.openapi()`.

Historical response publishes one ordered `samples` sequence per pair from the
business all-stages distribution: date, stage, selected metric/value/unit and
near/far real contract code, Close and last trading date, delta/DTE.
The four distributions retain ordered candidate_dates and sample_dates, accounting,
sample_count/status/reason/warnings, typed quantile spec/result and optional
histogram spec/result. sample_dates bind to that pair's samples by exact date;
the all-stages series is complete, never downsampled. Assessments bind by
distribution_stage and the pair's current_day observation, retaining kind,
status/reason/warnings and typed percentile spec/result with L/E/G counts.
NumericSample arrays and repeated raw observations are not transmitted.
Historical day date/status/reason summaries preserve closed dates; historical
accounting and evaluation current_day are explicit. Echoed request includes the
resolved default metric and null histogram_edges when omitted, as in the Python
business request. Request optional fields reject explicit null.

## Execution feedback and compatibility

All existing request/window/edge/response limits remain in force. HTTP consumes only
the Research facade, never DataLake services. No business auto-retry, Run Store,
background-job protocol or progress stream is added. Client cancellation isolates
results but does not guarantee worker termination or cache rollback; capacity stays
held through completion under the shared Daily transport contract.

Existing formal Demo captures remain valid 200 historical evidence; WP0 neither
recaptures nor changes Bundles. Static Demo renders those captures offline and never
submits this POST. Production submission is explicitly execution-oriented; updated
errors explain credential, compatibility or preparation failures without prescribing
manual Ensure. Cold/hot latency, timeout and capacity acceptance follow the
[shared synchronous boundary](../futures_calendar_spread/http-contract.md#issue-13-synchronous-acceptance-boundary).
