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

Use their public `create_service()`/`export()` boundaries under
[Calendar Service](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md)
and [Futures Service](../../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md).
No Index Daily, SSE calendar or Snapshot product is needed; the underlying identity
is metadata association, not a request for an underlying price. No Source client,
private catalog, SQLite, provider adapter or alternate price source is authorized.

## Read-only preparation and completeness

Validate explicit canonical product/date inputs before service construction or I/O.
Dates are date-only; reject timestamps, reversed ranges and market end dates after
the operation's Asia/Shanghai current date. Do not normalize or silently default
product/date inputs. Daily prepares `[trade_date, trade_date]`; Research prepares
`[history_start, evaluation_date]` with history_start strictly earlier than the
evaluation date. There is no implicit latest-session selection.

The two implemented product queries are synchronous and read-only: export Calendar
first, then Futures for the same window. They never call ensure or repair caches.
An operator can prepare caches separately with the existing public DataLake ensure
operations; this introduces no new acquisition command or startup behavior.

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
