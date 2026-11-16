# Calendar spread shared business boundary

Specializes [the case](ARCHITECTURE.md). All interfaces below are planned WP1–WP4
Python semantic boundaries, not implemented APIs or HTTP DTOs. They are published
through `market_research.descriptive.cases.futures_calendar_spread` when delivered.

## Shared capability

`compute_calendar_spread(near_close, far_close, near_last_trade_date,
far_last_trade_date)` is the sole pure implementation of the three financial
metrics and their between-contract day difference under [Definition](DEFINITION.md).
It returns immutable named metrics with units and the definition version, or an
explicit validation/calculation failure. Observation owns trade-date lifecycle
checks and nonpositive-price exclusion before invoking this capability. The public
function also rejects illegal prices/dates/delta rather than trusting its caller.

`prepare_inputs(product_code, start_date, end_date)` performs only the read-only
public input work in [Inputs](INPUTS.md); public-service injection is allowed for
deterministic tests. `construct_observations(prepared_inputs)` is pure. Both queries
compose these operations. They do not independently calculate financial values or
share a generic workflow base class.

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
Transport maps these categories without reclassifying normal product availability.
Closed dates, proven empty universes, nonpositive-price exclusions and empty/small
historical samples are valid product outcomes, not infrastructure exceptions.

Queries perform no ensure, writes, automatic retries, source substitution, background
execution or cross-request result persistence. They create no Run ID, durable store,
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
