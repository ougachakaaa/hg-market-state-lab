# UI-01-R2 reconciliation

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
