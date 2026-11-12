# D2-D — Shared Research Explorer presentation acceptance

Repository: `ougachakaaa/hg-market-state-lab`; branch `feat/github-pages-demo`.
Inspected baseline: `6ece288fa84ab327c7bd84d7eb1d3e5475f97d71` (D0–D2-C present).
The initial working tree was clean and HEAD exactly matched that baseline. This task
implements D2-D only; the static harness is not a D3 Example, D4 app or D2-E.

## Implementation and files

- Added `presentation.ts` as Explorer's transport-free public entry. It exports the shared
  Reader, `AnalysisDetails`, pure validators, static controller and generated contract
  types.
- Added `page/ResearchExplorerPresentation.tsx` as the one Reader page JSX: Publication
  list/cursor controls, Manifest scope/source/Jobs, Analysis details, ChartView selection
  and rendering, and loading/error/empty/unsupported states.
  `page/ResearchExplorerPage.tsx` is now a thin Production composition root.
- Added `components/{Facts,ErrorState,AnalysisDetails,displayValue}.tsx/ts`. Existing
  Analytics formatting, statistics tables, coverage evidence, labels and raw payload
  presentation are unchanged. Failure messages now live in a transport-free model module.
- Added `api/validateResearch.ts` with generated-schema matching for Publication List,
  Manifest, Analysis and View plus shared ChartView validation. `api/research.ts` retains
  only protected transport, URL construction, HTTP status/kind mapping and the distinct
  `invalid_view` classification.
- Updated `hooks/useExplorer.ts` as the Production controller: four independent load
  states, list/cursor pagination, lazy Manifest/Analysis/View reads, manual retry,
  cancellation plus request-token stale isolation, and explicit Publication/Analysis/View
  reset rules. Page changes retain the existing selection behaviour.
- Added `api/validateEmbeddedPublication.ts`. It validates paginated Publication Lists,
  Manifests, Analyses and ChartViews and enforces list→Manifest, Manifest Job→Analysis,
  Manifest summary→Analysis result, Publication/Analysis/View and View-reference identities.
  Missing embedded detail records are allowed as explicit missing states; duplicate,
  conflicting, unlisted or malformed records reject the whole set.
- Added `static/useStaticExplorer.ts`: validated record lookup, local page/Publication/
  Analysis/View selection, reset cascade and static missing/invalid states. It has no HTTP,
  Auth, retry, refresh or execution path.
- Added test-only `testing/publicationFixture.ts`, `testing/static/{index.html,main.tsx}`,
  `vite.explorer.config.ts`, `tsconfig.explorer.json`,
  `scripts/explorer_static_browser.mjs`, `scripts/explorer_static_isolation.test.ts` and
  npm commands. The fixture reuses the committed Research ChartView regression data and is
  explicitly not a D3 Publication Example.
- Extended the shared static dependency gate only by allowing the domain-neutral
  `shared/visualization` modules and the explicit test-only ChartView fixture path. No
  Auth, HTTP, Production controller/page or sibling feature is reachable.
- Updated Explorer authority, Demo implementation handoff and root `.gitignore`. No
  producer, Publication Store, HTTP contract, generated artifact, workflow, Catalog,
  Futures Basis or Backtesting implementation changed.

## Production controller and shared presentation

`useExplorer` continues to request only the list on mount; Manifest, Analysis and View
GETs remain lazy and selection-driven. Each layer has independent idle/loading/success/
error state, manual retry and abort cleanup. Selection changes increment request identities
so late responses cannot overwrite a newer selection; the existing opaque cursor bytes are
passed through unchanged. `ResearchExplorerPage` only passes the controller to the shared
presentation.

The shared presentation preserves the existing page header, Publication list and
pagination text, Manifest/Jobs/Analysis labels, `AnalysisDetails`, count/frequency/quantile
View buttons, ChartView rendering, unsupported-View warning and error/retry behaviour.
Production keeps its exact online wording and Refresh action.

## Static validation, selection and disclosure

Static input is an embedded set of list pages, Manifests, Analyses and keyed ChartViews.
Validation requires unique Publication IDs across pages, a listed Publication for every
Manifest, matching list/Manifest status, unique Manifests/Analyses/Views, declared
request/spec associations, Job→Analysis references with matching Job identity, Analysis
summary↔result identity and outcome/result agreement, and ChartView validity under both
the generated OpenAPI shape and the shared Visualization contract. Referenced Views and
Analyses may be omitted; the UI shows explicit "not embedded" states instead of success or
HTTP fallback.

The static controller reads already validated records and performs local page and
selection changes. Selecting a Publication resets Analysis and View; selecting an Analysis
resets View. Static disclosure states that the online Publication Store was not queried,
research was not executed, and Provenance/Source metadata does not establish market-source
authenticity. No Refresh, retry, preflight or execution affordance is rendered.

## Verification

Environment: Windows, Node 22.23.2, npm 11.12.1, Poetry 2.3.2, system Google Chrome
157.0.8103.39 via `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`. Browser evidence is in printed
system temporary directories; no evidence log or build artifact is committed.

| Command | Result |
| --- | --- |
| `npm run test` (default) | **FAIL** — 4 files / 6 existing MO tests reached the 5-second budget; 521 of 527 passed. All six were `Test timed out in 5000ms`, none in Explorer |
| `npm run test -- --maxWorkers=2 --testTimeout=15000` | **PASS** — 65 files, 527 tests |
| `npm run test -- src/features/research_explorer --maxWorkers=1 --testTimeout=15000` | **PASS** — 8 files, 65 tests |
| `npm run test -- scripts/explorer_static_isolation.test.ts --maxWorkers=1 --testTimeout=30000` | **PASS** — 6 negative build-isolation tests |
| `npm run test:explorer-static` | **PASS** — typecheck, Vite build and dependency gate |
| `npm run test:explorer-static-browser` | **PASS** — list/Manifest/Jobs/provenance, interval count/frequency and quantile Views, selection reset, empty state, Plotly rendering, reload and zero non-static requests |
| `npm run build` | **PASS** |
| `npm run lint` | **PASS** — 0 warnings, 0 errors |
| `npm run contract:check` | **PASS** — all consumed OpenAPI/generated artifacts current; no regeneration |
| `npm run test:auth-browser` | **PASS** (exit 0) — real registration/CLI approval/login, routes, MO products, reload/logout and Cookie/storage boundaries; required a test-run-only Windows process-tree cleanup hook for orphaned uvicorn pipes |
| `npm run test:research-browser` | **BLOCKED before browser** — fixture generation raises `PublicationUnavailable: publication storage requires POSIX descriptor-relative filesystem operations` on Windows. No D2-D code path was reached; this is the existing producer platform guard |
| `npm run demo:build` | **PASS** — V1 release entry unchanged |
| `npm run test:demo-browser` | **PASS** — V1 six-section reader, Plotly, disclosure, reload, invalid fixture and zero Auth/API |
| `npm run test:static-shell-browser` | **PASS** — D1 seven hashes, history/reload, Explorer leaf and zero non-static requests |
| `npm run test:option-chain-static-browser` | **PASS** — D2-A behavior/isolation |
| `npm run test:premium-static-browser` | **PASS** — D2-B behavior/isolation |
| `npm run test:catalog-static-browser` | **PASS** — D2-C behavior/isolation |
| `git diff --check` | **PASS** |

The default Vitest run was executed first. Its failures are the known resource-sensitive
five-second interaction timeout in existing MO tests, not Explorer assertions. Repository
test configuration and global timeout were not changed. The complete suite passes under
the explicitly adjusted two-worker/15-second invocation.

The static build graph contains the shared Reader, validators, static controller,
`AnalysisDetails`/Facts, shared Visualization, `AppUiProvider` and the explicit test-only
ChartView fixture. It contains no `shared/http`, `app/auth`, Production `research.ts`,
`useExplorer`, `ResearchExplorerPage` or sibling feature modules. The real built artifact
made only static document/script/stylesheet requests, with empty cookies and zero
Auth/API/provider/browser errors. Negative builds inject Auth, Production controller/HTTP/
page, indirect dynamic HTTP and an unresolved dynamic import; each actual build fails for
the expected isolation reason.

## Remaining risks and Linux gate

- Official D3 Publication Examples, D4 full application composition, D6 acceptance and
  D7 Pages release switching remain outstanding.
- The static fixture uses test-only regression data and is not a publishable Example. The
  deep embedded set is exercised in a real browser; additional invalid associations are
  covered by validator/controller tests rather than a fixture-variant framework.
- Production browser research coverage cannot run on this Windows host because the existing
  Publication Store requires POSIX descriptor-relative I/O. Unit production regressions,
  the Production build and the real Auth browser cover the changed controller/presentation,
  but this is not a substitute for the Linux browser gate.
- **Linux Regression Gate for D2-D:** rerun `npm run test:research-browser` on a POSIX host
  with the repository root Poetry environment and a real Publication Store fixture. This is
  required before claiming full Production browser acceptance.
- Source metadata/source digest remains evidence identity, not market-data authenticity.

## D2-E handoff

D2-E should apply the same split to Futures Basis Research:

1. Keep `useFuturesBasis` and `usePreflight` as the Production controller for admission,
   preflight, explicit Submit, URL Run restore, polling, status/error lifecycle,
   cancellation and Auth.
2. Extract the feature-owned page shell, fixed-request disclosure, run-status/result area
   and existing `Report.tsx` consumer; do not create a second report implementation.
3. Static composition should consume a validated embedded Run/Report or a fixed Example,
   with no Submit, preflight/refresh, polling or server Run restore and no fake
   PENDING/RUNNING/COMPLETED state.
4. Preserve all six report sections, provenance/coverage, local reader controls, existing
   disclosure and Plotly interactions; do not add Research execution or financial
   recomputation.
5. Add static dependency/browser gates and preserve the same offline Reader behaviour.

D2-E is not implemented here.
