# Daily Data — Futures Calendar Spread Presentation authority

Status: WP6 implemented and READY TO CLOSE; targeted evidence and unverified
real-data/deployment limits are recorded in [Acceptance](ACCEPTANCE.md).
Inherits [Web boundaries](../../../ARCHITECTURE.md) and
[Presentation architecture](../../../presentation-architecture.md).
Business meaning belongs to [Research](../../../../market_research/descriptive/cases/futures_calendar_spread/ARCHITECTURE.md);
transport belongs to [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md).

## Surface

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

Feature-owned HTTP types are generated from the delivered WP5 OpenAPI.
Use the existing Page/hooks/API/model/components boundary and domain-neutral shared
infrastructure. Expose a public pure validator and Presentation for future Demo
consumption; no generic feature framework or separate Demo financial page.
Verify explicit request identity, six-pair rendering, real-contract labels,
units/formatting, zero/null distinction and closed/empty/excluded/error outcomes
with targeted tests. WP6 registers the implemented Production page and completed Web overview card;
this does not imply input-cache readiness. Disclosure states actual Close source context and that
annualized price relationships are not returns or trading instructions.

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
