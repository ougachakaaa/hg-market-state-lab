# UI-01-R2 reconciliation

## Browser acceptance completed — 2026-11-15

Current UI-01-R2 status is **READY**. The NOT_READY entries below describe earlier
attempts and are superseded by this browser evidence. Acceptance used branch
`feat/ui-01-research-overview` at `727353b` (including the overview follow-up after
the supplied `d5b7beb` baseline).

Native Windows x64, Node 22.23.2, npm 11.0.0 and installed Playwright 1.64.1 were used.
`npx --no-install playwright install chromium` stalled while downloading. The exact
official Chrome for Testing 156.0.8078.4 headless-shell archive for revision 1248 was
downloaded with curl, reconstructed from HTTP ranges and verified against the official
response MD5 `rT33sBjoEAhkmSHMEEwqdA==` before extraction into
`%LOCALAPPDATA%/ms-playwright/chromium_headless_shell-1248`.
All tests launched that browser through their existing Playwright default path.
No package version or lockfile changed. Linux dependencies were inapplicable.

From `ui_web`, all three original entry commands passed real Chromium acceptance.

| Command | Result and local evidence under `%TEMP%` |
| --- | --- |
| `node tests/browser/catalog_static_browser.mjs` | PASS; `d2c-catalog-dJbxuu/acceptance.json`, desktop/mobile screenshots |
| `node tests/browser/static_shell_browser.mjs` | PASS; `d1-shell-browser-S9dZsn/acceptance.json`, expanded/collapsed screenshots |
| `node tests/browser/research_browser_smoke.mjs` | PASS, including the fourth script `research_browser_acceptance.mjs`; `hg-market-state-lab-web-workspace/acceptance.json`, `wp3a/1440x900` and `wp3a/1024x768` screenshots |

The Production composition used real authentication, Cookie, HTTP, temporary SQLite
and explicitly synthetic provider/publication fixtures. Both viewport acceptances
verified three cards, one completed/two incomplete states, removed technical/Explorer
buttons, direct Explorer access, and the collapsed introduction's two fields.
Static Shell verified all eight current routes, reload/history, hidden Explorer leaf
and shared Appstore overview icons. Static Catalog verified the shared Study-only
presentation and static-only network activity.

Additional existing scripts completed the requested report coverage.

- `node tests/browser/futures_basis_static_browser.mjs` — PASS; shared collapsed
  introduction, both fields, embedded report, section navigation and static isolation.
  Evidence is `%TEMP%/d2e-futures-basis-zgXoq5/acceptance.json` and screenshots.
- `node tests/browser/futures_basis_report_browser.mjs` — PASS; real offline charts,
  Trading Days/Calendar Days mapping, legend persistence, percentage hover, mouse
  box zoom, drag pan and reset. Evidence is
  `%TEMP%/r01a-offline-browser-8bpxvU/report-browser/acceptance.json` and screenshots.

No browser exceptions occurred in the successful runs. Static/offline checks reported
zero console errors. Production console review found the expected anonymous 401 and
injected 503 responses plus the existing Ant Design List deprecation warning.
The initial cold Vite run also logged an Outdated Optimize Dep 504, absent on rerun.
The first browser attempt failed a newly added icon assertion against an unmounted
narrow-screen submenu. The assertion now checks the expanded desktop layout, while
the existing narrow navigation checks remain. Failure evidence is retained locally
in `hg-market-state-lab-web-workspace/failure.json` and `failure.png`; the earlier
missing-executable failure is in `d2c-catalog-0ChOO3/acceptance.json`.
Final smoke output is retained in `%TEMP%/ui01-research-final.log`.

Only acceptance scripts and this reconciliation changed. Production UI and business
contracts required no fixes. Large browser artifacts remain outside Git. Test-owned
temporary Auth/Run/Publication stores were removed by the existing smoke teardown.

Non-mutating three-way inspection against DDB `9262eddf` using common ancestor
`a350fd8` and current UI HEAD reported no conflict markers. UI-01-R2 is ready for
integration into that DDB baseline. Official Bundle composition/build and integrated
Demo acceptance remain DDB-04 work. No merge, push or deployment was performed.

## Scope

Research Overview exposes Study navigation and minimal disclosure. Historical Basis
shares a collapsed two-field introduction across runtimes. Overview routes share the
existing overview icon. Canonical owners are workspace.md and the two feature authorities.

Controller/validator behavior, authentication, seven routes, Explorer direct access and
all Bundle, HTTP and backend contracts are preserved. Legacy browser assertions must
follow Study-only presentation and hidden Explorer navigation.

## Verification evidence

Commands run from ui_web.

- `npx vitest run src/features/research_catalog/page/ResearchOverviewPresentation.test.tsx src/features/research_catalog/page/ResearchWorkspacePage.test.tsx src/features/research_catalog/api/validateCatalog.test.ts src/features/futures_basis_research/page/FuturesBasisPresentation.test.tsx src/app/ApplicationShell.test.tsx src/app/routes.test.tsx src/app/App.test.tsx` initially passed 59 cases with 3 legacy App navigation failures.
- After fixing those cases, `npx vitest run src/app/App.test.tsx -t "opens all three|restores the Workspace|shows studies directly"` passed all 3 selected cases.
- After adding independent static controller coverage, `npx vitest run src/features/research_catalog/page/ResearchWorkspacePage.test.tsx` passed all 6 cases. Combined scoped evidence covers 64 passing cases.
- `npm run build` passed TypeScript and online Vite build, with an existing large-chunk advisory.
- `npm run lint` passed, including a final rerun after test edits.
- `node --check` passed for all four changed browser scripts.
- `node tests/browser/catalog_static_browser.mjs`, `node tests/browser/static_shell_browser.mjs` and `node tests/browser/research_browser_smoke.mjs` could not launch Chromium. Browser acceptance is NOT VERIFIED. The missing executable is `%LOCALAPPDATA%/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-win64/chrome-headless-shell.exe`. Research acceptance is invoked by the smoke and was not reached. No browser installation was attempted.

## Resolved presentation drift

The overview keeps the three Study cards, completion labels, Historical Basis callback
and footer, while removing technical tools and Catalog-only error presentation.
Catalog validation, retries, detail cancellation and stale isolation now have independent
controller tests. Formal validator tests remain intact. Security/Cookie assertions in
browser smoke remain intact. Explorer navigation uses direct URLs, while static shell
acceptance distinguishes seven registered routes from visible sidebar entries.

Both runtime introductions default collapsed, show the exact two approved sentences,
issue no requests and retain the report node and URL in focused tests. Report rendering
is mocked in these tests, so real chart interaction remains browser-unverified.

The actual UI baseline used `data` for /data, contrary to the supplied baseline note.
It now uses the existing shared `overview` icon identity, with a focused route test.

## DDB comparison and readiness

`git fetch github feat/demo-bundle-workflow` fetched target
`9262eddfc1250a498b9b6b372dc5aadd620f85f0`. Common ancestor is
`a350fd823ae89652c0d6e8f31231ad570d95ed9f`. Branches have diverged.
DDB changes eight Collector/build files. The UI branch changes Presentation, navigation,
authority and acceptance files, with no file overlap. Git 2.37.3 lacks merge-tree
--write-tree, so the supported three-argument `git merge-tree <base> <ddb> <ui>`
provides the non-destructive three-way inspection. It reports no conflict markers.
DDB-03 Collector files are preserved by the disjoint changes. No final merge occurred.

Final UI-01 status is NOT_READY because browser functional acceptance remains unverified.
All intended changes are committed and the final working tree check is recorded in the
final report. Bundle, HTTP, generated contracts and backend implementation are unchanged.

## Deferred DDB-04 integration

- Compose the current shared Study-only Presentation with admitted catalog/publications Bundles.
- Exercise direct Explorer hash navigation, reload and history without a sidebar entry.
- Verify the shared introduction with a real embedded report, preserving chart state and section navigation.
- Run the official Demo build and full Demo integration in its owning work package.

## Overview navigation follow-up

User approved three shared overview signals and a Backtesting overview. Completion
text now uses Ant Design success/secondary colors on Research, Daily Data and
Backtesting cards. Three overview destinations use AppstoreOutlined and visible instance
pages use FileTextOutlined. Business areas retain distinct icons.

Backtesting Overview lives at `/backtesting`; its single card opens
`/backtesting/futures-roll-long`. Production legacy root links with the `run_id` query
key use replace navigation preserving query and fragment, including anonymous login
and history restoration. The formal inventory now has eight pages. The overview never
mounts the execution controller. Existing Run submissions retain the instance pathname.

The retained StaticWorkspace exhaustive route map required both new identities for
TypeScript compilation, so it now composes the same overview and existing static Result
page. This minimal composition adjustment was necessary beyond the planned Shell harness.
DDB-04 still owns official Bundle integration/build and real static reader acceptance.

Verification from ui_web passed all 64 cases across App, routes, ApplicationShell,
Overview, ResearchOverviewPresentation and useBacktesting test files. `npm run build`
passed TypeScript and online Vite build with the large-chunk advisory. `npm run lint`
passed. Updated browser acceptance navigates Backtesting group to overview to instance;
existing legacy Run-link cases remain to verify redirection. Static Shell assertions
now use eight routes and all three area groups. Browser execution evidence follows.

Follow-up verification commands from ui_web:

- `npx vitest run src/app/routes.test.tsx src/app/ApplicationShell.test.tsx src/app/App.test.tsx src/app/Overview.test.tsx src/features/research_catalog/page/ResearchOverviewPresentation.test.tsx src/features/backtesting/hooks/useBacktesting.test.ts` — PASS, 6 files / 64 cases.
- `npm run build` — PASS after synchronizing the retained static route map.
- `npm run lint` — PASS.
- `node --check tests/browser/backtesting_browser_acceptance.mjs` and `node --check tests/browser/static_shell_browser.mjs` — PASS.
- `node tests/browser/static_shell_browser.mjs` — the first attempt exposed the new pure overview missing from the harness allowlist. Added only that Presentation to the allowlist and reran this check. Static build and dependency assertions passed. Chromium launch then failed because the executable under `chromium_headless_shell-1248` is absent. Browser acceptance is NOT VERIFIED. Backtesting browser E2E was not run because it uses the same unavailable browser.

The follow-up implementation is verified by scoped unit tests and online build. The
previous UI-01 NOT_READY browser-evidence limitation remains until browser acceptance
can execute. No browser installation, official Demo build or deployment was performed.
