# Calendar spread shared business boundary

Specializes [the case](ARCHITECTURE.md). The WP1 financial and WP2
preparation/construction APIs and WP4 independent queries are implemented through
`market_research.descriptive.cases.futures_calendar_spread`. They are Python
semantic boundaries; HTTP delivery is owned separately. Issue #13's explicit
execution APIs were delivered in Issue #13 WP1; HTTP/Web integration was delivered
in Issue #13 WP2. Operational verification limits are recorded below. The immutable
business schema and association contract are owned by [Query Results](QUERY_RESULTS.md).

## Shared capability

`compute_calendar_spread(near_close, far_close, near_last_trade_date,
far_last_trade_date)` is the sole pure implementation of the three financial
metrics and their between-contract day difference under [Definition](DEFINITION.md).
It returns immutable named metrics with units and the definition version, or an
explicit validation/calculation failure. Observation owns trade-date lifecycle
checks and nonpositive-price exclusion before invoking this capability. The public
function also rejects illegal prices/dates/delta rather than trusting its caller.

The public signature accepts `near_close: int | float`, `far_close: int | float`,
`near_last_trade_date: date` and `far_last_trade_date: date`, returning
`CalendarSpreadResult`. Prices accept only exact built-in int/float types (no bool,
subclasses, Decimal or implicit string conversion), converted to finite positive
binary64. Conversion overflow is an input failure. Dates require exact
`datetime.date` values, excluding timestamps and subclasses; delta_days must be
positive. All inputs are validated before financial arithmetic.

`CalendarSpreadResult` and `CalendarSpreadMetric` are frozen, slotted dataclasses.
The result contains `signed_spread`, `annualized_point_spread` and
`annualized_spread_ratio` as named metric carriers, `delta_days: int` and
`definition_version`, fixed by computation to
`futures_calendar_spread_definition_v1`. Each metric retains `value: float`,
`metric_id` equal to its result field name, and the corresponding Definition unit.
No mutable containers or presentation rounding are introduced.

The facade exports `CalendarSpreadValidationError(ValueError)` for illegal input
and `CalendarSpreadCalculationError(ArithmeticError)` for valid-input numerical
failure. Callers distinguish these by exception type, without parsing messages.
Arithmetic exceptions retain their cause. Each executed intermediate and result
must be finite; a zero price ratio from underflow fails rather than reaching a
successful result. Evaluation follows the Definition's written operation order,
without algebraic repair or partial success. The pure API performs no I/O and
requires neither trade_date nor near DTE; lifecycle checks belong to Observation.

## Preparation and construction

`prepare_inputs(product_code, start_date, end_date, *, calendar_service=None,
futures_service=None)` performs only the read-only public input work in
[Inputs](INPUTS.md); public-service injection is allowed for deterministic tests.
`prepare_inputs_for_execution` has the same parameters and returns the same
prepared carrier, with conditional Ensure under Inputs. It is the preparation
boundary for explicit execution only. `construct_observations(prepared_inputs)` is
pure. Read-only queries and execution entrypoints compose the selected preparation
with the same construction and statistical analysis. They do not independently
calculate financial values or share a generic workflow base class.

Preparation returns `PreparedCalendarSpreadInputs`; construction returns
`CalendarSpreadObservationSet`. Their immutable carriers and classified exceptions
are exported by the case facade under [Inputs](INPUTS.md#wp2-python-preparation-boundary)
and [Observation](OBSERVATION.md#wp2-public-construction).

## Independent product queries

| Operation | Explicit request | Successful result |
| --- | --- | --- |
| `query_daily_spreads` | `product_code`, `trade_date` | Case/definition identity, echoed request, candidate session status, six ordered Pair-day outcomes on open dates, accounting and source context |
| `query_historical_relative_value` | `product_code`, `history_start`, `evaluation_date`, `metric=annualized_spread_ratio`, optional `histogram_edges` | Identity/request, current Daily observation projection, six pairs' four independent historical distributions, matching-stage/all-stages current assessments, sample/candidate accounting and provenance/limitations |

Daily always returns all three metrics. Research's metric changes the analysis,
not the underlying Observation definition. A metric change is a new query identity;
viewing a different pair among a returned result does not cause business recomputation.
Quantile probabilities, ties rule and the small-sample threshold are case policy,
not frontend defaults. Explicit edges are optional method parameters; units come
from the selected metric and cannot be independently overridden.

Validate query semantics before I/O; validate legal optional statistical parameters
through Statistics public spec validation. Dates/product/case association, actual
contracts, null/zero semantics, status/reasons, sample identity, units, full method
parameters and source limitations must survive product projection. Public results
retain the underlying business evidence in Python; transport publishes safe source
context and sample dates/counts, never credentials or private filesystem paths.

## Failures and lifecycle

Business failure categories are `invalid_request`, `incomplete_inputs`,
`upstream_unavailable`, `input_contract_error`, `slot_resolution_error`,
`calculation_failure` and `statistical_failure`. Retain stage, dependency or pair/date
where applicable, method where applicable, safe reason and obtained evidence.
Preparation failures also propagate the optional reason_code, operation and
immutable attempts defined solely by [Inputs](INPUTS.md#execution-preparation-and-diagnostics-boundary);
application adaptation must not discard them.
Transport maps these categories without reclassifying normal product availability.
Closed dates, proven empty universes, nonpositive-price exclusions and empty/small
historical samples are valid product outcomes, not infrastructure exceptions.

The existing `query_*` functions perform no Ensure or writes. Explicit `execute_*`
functions may prepare caches only through Input Preparation. Both modes are
synchronous, without automatic retries, source substitution, background execution
framework or cross-request result persistence. They create no Run ID, durable store,
ResearchPlan, Batch, Publication or execution ownership identity. Existing repository
HTTP authentication gates access; it does not turn query results into stored Runs.

## Delivery owners

- [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md)
  and [Research HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md)
  own wire projection and status mapping.
- [Daily Web](../../../../ui_web/src/features/futures_calendar_spread/ARCHITECTURE.md)
  and [Research Web](../../../../ui_web/src/features/calendar_spread_relative_value/ARCHITECTURE.md)
  own independent Presentation, not formulas or numerical algorithms.
- [Demo integration](../../../../ui_web/demo/CALENDAR_SPREAD.md) consumes those formal
  HTTP Results only, after runtime delivery and Bundle admission.

## WP4 query execution

`query_daily_spreads(product_code, trade_date, *, calendar_service=None,
futures_service=None)` validates the request, calls WP2 prepare_inputs once for
that day, then construct_observations once, returning DailySpreadsResult.

`query_historical_relative_value(product_code, history_start, evaluation_date,
metric="annualized_spread_ratio", histogram_edges=None, *, calendar_service=None,
futures_service=None)` validates product, exact date-only ordered bounds,
Asia/Shanghai future-date exclusion, exact metric identity and optional explicit
IntervalCountSpec before I/O. It then prepares the inclusive window once and
constructs one ObservationSet. Dates strictly before evaluation_date supply all
historical groups; the final day supplies only current values. Statistics is
consumed only through its root public Python API. No injected clock, window
fallback, consumer-specific numeric algorithm or additional default is introduced.

Shared preparation performs core I/O, exporting Calendar then Futures once each. No
per-date, per-pair or per-method core exports occur. Missing/incomplete core caches
remain explicit failures; operators must prepare them separately. Both independent
snapshots and the lack of historical point-in-time metadata are disclosed in
returned source_context. Queries execute synchronously with memory/time growing
with the explicitly requested window; no arbitrary date cap or timeout is added.
Transport/resource limits and safe DTO/error projection belong to the published
HTTP contracts. This paragraph describes read-only Python queries only; formal
user execution uses the entrypoints below.

## Explicit execution entrypoints (Issue #13 target)

The case facade adds:

```text
execute_daily_spreads(product_code, trade_date, *, calendar_service=None,
                      futures_service=None) -> DailySpreadsResult
execute_historical_relative_value(product_code, history_start, evaluation_date,
    metric="annualized_spread_ratio", histogram_edges=None, *,
    calendar_service=None, futures_service=None) -> HistoricalRelativeValueResult
```

Arguments, exact validation, defaults and Result types match the corresponding
read-only query; injected dependencies implement the execution protocols in Inputs.
Validate the entire request, including Historical metric/edges, before factories
or upstream calls. Each execution invokes prepare_inputs_for_execution once and
construct_observations once, then reuses the existing Daily projection or Historical
Statistics/association path. Never prepare per date, pair or method, or call the
read-only query to reacquire inputs. No generic workflow abstraction is required.

The `query_*` entrypoints and export-only injection remain available unchanged.
No public boolean flag silently upgrades their permissions. Execution and read-only
results retain existing request.operation literals `query_daily_spreads` and
`query_historical_relative_value`: these identify the analysis, not acquisition
permission. Entry selection owns permission; no new result identity or Run is
created. Given identical final Exports and analysis parameters, financial values,
populations and statistics are identical under both modes.

[Query Results](QUERY_RESULTS.md) owns accurate source_context and internal
preparation evidence. Existing Demo results remain valid without a schema or
Bundle rewrite. Existing Daily GET delegates to query_daily_spreads; new Daily
POST delegates to execute_daily_spreads. Historical POST keeps its path and HTTP
operationId but explicitly changes to execute_historical_relative_value. This is
a documented execution-semantic change, not permission for arbitrary POST reads
to acquire facts. Preflight/Readiness and static Demo remain read-only.

## Operational verification limits

Explicit preparation remains synchronous. Bounded local WSL/browser cold/hot execution
was accepted; other deployment proxy deadlines, maximum legal 3660-date requests,
prolonged load and cold-cache concurrent Source contention remain NOT_VERIFIED.
Threadpool delegation is not a latency SLA. Client cancellation stops waiting, not
necessarily Source work or SQLite writes; shared capacity remains held through worker
completion. Collector's per-request timeout is independently configurable under the
[build contract](../../../../ui_web/demo/build/ARCHITECTURE.md).

## DD-02 Daily reference target

Implemented in DD-02 WP-01. [Daily Index Reference](DAILY_INDEX_REFERENCE.md) adds
independent reference Input Preparation after successful core construction. Only query_daily_spreads and
execute_daily_spreads add keyword-only `index_service=None`; query injection requires
export, execution injection requires export/ensure. Existing calendar_service injection
also handles explicit SSE requests with the corresponding permission. Callers may omit
the new injection; default factories remain lazy. Historical signatures, shared
preparation carriers/protocols and pure construction remain unchanged.

Daily always returns the new [Query Results](QUERY_RESULTS.md#daily-underlying-index-result-dd-02-target)
reference carrier, including classified acquisition failures. This deliberately
specializes whole-query failure policy for the independent reference only. Core and
Historical failures remain unchanged. GET never Ensures; POST permits bounded
preparation only. No range query, historical detail endpoint, Run or retry is added.
Issue #13's unchanged query/injection statements describe that earlier change;
DD-02 adds this Daily-only dependency without changing read-only permissions.
