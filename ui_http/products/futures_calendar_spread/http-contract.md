# Daily Data — Futures Calendar Spread HTTP contract

Status: WP5 and DD-02 WP-01 implemented; current delivery is recorded in the
[case Roadmap](../../../market_research/descriptive/cases/futures_calendar_spread/ROADMAP.md).
Specializes [HTTP ownership](../../ARCHITECTURE.md); business semantics and failures
belong to [the Research application](../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md).

Explicit execution and read-only permissions below implement Issue #13.
Current preparation behavior and operational limits belong to the
[Research application](../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md).

## Operation and request

`GET /data/futures-calendar-spread`, operationId `query_futures_calendar_spread`,
accepts exactly two required query parameters: `product_code` and `trade_date`.
Reject unknown/repeated parameters, absent values and implicit coercions.
Product is canonical IF/IH/IC/IM; date is canonical YYYY-MM-DD. Transport parses
date-only types; Research validates product/date semantics, including its future
date rule, before upstream calls. No implicit latest-date query or earlier-session
fallback is published. GET accepts no request body.

The GET adapter invokes only the case facade's `query_daily_spreads`. It never
imports DataLake or sibling case internals, resolves Slots, calls ensure, selects
prices or calculates metrics.

## Explicit execution POST

`POST /data/futures-calendar-spread/query`, operationId
`execute_futures_calendar_spread`, accepts no query parameters and a closed JSON
body with exactly required `product_code` and `trade_date`, under the same canonical
types and business validation as GET. Reject duplicate/unknown fields, nulls and
implicit coercions as 400 invalid_request. Use the POST body/media rules below and
existing Auth same-origin protection before product processing.

The adapter invokes only the case facade's `execute_daily_spreads`. Research Input
Preparation may conditionally Ensure legal incomplete Calendar/Futures inputs under
its public contract. HTTP never imports DataLake, calls Ensure or orchestrates
prerequisites. This is synchronous explicit execution; no Run identity is created.
The complete success body is the same DailyResponse as GET, including existing
request.operation=`query_daily_spreads`. The HTTP operationId identifies the new
entry; the echoed operation identifies the analysis. Execution source_context is
accurate under Query Results; no raw preparation diagnostics are projected.

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

Errors use `{error: {kind, detail, param, reason_code?}}`; param is a known input
field or null. reason_code is an optional closed string enum and is omitted when
unavailable, including ordinary transport errors. Existing bodies without it remain
valid. The additive values and allowed category pairs are:

| kind / HTTP status | reason_code |
| --- | --- |
| incomplete_inputs / 409 | cache_incomplete (read-only), final_export_incomplete (execution) |
| upstream_unavailable / 503 | credential_missing, cache_incompatible, operation_unavailable |
| input_contract_error / 502 | malformed_export, malformed_ensure_result, upstream_request_rejected |

Research owns these classifications under [Inputs](../../../market_research/descriptive/cases/futures_calendar_spread/INPUTS.md#execution-preparation-and-diagnostics-boundary).
Transport projects only the known kind/reason pair, without inspecting causes or
message strings. Successful preparation returns normal 200, without an error code.
Malformed/unexpected failure objects use the existing safe internal_error boundary.
Capacity saturation remains 503 transport_busy, independently of acquisition failure.

Details use fixed safe text selected by kind and recognized reason_code, never raw
exceptions, Token values, UnitFailure reasons, paths or Provider responses.
The explicitly declared 422 errors are domain execution failures, not FastAPI's
default validation envelope. Transport parse errors are 400 invalid_request.

## Access and publication

All access follows [existing Auth](../../AUTHENTICATION.md). Authenticate before
product invocation. Product responses are `Cache-Control: no-store`; no server Run,
owner-scoped store, job ticket or retry endpoint is introduced. GET never acquires
facts; POST permits only its explicit Research preparation contract.
OpenAPI publishes the actual DTOs/statuses in the composed app. The consuming
[Web feature](../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md)
owns generated artifacts under the existing feedback loop at WP6; WP5 generates
no Web artifacts.

## WP5 transport bounds and projection

All Calendar Spread routes (Daily GET, Daily POST and Historical POST) share a
process-wide nonblocking capacity of two in-flight workers (across app instances). A worker holds capacity through business
query, DTO validation and complete serialization, including client cancellation.
Saturation returns 503 `transport_busy`; there is no waiting business queue.
A client abort, replacement request, logout or HTTP/Gateway timeout does not promise
to stop the synchronous worker or roll back already committed DataLake units.
Capacity is released only when business work, projection and serialization finish.
No automatic retry or frontend/backend cancellation propagation is added.
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

## Issue #13 synchronous acceptance boundary

Keep the existing body/response limits, authentication, threadpool and capacity
semantics for the new POST; include its path in product routing, error handling and
OpenAPI publication. Both consuming features regenerate their affected contracts
when WP2 implements the wire change; WP0 changes no generated artifacts.

Threadpool execution alone does not prevent HTTP timeouts. Issue #13 WP3 must
record cold/hot request duration, the actual client/Gateway/server timeout settings,
Source availability, tested request windows, concurrent saturation and capacity
retained after client cancellation. No new arbitrary timeout or latency SLA is
claimed here. If the existing synchronous stack cannot complete the tested cold
execution, report operational acceptance failure and obtain a separate semantic
decision; do not silently introduce a queue, worker framework or asynchronous Run.

## DD-02 Daily index projection target

WP-00 encoded this additive contract; DTOs/OpenAPI are implemented in DD-02 WP-01.
Research owns [reference semantics](../../../market_research/descriptive/cases/futures_calendar_spread/DAILY_INDEX_REFERENCE.md)
and [business carriers](../../../market_research/descriptive/cases/futures_calendar_spread/QUERY_RESULTS.md#daily-underlying-index-result-dd-02-target).
GET/POST paths, requests, echoed operation, PairObservation and core failure mapping
remain unchanged. HistoricalResponse and its current-day projection do not gain a reference.

DailyResponse adds `underlying_index`, an optional, non-null object. When present all
six fields are required, and unknown object fields are forbidden:

| Field | Wire type |
| --- | --- |
| index_code | string, authority-governed full underlying code |
| trade_date | canonical ISO date, equal to request.trade_date |
| close | finite JSON number or null; original unrounded index points |
| availability | available / not_applicable / unavailable / error |
| reason_code | null / non_trading_day / cache_incomplete / final_export_incomplete / credential_missing / cache_incompatible / operation_unavailable / malformed_export / malformed_ensure_result / upstream_request_rejected |
| failure_category | null / incomplete_inputs / upstream_unavailable / input_contract_error |

Only the exact state/reason/category combinations in the Research reference table
are legal. available requires non-null close; all other states require null. Project
these fields explicitly, validate identity/date and association, and omit internal
reference evidence. A known reference error is part of HTTP 200 with complete original
pairs; it does not use the top-level error envelope. Core failures keep existing statuses.
Do not reclassify invalid carriers as reference errors or leak raw failure text.

New GET and POST success projection always includes a reference object; missing it is
an adapter defect. The published schema permits omission solely to admit pre-DD-02
captured results. Omission means reference information was not supplied, never that
that date's close was null. Explicit underlying_index=null is invalid. Serialization
must preserve omission when validating an old object, without injecting a null default.

The formal frontend validator keeps every existing structural/association check and
validates the new object when present; Online response adaptation additionally requires
presence. Demo uses the same validator with the formal optional-field contract. Do not
relax unrelated fields, store an alternate schema, rewrite old Bundle bytes or synthesize
an object. Generate affected OpenAPI/TypeScript under the normal feedback loop in WP-01;
WP-00 does not regenerate artifacts. Any generated sibling snapshot drift must be limited
to actual generator effects; Historical wire semantics stay unchanged.

## Daily futures–spot additive projection

DailyResponse adds optional, non-null `futures_spot_comparisons`. New Online GET/POST
success projections always include it and underlying_index; omission is accepted only
for older captured objects and preserved during serialization. Presence requires the
underlying_index object. Closed CFFEX days carry an empty collection; open days have
exactly M0/M1/Q1/Q2 in order. Missing does not mean four null outcomes.

Each item explicitly projects product_code, trade_date, slot, futures (the existing
Contract DTO or null), underlying_index (the existing reference DTO), remaining_days,
expiry_stage, signed_spread, annualized_point_spread, annualized_spread_ratio, outcome,
reason, failure_category and definition_version=daily_futures_spot_definition_v1.
Finite/null metrics and exact state combinations follow the independent Research
[authority](../../../market_research/descriptive/cases/futures_calendar_spread/DAILY_FUTURES_SPOT_COMPARISON.md).
Identity/date, reference equality, Slot-to-pair contract association, count/order and
state/metric relationships are validated, without financial recomputation.
No internal evidence is serialized. HistoricalResponse is unchanged.
