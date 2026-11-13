# D2-F — Shared Backtesting presentation acceptance

Repository: `ougachakaaa/hg-market-state-lab`; branch `feat/github-pages-demo`.
Inspected baseline: `ad53fdd1e107776a505aa6f2ec6768f87db6306a` (D0–D2-E and
D2-D R1 present); the initial working tree was clean. This task implements D2-F only.
The static harness is not a D3 Example, D4 composition, D5 gate or public V1 entry.

## Implementation and files

- Added `presentation.ts` as the transport-free feature entry: shared page presentation,
  static controller, pure validators, generated contract types and the existing Result
  Reader.
- Added `page/BacktestingPresentation.tsx`: the single formal page presentation (header,
  Production execution/readiness region, fixed immutable request facts, requested-vs-observed
  window and Result region). Production supplies only its query form/Preflight/Run nodes;
  static supplies the validated fixed request and complete Embedded Result. The static
  composition never renders Submit, Preflight, polling, retry, Run identity or phase.
- `page/BacktestingPage.tsx` is now the Production composition root. The four empty Query
  fields, generated options, explicit button-only Submit, Enter suppression, advisory
  Preflight, duplicate-POST guard, lost-response protection, Accept/`run_id` URL write,
  polling, terminal/error states, manual reads, identity checks and Auth remain in the
  existing hooks/API. The editable form is not the accepted Run identity.
- Added `api/validateResult.ts` with pure generated-contract validation:
  `matchesResponse`, `validateImmutableRequest`, `validateRunState`, `validateResult`,
  `validateResultResponse`, `sameRequest` and `validateEmbeddedBacktestResult`.
  `api/backtesting.ts` retains only protected transport, URL construction, HTTP status/kind
  mapping and the 401 boundary. Production Result reading calls the same validators as
  static composition.
- Added `static/useStaticBacktesting.ts`: validates the fixed request plus complete Producer
  Result once and exposes only `validated` / `invalid` state. It has no Run, HTTP, Auth,
  preflight, polling, retry or `run_id` restore.
- Updated `components/Result.tsx`: unchanged Summary, both V2 Charts, Trades, Rolls and
  Evidence; Evidence wording is now origin-aware. Production keeps the existing online
  summary. Static labels an Embedded Synthetic Example, states that no server backtest ran
  or full offline evidence package exists, does not claim market/cache/Provider readiness,
  preserves the original Evidence values and retains Ideal Close gross execution with no
  fee/slippage/margin. No export/copy/download was added.
- Added test-only `testing/backtestingFixture.ts`, `testing/static/{index.html,main.tsx}`,
  `vite.backtesting.config.ts`, `tsconfig.backtesting.json`,
  `scripts/backtesting_static_browser.mjs`, `scripts/backtesting_static_isolation.test.ts`
  and `test:backtesting-static*` npm commands. The fixture reuses
  `api/result.fixture.json` verbatim with its actual 2025-02-17..2025-03-25 request and
  five-session observed window. It is explicitly not a D3 Example, not real market
  performance and not the 2026 target window.
- Updated Backtesting and Demo authority/handoff, `.gitignore` and added this record.
  No producer, W2 strategy/Core/accounting, HTTP contract, OpenAPI, generated artifact,
  workflow or V1 entry changed.

## Production / Static boundaries

`BacktestingPresentation` is shared feature code, not a Demo page. Production and static
render the same header, request facts, requested-vs-observed card and `Result.tsx`. The
Production controller retains exclusive ownership of Query editing, inclusive dates,
profile selection, advisory Preflight, explicit Submit, Run identity/URL restore,
PENDING/RUNNING polling, cancellation, stale-response isolation, manual status/result retry
and 401 handling. Static composition owns no execution capability.

The static page shows Product, Strategy Profile, immutable Request window, Producer-observed
sessions, Result Profile, Definition Version and explicit Synthetic/Test-only disclosure.
Its success label means **the embedded Producer Result passed formal contract validation**,
never that the browser executed W2 Backtest Core or that a server Run existed.

## Pure validation and identity

`validateEmbeddedBacktestResult({request, result})` requires:

1. a generated `FuturesRollImmutableRequest`;
2. a complete generated `FuturesRollResult` (closed schema);
3. `futures_roll_long_result_v1`;
4. `futures_roll_long_definition_v1`;
5. `futures_roll_long_v1` case identity and `complete` status;
6. exact five-field request agreement (`case`, product, start, end, strategy);
7. a valid Returns View V2; and
8. a valid Drawdown View V2.

Invalid data remains an explicit static error with no request/Result region and no HTTP
fallback. Production keeps the generated HTTP response envelope check, Run ID check,
cross-Run request agreement and safe HTTP error mapping. The validator returns the original
payload by reference: no financial value, daily row, chart coordinate, trade or roll is
recomputed or rewritten.

## Verification

Environment: Windows 11, Node 22.23.2, npm 11.0.0, Poetry 2.3.2, system Google Chrome
157.0.8103.39 via `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`; WSL Ubuntu 24.04 (Node 22.22.1,
Python 3.13.15 in the existing Linux venv) for POSIX Backtesting/full-stack execution.
Browser evidence is in system temporary directories; no evidence log or build artifact is
committed.

| Command | Result |
| --- | --- |
| `npm run test` (default) | **FAIL** — 4 existing files / 7 tests reached the 5-second budget (MO Option Chain, MO Premium, Research Explorer); 573 of 580 passed. All were `Test timed out in 5000ms`; none were Backtesting assertions |
| `npm run test -- --maxWorkers=2 --testTimeout=15000` | **PASS** — 74 files, 580 tests |
| `npm run test -- src/features/backtesting --maxWorkers=1` | **PASS** — 7 files, 60 tests |
| `npm run test -- scripts/backtesting_static_isolation.test.ts --maxWorkers=1 --testTimeout=60000` | **PASS** — 7 negative build-isolation tests |
| `npm run test:backtesting-static` | **PASS** — typecheck, Vite build and dependency allowlist gate |
| `npm run test:backtesting-static-browser` (Windows Chrome) | **PASS** — fixed request/disclosure, Summary, both V2 Views, Trades/Rolls, Evidence, requested-vs-observed, invalid Result, mismatched request, ignored Production `run_id`, no Run/API/Auth, real Plotly Zoom/Pan/Reset, static-only requests |
| `npm run build` | **PASS** — Production TypeScript/Vite |
| `npm run lint` | **PASS** — 0 warnings, 0 errors |
| `npm run contract:check` | **PASS** — all seven consumed OpenAPI/generated pairs current; no regeneration |
| `npm run demo:build` | **PASS** — V1 entry/build unchanged |
| `npm run test:demo-browser` | **PASS** — V1 report, Plotly, disclosure, invalid fixture, zero Auth/API |
| `npm run test:static-shell-browser` | **PASS** — D1 seven hashes, history/reload, zero non-static requests |
| `npm run test:option-chain-static-browser` | **PASS** — D2-A behavior/isolation |
| `npm run test:premium-static-browser` | **PASS** — D2-B behavior/isolation |
| `npm run test:catalog-static-browser` | **PASS** — D2-C behavior/isolation |
| `npm run test:explorer-static-browser` | **PASS** — D2-D behavior/isolation |
| `npm run test:futures-basis-static-browser` | **PASS** — D2-E behavior/isolation |
| `npm run test:backtesting-browser` (Windows) | **BLOCKED before browser** — both port guards saw an unrelated pre-existing developer server: `EADDRINUSE 127.0.0.1:8011` (verified as `ui_http/scripts/api.py` plus a separate Vite at 5173, started outside this task) |
| `npm run test:backtesting-browser` (WSL Ubuntu, temporary in-copy ports 8021/5183) | **PASS** — real Chromium → Vite → FastAPI → worker → public-service fixtures; both profiles, PENDING/RUNNING/COMPLETED, 409, URL restore, Back/Forward, lost POST without replay, read_busy manual recovery, terminal FAILED/INTERRUPTED, corrupt/oversize/unavailable/invalid responses, ownership/404 and final 401. Evidence: `C:\Users\Benjamin\AppData\Local\Temp\d2f-wp7-evidence-2\acceptance.json`. One intermediate rerun hit the intermittent WSL auth-session loss described below; a clean rerun passed |
| `npm run test:auth-browser` (Windows default) | **BLOCKED before browser** — same unrelated pre-existing 8011/5173 listeners (`EADDRINUSE`) |
| Auth browser, temporary relocated Windows copy | **FAIL before completion** — registration POST timed out with no response; consistent with the known Windows Poetry temporary-SQLite limitation recorded by D2-E, not a D2-F code path |
| Auth browser, WSL relocated copy | **FAIL (pre-existing flake)** — after relocating every in-copy test port, several attempts lost the authenticated session (`/auth/me` 401 → login gate) at different post-login points. One earlier failure was an unrelocated 5173 reference in the neutral-dark helper and is not counted as a session regression. D2-E recorded the same WSL session-loss flake, and no Auth/session code changed in D2-F. Backtesting's clean WSL full-stack run independently exercised real registration, login, protected API access and 401 teardown |
| `git diff --check` | **PASS** |

The default Vitest run was executed first; its failures are resource-sensitive five-second
timeouts in untouched MO/Explorer tests. Repository test configuration, global timeout and
assertions were not relaxed. The complete suite passed under the explicit two-worker /
15-second invocation.

## Dependency and browser evidence

The static graph contains the shared page presentation, `Result.tsx`, pure validators,
static controller, generated OpenAPI schema, shared visualization, `AppUiProvider`, theme
and the explicit test-only fixture. It contains no `useBacktesting`, Production
`usePreflight`, `api/backtesting.ts`, `protectedRequest`, Auth, Production App/Page or
sibling feature module. Negative builds inject Auth, the Run hook, the Preflight hook, the
Production HTTP client, the Production Page, an indirect dynamic HTTP import and an
unresolved dynamic import; every actual build fails for the expected isolation reason.

The real static Chromium run requested only document/script/stylesheet assets under the
Pages base, with empty cookies, no `/api` or `/auth` requests, no POST, no resource failures
and no console/page errors across valid, invalid-Result and invalid-request states.

## Remaining risks and D3 handoff

- D3 must generate the official IM 2026-01-01..2026-11-11 Backtesting Example through the
  formal W2 producer and published Result projection. This task intentionally did not
  relabel the 2025 regression fixture.
- D4 must compose the seven-page static runtime; D5 must add cross-page fixture/route gates;
  D7 must switch release triggers. The D2-F static harness is test-only.
- The Production full-stack regression passed on WSL with an in-copy port relocation because
  this Windows host's 8011/5173 were already occupied. The script logic and assertions were
  unchanged apart from ports; no tracked test was altered.
- The Auth browser did not reach a clean PASS in this environment. This is the previously
  documented WSL auth-session flake plus the Windows temporary-SQLite limitation; D2-F does
  not touch Auth and the Backtesting full-stack run covered real login/protected access/401.
- No W2 financial, strategy, accounting, DataLake or HTTP contract drift was introduced.

## D2 status

D2-A through D2-F are complete. No blocking drift was found for entering D3 Static Examples.
