# D2-A — Shared MO Option Chain Presentation acceptance

Scope: `feat/github-pages-demo`, baseline `1e2eb0f9fb9b5c019fdda60cc6ac6184c320c827`.
This is shared presentation verification, not a published MO Example or D4 completion.

## Implementation

- `page/OptionChainPage.tsx` remains the Production composition root. `hooks/useOptionChain.ts`
  owns explicit date selection, protected requests, cancellation, request IDs and
  idle/loading/success/error state. No default date, query identity or Auth behavior changes.
- `presentation.ts` is the transport-free public entry. `page/OptionChainPresentation.tsx`
  owns the existing layout/query/result composition and uses the same controls, summary,
  chart, expiry details and Copy/Export components in both runtimes.
- `hooks/useOptionChainPresentation.ts` consumes a validated result or null, owns expiry
  selection, series colors and strike width, and projects selected groups/set and X domain.
  A new result selects all expiries; clearing the result clears selection. Colors/width
  survive result changes; the final selected expiry cannot be deselected.
- `api/validateOptionChain.ts` compiles the unchanged generated OpenAPI response schemas.
  Production error mapping and validation rules remain unchanged. Generated types are
  reused; no handwritten business DTO or financial computation is added.
- Static consumers validate once, call `useOptionChainPresentation(chain)` and supply
  `page: { status: 'ready', chain }` and `query: { mode: 'static', selectedDate,
  sourceDisclosure }` to the shared component. No query callback exists in that capability.
  The fixed DatePicker is disabled and Form submission has no business action.
- Copy/Export receives the complete validated chain, independently of selected groups,
  viewport and colors. Static disclosure stays in adjacent UI, outside Raw/Context/CSV.
  Production source remains the complete current validated HTTP result.
- Components/charts/models import generated-result types from the pure validation module.
  `OptionChainResults` references `ChainRequestError` only through `import type`.

Additional files: `testing/chainFixture.ts` centralizes existing page regression data;
`testing/static/{index.html,main.tsx}`, `vite.option-chain.config.ts`,
`tsconfig.option-chain.json`, npm commands and `scripts/option_chain_static_browser.mjs`
provide a separate test artifact. Feature component/hook tests and
`scripts/option_chain_static_isolation.test.ts` cover the new boundary. Root `.gitignore`
excludes that artifact. No official fixture, other feature implementation or workflow changes.

## Reconciliation

Conforms to D0 controller/presentation ownership; the narrow feature entry and D2 handoff
now record implementation. No cross-feature or reverse-layer runtime dependency is added.
The static build checks all loaded project modules and static/dynamic edges before tree
shaking, rejecting Auth, HTTP and Production controller imports. Negative builds inject
Auth, Production query, indirect dynamic HTTP and unresolved dynamic imports.

Production Option Chain intentionally fixes both axes, disables dragging, hides the
Plotly modebar and uses feature viewport buttons. Browser acceptance preserves this
existing behavior and exercises real Hover and the viewport; it does not enable new
Plotly Zoom/Pan/Reset actions.

## Verification

Final command results and local browser evidence are recorded below. Build warnings about
large existing Plotly bundles and existing Ant Design List deprecation are non-failing.

Verified 2026-11-12 from `ui_web/`:

| Command | Result |
| --- | --- |
| `npm run test -- --maxWorkers=2 --testTimeout=15000` | PASS — 55 files, 470 tests; includes component/hook, existing Production regression and four static negative-import tests |
| `npm run build` | PASS |
| `npm run lint` | PASS — no final warnings |
| `npm run contract:check` | PASS — all consumed products unchanged/current |
| `npm run test:daily-data-copy-export-browser` | PASS |
| `npm run test:auth-browser` | PASS |
| `npm run demo:build` | PASS |
| `npm run test:demo-browser` | PASS — V1 regression |
| `npm run test:static-shell-browser` | PASS — D1 regression |
| `npm run test:option-chain-static` | PASS — typecheck/build and dependency gate; also built by the browser command |
| `npm run test:option-chain-static-browser` | PASS — fixed input, Form submit, local controls, real Plotly Hover, full Clipboard/CSV/Context downloads, reload and zero non-static network |
| `git diff --check` | PASS |

Initial `npm run test` alongside several builds/browser suites failed on 5-second test
budgets; a two-worker retry at the original 5-second budget still timed out in one existing
Copy/Export test. The final complete run above passed with two workers and a 15-second
per-test budget. No assertions were removed and repository test timeout configuration was
not changed. Initial static-harness development failures (provider import and an attempted
modebar selector) were corrected; the final browser evidence tests the actual fixed-axis
Production contract. No checks remain NOT RUN or BLOCKED.

Local evidence (ephemeral, not public Example assets):

- D2-A static browser: `/tmp/d2a-option-chain-EP2FoS/acceptance.json`, dependency graph and screenshots.
- Daily Data browser: `/tmp/daily-data-evidence-vfxodV/acceptance.json` and exported data/screenshots.
- Auth/Shell screenshots: `/tmp/s2-wp1-shell-Zlo9PZ`.
- V1 Demo: `/tmp/wp3-demo-browser-98BNC8/acceptance.json`.
- D1 Shell: `/tmp/d1-shell-browser-TFRv5I/acceptance.json`.
- Full unit log: `/tmp/d2a-unit-final.log`; other command logs: `/tmp/d2a-*.log`.

## Next handoff

D2-B should extract Premium's own pure validation and local presentation state while
retaining its complete raw payload, nonempty-Points check, request/error behavior and
Inspector/serializers. Use fixed query capability and adjacent source disclosure, plus
feature-local static component and runtime-graph/browser verification. Do not share
Option Chain DTOs/state across features or introduce a generic runtime. D2-B is not
implemented here. D3 fixture generation and D4 full static composition remain outstanding;
V1 entry, deployment workflow and publication branch are unchanged. Stop for D2-A review.
