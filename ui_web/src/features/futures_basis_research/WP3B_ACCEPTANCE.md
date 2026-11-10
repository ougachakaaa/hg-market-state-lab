# S2-WP3B acceptance — 2026-11-10

Execution evidence for [feature authority](ARCHITECTURE.md), not a new UI or
financial contract. Deterministic Linux/Chromium acceptance only.

## Baseline and WP3-A closure

- Branch: `feat/web-ui-ux-polish`; initial working tree clean.
- Required and observed HEAD before modification:
  `0cbd555efb228a0fba791536d88179310ab99a74`.
- Before WP3-B implementation, repaired three stale accessible selectors in
  `scripts/futures_basis_online_browser.mjs`:
  `Local and offline` → `本地研究与离线工作流`,
  `View details` → `查看详情`, and the additionally discovered
  `Open Futures Basis Research` → `打开 Futures Basis Research`.
- Preflight `npm run test:research-browser` and
  `npm run test:futures-basis-online-browser`: PASS. Real Chromium navigation
  from Research Workspace to Futures Basis, actual Auth/CLI/Cookie, actual HTTP
  POST/poll/report, Plotly, refresh and Back/Forward all passed. Assertions and
  interactions were retained. WP3-A regression is closed.

## Implementation and file ownership

Paths below are relative to `ui_web/`.

| Files | Change |
| --- | --- |
| `src/features/futures_basis_research/page/FuturesBasisPage.tsx` | Chinese query controls, explicit button action, compact query/status Cards, immutable request descriptions, actual state Badge/Tag, contextual read recovery and explicit new-Run retry |
| `src/features/futures_basis_research/hooks/useFuturesBasis.ts` | Retain whether a failed GET was status or report so UNAVAILABLE recovery cannot infer the wrong operation from an old terminal Run |
| `src/features/futures_basis_research/report/Report.tsx` | Single shared reader; mode-aware heading hierarchy, wrapping six-section navigation, readable table scroll containers, chart containment, formula/runtime disclosure and visible censored lower-bound caveat |
| `src/offline/futures_basis/report.css` | Reset standalone browser body margin; retain embedded font and Plotly fallback |
| `src/offline/futures_basis/assets/report-cjk.woff`, `assets/README.md` | Retain previous glyph coverage and derived licensed family; include new fixed reader copy, using the same upstream OTF and documented SHA-256 |
| `src/features/futures_basis_research/page/FuturesBasisPage.test.tsx` | Empty form, Enter, read recovery, unavailable old-completed-Run context, immutable new-Run action and retained-result checks |
| `src/features/futures_basis_research/hooks/useFuturesBasis.test.ts` | Regression for failed status read with a previous completed Run |
| `src/features/futures_basis_research/report/Report.test.tsx` | Mode-aware document titles and payload non-mutation |
| `scripts/futures_basis_online_browser.mjs` | WP3-A selector repair, WP3-B control labels and acceptance-helper composition |
| `scripts/futures_basis_polish_acceptance.mjs` | Real POST with held response; explicit synthetic GET lifecycle/fault fixtures; two viewports and manual read recovery, local control and navigation request assertions |
| `scripts/futures_basis_report_browser.mjs` | Preserve original real chart interactions; add standalone heading, both viewport sizes, navigation, expanded evidence and overflow checks |
| This file | Acceptance record |

Online uses one feature title and a subordinate report heading. Offline retains
one standalone document title, its own theme/font shell, file loading and adjacent
evidence/verify/replay instructions. Both modes use the same six-section reader.
No application/auth/router/HTTP dependency enters that reader or offline graph.

## Semantics and reconciliation

- POST remains explicit and non-idempotent. No input defaults, implicit submission,
  automatic retry, additional inputs or frontend eligibility rules were added.
- A native submit button was replaced by an explicit button calling form.submit;
  input Enter only commits input. Server validation remains authoritative.
- Server Run ID and immutable request, URL restoration, refresh/Back/Forward,
  cancellation, stale-response isolation and terminal-report preservation remain.
- Poll scheduling remains 1.5 seconds with no overlap, ending at terminal states.
  Failed/interrupted execution retry creates a new Run from its immutable request.
- Status/report GET recovery follows the failed read context, including UNAVAILABLE
  after restoring a formerly completed Run. This implements the existing separate
  retry invariant; no new lifecycle state or execution behavior is introduced.
- Completed execution and report availability are shown separately. Partial is
  completed science, with failed-method evidence retained. No numeric progress.
- Exactly `section-0` through `section-5` remain. Navigation scrolls to those
  anchors without changing history and accidentally restoring/reloading the Run.
- All numerical projections, Views, colors, Slot identities, bins/quantiles,
  populations, events, nulls, complete/censored runs and limitations are unchanged.
  No backend, generated contract, numerical calculation or statistical method changed.
- Reconciled against feature, offline, UI-system, presentation, HTTP, online
  application and shared Visualization authority. No missing invariant or authority
  drift; no authority rewrite or centralized UI specification was needed.

## Verification

Commands use `ui_web/`, except the explicitly root-scoped Python checks.

| Command | Final result |
| --- | --- |
| `npm run contract:check` | PASS; all consumed OpenAPI and generated TypeScript current |
| `npm test` | PASS: 40 files, 364 tests, serial uncontended final run |
| `npm run build` | PASS: TypeScript and Vite production bundle |
| `npm run lint` | PASS: no warnings/errors |
| `npm run test:research-browser` | PASS; both sizes, workspace/explorer and navigation/history |
| `npm run test:futures-basis-online-browser` | PASS: real HTTP flow plus deterministic two-viewport state/report matrix; zero page errors |
| `npm run test:futures-basis-report-browser` | PASS: packaged file:// report, both viewports, original chart interactions, no external requests or errors |
| `npm run test:auth-browser` | PASS; actual registration, approval, Cookie, refresh and logout |
| Root: `poetry run pytest ui_http/tests/test_auth*.py ui_http/tests/test_architecture.py market_research/tests/test_futures_basis_report.py ui_web/scripts/test_export_contracts.py` | PASS: 228 tests; includes TLS, offline integrity/replay/corruption and contract checks |
| Root: `poetry run python market_research/tests/futures_basis_report_browser_fixtures.py --output /tmp/wp3b-offline-edge` | PASS; actual producer empty and failed-statistics fixtures, offline Chromium, no external requests/errors |
| `git diff --check` and complete diff review | PASS |

Earlier verification findings were resolved without relaxing assertions: loading
icons change button accessible names; ordinary hash navigation re-entered URL
restoration; an unrelated MO Option Chain test hit its existing 5s timeout while
heavy browser checks ran concurrently. The final suite is run serially. Logs retain
the earlier timeout as `/tmp/wp3b-vitest-concurrent-timeout.log`.
Existing warnings: large Plotly production chunk, Ant Design List deprecation in
the unchanged Research catalog, and FastAPI TestClient deprecation. No dependency
or timeout changes were made.

## Browser evidence

Chromium 156.0.8078.4, real headless browser. Target sizes are 1440×900 and 1024×768.
Screenshots were inspected for heading hierarchy, CJK readability and containment.
No remaining visual defect was observed at the two target sizes; standalone body
margin and oversized Card heading clipping found during review were corrected.

- Online: `/tmp/wp8b-online-browser/wp3b/{1440x900,1024x768}/`.
  Each contains `initial-query.png`, `submitting.png`, `pending.png`, `running.png`,
  `completed.png`, `partial.png`, `failed.png`, `interrupted.png`, `status-error.png`,
  `report-error.png`, `full-report.png`, `history-chart.png`,
  `distribution-table.png`, `comparison-details.png`, `expanded-evidence.png`.
- Online assertions: `/tmp/wp8b-online-browser/wp3b/acceptance.json`;
  HTTP/state evidence: `/tmp/wp8b-online-browser/http-evidence.json`.
- Offline final package: `/tmp/r01a-offline-browser-FE54zT/report/report.html`;
  screenshots/results: `/tmp/r01a-offline-browser-FE54zT/report-browser/`.
  Includes per-viewport `overview`, `chart`, `evidence`, `full` screenshots,
  actual hover screenshot and `acceptance.json`.
- Offline edge reports: `/tmp/wp3b-offline-edge/{empty,failure}/report.html`;
  screenshots/results in the corresponding `{empty,failure}-browser/` directories.
- Research regression: `/tmp/hg-market-state-lab-web-workspace/wp3a/{1440x900,1024x768}/`.
- Logs: `/tmp/wp3b-{contract,vitest,build,lint,online,offline,offline-edge,python,auth-browser,research-browser}.log`.

The online base flow uses actual FastAPI/Auth/worker/public fixture services. The
additional visual matrix uses real accepted POSTs and the real synthetic producer
report, with explicit GET fixtures for deterministic partial/failure/read-error
states. They are presentation fixtures, not evidence of those faults in a live
provider. Offline loads packaged file:// HTML with Chromium offline; embedded JSON
must equal the producer payload exactly, and external requests/errors must be empty.
No live market/provider/cache readiness or production deployment is claimed.

## Closure

PASS within deterministic synthetic acceptance. WP3-A regression is closed;
WP3-B can close, and WP4 Final Visual Reconciliation may begin as a separate task.
One focused WP3-B commit includes the necessary WP3-A test repair; the delivery
message reports its SHA. No merge or push; no WP4 work was started.
