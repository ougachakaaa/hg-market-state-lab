# Calendar spread public inputs and reproduction

Specializes [the case](ARCHITECTURE.md) and [Research upstream policy](../../../UPSTREAM.md).
Only Input Preparation performs upstream I/O. Financial construction, population
selection, Statistics adaptation and result projection perform none.

## Selected public capabilities

DataLake-first review finds the required facts and completeness publicly available:

| Required facts | Selected public Python boundary |
| --- | --- |
| Complete CFFEX calendar, including closures | `data_lake.datasets.tushare_trade_calendar`: `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`, calendar schema 1 |
| Same-day real-contract Close and metadata | `data_lake.datasets.tushare_equity_index_futures`: `FuturesDailyRange(product_codes=[product_code], start_date, end_date)`, futures_daily schema 2 |

Use their public `create_service()`/`export()`/`ensure()` boundaries under
[Calendar Service](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md)
and [Futures Service](../../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md).
No Index Daily, SSE calendar or Snapshot product is needed; the underlying identity
is metadata association, not a request for an underlying price. No Source client,
private catalog, SQLite, provider adapter or alternate price source is authorized.

<a id="read-only-preparation-and-completeness"></a>

## Preparation modes and completeness

Issue #13 defines the execution target below; the existing read-only APIs remain
supported. [Application](APPLICATION.md) owns execution entrypoints and operational
verification limits, not an alternative input policy.

Validate explicit canonical product/date inputs before service construction or I/O.
Dates are date-only; reject timestamps, reversed ranges and market end dates after
the operation's Asia/Shanghai current date. Do not normalize or silently default
product/date inputs. Daily prepares `[trade_date, trade_date]`; Research prepares
`[history_start, evaluation_date]` with history_start strictly earlier than the
evaluation date. There is no implicit latest-session selection.

The existing `prepare_inputs`, `query_daily_spreads` and
`query_historical_relative_value` remain synchronous and read-only: export Calendar
first, then Futures for the same window; fail on legal incomplete inputs without
Ensure. Their injectable service protocols continue to require only `export`.

Explicit execution uses `prepare_inputs_for_execution` through the two `execute_*`
application entrypoints. After validating the entire business request:

1. Export the exact-window CFFEX Calendar; validate the whole public view, including
   a partial view, before deciding whether preparation is permitted.
2. If legal but incomplete, Ensure that same request at most once, validate and
   retain the normal EnsureResult, then export and validate again. A complete first
   Export is already the final Export; no extra operation is needed on a hot cache.
3. Require a complete final Calendar before determining ordered CFFEX open dates.
4. Export the exact-window single-product Futures request and validate against that
   full session domain. Apply the same conditional, at-most-once Ensure and final
   Export validation. Require complete final Futures before Observation/Statistics.

A normally returned EnsureResult, including complete=false or UnitFailures, always
leads to the final Export check. Only that Export's proof and payload determine
availability; Ensure complete=true does not authorize proceeding without it.
Operation-level exceptions or malformed public results fail immediately, without
retry or another dependency call. Never use Ensure to repair malformed evidence,
incompatible caches or arbitrary OperationError. No redundant coverage call,
per-date/per-pair acquisition, source substitution or unbounded retry is authorized.

The Case limit is one Ensure per dependency per formal execution. Futures retains
its own Calendar prerequisite under [TRADING_DAYS](../../../../data_lake/datasets/tushare_equity_index_futures/TRADING_DAYS.md);
its internal public Calendar calls are not additional Case attempts. Do not
reimplement, bypass or inject a private prerequisite context. Independent operations
may observe changed Calendar state: a prerequisite failure or Futures target/row
mismatch with the retained Case Calendar fails explicitly, without restarting the
Case sequence. No cross-Dataset snapshot or lock is promised.

Factories remain lazy and follow dependency order. Full legal hot caches and a
complete closed-day Calendar with zero Futures targets require no Case Ensure or
Source credentials. A complete empty active universe remains a valid business input.
No startup preparation, cache deletion or automatic rebuild is introduced.

Validate final Dataset/view/schema, scope/window, full coverage counters, complete
formula, ordered unique records, all public field legality and product/lifecycle
associations. Calendar must prove every natural date, including closures. Futures
must prove every product × CFFEX open date; its row count need not equal its unit
count. Proof and payload must come from the same final Export. An incomplete
Calendar or Futures Export is a classified incomplete-input failure, never an
accepted subset or normal missing quote. Malformed evidence and OperationError
are separate explicit failures, never legal emptiness.

A complete product-day with no records proves an empty active universe. Otherwise
its complete rows supply that day's active metadata and quotes. Construct the
published `ContractMetadata` and `DailyUniverseEvidence` carriers only after
validation, retaining their exact association to the final Export; invoke
`resolve_daily_slots` through the public Futures Basis facade. Never union catalog
metadata across days, use price availability to change mapping or set complete=True
without producer proof. Irregular active sets fail explicitly.

Finite nonpositive Close values may be legal producer facts but are excluded by
this case's financial legality. Missing/non-finite required fields inside a
successful row violate the upstream contract and fail preparation. No fallback,
filling or date shifting is allowed.

## Evidence and limits

Retain immutable copies or lossless equivalents of explicit requests, final typed
Exports with their complete public fields/proofs, validated session domain, daily
Slot mappings, definition version and observation outcomes. Historical results
also retain population identities, selected metric, actual sample dates, numerical
specs/results and evaluation cutoff. Caller-retained in-memory evidence is enough;
no Run Store, filesystem evidence format or mandatory persistence is introduced.
A digest, date window or mutable upstream cache alone does not reproduce inputs.

Ensure diagnostics are acquisition evidence only, not financial inputs or a
replacement for final Exports. Keep them in caller-retained Python objects; do not
serialize raw UnitFailure reasons or exception causes to HTTP/Web.

The two dependency exports are independent snapshots; they promise neither common
acquisition time nor provider-current freshness. Futures metadata is the producer's
retained successful basis and is not guaranteed to be metadata known on trade_date.
Filtering sample dates before evaluation_date prevents future observation leakage;
it does not assert a historical point-in-time metadata dataset. Expose this limit
truthfully, without fetching a replacement catalog or inventing stronger evidence.

## WP2 Python preparation boundary

`prepare_inputs(product_code, start_date, end_date, *, calendar_service=None,
futures_service=None)` returns frozen `PreparedCalendarSpreadInputs`. Only exact
canonical product strings and date-only dates are accepted, with inclusive ordered
bounds and end_date no later than the operation's Asia/Shanghai current date.
The injectable service protocols require only the corresponding public `export`.
Default factories are constructed lazily, after request validation and in export
order. Each dependency is exported once; no coverage/ensure or retry occurs.

Prepared inputs retain `CalendarSpreadRequest`, both public semantic requests,
validated immutable copies of both typed Exports and `candidate_dates`. Every
published field is retained; sequence fields are copied to tuples, including
scope and records. Evidence binds each final Export to its exact request. Complete
Calendar proves every natural day; complete Futures coverage proves each open
product-day, including zero-record success. A nonempty irregular active set is
not repaired; Slot structure is validated by the public resolver in construction.

`InputPreparationError` retains category, stage, dependency, reason and a tuple
of `InputEvidence` for already validated exports (including a legal incomplete
export that causes failure). Malformed exports are not advertised as legal evidence.
Invalid caller semantics map to `invalid_request`; legal incomplete proof maps to
`incomplete_inputs`; public OperationError maps to `upstream_unavailable`;
malformed exports or rejected validated upstream requests map to
`input_contract_error`. Unexpected service/programming exceptions propagate.
Construction revalidates retained requests, exports and candidate association,
without applying a new current-date check or performing I/O.

## Execution preparation and diagnostics boundary

`prepare_inputs_for_execution(product_code, start_date, end_date, *,
calendar_service=None, futures_service=None)` returns the same
`PreparedCalendarSpreadInputs`. It preserves read-only request validation and
final-proof rules. The facade adds `ExecutionCalendarService` and
`ExecutionFuturesService` protocols requiring the respective public `export` and
`ensure(request) -> EnsureResult`; existing export-only protocols stay unchanged.
Both modes reuse validation and immutable final-input assembly within this Case.

The facade adds frozen `InputPreparationAttempt` carriers containing `dependency`,
exact public `request`, optional validated immutable `preliminary_export`, optional
validated immutable `ensure_result`, optional validated immutable `final_export`,
and optional safe `reason_code`. `PreparedCalendarSpreadInputs` adds an immutable
`attempts` tuple with an empty default for existing callers. Execution records one
attempt per reached dependency; a complete first Export is both preliminary and
final. Record the attempt before calling the service, so a failure retains its
request and preceding evidence. No malformed result is labeled validated evidence.
The existing `evidence` projection continues to describe final inputs only.

Validate EnsureResult public non-bool nonnegative counters, boolean complete,
public attempt accounting, exact requested target count, failures count and unique
target UnitFailure identities with public semantic types and string reasons.
Calendar targets are CFFEX × every natural date and records_written equals
succeeded_units; Futures targets are the selected product × complete CFFEX sessions,
and records_written is a contract-row count, not succeeded_units. Retain every
published result field and UnitFailure in an immutable copy. Do not compare Ensure
counts to a later Export as if they were one snapshot or infer Source causes from
aggregate failures. A malformed EnsureResult fails `input_contract_error` before
another Export.

`InputPreparationError` and its application adaptation retain existing categories,
validated InputEvidence, immutable attempts and optional safe `reason_code` and
`operation` (`export`, `ensure`, `final_export`; absent for request validation).
The existing stage `input_preparation` and dependency remain available. Additive
fields have empty/None defaults; existing constructors and export-only injection
remain compatible. Known failures use fixed safe reasons; raw upstream text is not
copied into user-facing fields. Unexpected programming exceptions still propagate.

| Condition | Existing category | reason_code |
| --- | --- | --- |
| Invalid business request | invalid_request | None |
| Legal incomplete Export in read-only preparation | incomplete_inputs | cache_incomplete |
| Legal final Export still incomplete after Ensure | incomplete_inputs | final_export_incomplete |
| Public CredentialMissingError | upstream_unavailable | credential_missing |
| Public CacheIncompatibleError | upstream_unavailable | cache_incompatible |
| Other public OperationError | upstream_unavailable | operation_unavailable |
| Malformed public Export | input_contract_error | malformed_export |
| Malformed normal EnsureResult | input_contract_error | malformed_ensure_result |
| Validated request rejected by public service as InvalidRequestError | input_contract_error | upstream_request_rejected |

Catch the public OperationError subclasses before their base class; do not match
messages, inspect Provider internals or reinterpret a generic wrapped prerequisite
OperationError as a more specific cause. UnitFailures followed by an incomplete
final Export use final_export_incomplete; a later complete legal Export can succeed
while retaining those diagnostics. Missing input that is successfully prepared is
normal success, not a new warning/error category. This remains a complete-input
Case; no legal partial final Calendar/Futures is accepted.
