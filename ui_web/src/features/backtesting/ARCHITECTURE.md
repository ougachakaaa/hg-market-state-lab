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

Page composes hooks/components; API owns validation/association; hooks own admission,
abort/history/polling; model owns display formatting. React never recomputes financial
metrics, curves, trades or slots. Summary/Trades/Rolls/Evidence project Result unchanged.
Shared ChartView renders returns/drawdown, date/decimal_ratio, producer event details
and Zoom/Pan/Reset. Requested and observed windows remain distinct. Evidence is an
expandable online summary, not the full offline package. Explain ideal Close gross
execution, no fees/slippage/margin, index price benchmark, historical metadata
assumptions, and cache completeness versus freshness. No export/copy/download capability.

Readiness uses friendly dependency/status labels and Dataset-owned target-unit coverage counts. Unknown targets are not missing datasets; no separate SSE readiness is fabricated. Refresh only checks cache. Failure presentation is a case-owned pure mapping of status and safe OnlineFailure: title, explanation and action, with stage/category/dependency/reason and Run ID in collapsed details. Only ensure/upstream_operation/credential_missing identifies absent Tushare configuration; other and historical failures use conservative guidance. No automatic submission/acquisition or change to Result/date-axis state is introduced.

## Date-axis presentation

Returns and drawdown share one date-axis control in the Result region, following the
repository [date-axis presentation authority](../../../DATE_AXIS_PRESENTATION.md):
`Trading Days` (default) maps both charts onto the ordered
`BacktestResult.daily[].trade_date` domain with one position per observed CFFEX
session; `Calendar Days` keeps real date spacing. The daily order is the authoritative
domain; the feature never infers sessions from contract codes, provider calendars,
weekday heuristics or date arithmetic, and its Charts/Model never recalculate values.

The mode is local Result presentation state: it changes neither the Run identity nor
the Run Request, performs no GET/POST/preflight, writes no URL or browser storage, and
leaves dates, values, trades, rolls, evidence and fingerprint unchanged. Both charts
receive the same memoized options object and date domain, so a switch resets the
horizontal viewport to the new coordinate system, preserves legend selection and keeps
event annotations aligned. A different Run remounts Result and restores the default.

## Verification

API, hook and page tests are feature-local. Real Chromium acceptance uses Vite,
FastAPI, actual Auth/worker/temporary Store and synthetic public services. Actual
results and remaining gates are recorded in [acceptance](ACCEPTANCE.md).
Full-window real-market and Windows Chrome evidence is owned by the independent
[WP8 acceptance record](../../../../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md).
