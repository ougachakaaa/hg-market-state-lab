# D2-E — Shared Futures Basis presentation acceptance

Repository: `ougachakaaa/hg-market-state-lab`; branch `feat/github-pages-demo`.
Inspected baseline: `ab7ebc44e7116755dabea91354ff1f38c2073a4a` (D0–D2-D present).
Phase R1 reconciliation was committed first as
`d1c7e64790807e052e1a6af7385480fd9b027874`. The working tree was clean at that commit.
This task implements D2-E only; the static harness is not a D3 Example, D4 composition or
D2-F, and the V1 Pages entry/workflow is unchanged.

## Implementation and files

- Added `presentation.ts` as the feature's transport-free public entry: shared page
  presentation, static controller, pure validators, generated contract types, coverage
  projection and the existing six-section Reader.
- Added `page/FuturesBasisPresentation.tsx`: the single formal page presentation (feature
  header, Research parameter region, immutable request facts, Result region and the shared
  `Report` composition). Its input is a discriminated composition: Production supplies only
  its execution regions (query form/preflight/Submit and real Run lifecycle); static supplies
  the validated fixed request plus Embedded Report. Preflight/Submit/Run status are not
  rendered in static mode at all.
- `page/FuturesBasisPage.tsx` is now the Production composition root. The form, Shanghai
  default, format/order hints, preflight confirmation, explicit Submit, immutable Run
  identity, URL `run_id`, polling, cancellation, statuses, failures, manual retries and
  Report reads are unchanged; only the page structure moved into the shared presentation.
- Added `api/validateResult.ts` with pure generated-contract validation:
  `matchesResponse`, `validateImmutableRequest`, `validateReaderReport` (shared by
  Production report reading) and `validateEmbeddedReport`. `api/futuresBasis.ts` retains
  only protected transport, URL construction, generated product enum re-export and HTTP
  status/kind mapping.
- Added `model/basisPresentation.ts`: produced-only coverage projection plus static
  disclosure text.
- Added `static/useStaticFuturesBasis.ts`: validates the fixed request and complete
  producer reader payload once and exposes only validated facts. It has no Run, HTTP,
  Auth, preflight, polling or `run_id` restore.
- Updated `report/Report.tsx` with an explicit `sectionNavigation` capability: the shared
  six-section reader keeps fragment links for online/offline/V1 delivery, and `local`
  scrolls between sections without a fragment or history entry for the static hash route.
- Added `testing/embeddedReportFixture.ts` (test-only input from the committed V1
  Synthetic report, 2024 window/profile unchanged), `testing/static/{index.html,main.tsx}`,
  `vite.futures-basis.config.ts`, `tsconfig.futures-basis.json`,
  `scripts/futures_basis_static_browser.mjs`, `scripts/futures_basis_static_isolation.test.ts`
  and the `test:futures-basis-static*` npm commands.
- Updated feature authority and Demo implementation handoff, root `.gitignore`, and made
  four existing browser scripts pass their npm build step on Windows (`shell` for
  `spawnSync('npm', …)`; test-only cross-platform correction, assertions unchanged).
- No producer, DataLake, HTTP contract/OpenAPI, generated artifact, financial calculation,
  profile, workflow or V1 entry changed.

## Shared presentation and Production composition

`FuturesBasisPresentation` is shared code, not a Demo page. Production and static render the
same header, parameter card, request facts, Result region and `Report.tsx`; only the
execution/parameter content differs. Production keeps its accepted-Run request separate from
the editable query form, and the Report is keyed by `run_id` so reader-local state resets
only for a different Run. The Production page has no execution affordance in the static
composition and no static disclosure in Production.

## Pure validation boundary

`validateReportData` remains the single reader-shape/Visualization validator. The new module
adds the published immutable request structure (generated OpenAPI), the
Report Profile/status/definition check, the Fixed Request / Observation association and the
optional Report Status agreement with an HTTP envelope. Production report reading calls the
same function; static composition validates the complete producer reader payload directly,
accepting no forged Run envelope. Invalid or mismatched embedded data shows an explicit
static error with no reader and no HTTP fallback.

## Static semantics

The static surface shows the fixed Example request, the producer's actual observed coverage
(candidate dates, coverage completeness, status, definition, profile and input fingerprint),
and states explicitly that the requested window is not the observed coverage. Success is
labelled **Embedded Report 已通过静态校验** and says validation does not mean a server Run
executed or that the online service is ready. There is no Submit, Preflight, Refresh,
Polling, fetch, `run_id` restore, fake Run ID or fake lifecycle state.

## Section navigation

`Report` renders six local-scroll controls in `local` mode (`navigation` landmark,
keyboard-focusable buttons, no `href`), so clicking or pressing Enter on a section never
replaces `#/research/futures-basis` and never pushes history. Online/offline/V1 delivery
retain their existing fragment links and titles; the Production browser acceptance still
asserts six `role=link` section items.

## Verification

Environment: Windows 11, Node 22.23.2, npm 11.0.0, Poetry 2.3.2, system Google Chrome
157.0.8103.39 via `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`; WSL Ubuntu 24.04 (Python 3.13.15,
Node 22.22.1) for the POSIX-only gates. Browser evidence is in printed system temporary
directories; no evidence log or build artifact is committed.

| Command | Result |
| --- | --- |
| `npm run test` (default) | **FAIL** — 3 files / 4 existing MO Option Chain/Premium tests reached the 5-second budget; 551 of 555 passed. All four were `Test timed out in 5000ms`, none in Futures Basis |
| `npm run test -- --maxWorkers=2 --testTimeout=15000` | **PASS** — 70 files, 555 tests |
| `npm run test -- src/features/futures_basis_research --maxWorkers=1 --testTimeout=15000` | **PASS** — 10 files, 57 tests |
| `npm run test -- scripts/futures_basis_static_isolation.test.ts --maxWorkers=1 --testTimeout=60000` | **PASS** — 7 negative build-isolation tests |
| `npm run test:futures-basis-static` | **PASS** — typecheck, Vite build and dependency gate |
| `npm run test:futures-basis-static-browser` | **PASS** — fixed request/coverage/disclosure, six sections, Plotly, local Metric/Slot/Trading-Calendar controls, section/route coexistence, keyboard, Back/Forward, reload, ignored `run_id`, invalid payload, zero non-static requests |
| `npm run build` | **PASS** — Production TypeScript/Vite |
| `npm run lint` | **PASS** — 0 warnings, 0 errors |
| `npm run contract:check` | **PASS** — all consumed OpenAPI/generated artifacts current; no regeneration |
| `npm run demo:build` | **PASS** — V1 entry/build unchanged |
| `npm run test:demo-browser` | **PASS** — V1 six sections, Plotly, disclosure, mobile viewport, invalid fixture, zero Auth/API |
| `npm run test:static-shell-browser` | **PASS** — D1 seven hashes, Explorer leaf, history/reload, zero non-static requests |
| `npm run test:option-chain-static-browser` | **PASS** — D2-A behavior/isolation |
| `npm run test:premium-static-browser` | **PASS** — D2-B behavior/isolation |
| `npm run test:catalog-static-browser` | **PASS** — D2-C behavior/isolation |
| `npm run test:explorer-static-browser` | **PASS** — D2-D behavior/isolation |
| `npm run test:auth-browser` (Windows) | **BLOCKED** — the Poetry Python cannot create the temporary Auth SQLite outside the workspace in this session (`sqlite3.OperationalError: unable to open database file`); registration receives no response |
| `npm run test:auth-browser` (WSL Ubuntu 24.04) | **PASS** — real registration, CLI approval, login, seven routes with collapse/history/overflow, both MO fixture results, reload, logout and Cookie/storage boundaries |
| `npm run test:futures-basis-online-browser` (Windows) | **BLOCKED** — the producer `FuturesBasisOnlineApplication` rejects storage when POSIX `os.getuid`/`O_DIRECTORY`/`O_NOFOLLOW`/dir-fd support is absent (`OnlineError: unavailable`); no D2-E code path is reached |
| `npm run test:futures-basis-online-browser` (WSL Ubuntu 24.04) | **PASS** — real Chromium → Vite → FastAPI → synthetic public services: registration/CLI approval/login, catalog, Generate, preflight, PENDING/RUNNING polls, partial result, Failed/Interrupted, status/report retry fixtures, Plotly report at two viewports, refresh, Back/Forward, lost-POST isolation, repeated logout and HttpOnly Cookie boundary |
| `npm run test:futures-basis-report-browser` (Windows) | **BLOCKED** — the Python fixture generator cannot create its external temporary report directory in this Windows session (`PermissionError [WinError 5]` on `%TEMP%` writes from the Poetry Python); packaging is not reached |
| `npm run test:futures-basis-report-browser` (WSL Ubuntu 24.04) | **PASS** — full offline report acceptance (font, six sections exact payload/fingerprint, three metrics, hover/legend/Zoom/Pan/Reset, evidence and two viewports) |
| `git diff --check` | **PASS** |

The default Vitest run was executed first; its failures are the known resource-sensitive
five-second interaction timeout in existing MO tests, not Futures Basis assertions.
Repository test configuration and global timeout were not changed. The complete suite
passes under the explicitly adjusted two-worker/15-second invocation.

The POSIX-only suites ran in a native WSL Ubuntu 24.04 copy of the working tree (Python
3.13.15, Node 22.22.1, Playwright browsers with locally extracted NSS/ALSA libraries). Two
earlier WSL executions lost the authenticated session at unrelated assertions (one in the
Auth route walk, one after report Back) and showed the login form; both suites then passed
clean reruns without any Auth, session, transport or routing code change, and the same
failure mode never touched the changed Futures Basis presentation. This is recorded as a
WSL session/runner flake, not a D2-E regression; the Linux CI host remains the stable gate.

## Dependency and browser evidence

The built static graph contains the shared page presentation, six-section Reader, reader
validators, pure result validators, static controller, shared Visualization, generated
Futures Basis OpenAPI schema, `AppUiProvider`, the D1 hash adapter and the explicit test-only
V1 fixture. It contains no `shared/http`, `app/auth`, `api/futuresBasis.ts`,
`hooks/useFuturesBasis.ts`, `hooks/usePreflight.ts`, `page/FuturesBasisPage.tsx`, V1 Demo
entry or sibling feature module. Negative builds inject Auth, the Run hook, the Preflight
hook, the Production HTTP client, the Production Page, an indirect dynamic HTTP import and an
unresolved dynamic import; each actual build fails for the expected isolation reason.

The real built artifact made only static document/script/stylesheet requests, with empty
cookies and zero Auth/API/Preflight/Run requests or browser errors across initial load,
navigation, Back/Forward, reload and all local controls.

## Remaining risks and D2-F handoff

- Official D3 Examples, D4 full composition, D5 compatibility gates and D7 release switching
  remain outstanding; the D2-E harness is test-only and keeps the V1 2024 window.
- The two POSIX-only full-stack gates passed in WSL, not on the Windows host: the producer
  Run store rejects non-POSIX storage and the Poetry Python cannot write its temporary Auth
  SQLite outside the workspace here. These Windows BLOCKED results are environment evidence,
  not product regressions, and the Linux CI host is the stable gate for both suites.
- A `partial` embedded report remains a completed scientific result with visible failed
  methods; the static fixture is complete and partial behaviour stays covered by the shared
  reader tests.
- D2-F is Backtesting: extract its request/readout into a shared presentation with a
  capability-aware execution area, preserve W2 strategy/Core results, request agreement and
  both V2 Views, and never fabricate a completed Run. Official D3 Examples and full static
  composition remain separate work.
