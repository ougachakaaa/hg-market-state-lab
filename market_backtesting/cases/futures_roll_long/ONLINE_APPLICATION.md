# Futures Roll Long online application, run lifecycle and delivery ownership

## Storage authority and delivery status

Business lifecycle and public interfaces remain owned here. SQLite is the sole online
storage implementation; [Online storage](ONLINE_STORAGE.md) owns its physical layout,
transaction, integrity, portable path and initialization requirements.

This contract owns the case-specific online request, read-only readiness assessment,
run lifecycle, runtime result store, owner boundary and read semantics for the
[case](ARCHITECTURE.md). HTTP transport belongs to `ui_http` (WP6); browser interaction
belongs to `ui_web` (WP7). This document does not define the HTTP DTO/OpenAPI or the Web
layout, and does not own Policy, Core, Performance, Inputs or Result semantics.

The design deliberately reuses operational principles validated by
[W1 R01-A online application](../../../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md),
but never its run identity, storage, result profile or business semantics. It is not
Research Publication, a ResearchPlan/Job/BatchResult, a Workbench Run, or a generic
durable execution framework.

## Scope and non-goals

The first online release accepts exactly one case, one product, one inclusive
date-only window and one explicit strategy profile per execution. It returns one
validated `futures_roll_long_result_v1` result and no partial result.

No queue, message broker, scheduler, Celery/Redis, database migration, distributed
execution, list/cancel/delete/retry API, production SLA or automatic cleanup is
introduced. The disposable runtime store is application state, not market facts,
Research evidence, Publication or Workbench history.

## Semantic request

```text
case              = futures_roll_long_v1
product_code      = IM | IC | IF | IH
start_date        = date (inclusive)
end_date          = date (inclusive)
strategy_profile  = expiry_to_M1_v1 | expiry_to_Q1_v1
```

There is no product, date, profile, benchmark, multiplier or roll-rule default. The
client cannot select a different case, benchmark, multiplier, roll rule, fee model or
strategy parameter. The case is bound by the application; only the four client
parameters above are accepted under the WP6 wire contract.

Pure request validation delegates to the [case request contract](ARCHITECTURE.md#request-and-identity)
before run creation or upstream I/O. It applies the canonical product/profile,
date-only, inclusive-window, Asia/Shanghai future-date and maximum-span rules.

The request does not carry a session count; whether the window contains at least two
CFFEX sessions is established during input preparation and fails as
`prepare/invalid_case_input/insufficient_sessions` if not. The HTTP layer strictly parses the
request and maps the owning application's classified failure; it does not duplicate a
second semantic validator.

## Read-only readiness assessment

`preflight` is an authenticated, read-only operation over the same semantic request.
It never creates a run, calls `ensure`, performs Source I/O or writes a cache. It
evaluates exact-window Calendar/Futures/Index coverage/export where those public
read-only facts are available, and reports per-dependency status plus limitations.

Readiness is advisory:

- `ready=true` means the exact public cache coverage is complete, not that rows, Slot
  structure, values, provider freshness or eventual execution will succeed;
- `ready=false` does not block submission; execution may still ensure missing cache
  units and then revalidate;
- Calendar incompleteness makes downstream readiness `unknown`, not guessed;
- Index readiness is `unknown` when the underlying cannot be derived without a usable
  Futures row;
- preflight never acquires data and never returns a fake successful result.

The Web surface may present readiness before submit, but it must preserve this
advisory/non-guarantee distinction.

## Run identity, owner and lifecycle

A run has a server-generated opaque `run_id`: 128-bit rendered as 32 lowercase hex
characters. It contains no product, date, owner, sequence or filesystem information;
clients must not parse it. A malformed ID is treated as not found before storage access.

Each run binds an immutable request and an `owner_scope` supplied by the authenticated
`ui_http` boundary. The owner is an application privacy key, not a second
authentication mechanism. It is stored only in server-owned metadata and is never
returned by a status, result, error or Web projection. Unknown, malformed and foreign
run IDs all classify as `run_not_found`, so existence is not disclosed.

Execution states:

| State | Result available | Transitions |
| --- | --- | --- |
| `PENDING` | no | `RUNNING`, `FAILED`, `INTERRUPTED` (restart) |
| `RUNNING` | no | `COMPLETED`, `FAILED`, `INTERRUPTED` |
| `COMPLETED` | yes | terminal |
| `FAILED` | no | terminal |
| `INTERRUPTED` | no | terminal |

`COMPLETED` always has a validated result. `FAILED` and `INTERRUPTED` never serve a
result. A run cannot transition out of a terminal state. There is no partial result
state in v1.

## Execution and concurrency

- Only one execution may be active across the backend process.
- A submission while one is active is rejected as busy before any Run is
  created; there is no queue and no waiting list.
- Submission returns immediately (the HTTP request is accepted; no request remains open
  during acquisition or computation). A single in-process worker performs input
  preparation, Policy-driven Core Replay and case performance analysis; the browser polls status.
- Status reads are cheap and may proceed concurrently. They inspect stored metadata
  only; they do not execute the backtest, parse the result or acquire a result-read
  permit.
- A full result read is bounded to one reader permit per process. Excess concurrent
  full reads are a manual-retry `read_busy` condition, not a queue. Status reads do not
  consume that permit.
- MVP support is a single backend process. Multiple processes/workers sharing a root,
  distributed locks, external queues or durable workers are unsupported because the
  in-process active-run guard and restart recovery would conflict.
- No wall-clock deadline or cancellation is provided; provider availability and
  long-running work are not promised.

## Execution path and publication

The worker executes the accepted public path:

```text
validated semantic request
  → public input preparation (Calendar / Futures / Index)
  → complete input validation + canonical fingerprint
  → price-free W2 Policy targets (authorized W1 Slots on entry/roll only)
  → Core Replay: Transition → Accounting → Recorder on every session
  → W2 Performance Analyzer: Core consumption + benchmark / excess / drawdown
  → immutable BacktestResult + evidence summary + V2 views
  → validate profile, request association, coverage, invariants and finite JSON
  → atomically commit result bytes and COMPLETED in one SQLite transaction
```

Before publication, validate at least: result profile is exact; status is `complete`;
the request matches the run request; the fingerprint is present and belongs to the
prepared inputs; all daily/trades/summary/evidence invariants from [Result](RESULT.md)
hold; the views validate against V2; the serialized payload is finite canonical JSON;
and the serialized result is at most 32 MiB.

Exceeding the size bound fails the run with
`result_publication/result_too_large`; it never truncates. Result bytes and COMPLETED
are committed together. A reader must never see a completed run without a validated result. A storage failure is classified, never silently
repaired.

## Failure classification

Run failures expose a safe `{stage, category, dependency, reason}` record. HTTP may
map the category to a transport status/body, but must not reclassify the financial or
application meaning.

| Stage | Meaning |
| --- | --- |
| `request` | WP3 pure request validation |
| `export`, `ensure`, `prepare` | Actual WP3 public input operation |
| `replay` | Actual WP3 replay operation, including Policy, Transition and Accounting |
| `analysis` | Actual WP3 Analyzer operation |
| `result_validation` | WP4 result construction and validation |
| `result_publication` | Bounded serialization and atomic publication |
| `execution` | Thread startup, recovery or unknown failure |

Preserve recognized `FuturesRollApplicationError.stage`, category, reason and dependency.
Dependencies are `calendar_cffex`, `calendar_sse`, `futures`, `index` or null.
The already public category is `incomplete_input`, not `incomplete_required_input`;
fewer than two sessions remains `invalid_case_input/insufficient_sessions`.
Core/Case `invalid_numeric`, `invalid_accounting`, `accounting_failure`, `invalid_result`
and `invalid_evidence` retain their category/reason. Stage follows the actual operation:
accounting failure during replay is `replay`, not synthetic `accounting`.
The existing `missing_instrument_quote` to `missing_contract_row` translation remains.

An explicit safe category/reason allowlist excludes arbitrary exception text.
Unknown exceptions/classifications become fixed `{stage: execution, category:
internal_failure, dependency: null, reason: internal_failure}`.
Publication uses fixed category/reason `result_too_large`, `serialization_failure` or
`storage_failure`; recovery uses `execution/interrupted/interrupted`.
Diagnostics, detail, provider messages, credentials and paths are never projected.

The public DataLake `CredentialMissingError` is translated to `upstream_operation / credential_missing`, preserving actual stage/dependency, and is included in the safe reason vocabulary. Generic OperationError remains `operation_unavailable`; the typed cache incompatibility specialization is defined below. Preflight stays read-only; submit-time Ensure, HTTP DTO shape and persistence behavior are unchanged.

Representative preserved Core/Case reasons:

| Category | Representative stable reasons |
| --- | --- |
| `invalid_case_input` | `invalid_product_code`, `invalid_strategy_profile`, `insufficient_sessions`, `session_order_not_increasing`, `duplicate_session`, `invalid_session_facts`, `duplicate_session_facts`, `unknown_contract_fact` |
| `slot_resolution` | `missing_decision_evidence`, `invalid_decision_evidence`, `w1_slot_resolution_error` |
| `missing_market_fact` | `missing_session_facts`, `missing_contract_row`, `missing_active_contract_metadata` |
| `invalid_price` | `non_finite_close`, `non_positive_close` |
| `roll_target_invalid` | `target_not_resolved`, `target_expired`, `target_without_holding_period`, `target_equal_held_contract`, `target_inactive` |
| `invalid_contract_lifecycle` | `invalid_contract_metadata`, `duplicate_contract_code`, `duplicate_delivery_month`, `conflicting_product`, `conflicting_underlying`, `held_contract_inactive`, `held_contract_missing_from_active_set`, `expiring_held_contract_not_m0` |
| `invalid_position_state` | `held_contract_expired_without_roll`, `no_position_on_final_session`, `unexpected_flat_state`, `final_state_not_flat` |
| `accounting_failure` | `multiplier_mismatch`, `non_positive_equity` |
| `invalid_input` / `invalid_target` | Core validation reasons such as `sessions_not_increasing`, `snapshot_date_mismatch`, `instrument_reference_conflict`, `quantity_change_unsupported` |
| `invalid_accounting` | `inconsistent_previous_accounting`, `session_already_accounted` |
| `invalid_numeric` | Name of the rejected numeric value, such as `initial_capital`, `daily_pnl`, `equity` or `cumulative_return` |

`no_position_on_final_session` is unreachable under valid v1 input and remains a
defensive failure guard, consistent with [Strategy](STRATEGY.md). A
`held_contract_expired_without_roll` failure is reachable when the observed session set
skips the held contract's actual last trading day. Missing data, an illegal target or an
illegal state is always a classified failure; it never becomes a partial result.

Reasons are fixed safe text or sanitized with the case policy. No filesystem path,
provider credential, URL, raw exception, traceback, SQL or private metadata enters a
run, HTTP projection or Web display. Missing data is a classified failure, not a
legal partial result.

## Runtime storage and retention

The case owns an independent SQLite runtime store. [Online storage](ONLINE_STORAGE.md)
is the canonical owner of root configuration, database layout, bounded reads,
transactions and portable filesystem checks. Unavailable storage isolates this product;
preflight and unrelated HTTP products remain usable. Old Run directories are ignored,
without migration or automatic deletion. Operators own retention and capacity.

## Startup recovery

At startup, every persisted `PENDING` or `RUNNING` run is marked `INTERRUPTED` with a
recovery finish time. A run that is not the current process's active run is never
reported as running. If the process stops after result bytes are written but before the
completed state is committed, the result is not served; the run remains interrupted.
No partial or orphaned result may appear completed.

## HTTP and Web ownership

`ui_http` (WP6) owns the HTTP product contract: strict JSON parsing and transport
limits, DTO projection, status/error mapping, OpenAPI publication, authentication
integration and no-store behavior. It consumes only this application's published
operations:

```text
read-only preflight
submit run
read run status
read validated result
```

Exact paths, operation IDs, DTO field names, HTTP statuses and OpenAPI components are
WP6 deliverables and are not claimed by this authority gate. The HTTP DTO must remain a
faithful projection of the owning result; it must not compute PnL, returns, benchmark,
drawdown, trades, coverage or limitations. There is no list/cancel/delete/retry
operation in v1.

`ui_web` (WP7) owns the `/backtesting` page interaction and presentation:
Ant Design controls, request/preflight presentation, submit/poll, producer-owned V2
charts, trades/rolls table, evidence/limitations and busy/failed/interrupted/error
states, plus the feature's generated OpenAPI/TypeScript contract freshness loop. The
page must not fabricate results, controls or readiness. WP7 replaced the previously
planned page with the real workflow; actual Web acceptance is recorded in
[WP7 acceptance](../../../ui_web/src/features/backtesting/ACCEPTANCE.md) and the
full real-market/Windows evidence in [WP8](WP8_ACCEPTANCE.md).

Auth and access:

- every operation uses the existing authenticated Cookie/Auth gate; no anonymous
  health, bypass or alternate access path is created;
- unsafe methods require the existing same-origin check;
- all authenticated responses are no-store;
- owner isolation is enforced by this application, with Auth supplying the identity;
- HTTP Auth errors are handled before business validation/invocation;
- no new user, role, approval, token or session mechanism is introduced.

## Deferred online scope

Explicitly deferred or out of scope for W2 v1:

- list/history, delete, cancel, retry, idempotency keys, queue/fair scheduling and
  automatic cleanup;
- multi-process execution, distributed locking, workers and durable recovery beyond
  startup interruption;
- a separate online evidence/replay endpoint (the result carries the evidence summary;
  the full package/replay belongs to WP4);
- Publication admission, Research Explorer admission and Workbench Run integration;
- production deployment, public ingress, trusted-proxy client IP handling, Nginx/Docker
  packaging, SLA claims.

These are not implied by a successful WP5/WP6/WP7 run. WP8 records the actual integrated
acceptance and any NOT RUN platform/deployment boundaries.

## WP5 public Python facade

The case package exports `create_futures_roll_online_application`,
`FuturesRollOnlineApplication`, `OnlineRunStatus`, `OnlineFailure` and
`FuturesRollOnlineError`. Operations are `preflight(request, owner_scope)`,
`submit(request, owner_scope)`, `get_status(run_id, owner_scope)` and
`get_result(run_id, owner_scope)`. Status/failure carriers are frozen; result is the
existing BacktestResult. Preflight delegates to WP3 independently of store availability.
Every operation requires a nonempty string owner. Public operation errors classify as
`invalid_request`, `run_busy`, `read_busy`, `run_not_found`, `result_not_ready`,
`unavailable` or `corrupt`; messages contain only that fixed classification.

Private records bind run ID, immutable request/owner, UTC ISO timestamps and version 1.
Process-wide admission also serializes initialization/recovery; recovery skips the
actual current-process active run. Terminal-persistence failure makes the application
unavailable until restart, preventing stale RUNNING responses. Corruption fails closed.

Minimal single-process usage:

```python
app = create_futures_roll_online_application()
readiness = app.preflight(request, owner_scope)
accepted = app.submit(request, owner_scope)
status = app.get_status(accepted.run_id, owner_scope)
# Poll status; only COMPLETED permits:
result = app.get_result(accepted.run_id, owner_scope)
```

Optional `LAB_BACKTESTING_RUN_ROOT` uses lab_config and root `.env`/process environment.
Native Windows uses the same SQLite implementation as Linux/WSL on local filesystems.

## Safe cache incompatibility failure

`cache_incompatible` is a fixed safe OnlineFailure reason for `upstream_operation`, preserving the acquisition stage and dependency from the application. Status persistence retains this reason; arbitrary exception messages, SQLite details and paths never enter the public failure. See [Inputs](INPUTS.md#cache-incompatibility-classification) for producer classification.
