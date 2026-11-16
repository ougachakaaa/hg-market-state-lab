# WP6 Daily Web consumer acceptance — 2026-11-16

**READY TO CLOSE**, from baseline `e18c52c3dc4a494c0163665bd3c371561f2b7b1a`.
The delivery commit is identified by Git history, not self-embedded here.

## Delivered and verified

- Authenticated `/data/futures-calendar-spread`, explicit Product/Trade Date and query
  button, six ordered pairs, real contracts/Close/last trading dates, three named
  metrics and units, delta/DTE/stage/outcome/reason. Zero, null, closed, proven empty
  and nonpositive exclusion remain distinct. Folded source and financial limitations.
- Generated `api/calendarSpread.openapi.json` and `api/calendarSpread.generated.ts`
  come from the actual composed WP5 operation. The pure validator rejects malformed
  or misassociated payloads; `presentation.ts` exposes validator/types/Presentation
  without production HTTP/auth dependencies.
- API/controller checks cover required status kinds, network/invalid response, no
  automatic retry, abort/stale response, unmount and closed authentication lifecycle.
  Original failed request identity is retained for explicit retry.
- Scoped Vitest: feature `api/validateResult.test.ts`, `api/query.test.ts`,
  `hooks/useQuery.test.ts`, `page/DailyPage.test.tsx`; shared changed app tests
  `App.test.tsx`, `ApplicationShell.test.tsx`, `Overview.test.tsx`, `routes.test.tsx`.
  PASS in scoped groups; after related fixes only failed cases were rerun.
- Exporter pytest file: seven cases PASS. Nine-pair `npm run contract:check` PASS;
  original seven artifacts unchanged. `npm run build` PASS; `npm run lint` PASS
  with only pre-existing warnings in unrelated `scripts/demo_artifact.test.mjs` and
  `demo/build/build.mjs`. Build reports a large JS chunk; no new splitting work.
- `node tests/browser/calendar_spread_browser.mjs` PASS with installed Chromium,
  actual composed FastAPI/Auth and synthetic public Research input services. Direct
  page/reload returns SPA; `/api/data` reaches the actual Daily route and returns
  its validated six-pair JSON. Login preserves deep link; history/logout verified.
  Date input Enter commits the date without implicitly querying. Only explicit
  query-button activation starts the request (including keyboard button activation).

## Evidence and limits

Test-only DTO fixtures are generated explicitly from actual public Research results
and HTTP projection by `ui_web/tests/fixtures/calendar_spread_fixtures.py`; they are
synthetic tests, never Demo or live-market evidence. Local ignored browser diagnostics
and screenshot live under `ui_web/.build/calendar-spread-acceptance/`.

Actual Production Gateway is **NOT VERIFIED**: no Nginx site configuration is tracked.
Vite forwarding and SPA fallback passed locally; deployment requirements are in
[Workspace](../../../workspace.md) and [deployment usage](../../../deploy/README.md).
Real market availability and other browsers/platforms are **NOT VERIFIED**.
No real market data/cache or historical Run/Publication store was modified. User
configuration was not changed and credential values were never recorded in evidence.
Browser cleanup removed only runner-created temporary auth SQLite/directories. No Demo build, new Bundle, merge or publication was performed.
WP7 can consume the public Presentation/validator; Demo Bundle delivery remains
**BLOCKED / NOT IMPLEMENTED** pending its own capture/admission/artifact work.
