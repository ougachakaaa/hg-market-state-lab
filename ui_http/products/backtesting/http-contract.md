# Futures Roll Backtesting HTTP contract V1

This product specializes [HTTP ownership](../../ARCHITECTURE.md) and the existing
[Auth gate](../../AUTHENTICATION.md). Business semantics belong exclusively to the
[W2 Online Application](../../../market_backtesting/cases/futures_roll_long/ONLINE_APPLICATION.md)
and [BacktestResult](../../../market_backtesting/cases/futures_roll_long/RESULT.md).
It is independent of Research, Publication and Workbench.

## Operations and strict request

| Method / path | operationId | Success |
| --- | --- | --- |
| POST `/backtesting/futures-roll/preflight` | `preflight_futures_roll_backtest` | 200 |
| POST `/backtesting/futures-roll/runs` | `submit_futures_roll_backtest` | 202 |
| GET `/backtesting/futures-roll/runs/{run_id}` | `get_futures_roll_backtest_run` | 200 |
| GET `/backtesting/futures-roll/runs/{run_id}/result` | `get_futures_roll_backtest_result` | 200 |

No list/history, cancellation, deletion or retry operation exists. All four
operations forbid query parameters. POST accepts exactly these four required fields:

```json
{"product_code":"IM","start_date":"2025-02-17","end_date":"2025-03-24","strategy_profile":"expiry_to_M1_v1"}
```

Product is exactly IM/IC/IF/IH; strategy is exactly expiry_to_M1_v1/expiry_to_Q1_v1.
Dates are canonical YYYY-MM-DD strings. Unknown/missing/duplicate keys, non-string
values, aliases, timestamps, malformed JSON and implicit conversions are rejected.
Content-Type must be application/json (charset parameter allowed). Content-Encoding
must be absent or identity; compressed bodies are never decoded. Multiple transport
header values do not create an alternative parsing path. The body is limited to
4096 bytes while streaming, independent of Content-Length.

HTTP parses syntax/types only, then delegates to validate_futures_roll_request
before obtaining the runtime or invoking an operation. Date ordering, future-date
and window semantics remain producer-owned. Invalid input creates no Run and touches
no DataLake service. There are no defaults or owner/case/benchmark/fee/multiplier/
strategy-parameter overrides.

## Auth and privacy

The existing AccessGate validates JWT Cookie, active user and POST same-origin
before product parsing or invocation. The stable authenticated user ID alone is
owner_scope. It never enters public DTOs. Malformed, unknown and foreign Run IDs
are indistinguishable 404 run_not_found. Result authorizes through get_status before
trying HTTP delivery capacity, so foreign IDs do not observe reader contention.
All responses are Cache-Control: no-store; only successful responses renew the
Cookie under existing Auth rules. No cache, ETag or alternate authentication exists.

## Concrete DTO projections

All DTOs have product-prefixed OpenAPI names and closed object fields. Immutable
request is the four input fields plus case=futures_roll_long_v1. Timestamps are UTC
ISO date-times from the producer; run_id is opaque 32 lowercase hex characters.

- Preflight: `{request, ready, calendar_cffex, futures, index}`. Each dependency is
  `{dependency, state, reason, coverage}`. State preserves complete/incomplete/
  unavailable/unknown; reason preserves the producer's fixed safe code. Coverage
  is null or the six public fields requested_units, successful_units, missing_units,
  pending_units, failed_units, complete. No new SSE assessment is invented.
- Accepted: `{run_id, status, request, created_at}`. status is the persisted PENDING
  admission snapshot, even when the worker has already progressed or startup failed.
- Status: `{run_id, request, status, created_at, started_at, finished_at,
  result_available, failure}`. The five states are PENDING/RUNNING/COMPLETED/FAILED/
  INTERRUPTED. result_available is purely status == COMPLETED. Nullable failure
  preserves the OnlineFailure `{stage, category, dependency, reason}` safe vocabulary,
  including publication and recovery failures. It contains no provider diagnostics.
- Result: `{run_id, request, data}`. data is the complete validated
  futures_roll_long_result_v1: profile/case/definition_version/status/request/window,
  benchmark/initial_notional/daily/trades/rolls/summary/evidence/views. All nested
  structures, including V2 date/decimal_ratio axes, line bindings, marks, events,
  layout and presentation, have concrete schemas. HTTP only serializes producer
  values without recomputation, rounding or percent conversion. The envelope request
  must equal data.request. No portable full evidence package is added.

Preflight remains advisory and read-only: no submit, ensure, Source initialization,
cache repair or result computation; ready=false does not block Submit.
Status reads metadata only and never acquire either full-result reader permit.

## Closed error mapping and WP5 reconciliation

Errors use `{error:{kind,detail,param}}`; detail is fixed safe text, param is null.
No raw exception, path, owner, credential or persistence metadata is exposed.

| HTTP | kind | Fixed detail |
| --- | --- | --- |
| 400 | invalid_request | Request must match the strict Futures Roll schema. |
| 400 | request_too_large | Request body exceeds 4 KiB. |
| 404 | run_not_found | Run not found. |
| 409 | run_busy | A backtest is already running. |
| 409 | result_not_ready | The run has not completed. |
| 409 | corrupt | Stored run or result is corrupt. |
| 413 | result_too_large | Stored result exceeds the 32 MiB bound. |
| 413 | response_too_large | Result response exceeds the 32 MiB delivery bound. |
| 503 | unavailable | Backtesting online application is unavailable. |
| 503 | read_busy | Result reader capacity is occupied; retry manually. |
| 500 | internal_error | Backtesting HTTP operation could not be completed. |

Auth independently supplies its existing 401, POST 403 and safe 500 envelopes.
All endpoints may reject forbidden query parameters with 400. POST additionally
declares body errors; Submit declares run_busy/unavailable; reads declare not-found,
corrupt and unavailable; Result additionally declares not-ready, size and read-busy.
There is no framework 422.

WP5 result_not_ready covers every non-COMPLETED state, including FAILED/INTERRUPTED;
there is no result_unavailable category. Unknown stored schemas classify as corrupt,
not a fabricated unsupported_version category. result_too_large preserves WP5's
operation error; response_too_large is the HTTP envelope bound. WP5's metadata-only
status check classifies a tampered oversized stored result as corrupt (409), which
HTTP preserves; HTTP does not inspect private files to reclassify it as 413.
Producer publication rejects oversized computed results as a failed Run with
result_publication/result_too_large, rather than publishing an oversized result.
Worker failure
categories such as serialization_failure/storage_failure remain Status data, not
new operation errors. Unknown adapter failures map to internal_error.

## Bounds, composition and OpenAPI

Preflight/Accepted/Status responses are at most 64 KiB. Result's complete serialized
envelope is at most 32 MiB (33,554,432 bytes); never truncate. A nonblocking process
HTTP reader permit covers get_result, projection, validation and serialization,
separately from WP5's Store permit. Every exit releases it. Contention is manual
retry, never a server-side queue. JSON encoding is finite and incrementally bounded.

The existing composition root obtains one application per process through a locked,
once-only runtime holder; lifespan and lazy request access share it. Store failure
does not discard an otherwise usable WP5 application: preflight remains available.
Initialization failure is isolated from sibling HTTP products. No import starts a
worker, opens a Store or performs recovery. Only the public case facade is imported;
HTTP does not import private Store/Codec or acquire market facts itself.

Offline create_app().openapi() publishes all operations, exact DTOs, CookieSession
security, declared statuses and no-store headers without Auth configuration,
Tushare credentials, runtime directory or active worker. Existing products remain
unchanged. [WP7 contract ownership](../../../ui_web/contracts.md) now assigns Backtesting's
generated OpenAPI/TypeScript to the independent Web consumer, included in the
complete generation/freshness loop. WP6's original acceptance checked the six
pre-existing consumers; WP7 adds the seventh. Single-process/POSIX storage limitations remain producer-owned.
