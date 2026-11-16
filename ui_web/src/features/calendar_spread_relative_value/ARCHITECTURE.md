# Calendar Spread Historical Relative Value Presentation plan

Status: planned WP6; no Web page, route, generated contract or Presentation exists.
Inherits [Web boundaries](../../../ARCHITECTURE.md) and
[Presentation architecture](../../../presentation-architecture.md).
Financial/population meaning belongs to [Research](../../../../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md);
transport belongs to [Research HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md).

## Planned surface and state

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

Consume feature-owned generated HTTP types after WP5; expose pure validation and
public Presentation for Demo. Backend owns every financial value, stage, population,
quantile, histogram and percentile. Targeted tests verify query versus local state,
cutoff/metric labels, both assessment identities, empty/small-sample explanations,
histogram outside values, error isolation and null/zero formatting. Do not announce
Web completion until the actual consumer exists.
