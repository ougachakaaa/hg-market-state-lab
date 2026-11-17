# Calendar Spread Historical Relative Value Presentation authority

Status: implemented. Current deployment/live-source readiness requires separate verification.
Inherits [Web boundaries](../../../ARCHITECTURE.md) and
[Presentation architecture](../../../presentation-architecture.md).
Financial/population meaning belongs to [Research](../../../../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md);
transport belongs to [Research HTTP](../../../../ui_http/products/calendar_spread_relative_value/http-contract.md).

## Issue #13 execution target

Production uses explicit execution under the [Research application](../../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md),
which owns preparation and operational limits. Static controllers consume admitted Bundles only.

## Surface and state

The independent Research page is `/research/calendar-spread-relative-value`, titled
“Calendar Spread Historical Relative Value”. Require explicit product,
history_start and evaluation_date; default metric comes from the business contract
(`annualized_spread_ratio`). Offer the other two named metrics and optional explicit
histogram edges. No automatic frontend binning. Submission is explicit execution
through the existing
`POST /research/calendar-spread-relative-value/query` (gateway `/api/research/…`).
The backend may automatically prepare missing required caches; no separate manual
Ensure step is a normal prerequisite.

The query returns all six pairs. Selecting a returned pair is local state; changing
metric, dates or edges changes query identity and requires explicit new submission.
Production hooks own loading, cancellation and stale-response isolation. There is
no Run creation, polling, restore ticket or Publication dependency. The sibling
Daily page is an independent consumer, not a source of shared semantic state.

## Presentation

Display current actual contracts/value/stage, all four historical group sizes and
quantile values, and separately labeled matching-stage/all-stages assessments.
Render Histogram only from supplied IntervalCount boundaries/counts/frequencies,
including underflow/overflow. Display formatting follows the
[presentation formatting authority](../../../PRESENTATION_FORMATTING.md): decimal ratios,
percentile and frequency display as one-decimal percentages; non-integer point/price
values display with two decimals; N, DTE and counts remain integers. Percentile text may
multiply a returned fraction by 100 for formatting; never derive it from quantile
interpolation or histogram bins. Distinguish historical quantile values from current
empirical percentile.

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
histogram outside values, error isolation and null/zero formatting. WP6 registers the actual Production consumer; WP7 records actual Demo admission and offline acceptance.

## WP6 consumer contract

Production uses feature-local explicit-submit controls and `protectedRequest`. Draft
inputs, submitted identity and local display selection are distinct. Editing a draft
never changes the identity displayed with an existing result; resubmission clears the
old result, aborts its request and isolates late completion by request token. Retry
uses the last failed submitted identity. Unmount and authentication closure cancel
and isolate requests. No polling, Run, acquisition from draft edits/mounts/local
selections, or automatic retry. Only explicit Production submission authorizes the backend execution target.

Generated OpenAPI/TypeScript in `api/` remain the only wire schema. The pure validator
checks structure, finite values, order, null/zero, identity, dates, outcome/count and
statistical association as applicable; it never computes financial/statistical results.
The public `presentation.ts` exports the transport-free Presentation and validator for
future WP7. Daily and Research own independent types, query state and projections.

Production routes are separate from gateway paths: requests use `/api/data/…` or
`/api/research/…`, stripping only `/api` before reaching unchanged FastAPI routes.
WP7 admits the real Bundle and exposes this page in the sole static runtime.
Static composition consumes this public Presentation without Production query hooks.

## Date chart

Use the shared DateAxisControl, default Trading Days. The session domain is the
ordered open dates of historical_days plus the open evaluation current_day. Missing
values retain positions. Lines break at missing sessions and actual contract changes;
hover retains raw dates, values and both real contracts. Current valid observation is
a separate evaluation mark. Calendar Days changes spacing only. Axis switches reset
the horizontal viewport while retaining legend selection, without HTTP or recomputation.
A new submitted result resets local pair and axis selection. Histograms render supplied
bins as bars, including explicit outside counts; never use Plotly automatic binning.

## Production automatic preparation feedback

Submission may take longer on a cold cache. Show one indeterminate message,
"正在准备所需数据并计算结果，请稍候。" No real progress events are published:
do not invent exact stages, percentages, completion estimates or polling. Keep
submitted identity, loading state and stale-response isolation independent of draft
edits. Retry remains a deliberate user action against the failed submitted identity.

Read the generated optional error.reason_code together with error.kind; fixed safe
presentation distinguishes these cases:

| Backend signal | User explanation and action |
| --- | --- |
| invalid_request | Check the submitted parameters. |
| credential_missing | Required data credentials are not configured; ask the operator to configure them. Never request a Token through the research form. |
| cache_incompatible | The data cache is incompatible; ask the maintainer to inspect/rebuild the owning cache. The page performs no rebuild. |
| final_export_incomplete | Automatic preparation finished but required data remains incomplete; retry later or contact the maintainer if it persists. Do not claim a specific Source cause. |
| operation_unavailable | Data preparation/read failed; retry later or contact the maintainer. |
| malformed_export / malformed_ensure_result / upstream_request_rejected | The upstream contract could not be validated; contact the maintainer. |
| transport_busy | Service capacity is full; retry manually later. |
| Missing reason_code or cache_incomplete | Keep a safe kind-based fallback explaining unavailable/incomplete inputs; never instruct manual Ensure. |

Preserve other business/transport error presentations and normal closed, empty,
excluded or small-sample results. Successful automatic preparation is an ordinary
200 Result, not a failure or reason to submit again. Never display raw exceptions,
Provider responses, Token values, storage paths or internal diagnostics.

Abort/replacement/unmount/logout stops client waiting and rejects late results; it
does not promise server-worker termination or rollback of prepared cache units.
A replacement or retry may meet transport_busy while the earlier worker finishes.
Do not auto-resubmit on cancellation, timeout, authentication restoration or mount.

Generated OpenAPI/TypeScript remains the wire owner. WP2 regenerates only affected
product artifacts and adapts error/result validation to the added POST/reason_code.
Success request.operation and existing result shape remain compatible; source_context
text describes the actual entry permission. No hardcoded new disclosure string is
required to validate historical captured results.

Static Demo mounts only its existing Bundle controller and shared pure Presentation.
It has no execution controls, Production hooks, HTTP/Auth/Source calls or Ensure.
Local pair/axis/viewport interactions retain their offline behavior; no Bundle,
Manifest, capture, financial value or admission contract changes for Issue #13.
