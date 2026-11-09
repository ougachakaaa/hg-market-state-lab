# WP8-B Web acceptance — 2026-11-09

**PASS within deterministic synthetic Linux acceptance. WP9 is NOT RUN.**
This records execution evidence for the [frontend authority](ARCHITECTURE.md),
not a second financial, HTTP or lifecycle contract.

## Baseline and delivery

- Repository: `ougachakaaa/hg-market-state-lab`.
- Branch: `feat/web-ui-workspace-redesign`.
- Required and observed baseline: `f1bc3a21c4b72a60ddf955a2cfdf70e4379a73cd`;
  clean initial worktree.
- Delivery is one independent WP8-B commit containing this document. Its SHA/final
  HEAD is reported with delivery and can be read with `git rev-parse HEAD`.
- No new branch, merge, push, real market acquisition, production cache changes,
  Daily Data WP5 or Backtesting implementation.

## Ownership and reconciliation

| Boundary | Implemented responsibility |
| --- | --- |
| Feature `api/` | Own OpenAPI projection/generated types, strict response validation, three same-origin protected HTTP operations; generated envelope plus existing versioned reader payload |
| Feature `hooks/` | Run identity, status polling, cancellation, stale-response isolation, manual retry and URL restoration |
| Feature `page/` | Ant Design query form, immutable Run identity, safe error/empty/retry presentation and reader composition |
| Feature `report/` | Single pure six-section reader, existing reader types and structural/View validation; no HTTP/Auth/runtime import |
| Offline entry | Standalone theme, embedded Chinese font, file entry and single-file packaging; imports only pure reader subpath |
| Application | Navigation, Auth gate and protected-request lifetime; compatible optional POST request parameters |

New page: `/research/futures-basis?run_id=<opaque>`; Catalog selection and the
Research sidebar lead to it. Existing Research, Explorer, MO and Backtesting
routes remain available. Readiness descriptions distinguish implemented execution,
independent offline generation and unverified live Provider/Cache readiness.
Research entry/readiness documents are reconciled without changing numerical APIs.

A validated 202 pushes the Run ID into browser history. Mount, refresh and
same-path Back/Forward query changes start with a real status read. Settled
PENDING/RUNNING queries schedule one subsequent request after 1.5 seconds; terminal
states stop polling. Completion reads the report once per restored lifecycle,
with explicit report retry after a read error. Partial remains completed science.

Submission feedback is separate from the current terminal report. Rejection or
lost response preserves that report; POST is never automatically retried. Failed
or interrupted Runs can be manually submitted as a new Run using their immutable
request. Status/report errors retry only the corresponding read operation.
Enter in a form input commits its selection without implicitly submitting a Run.

URL replacement/unmount cancels timers/requests and invalidates old generations;
new acceptance invalidates the previous generation before React commits the URL.
Unknown/foreign Runs have one indistinguishable message and remove the inaccessible
query identity. A current-lifetime 401 closes the application gate, even if its
feature request was cancelled; a closed old auth lifetime cannot affect a new login.
No identity/report storage, JWT parsing or client financial computation is added.

The six-section reader preserves producer Views, M0/M1/Q1/Q2, nulls, events,
quantiles/means/counts, population/coverage/provenance, failed methods and
complete/censored persistence. Requested dates and actual candidate coverage remain
separate. Online disclosure shows the producer request and describes the actual
HTTP evidence boundary. Adjacent-file/verify/replay instructions remain offline.
Packaging now rejects app/auth/HTTP/polling imports in the offline bundle graph.

## Actual verification

Commands run from `ui_web/` unless stated otherwise.

| Check | Result |
| --- | --- |
| `npm run contract:generate`, then `npm run contract:check` | PASS; all six consumers; existing five generated artifacts have no content drift |
| `npm run test` | PASS: 32 files, 279 tests |
| `npm run build` | PASS: TypeScript + Vite production build |
| `npm run lint` | PASS, no warnings |
| `npm run test:futures-basis-online-browser` | PASS: real Chromium/Vite/FastAPI, temporary Auth/Run stores, actual registration/operator approval/Cookie login, synthetic public services and real Plotly |
| `npm run test:futures-basis-report-browser` | PASS with no arguments: automatically generates a synthetic report, packages one HTML and verifies offline file reading |
| Existing empty/failure offline Chromium fixtures | PASS: all-null findings, original failed-method evidence and escaped script-ending text |
| `npm run test:auth-browser` | PASS: actual authentication and both MO products |
| `npm run test:research-browser` | PASS: Catalog/Explorer, both MO products, deep URL, reload/history and logout |
| Root: `poetry run pytest ui_http/tests ui_web/scripts/test_export_contracts.py data_snapshot/tests/test_authority_topology.py` | PASS: 493 tests |
| Root: `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py` (after readiness reconciliation) | PASS: 21 tests |
| Root: `poetry run pytest market_research/tests` | PASS: 1,255 passed, 1 existing platform-specific skip |
| Root: `poetry run ruff check market_research ui_http ui_web/scripts` | PASS |
| Root: `poetry run mypy ui_http` | PASS: 54 source files |
| Root: `poetry run mypy market_research/tests` | PASS: 47 source files |
| Full diff, changed Markdown relative targets and `git diff --check` | Reviewed / PASS |

Browser: Chromium `156.0.8078.4`. This host initially lacked `libnspr4.so` on its
loader path. Browser checks passed using the existing isolated libraries via
`LD_LIBRARY_PATH=/tmp/msl-playwright-libs/extracted/usr/lib/x86_64-linux-gnu`;
no system installation or production configuration was changed. The existing Auth
and Research browser runners now also select temporary Run stores. Their earlier
startup initialized an empty ignored default Run directory; it contains no Run
files, and no production market cache was accessed or changed.

The online browser observes RUNNING and COMPLETED, checks a real 409 busy rejection,
a real 400 invalid request preserving the old report, no implicit POST while
editing dates, two accepted Run identities, refresh, same-path Back/Forward,
logout denial of the old report and empty browser storage. It records zero
page errors. Unit tests additionally cover independent retry contexts, invalid
DTO/error combinations, profile/request/View association, late responses, failed
immutable-request submission and cancellation. Existing HTTP tests cover owner
isolation, partial science, interrupted Runs and transport failure mappings.

Early Catalog checks failed because their expectations still required the old
"authority only" readiness; those assertions were reconciled. Two existing MO
tests timed out at 5 seconds while heavy builds/browser checks ran concurrently;
a subsequent uncontended full run passed without changing their timeouts.

## External evidence and reproduction

- Online overview: `/tmp/wp8b-online-browser/online-overview.png`.
- Online full report: `/tmp/wp8b-online-browser/online-report.png`.
- Online HTTP/state evidence: `/tmp/wp8b-online-browser/http-evidence.json`.
- Final offline report: `/tmp/r01a-offline-browser-JPjStP/report/report.html`.
- Final offline screenshots: `/tmp/r01a-offline-browser-JPjStP/report-browser/report.png`
  and `hover.png`; `acceptance.json` records zero external requests/page errors.
- Empty/failure screenshots and acceptance JSON:
  `/tmp/wp8b-offline-edge/{empty,failure}-browser/`.
- Test logs: `/tmp/wp8b-{vitest,build,contract,lint,python,research-tests,online,offline-final,offline-edge,auth-browser,research-browser}.log`.

Reproduce the online and normal offline checks with their npm commands above;
Playwright Chromium and its system libraries are prerequisites. The online runner
requires free 5173/8011 ports, refuses existing listeners and cleans its temporary
stores/processes. Screenshots and HTTP evidence remain external.
For offline edge reports, from the repository root run
`poetry run python market_research/tests/futures_basis_report_browser_fixtures.py --output <new-external-directory>`.
All three paths use synthetic facts, not live markets.

## Remaining boundaries and WP9 prerequisites

- WP9 real market acquisition, actual Provider/Cache readiness, WSL/Windows Chrome,
  restart-in-browser and production deployment acceptance: **NOT RUN**.
- Online storage still requires the existing POSIX capabilities and one backend
  process. Native Windows unavailability is surfaced through the published contract.
- Offline font embedding is verified without system CJK fonts. Online presentation
  inherits application/host fonts; this minimal headless host lacks a system CJK
  font, so online screenshots show missing Chinese glyphs. No remote font is added.
- Vite retains its large Plotly-containing bundle warning; existing Ant Design List
  and FastAPI TestClient deprecation warnings remain. No dependency upgrade is made.
- WP9 must establish bounded real IM/provider/cache readiness and the target
  browser/platform/deployment conditions without treating this synthetic PASS as
  real-market acceptance. Work stops at WP8-B.

## Added and modified files

- M `DEVELOPMENT.md`
- M `market_research/AGENTS.md`
- M `market_research/ARCHITECTURE.md`
- M `market_research/descriptive/cases/futures_basis/ARCHITECTURE.md`
- M `market_research/descriptive/cases/futures_basis/ROADMAP.md`
- M `ui_web/FEATURES.md`
- M `ui_web/application.md`
- M `ui_web/contracts.md`
- M `ui_web/package.json`
- M `ui_web/scripts/auth_browser_smoke.mjs`
- M `ui_web/scripts/contract_types.mjs`
- M `ui_web/scripts/export_contracts.py`
- A `ui_web/scripts/futures_basis_browser_app.py`
- A `ui_web/scripts/futures_basis_offline_fixture.py`
- A `ui_web/scripts/futures_basis_online_browser.mjs`
- M `ui_web/scripts/futures_basis_report_browser.mjs`
- M `ui_web/scripts/package_futures_basis_report.mjs`
- M `ui_web/scripts/research_browser_smoke.mjs`
- M `ui_web/scripts/test_export_contracts.py`
- M `ui_web/src/app/App.test.tsx`
- M `ui_web/src/app/App.tsx`
- M `ui_web/src/app/routes.ts`
- A `ui_web/src/features/futures_basis_research/ACCEPTANCE.md`
- M `ui_web/src/features/futures_basis_research/ARCHITECTURE.md`
- A `ui_web/src/features/futures_basis_research/api/futuresBasis.generated.ts`
- A `ui_web/src/features/futures_basis_research/api/futuresBasis.openapi.json`
- A `ui_web/src/features/futures_basis_research/api/futuresBasis.test.ts`
- A `ui_web/src/features/futures_basis_research/api/futuresBasis.ts`
- A `ui_web/src/features/futures_basis_research/hooks/useFuturesBasis.test.ts`
- A `ui_web/src/features/futures_basis_research/hooks/useFuturesBasis.ts`
- A `ui_web/src/features/futures_basis_research/page/FuturesBasisPage.tsx`
- A `ui_web/src/features/futures_basis_research/report/Report.test.tsx`
- A `ui_web/src/features/futures_basis_research/report/Report.tsx`
- A `ui_web/src/features/futures_basis_research/report/reader.fixture.ts`
- A `ui_web/src/features/futures_basis_research/report/types.ts`
- A `ui_web/src/features/futures_basis_research/report/validate.ts`
- M `ui_web/src/features/research_catalog/ARCHITECTURE.md`
- M `ui_web/src/features/research_catalog/model/localCases.ts`
- M `ui_web/src/features/research_catalog/page/ResearchWorkspacePage.test.tsx`
- M `ui_web/src/features/research_catalog/page/ResearchWorkspacePage.tsx`
- M `ui_web/src/offline/futures_basis/ARCHITECTURE.md`
- M `ui_web/src/offline/futures_basis/Report.tsx`
- M `ui_web/src/offline/futures_basis/types.ts`
- M `ui_web/src/shared/http/protectedRequest.test.ts`
- M `ui_web/src/shared/http/protectedRequest.ts`
- M `ui_web/workspace.md`
