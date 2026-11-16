# Daily Data — Futures Calendar Spread Presentation plan

Status: planned WP6; no Web page, route, generated contract or Presentation exists.
Inherits [Web boundaries](../../../ARCHITECTURE.md) and
[Presentation architecture](../../../presentation-architecture.md).
Business meaning belongs to [Research](../../../../market_research/descriptive/cases/futures_calendar_spread/ARCHITECTURE.md);
transport belongs to [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md).

## Planned surface

The independent Daily Data page is `/data/futures-calendar-spread`, titled
“Futures Calendar Spread”. Explicit product/date controls issue the formal Daily
query. Do not invent a product, latest date or prior-session fallback. Production
mounts its authenticated HTTP controller; static Demo later mounts a Bundle controller
with the same public Presentation entry.

Show the six ordered pairs with actual near/far contract codes, same-day Close,
last trading dates, day difference, near DTE/stage and all three named metrics/units.
Preserve producer order, outcome/reason and null/zero differences. Surface closed
date, proven no-active-contract, nonpositive-price exclusion, incomplete inputs,
unavailability and loading/error independently; do not hide empty data with zeros.

Frontend only adapts requests and projects/labels/formats producer-owned values.
It never resolves Slots, subtracts prices, annualizes values, calculates DTE/stage
or derives a financial interpretation from quote rows. Formatting includes decimal
ratio→percent text only, retaining original numerical values. State is feature-local;
the Research sibling does not consume this feature's DTOs, hooks or projections.

## Integration and acceptance

Generate feature-owned HTTP types only after WP5 publishes the actual OpenAPI.
Use the existing Page/hooks/API/model/components boundary and domain-neutral shared
infrastructure. Expose a public pure validator and Presentation for future Demo
consumption; no generic feature framework or separate Demo financial page.
Verify explicit request identity, six-pair rendering, real-contract labels,
units/formatting, zero/null distinction and closed/empty/excluded/error outcomes
with targeted tests. This authority does not register an implemented page or mark
an overview card completed. Disclosure states actual Close source context and that
annualized price relationships are not returns or trading instructions.
