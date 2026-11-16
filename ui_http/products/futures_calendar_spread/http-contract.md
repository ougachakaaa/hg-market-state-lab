# Daily Data — Futures Calendar Spread HTTP plan

Status: WP0 authority only. No endpoint, DTO or OpenAPI operation is implemented.
Specializes [HTTP ownership](../../ARCHITECTURE.md); business semantics and failures
belong to [the Research application](../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md).

## Planned operation and request

`GET /data/futures-calendar-spread`, operationId `query_futures_calendar_spread`,
accepts exactly two required query parameters: `product_code` and `trade_date`.
Reject unknown/repeated parameters, absent values and implicit coercions.
Product is canonical IF/IH/IC/IM; date is canonical YYYY-MM-DD. Transport parses
date-only types; Research validates product/date semantics, including its future
date rule, before upstream calls. No implicit latest-date query or earlier-session
fallback is published. GET accepts no request body.

The adapter invokes only the new case facade's `query_daily_spreads`. It never
imports DataLake or sibling case internals, resolves Slots, calls ensure, selects
prices or calculates metrics.

## Planned result and errors

200 projects the complete Daily business Result: case/definition identity, echoed
request, session status/reason, ordered pair outcomes with real contracts, Close,
last trading dates, delta_days/near_dte_days/stage, three named metrics/units,
accounting and safe public source context/limitations. Dates become ISO strings;
absent values become null, zero stays zero, arrays retain producer order, finite
numbers remain unrounded JSON numbers. Closed dates are successful not-applicable
Results with no rows; proven empty open dates retain six not-applicable pairs.

| Business failure | HTTP status / error kind |
| --- | --- |
| invalid_request | 400 / invalid_request |
| incomplete_inputs | 409 / incomplete_inputs |
| upstream_unavailable | 503 / upstream_unavailable |
| input_contract_error | 502 / input_contract_error |
| slot_resolution_error | 422 / slot_resolution_error |
| calculation_failure | 422 / calculation_failure |
| Unexpected adapter defect | 500 / internal_error |

Errors use `{error: {kind, detail, param}}`; param is a known input field or null.
Details use fixed safe text, never raw exceptions, paths or upstream responses.
The explicitly declared 422 errors are domain execution failures, not FastAPI's
default validation envelope. Transport parse errors are 400 invalid_request.

## Access and publication

All access follows [existing Auth](../../AUTHENTICATION.md). Authenticate before
product invocation. Product responses are `Cache-Control: no-store`; no server Run,
owner-scoped store, job ticket, implicit acquisition or retry endpoint is introduced.
OpenAPI must publish the actual DTOs/statuses when implemented. The consuming
[Web feature](../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md)
owns generated artifacts under the existing feedback loop; WP0 generates none.
DTO names and implementation layout may be chosen at WP5 without changing this
business projection or creating a competing financial schema.
