# Research — Calendar Spread Historical Relative Value HTTP plan

Status: WP0 authority only. No endpoint, DTO or OpenAPI operation is implemented.
Specializes [HTTP ownership](../../ARCHITECTURE.md). Query/result, sample policy and
failure classification belong to [Research](../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md),
with numerical semantics under [Relative value](../../../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md).

## Planned operation and body

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

This POST is a synchronous read-only analytical query. It invokes only the case
facade's `query_historical_relative_value`, performs no ensure or writes and creates
no durable execution identity. It is independent of `/research/execute`, capability
discovery, Plan/Batch, Publication and Futures Basis online Runs.

## Planned result and errors

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
[Daily HTTP](../futures_calendar_spread/http-contract.md), adding
`statistical_failure` → 422 / statistical_failure. Illegal statistical request
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
