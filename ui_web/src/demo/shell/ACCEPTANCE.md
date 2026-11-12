# D1 shared Shell acceptance — 2026-11-12

This is implementation evidence under [Demo implementation handoff](../IMPLEMENTATION.md),
not Demo V2 readiness or a new business authority.

## Baseline and scope

Branch `feat/github-pages-demo`, baseline `73de9e077aafcd9c90e02fda9f22b10357b5e9a5`;
initial working tree clean. Local `develop` had zero exclusive commits and this branch
had three (`2c1ed5b`, `bdda39c`, D0 `73de9e0`). D0 authority encoding was present;
its requested D1 implementation was absent. No fetch, branch creation, rebase, merge,
push or deployment was performed.

Runtime: Linux, Node 22.23.2, npm 10.9.8, Playwright Chromium 156.0.8078.4.
All npm commands below run from `ui_web/`; Python-backed contract/browser checks use
the existing repository-root Poetry environment and temporary synthetic stores.

## Implementation and changed files

- `src/app/ApplicationShell.tsx`: shared sidebar, header, breadcrumb, responsive
  layout, collapse/open state and content region. API: `path`, `navigate`, `href`,
  rendered `header`, rendered `children`. No Auth, feature, query or transport imports.
- `src/app/routeInventory.ts`: single pure source of seven route identities,
  titles, area/category and icon identifiers. Both menus use the same declaration;
  Explorer is a selected Research leaf, including collapsed popups.
- `src/app/App.tsx`: Production composes existing online Pages and user/logout around
  the shared Shell. AuthenticationGate, useAuthentication and request boundary remain
  Production concerns. `src/app/routes.ts` consumes the inventory; pathname/history
  logic and same-page `run_id` preservation are unchanged.
- `src/app/DailyDataLanding.tsx`: extracted existing Daily Data presentation and both
  MO entry buttons, reused by both compositions without a second Landing.
- `src/demo/shell/{StaticShellHarness.tsx,hashRoutes.ts,main.tsx,index.html}`:
  anonymous verification entry, shared provider/Shell/Landing, neutral content for
  the remaining routes; hash navigation stays under the Pages base. No feature results,
  fake user, server Run, fixture/controller or HTTP simulation.
- `vite.shell.config.ts`, `tsconfig.shell.json`, `package.json`, root `.gitignore`:
  reuse V1 Vite settings with separate entry and `dist-demo-shell` output; add only
  verification commands, no dependencies or second release pipeline.
- `src/app/{ApplicationShell.test.tsx,routes.test.tsx,App.test.tsx}`,
  `scripts/{static_shell_browser.mjs,static_shell_isolation.test.ts,auth_browser_smoke.mjs}`:
  composition/routes/isolation tests and updated Explorer expectations/waits.
- `workspace.md`, `src/demo/IMPLEMENTATION.md`, this record: D1 status, navigation
  and evidence. Existing V1 source, fixture, historical acceptance and Pages workflow
  are unchanged.

No new semantic decision or cross-layer dependency was required. D1 implements D0;
Workspace now records the Explorer leaf as implemented. The harness is a temporary
verification composition, not a second business UI or the V2 release entry.

## Verification results

| Command | Result | Evidence |
| --- | --- | --- |
| `npm run test` | PASS | 52 files, 463 tests; includes Auth/401/stale/logout isolation, both Run route identities, Shell composition and three real-build isolation rejection tests |
| `npm run build` | PASS | Production TypeScript and Vite artifact |
| `npm run lint` | PASS | oxlint |
| `npm run contract:check` | PASS | All seven consumed OpenAPI/TypeScript artifacts current; no regeneration |
| `npm run test:auth-browser` | PASS | Real registration, CLI approval, login, MO results, reload/logout, seven routes, collapsed navigation, Explorer selection, breadcrumb/history; 1440/1024 widths |
| `npm run test:research-browser` | PASS | Real catalog/Explorer reads, Views, failure/retry, deep URL, reload/history and logout |
| `npm run test:futures-basis-online-browser` | PASS | Real synthetic Run admission/polling/result, refresh and Back/Forward restoration, reader interactions/logout |
| `npm run test:backtesting-browser` | PASS | Real worker/Run/result, history, failure/retry and protected 401 isolation |
| `npm run demo:build` | PASS | Existing V1 npm-only build, unchanged release entry |
| `npm run test:demo-browser` | PASS | Six-section Reader/Plotly, disclosure, desktop/mobile, reload, invalid-fixture handling, zero Auth/API |
| `npm run test:static-shell` | PASS | Typecheck/build and complete loaded project graph with static/dynamic edges; also run by static browser command |
| `npm run test:static-shell-browser` | PASS | Actual built static files, all seven identities, direct hash/reload/history, runtime hrefs, fallback, no server Run restore, both MO Landing buttons, Explorer/collapse at 1440/390 widths; zero Auth/API/external requests |
| `git diff --cached --check` | PASS | Reviewed full staged diff |

The isolation gate permits only the ten declared project modules plus bundled library
infrastructure. It inspects loaded modules before tree shaking, rejects nonliteral
dynamic imports and rejects undeclared modules through either static or dynamic edges.
Negative tests inject a direct Auth import, indirect dynamic protected-request import
and variable dynamic import in memory; all three actual builds must fail for the
specified isolation reason. Type-only imports introduce no runtime edge.

During implementation: FAIL runs exposed an obsolete DOM-text selector, popup timing
and popup/inline selector ambiguity, narrow text overflow, and Vitest's browser URL
transformation of build config imports. These were corrected. One initial full suite
run had ten timing failures while builds and browser work competed for resources;
all existing 460 assertions then passed with one worker. After the isolation-test fix,
the final unmodified `npm run test` command passed all 463 tests without concurrent
builds. No failed attempt is counted as PASS. BLOCKED: none.

NOT RUN: new V2 Example/feature-content acceptance (D2–D6), live market-data validation,
public Pages deployment/HTTP acceptance, full backend suites, standalone offline Reader
and dedicated Copy/Export browser commands. Their implementations/contracts were not
changed; this record makes no new release or live-market readiness claim. Existing
Ant Design List deprecation and Vite chunk-size warnings remain non-blocking.

Browser JSON/screenshots are emitted under the printed system temporary directories.
These local artifacts are disposable; the committed assertions and this result summary
are the durable evidence. To review locally after `npm run test:static-shell`, run
`npx vite preview --config vite.shell.config.ts` and open the printed origin at
`/hg-market-state-lab/#/research`. This does not replace or publish V1.

## Remaining work and D2 handoff

Online feature Pages still own coupled query/execution and presentation. No D1 harness
route claims a shared business Page, Example result or V2 feature coverage. Static
fixtures, validation-only feature entries and read-only controllers remain later work;
V1 remains a single Futures Basis report with the existing 2024 synthetic fixture.

Report section anchors must use local scrolling or explicit route-aware encoding when
composed with the hash router. A bare `#section-*` currently normalizes as an unknown
route; the six-section Reader was intentionally left unchanged in D1.

Split D2 by owning feature/domain: MO Chain and Premium separately (query versus local
presentation state and pure validation), Catalog/Explorer separately (HTTP reads versus
shared discovery/reader presentation), then Futures Basis and Backtesting separately
(execution/preflight/Run controls versus existing result presentation). Keep each change
paired with its Production regressions; preserve the current public feature boundaries
and reuse the already independent result components. Do not refactor all six Pages in
one package or add a generic feature runtime. D2 has not been executed.
