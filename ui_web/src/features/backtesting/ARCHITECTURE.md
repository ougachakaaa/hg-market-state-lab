# Backtesting Web feature authority

This formal independent Web feature follows [presentation architecture](../../../presentation-architecture.md),
[application](../../../application.md), [contract ownership](../../../contracts.md), and the
[WP6 HTTP contract](../../../../ui_http/products/backtesting/http-contract.md).
Financial semantics belong to the [W2 case](../../../../market_backtesting/cases/futures_roll_long/ARCHITECTURE.md).

## Input and readiness

Only Futures Roll Long is available. A request explicitly selects one product,
one inclusive window and one published strategy profile. No defaults; options derive
from OpenAPI. Dates remain YYYY-MM-DD without timezone conversion. Local validation
checks only shape/order; Asia/Shanghai and business validation stay producer-owned.
Preflight is read-only advisory, never admission. Complete-shaped input triggers a
check; edits immediately invalidate and abort/ignore stale readiness. Manual check
is available. ready=false never blocks Submit. Preflight fetches no facts and creates
no Run; Submit may fetch missing data; ready=true cannot guarantee success.

## Identity and lifecycle

Editable form state and accepted immutable Run request are separate. Only clicking
开始回测 submits; Enter, edits, effects and read retries never POST a Run.
A synchronous guard prevents duplicate pending POSTs. No automatic POST replay exists,
including lost responses that might already have created a Run. Busy creates no local Run.
Successful Submit pushes `/backtesting?run_id=<opaque>`. Reload and Back/Forward
restore Status; identity changes abort previous polling/result work and immediately
hide old results. URL stores only Run identity; no result/market data enters browser storage.
Run presentation phases: IDLE, STATUS_LOADING, PENDING, RUNNING, COMPLETED,
RESULT_LOADING, RESULT_READY, FAILED, INTERRUPTED, STATUS_ERROR, RESULT_ERROR,
UNKNOWN_RUN, UNAVAILABLE. SUBMITTING is an independent submission flag; RUN_BUSY is
submission feedback, not a Run phase. These do not extend backend states.
Only PENDING/RUNNING poll; COMPLETED separately
loads Result. Read errors stop polling and allow manual GET retry. FAILED/INTERRUPTED
have no result. Result requires a completed identity-matching Run, envelope/data
request agreement and published result profile/definition version.
Submit feedback, status/result state and form/preflight state remain independent.

All requests use protectedRequest, same-origin /api and Cookie Auth. Application owns
401, including obsolete requests. Unmount aborts work; stale success cannot restore
protected content. Runtime shapes derive from generated OpenAPI; shared V2 validator
checks Views. Errors use safe local text, never raw diagnostics, paths or credentials.

## Readout ownership

Page composes hooks/components; pure validators own generated schema, immutable request,
Run-state coherence, Result association and V2 View checks; the Production API owns
protected transport and safe error mapping; hooks own explicit submission, abort/history,
and polling; model owns display formatting. React never recomputes financial metrics,
curves, trades or slots. Summary/Trades/Rolls/Evidence project Result unchanged.
Shared ChartView renders returns/drawdown, date/decimal_ratio, producer event details
and Zoom/Pan/Reset. Requested and observed windows remain distinct. Evidence is an
expandable online summary, not the full offline package. Explain ideal Close gross
execution, no fees/slippage/margin, index price benchmark, historical metadata
assumptions, and cache completeness versus freshness. Evidence wording is origin-aware:
Static labels the actual embedded origin under the [Example contract](../../demo/EXAMPLES.md),
with real-market provenance for formal V2 and Synthetic disclosure for test-only results, and does not claim server execution, a full
offline evidence package, or current market/cache/Provider readiness. No export/copy/download
capability.

## Verification

API, hook and page tests are feature-local. Real Chromium acceptance uses Vite,
FastAPI, actual Auth/worker/temporary Store and synthetic public services. The feature-local
Shared Presentation and Static Controller also have a test-only static build/browser harness
that validates the committed producer regression Result without Production transport.
Actual results and remaining gates are recorded in [acceptance](ACCEPTANCE.md) and the
[D2-F acceptance](testing/ACCEPTANCE.md).
Full-window real-market and Windows Chrome evidence is owned by the independent
[WP8 acceptance record](../../../../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md).

## Runtime scope

Query inputs, protected HTTP reads, preflight, retries and Run lifecycle in this feature
authority describe the Production controller. `page/BacktestingPage.tsx` is that Production
composition root; `page/BacktestingPresentation.tsx` is the single formal page Presentation
shared with [Static Demo Runtime](../../demo/ARCHITECTURE.md). The transport-free public
entry is `presentation.ts`; `api/validateResult.ts` owns pure generated-contract validation;
`static/useStaticBacktesting.ts` validates a fixed request plus complete Embedded Backtest
Result once. Static composition never mounts the production controller or fabricates its
lifecycle, Run ID or phase, and it preserves this feature's Result/visualization semantics.
Shared presentation remains here, not in parallel Demo pages.

## V2 origin policy reconciliation

[Demo Example authority](../../demo/EXAMPLES.md) owns formal V2 real-market dates and
packaging; [authenticity and rights](../../demo/AUTHENTICITY.md) owns evidence and admission.
This feature owns only their presentation. Static delivery is not a Synthetic source label
or proof of authenticity. Preserve historical V1/test disclosures, use actual real-market
origin for V2, and never promote regression inputs to formal Examples. Pending origin-code
changes are tracked in the [D3 handoff](../../demo/IMPLEMENTATION.md); R0 changes no code.
