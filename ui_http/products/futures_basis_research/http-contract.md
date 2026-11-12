# Online Futures Basis Research HTTP contract V1

## Storage transition status

The approved [portable storage target](../../../market_research/descriptive/cases/futures_basis/ONLINE_STORAGE.md) is not implemented by storage WP0.
Any POSIX/platform-unavailable statements below describe the current adapter only;
SQLite cutover removes that capability gate while preserving endpoints, DTOs, Auth,
owner isolation where applicable, safe error mapping and existing unavailable/corrupt
behavior for real storage failures. No wire contract or generated artifact changes.

This contract specializes [HTTP ownership](../../ARCHITECTURE.md) and is cataloged
in [HTTP_PRODUCTS](../../HTTP_PRODUCTS.md). Research owns the
[online application, profile and run lifecycle](../../../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md),
the R01-A result and its reader projection. HTTP owns strict parsing, bounded
projection, transport status mapping and OpenAPI. All operations require the
repository [access gate](../../AUTHENTICATION.md).

This is an independent product. It does not modify the semantics of
`POST /research/execute`, `GET /research/capabilities*`, Research Publication V1 or
Research Explorer. R01-A is not admitted to the Descriptive Research capability,
Plan/Batch or Publication paths.

## Operations

| Method / path | Stable operationId | Success |
| --- | --- | --- |
| `POST /research/futures-basis/preflight` | `preflight_futures_basis_research` | `200` assessment |
| `POST /research/futures-basis/runs` | `submit_futures_basis_research_run` | `202` accepted run |
| `GET /research/futures-basis/runs/{run_id}` | `get_futures_basis_research_run` | `200` run status |
| `GET /research/futures-basis/runs/{run_id}/report` | `get_futures_basis_research_report` | `200` validated report |

There is no list, cancel, delete or retry endpoint. `{run_id}` is an opaque
32-lowercase-hex identifier. Any other path value is treated as `run_not_found`
before storage access. GET operations accept no query parameters; POST accepts no
query parameters and only the exact JSON body below. GET report never executes
Research, acquires facts or recomputes statistics.

## Strict request

```json
{
  "product_code": "IM",
  "start_date": "2024-01-01",
  "end_date": "2026-10-30"
}
```

- Content type must be `application/json` (an optional charset is allowed); body is
  bounded to `4 KiB` while streaming, before JSON parsing.
- Exactly three fields are accepted. Unknown fields, duplicate keys, malformed
  JSON, non-string types and implicit conversions are `400 invalid_request`.
- `product_code` is the exact canonical enum `IM | IC | IF | IH`; no normalization.
- Dates are strict date-only `YYYY-MM-DD`; timestamps and noncanonical spellings are
  rejected. Both ends are inclusive.
- Research validates product membership, date order, the Asia/Shanghai future limit
  and the `1,096`-inclusive-day maximum before any run creation or I/O. HTTP maps
  the classified failure and never runs a parallel semantic validator.
- The server selects the immutable profile `r01a_standard_v1`; the client cannot
  select or override quantiles, histogram edges, methods, strategy parameters or
  backtest behavior.

## DTOs

### `FuturesBasisRunRequest`

```text
product_code: "IM" | "IC" | "IF" | "IH"
start_date:   YYYY-MM-DD
end_date:     YYYY-MM-DD
```

### `FuturesBasisRunAccepted` (202)

```json
{
  "run_id": "0123456789abcdef0123456789abcdef",
  "status": "PENDING",
  "request": {
    "case": "futures_basis_v1",
    "product_code": "IM",
    "start_date": "2024-01-01",
    "end_date": "2026-10-30",
    "analysis_profile": "r01a_standard_v1"
  },
  "created_at": "2026-11-06T13:44:29Z"
}
```

The response always reports the accepted snapshot as `PENDING`; a later GET may
already observe `RUNNING` or a terminal state. There is no `Location` requirement.

### `FuturesBasisRun` (200 GET run)

```json
{
  "run_id": "0123456789abcdef0123456789abcdef",
  "request": {
    "case": "futures_basis_v1",
    "product_code": "IM",
    "start_date": "2024-01-01",
    "end_date": "2026-10-30",
    "analysis_profile": "r01a_standard_v1"
  },
  "status": "COMPLETED",
  "created_at": "2026-11-06T13:44:29Z",
  "started_at": "2026-11-06T13:44:30Z",
  "finished_at": "2026-11-06T13:49:12Z",
  "result_available": true,
  "result_status": "complete",
  "failure": null
}
```

- `status` is exactly `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` or `INTERRUPTED`.
- `result_available` is true exactly for `COMPLETED`; only then is
  `result_status` `complete` or `partial`.
- `started_at` is null while `PENDING`; `finished_at` is null while `PENDING` or
  `RUNNING`.
- `failure` is null unless `FAILED` or `INTERRUPTED`.
- No owner, path, raw exception, attempt, provider diagnostic or private source
  metadata is returned.

### `FuturesBasisFailure`

```json
{
  "stage": "input_preparation",
  "category": "upstream_operation",
  "dependency": "futures",
  "reason": "Required market facts could not be acquired from the configured public source."
}
```

`stage` is one of `input_preparation`, `observation_construction`,
`report_composition`, `result_publication`, `execution`. `category` is the
Research-owned closed category for that stage, `dependency` is null or one of
`request`, `calendar_cffex`, `calendar_sse`, `futures`, `index`, and `reason` is
fixed safe text. HTTP never rewrites a Research classification.

### `FuturesBasisReportResponse` (200 GET report)

```json
{
  "run_id": "0123456789abcdef0123456789abcdef",
  "request": {
    "case": "futures_basis_v1",
    "product_code": "IM",
    "start_date": "2024-01-01",
    "end_date": "2026-10-30",
    "analysis_profile": "r01a_standard_v1"
  },
  "result_status": "complete",
  "data": {
    "profile": "futures_basis_report_evidence_v1",
    "status": "complete",
    "request": {
      "observation": {
        "product_code": "IM",
        "start_date": "2024-01-01",
        "end_date": "2026-10-30",
        "case": "futures_basis_v1"
      },
      "quantile": { "method": "quantile", "points": [0, 0.25, 0.5, 0.75, 1] },
      "histograms": [
        { "method": "interval_count", "unit": "index_points", "edges": [-1000, -500, -100, 0, 100, 500, 1000] },
        { "method": "interval_count", "unit": "decimal_ratio", "edges": [-1, -0.1, -0.01, 0, 0.01, 0.1, 1] },
        { "method": "interval_count", "unit": "decimal_ratio", "edges": [-10, -1, -0.1, 0, 0.1, 1, 10] }
      ]
    },
    "fingerprint": "…",
    "definition_version": "futures_basis_definition_v1",
    "coverage": {},
    "accounting": [],
    "candidate_dates": [],
    "formulas": [],
    "sources": "…",
    "summary": "…",
    "limitations": [],
    "distributions": [],
    "comparisons": [],
    "persistence": [],
    "views": { "history": {}, "histograms": {} }
  }
}
```

`data` is the complete existing `futures_basis_report_evidence_v1` reader
projection owned by [Evidence](../../../market_research/descriptive/cases/futures_basis/EVIDENCE.md)
and [Delivery](../../../market_research/descriptive/cases/futures_basis/DELIVERY.md).
It is a versioned producer payload, not a second financial DTO or an HTTP-only
schema. The envelope is typed; the frontend owns the reader types and validates
`data.profile`, `data.status`, the request association and every View before
rendering.

`data.request` is the formal `ReportRequest` projection: `observation`, the
explicit quantile specification and the three ordered histogram specifications.
Top-level `request` is the run identity. The server verifies
`data.request.observation` matches the run request, `data.status == result_status`,
and the reader profile is exact. `data.views.history` contains V2 date-series
Views; `data.views.histograms` contains V1 categorical Views. `partial` is a
successful HTTP read with a partial scientific status.

## Status and access matrix

| Endpoint | Status | Kind | Meaning |
| --- | --- | --- | --- |
| POST | 202 | — | Run accepted as `PENDING`; no market acquisition or statistics in the request; run metadata is persisted |
| POST | 400 | `invalid_request` | Strict body, type, canonical date or semantic request failure; no run created |
| POST | 400 | `request_too_large` | Body exceeds 4 KiB; no run created |
| POST | 409 | `run_busy` | Another run is active; no run created and no queue |
| POST | 503 | `unavailable` | Run storage configuration or I/O is unavailable |
| POST | 500 | `internal_error` | Unexpected transport/runtime defect |
| GET run | 200 | — | Existing owned run in any state |
| GET run | 400 | `invalid_request` | Query parameters are forbidden |
| GET run | 404 | `run_not_found` | Unknown, malformed or foreign run |
| GET run | 409 | `corrupt` | Stored request/state/result association is corrupt |
| GET run | 409 | `unsupported_version` | Unknown stored run schema |
| GET run | 503 | `unavailable` | Run storage unavailable |
| GET run | 500 | `internal_error` | Unexpected transport/runtime defect |
| GET report | 200 | — | `COMPLETED` result with `complete` or `partial` status |
| GET report | 400 | `invalid_request` | Query parameters are forbidden |
| GET report | 404 | `run_not_found` | Unknown, malformed or foreign run |
| GET report | 409 | `result_not_ready` | Run is `PENDING` or `RUNNING` |
| GET report | 409 | `result_unavailable` | Run is `FAILED` or `INTERRUPTED` |
| GET report | 409 | `corrupt` | Stored result/profile/association is corrupt |
| GET report | 409 | `unsupported_version` | Unknown stored run or reader profile version |
| GET report | 413 | `response_too_large` | Stored result exceeds the 32 MiB delivery bound |
| GET report | 503 | `unavailable` | Run storage unavailable |
| GET report | 503 | `read_busy` | Process report-reader capacity is occupied; manual retry |
| GET report | 500 | `internal_error` | Unexpected transport/runtime defect |

All operations may return the independent Auth errors `401 authentication_required`,
`403 origin_forbidden` (POST) and Auth `500 internal_error`. Auth envelopes are
never mixed into the product error enum. No endpoint publishes `422`.

Product errors use:

```json
{"error":{"kind":"invalid_request","detail":"end_date must not be after the current date in Asia/Shanghai.","param":"end_date"}}
```

`param` is a declared input field or null. Details are fixed safe text and never
echo unknown fields, paths, credentials, raw exception text or provider payloads.

## Resource, concurrency and caching bounds

- Request body: 4 KiB; run status response: 64 KiB; report response: 32 MiB.
- Result publication rejects a serialized reader payload above 32 MiB as a run
  failure; delivery never truncates.
- One active execution per process; no queue. POST busy is `409 run_busy`.
- GET run is a small state read and may proceed concurrently.
- GET report is bounded to one reader permit per process; contention returns
  `503 read_busy` without queueing. HTTP delivery holds its permit through envelope
  validation and serialization; Research retains its independent full-reader guard.
  No report is cached across requests.
- GET run checks result presence/size before advertising availability; GET report
  verifies digest and associations before serving.
- All responses are `Cache-Control: no-store`; no shared/browser caching, ETag or
  cross-user read is allowed. `run_id` alone is never sufficient authorization.
- POST is not idempotent: a lost response may have created a run. Clients must not
  silently retry; a new submission is a new run.

## Auth, OpenAPI and generated contract

The adapter obtains the authenticated user identity from the existing Auth
composition and passes its stable ID as the opaque `owner_scope` to Research. It
never accepts an owner, user or scope from the request. Authentication and
same-origin checks happen before body parsing, run lookup or Research calls. A
foreign owner and an unknown ID are indistinguishable as `run_not_found`.

OpenAPI publishes the four operations, the Cookie security requirement, the
accepted/run/report/failure/error DTOs, concrete statuses and `no-store` behavior;
it removes the unused framework `422`. The HTTP composition initializes and reuses
one process-wide online application.
Initialization is attempted once per process. Failure makes only this product
unavailable until backend restart. Offline OpenAPI export does not initialize run
storage.

WP8-A implements HTTP delivery only; WP8-B introduces the first Web consumer and
its generated artifacts and freshness checks. The new frontend feature owns its committed
OpenAPI representation and generated TypeScript contract under
[ui_web/contracts.md](../../../ui_web/contracts.md). The reader payload remains
the versioned producer projection and must not be replaced by a hand-written
competing backend schema.

## Compatibility and non-goals

- `POST /research/execute`, `GET /research/preview`, `GET /research/capabilities*`
  and their Plan/Batch semantics are unchanged and do not accept R01-A.
- Research Publication V1 and Research Explorer remain unchanged; online runs are
  not publications.
- No Celery, Redis, queue, database, scheduler, distributed lock, progress stream
  or generic task framework is introduced.
- No backtest, strategy parameter, multi-product comparison, client method
  selection, full offline evidence download or report HTML endpoint is introduced.
- Deployment, HTTPS termination, proxy trust and public exposure remain outside
  this contract and follow the existing Auth deployment boundary.

## Runtime acceptance

WP8-A synthetic runtime evidence and handoff are recorded in [HTTP acceptance](ACCEPTANCE.md).

## Input preflight delivery

`POST /research/futures-basis/preflight` consumes the same strict three-field body,
4 KiB bound, authentication/same-origin gate and no-query rule as submission. It
invokes Research [Preflight](../../../market_research/descriptive/cases/futures_basis/PREFLIGHT.md)
without initializing Run storage. Success, including a blocked assessment or a
classified dependency failure, is 200. L1/body failures are 400 invalid_request
(or request_too_large); semantic L1 errors include the safe Research-owned field
param and message. Unexpected defects are 500 internal_error. Auth errors
remain independent; no 422 is published. Responses are no-store and bounded to
64 KiB. There is no Run ID or preflight ticket.

The response is `{request, checked_at, market_date, submission, today_gate,
dependencies}`. Request is FuturesBasisImmutableRequest; checked_at is UTC ISO
timestamp and market_date an ISO date. submission is allowed/confirm_required/blocked;
today_gate is not_applicable/ready/not_ready/unknown. Each dependency has
`dependency` (calendar_cffex/calendar_sse/futures/index), `scope` (window/today),
`state` (complete/needs_fetch/unknown/operation_error/contract_error), `coverage`
(public six-field Coverage or null), `reason_code` (null/cache_incomplete/
prerequisite_incomplete/prerequisite_unavailable/operation_failed/invalid_evidence),
and fixed safe `message`. Research owns all classification and aggregation.
