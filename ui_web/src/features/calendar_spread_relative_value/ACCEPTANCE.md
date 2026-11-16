# WP6 Historical Relative Value Web acceptance — 2026-11-16

**READY TO CLOSE**. Shared tooling, baseline and deployment limits are recorded in
[Daily acceptance](../futures_calendar_spread/ACCEPTANCE.md); business authority remains
[Relative Value](../../../../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md).

## Delivered and verified

- Authenticated `/research/calendar-spread-relative-value`; explicit Product/history
  start/evaluation date, default annualized ratio and two other metric choices,
  optional explicit JSON histogram edges. No automatic query or auto binning.
- Independent generated OpenAPI/TypeScript, API/controller, pure validator and public
  transport-free Presentation. Draft edits retain the old submitted identity with an
  explicit notice; replacement clears the old result. Pair selection consumes all
  six returned pairs locally. No sibling Daily DTO/state dependency or Run lifecycle.
- Current real contracts/value, separate Matching-stage/All-stages midrank percentiles,
  four distributions/Quantiles, actual cutoff/sample dates/counts, Histogram/outside
  counts and source/financial disclaimers. N=0/1/29/30 and unavailable current cases
  use actual DTO projections. Empty Matching-stage does not substitute All-stages;
  valid historical distributions survive unavailable current observations.
- Feature-scoped Vitest `api/validateResult.test.ts`, `api/query.test.ts`,
  `hooks/useQuery.test.ts`, `page/RelativeValuePage.test.tsx`, `model/charts.test.ts`
  PASS, as do changed Research Overview and app composition tests. Combined WP6
  verification covers the directly affected Vitest cases in 14 files, in scoped groups.
  Pure chart tests verify exact dates/values/contracts, preserved input, missing
  session breaks and contract-transition segmentation. Invalid DTOs are rejected.
- Contract Check, TypeScript/Production build and Lint PASS; seven exporter pytest
  cases PASS. No backend financial/statistical code was changed or copied.

## Date-axis Chromium conformance

`node tests/browser/calendar_spread_browser.mjs` PASS using real Vite forwarding,
composed FastAPI/Auth and synthetic public Research inputs. The session domain comes
only from open historical/current Calendar summaries. Verified default Trading Days
ordinal coordinates, Calendar Days raw dates, identical y data, current evaluation
mark, raw-value/contract/date Hover, Zoom/Pan/Reset in both modes and legend retention
across switching. Pair, axis and viewport changes make no HTTP requests. Draft edits,
explicit submission, SPA deep reload, Back/Forward and logout also passed. The runner
caught and verified the date-field implicit Enter-submit fix.

Local ignored evidence is `ui_web/.build/calendar-spread-acceptance/diagnostics.json`
and `research.png`. This is targeted Chromium acceptance, not a browser matrix,
real-market validation, Production Gateway check or Demo artifact. User configuration
and real market caches were not modified; only runner-owned temporary auth
storage was cleaned up. No WP7 Bundle/Manifest/Registry/capture changes or Demo build.
The reusable Presentation/validator prerequisite is ready; **WP7 Demo Bundle remains
BLOCKED / NOT IMPLEMENTED** pending its own delivery and acceptance.
