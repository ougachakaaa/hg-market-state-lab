# D2-B — Shared MO Premium Plane Presentation acceptance

Repository: `ougachakaaa/hg-market-state-lab`; branch: `feat/github-pages-demo`.
Expected and inspected baseline: `6d4858d3bbbf8717e583b6f8704a890a9de22069`.
The initial working tree was clean, HEAD was exactly the baseline, and no subsequent
commit superseded it. D0 authority, D1 Shell and D2-A Option Chain implementation were
present. This task implements D2-B only; the static harness is not a D3 Example or D4 app.

## Implementation and files

- Added `presentation.ts` as Premium's transport-free public entry, exporting
  `PremiumPlanePresentation`, `usePremiumPresentation`, `validatePremiumPlane` and
  generated result types. `page/PremiumPlanePresentation.tsx` is the sole page layout.
- Updated `page/PremiumPlanePage.tsx` to compose Production query state with that same
  presentation. `hooks/usePremiumPlane.ts` retains explicit date/price inputs, default
  close/no date, protected HTTP, cancellation, stale-response handling and error lifecycle.
  Only real query inputs trigger requests; no default/latest date or fallback is added.
- Added `hooks/usePremiumPresentation.ts` for side, all four metric coordinates, expiry
  selection/set and sparse projection. The formal defaults apply on result replacement.
  Production passes a query revision to preserve reset-at-query-start even when consecutive
  queries both have no loaded result. The revision is local lifecycle coordination,
  never a query parameter or financial identity. At least one expiry remains selected.
- Added `api/validatePremiumPlane.ts`; `api/moOptionPremium.ts` reuses its exact schema
  matching and nonempty-Points success predicate. Structural validity with `points=[]`
  still fails as invalid_response in Production. Static uses the same predicate. The
  validator returns `{ plane, rawPayload }` referencing the original payload, without
  cloning, filtering, metric calculations or handwritten DTOs. Access/error mappings stay
  in the Production API. OpenAPI/generated TypeScript artifacts are unchanged.
- Updated `components/PremiumControls.tsx` with an explicit static query capability,
  disabling date/price controls and providing no business callbacks. Form submit is inert.
  Local metric/side/expiry controls remain usable.
- Updated `components/PremiumResults.tsx` to use type-only `PremiumRequestError` and
  origin-aware Inspector labels: Production retains “Raw backend response”; Static uses
  “Validated embedded Example payload”. Required static disclosure appears next to
  Copy/Export and inside the Inspector, outside serialized data.
- `PremiumCopyActions` and `model/{premiumPlane,copyText,csvExport}.ts` now import generated
  types from the pure contract module. Projection, formatting, reference coloring and
  serializer algorithms are unchanged. Raw/Context/Inspector use complete rawPayload;
  CSV uses all real points and all 16 existing leaves of its paired validated plane.
- A result revision keys the complete result section, retiring old Clipboard pending/
  feedback and Inspector state on replacement, including same-observation replacements.
  Query loading/error still removes the previous result and payload immediately.
- Added `testing/planeFixture.ts` by extracting existing page regression data verbatim;
  `PremiumPlanePage.test.tsx` now imports it. Added hook/component tests and
  `testing/static/{index.html,main.tsx}`, `vite.premium.config.ts`, `tsconfig.premium.json`,
  `scripts/premium_static_browser.mjs`, `scripts/premium_static_isolation.test.ts` and npm
  commands. `.gitignore` excludes the new test build artifact.
- Extracted D2-A's existing Vite isolation plugin into the shared **build-time test utility**
  `scripts/staticPresentationIsolation.ts`. Both feature Vite configs supply their own
  owner and forbidden-controller paths. It checks loaded modules and static/dynamic edges
  before tree shaking and rejects unresolved dynamic imports. This shares verification
  mechanics without introducing a feature runtime, store or cross-feature business imports.
- Updated narrow Feature authority/visualization specialization and Demo implementation
  handoff. V1 release entry, D1 harness, workflows, Python modules and other features'
  runtime code are unchanged.

## Static consumption and reconciliation

Static composition calls `validatePremiumPlane(embeddedPayload)` once, then
`usePremiumPresentation(result.plane)`. It passes the local state with
`page: { status: 'ready', ...result }` and fixed `query: { mode: 'static', selectedDate,
priceType, sourceDisclosure }` to `PremiumPlanePresentation`. No Production hook, Auth,
HTTP client, Python or mock service is involved. Unknown/empty/invalid results fail
validation before becoming ready; the harness has only known-valid regression data.

D0 ownership and dependency direction remain intact. Premium has no Option Chain runtime,
DTO or state dependency; each uses its own generated contract. Sparse projection still
reads one existing four-dimensional leaf, keeps backend identities/order and strike union,
and distinguishes absent Point, null metric and numeric zero. No interpolation, fill,
annualization, premium/yield recomputation, schema change or business-semantic drift.

Raw source is the actual validated HTTP body in Production and the validated embedded
payload in Static. Both use the existing serializers unchanged. Disclosure is adjacent UI;
Raw JSON and Context V1 retain their original structure and complete data. Test-only
regression data is explicitly labelled and is not an official Synthetic Example.

## Verification

Verified on 2026-11-12 from `ui_web/`:

| Command | Result |
| --- | --- |
| `npm run test` | FAIL on initial default run: 5 tests reached the 5-second budget; 474 passed |
| `npm run test -- --maxWorkers=2 --testTimeout=15000` | PASS — 58 files, 479 tests, including both features' negative static import tests |
| `npm run test -- src/features/mo_option_premium --maxWorkers=2 --testTimeout=15000` | PASS — 9 files, 50 tests |
| `npm run test -- src/features/mo_option_premium/page/PremiumPlanePresentation.test.tsx --maxWorkers=2 --testTimeout=15000` | PASS — 4 tests after test typing correction |
| `npm run build` | PASS after fixing test-only TypeScript errors |
| `npm run lint` | PASS |
| `npm run contract:check` | PASS — all consumed contracts/generated types current |
| `npm run test:daily-data-copy-export-browser` | PASS — both products and protected lifecycle |
| `npm run test:auth-browser` | PASS after the narrow test locator correction described below |
| `npm run demo:build` | PASS |
| `npm run test:demo-browser` | PASS — V1 unchanged |
| `npm run test:static-shell-browser` | PASS — D1 unchanged |
| `npm run test:option-chain-static-browser` | PASS — D2-A, including reused isolation build |
| `npm run test:premium-static` | PASS — generated validator + transport-free build |
| `npm run test:premium-static-browser` | PASS — fixed query/Form submit, default and four-axis/side/expiry selection, legal empty projection, sparse facts/coloring, complete Inspector and Clipboard/CSV/Context downloads, reload, only static network assets |
| `git diff --check` | PASS |

The default full Vitest run timed out in five Ant Design interaction tests across both
features (all reported `Test timed out in 5000ms`), without another build/browser suite
running. The final full two-worker/15-second run passed every assertion; repository test
configuration and assertions were not relaxed. Raw logs preserve both outcomes:
`/tmp/d2b-unit.log` and `/tmp/d2b-unit-final.log`.

Development corrections: the initial build found unsupported Testing Library `exact`
options and a type import removed during fixture extraction; both test typing issues were
fixed before the successful build. The initial static browser selector targeted the hidden
Ant Design Put radio input; the final harness clicks its visible label, with the same
selected-side assertions. The initial failure artifact is `/tmp/d2b-premium-lfdurk`.

Auth browser failed twice at the pre-existing collapsed Explorer assertion: leaf visibility
had been awaited, then the parent `:visible` locator yielded a count of zero. Only
`scripts/auth_browser_smoke.mjs`'s parent locator was corrected to retain the popup through
its animation. The script still waits for the Explorer leaf itself to be visible, asserts
exactly one accessible leaf, rejects a clickable group heading and verifies route/selection.
Application Shell/Auth code and all assertions remain unchanged. The final full Auth
browser command passed registration/CLI approval/login, both product reads, reload,
all routes/collapse/history, Cookie/storage boundaries and logout. Initial/retry logs:
`/tmp/d2b-auth-browser-initial.log`, `/tmp/d2b-auth-browser-retry.log`; final:
`/tmp/d2b-auth-browser-final.log`.

Final local evidence is ephemeral verification output, not public Example assets:

- Premium static browser: `/tmp/d2b-premium-pQK1g1/acceptance.json`, dependency graph and screenshots.
- Daily Data: `/tmp/daily-data-evidence-Crx9ow/acceptance.json`, complete exports and screenshots.
- Auth/Shell screenshots: `/tmp/s2-wp1-shell-ajxBJz`.
- V1 Demo: `/tmp/wp3-demo-browser-I2yF7m/acceptance.json`.
- D1 Shell: `/tmp/d1-shell-browser-T1bhFj/acceptance.json`.
- D2-A: `/tmp/d2a-option-chain-VzFQyF/acceptance.json`.
- Other command logs: `/tmp/d2b-*.log`.

No required command remains NOT RUN or BLOCKED. Existing large-bundle and Ant Design List
deprecation warnings are non-failing. The successful full unit suite was rerun with explicit
resource parameters; the original default command's failure is retained above.

## D2-C handoff

Catalog's `ResearchWorkspacePage` currently contains reusable CapabilityDetails, local-case
readout, list/detail layout and online/local selection. `useCatalog` owns mount list GET,
selected detail GET, cancellation, retries and protected access. Extract feature-local
shared presentation and descriptor validation; leave GET/retry lifecycle in Production.
The Static controller should consume a validated embedded list/detail set, verify matching
IDs and select locally. Reuse existing localCases and supplied navigation callbacks;
origin-aware labels must distinguish embedded descriptions from authenticated discovery.
Keep readiness/limitations as published facts, without provider probes or inferred runtime
availability. No Research execution or Explorer refactor is needed for D2-C. D2-C is not
implemented here. Official Examples, full static composition and release switching remain
D3/D4/D7 work. Stop after the independent D2-B commit for review.
