# Daily Data — Futures Calendar Spread Presentation authority

Status: existing surface implemented. DD-02 Chinese/index/export changes below are
authority targets until their work packages are accepted. Current deployment/live-source
readiness requires separate verification.
Inherits [Web boundaries](../../../ARCHITECTURE.md) and
[Presentation architecture](../../../presentation-architecture.md).
Business meaning belongs to [Research](../../../../market_research/descriptive/cases/futures_calendar_spread/ARCHITECTURE.md);
transport belongs to [Daily HTTP](../../../../ui_http/products/futures_calendar_spread/http-contract.md).

## Issue #13 execution target

Production uses explicit execution under the [Research application](../../../../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md),
which owns preparation and operational limits. Static controllers consume admitted Bundles only.

## Surface

The independent Daily Data page is `/data/futures-calendar-spread`, titled
“股指期货跨期价差” (DD-02 target). Explicit product/date controls issue the formal Daily
execution through `POST /data/futures-calendar-spread/query` (gateway
`/api/data/futures-calendar-spread/query`). Existing GET remains read-only for its
callers; Production submit/retry uses POST and never falls back to GET. Do not invent
a product, latest date or prior-session fallback. Production
mounts its authenticated HTTP controller; static Demo mounts a Bundle controller
with the same public Presentation entry.

Show the six ordered pairs with actual near/far contract codes, same-day Close,
last trading dates, day difference, near DTE/stage and all three named metrics/units.
Preserve producer order, outcome/reason and null/zero differences. Surface closed
date, proven no-active-contract, nonpositive-price exclusion, incomplete inputs,
unavailability and loading/error independently; do not hide empty data with zeros.

Frontend only adapts requests and projects/labels/formats producer-owned values.
It never resolves Slots, subtracts prices, annualizes values, calculates DTE/stage
or derives a financial interpretation from quote rows. Display formatting follows the
[presentation formatting authority](../../../PRESENTATION_FORMATTING.md): decimal ratios
display as one-decimal percentages, non-integer point/price values display with two
decimals, and counts/DTE remain integers. Original numerical values are retained.
State is feature-local; the Research sibling does not consume this feature's DTOs,
hooks or projections.

## Integration and acceptance

Feature-owned HTTP types are generated from the delivered WP5 OpenAPI.
Use the existing Page/hooks/API/model/components boundary and domain-neutral shared
infrastructure. Expose a public pure validator and Presentation for Demo
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

## DD-02 Chinese presentation and index target

All user-facing labels, controls, status/reason explanations and feature-owned
reading notes use Chinese. Product options retain IF/IH/IC/IM, with underlying names
as labels; these names never select prices. Label fields as 品种、查询日期、跨期组合、
近端合约、远端合约、近端收盘价、远端收盘价、近端最后交易日、远端最后交易日、
价差（点）、年化点差（点 / 365 自然日）、年化价差比例（%）、期限差（自然日）、
近端剩余到期天数、到期阶段、结果状态、原因. Slots retain M0/M1/Q1/Q2 identities.
Stage labels are 0–7 天、8–21 天、22 天及以上; machine values/boundaries remain
0_7, 8_21, 22_plus. Preserve every existing datum, six-pair order and all metrics;
column widths, wrapping, grouped headers and fixed columns may support readability.

Add an independent 标的指数参考 section with returned index identity, date, Close
and Chinese availability/reason. Format Close under the common number policy.
Do not derive identity/price, calculate metrics, infer closure from the Futures day
or use earlier prices. Translate known state/reason codes using fixed labels;
reference errors remain visible alongside intact pairs. unavailable/cache_incomplete
means 缓存尚不完整, not proven Source absence; final_export_incomplete means
自动准备后数据仍不完整. Distinguish credential/cache/operation/contract failures.

An omitted underlying_index displays 历史数据包未提供指数参考信息. Explicit null,
wrong identity/date or illegal state combinations fail contract validation. The public
validator accepts omission under the formal additive schema; Online loadQuery additionally
requires the field. Neither path mutates validated payloads or relaxes existing checks.
Translate fixed known source-context explanations for display while retaining raw strings
for export; unknown captured prose is preserved verbatim rather than silently discarded
or interpreted. Machine JSON keys, HTTP enums and result identity remain unchanged.

Four local actions and complete business column/context mappings are owned by
[Daily Export](EXPORT.md), inheriting [Daily Data Copy / Export](../../../data-copy-export.md).
Online and Demo reuse these builders through the same public Presentation. New query
clears the copy source; changing draft controls alone keeps the existing submitted
result identity. Demo discloses capture origin and exposes no execution controls.
