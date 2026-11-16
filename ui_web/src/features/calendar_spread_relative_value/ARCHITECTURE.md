# Calendar Spread Historical Relative Value Presentation authority

Status: WP6 implemented and READY TO CLOSE; targeted evidence and unverified
real-data/deployment limits are recorded in [Acceptance](ACCEPTANCE.md).
Inherits [Web boundaries](../../../ARCHITECTURE.md) and
[Presentation architecture](../../../presentation-architecture.md).
Financial/population meaning belongs to [Research](../../../../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md);
transport belongs to [Research HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md).

## Surface and state

The independent Research page is `/research/calendar-spread-relative-value`, titled
“Calendar Spread Historical Relative Value”. Require explicit product,
history_start and evaluation_date; default metric comes from the business contract
(`annualized_spread_ratio`). Offer the other two named metrics and optional explicit
histogram edges. No automatic frontend binning. Query submission is explicit.

The query returns all six pairs. Selecting a returned pair is local state; changing
metric, dates or edges changes query identity and requires explicit new submission.
Production hooks own loading, cancellation and stale-response isolation. There is
no Run creation, polling, restore ticket or Publication dependency. The sibling
Daily page is an independent consumer, not a source of shared semantic state.

## Presentation

Display current actual contracts/value/stage, all four historical group sizes and
quantile values, and separately labeled matching-stage/all-stages assessments.
Render Histogram only from supplied IntervalCount boundaries/counts/frequencies,
including underflow/overflow. Percentile text may multiply a returned fraction by
100 for formatting; never derive it from quantile interpolation or histogram bins.
Distinguish historical quantile values from current empirical percentile.

Show the explicit historical cutoff and actual sample date coverage/count. Keep
empty samples, 1–29 small-sample warnings, excluded current values and closed dates
visible; an all-stage comparison never masks an unavailable matching-stage result.
Higher percentile may be explained as a historically higher, relatively more
favorable long-roll Close relationship within the stated metric/population.
Include the business limits: no return prediction, trading instruction, waiting
value or point-in-time metadata guarantee. No traffic-light trading threshold.

## Integration and acceptance

Consume feature-owned generated WP5 HTTP types; expose pure validation and
public Presentation for Demo. Backend owns every financial value, stage, population,
quantile, histogram and percentile. Targeted tests verify query versus local state,
cutoff/metric labels, both assessment identities, empty/small-sample explanations,
histogram outside values, error isolation and null/zero formatting. WP6 registers the actual Production consumer; Demo admission remains WP7.

## WP6 consumer contract

Production uses feature-local explicit-submit controls and `protectedRequest`. Draft
inputs, submitted identity and local display selection are distinct. Editing a draft
never changes the identity displayed with an existing result; resubmission clears the
old result, aborts its request and isolates late completion by request token. Retry
uses the last failed submitted identity. Unmount and authentication closure cancel
and isolate requests. No polling, Run, implicit acquisition or automatic retry.

Generated OpenAPI/TypeScript in `api/` remain the only wire schema. The pure validator
checks structure, finite values, order, null/zero, identity, dates, outcome/count and
statistical association as applicable; it never computes financial/statistical results.
The public `presentation.ts` exports the transport-free Presentation and validator for
future WP7. Daily and Research own independent types, query state and projections.

Production routes are separate from gateway paths: requests use `/api/data/…` or
`/api/research/…`, stripping only `/api` before reaching unchanged FastAPI routes.
Static navigation does not expose these pages until WP7 Bundle admission.

## Date chart

Use the shared DateAxisControl, default Trading Days. The session domain is the
ordered open dates of historical_days plus the open evaluation current_day. Missing
values retain positions. Lines break at missing sessions and actual contract changes;
hover retains raw dates, values and both real contracts. Current valid observation is
a separate evaluation mark. Calendar Days changes spacing only. Axis switches reset
the horizontal viewport while retaining legend selection, without HTTP or recomputation.
A new submitted result resets local pair and axis selection. Histograms render supplied
bins as bars, including explicit outside counts; never use Plotly automatic binning.
