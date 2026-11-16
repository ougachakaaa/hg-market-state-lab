# Daily Data — Futures Calendar Spread HTTP contract

Status: WP5 implemented; acceptance is recorded in the
[case Roadmap](../../../market_research/descriptive/cases/futures_calendar_spread/ROADMAP.md).
Specializes [HTTP ownership](../../ARCHITECTURE.md); business semantics and failures
belong to [the Research application](../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md).

## Operation and request

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

## Result and errors

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
OpenAPI publishes the actual DTOs/statuses in the composed app. The consuming
[Web feature](../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md)
owns generated artifacts under the existing feedback loop at WP6; WP5 generates
no Web artifacts.

## WP5 transport bounds and projection

Both Calendar Spread operations share a process-wide nonblocking capacity of two
in-flight workers (across app instances). A worker holds capacity through business
query, DTO validation and complete serialization, including client cancellation.
Saturation returns 503 `transport_busy`; there is no waiting business queue.
Workers use Starlette's threadpool; synchronous Research and serialization never
execute on the event loop. Limits are per process, not distributed.

Bodies are read incrementally with a 16 KiB cumulative limit; overflow returns
413 `request_too_large`. GET rejects any nonempty body with 400. POST requires a
single application/json Content-Type, optionally a single UTF-8 charset parameter;
compressed bodies and other parameters/encodings are rejected with 400.

The complete UTF-8 JSON response is encoded into a bounded buffer before response
start, maximum 32 MiB. Overflow returns 413 `response_too_large`; malformed or
nonfinite result projection returns 500 `internal_error`. No truncation, partial
200, implicit window adjustment or presentation rounding is permitted.
Resource errors use the same typed product envelope and fixed safe details.
Business validation remains authoritative (including legal dates/window/edges).
Known wire-field failures carry that field in `param`; unassignable business
failures use null, without inspecting exception text.

Concrete request/response/error DTOs are owned by each product's Python
`schemas.py` and published by the composed app's offline `.openapi()`.
Only explicitly selected fields are projected from business objects; never raw
Exports, internal evidence references, full source rows or exception messages.
Safe source context contains provider/exchange/price field and limitations.

DailyResponse contains `request` (including Python operation identity),
`day.trade_date/status/reason/observations`, `accounting`, `source_context`,
`case` and `definition_version`. Each observation preserves near/far Slots,
`near/far.contract_code/close/delist_date` (delist_date means last trading date),
delta/DTE/stage, all three named `metrics`, outcome and reason. Internal Slot
resolution and raw source evidence are not serialized. DailyRequest owns the
query DTO; DailyErrorResponse owns the product error DTO. Historical delivery
reuses these value projections without introducing a second financial definition.
