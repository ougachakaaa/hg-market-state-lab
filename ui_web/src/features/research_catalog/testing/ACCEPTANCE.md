# D2-C — Shared Research Overview presentation acceptance

Repository: `ougachakaaa/hg-market-state-lab`; branch `feat/github-pages-demo`.
Inspected baseline: `0b2a3a235ca60819a925c7b7219caff9bf5a495c` (D0–D2-B present).
The local branch ref was stale; the remote branch was fetched and the local branch reset
to that exact commit before implementation. The working tree was clean. This task
implements D2-C only; the static harness is not a D3 Example, D4 composition or D2-D.

## Implementation and files

- Added `presentation.ts` as Catalog's transport-free public entry. It exports the shared
  `ResearchOverviewPresentation`, `useStaticCatalog`, pure validators and generated
  contract types.
- Added `page/ResearchOverviewPresentation.tsx` as the single Research Overview page JSX:
  header, descriptive topic card, online Capability list, local cases, selected details,
  Explorer card and Futures Basis action. `page/ResearchWorkspacePage.tsx` is now a thin
  Production composition root.
- Added `components/CapabilityDetails.tsx` and `components/LocalCaseDetails.tsx`. Existing
  descriptor fields, raw JSON, local-case facts and access text are preserved. Static mode
  adds origin/access disclosure outside the serialized descriptor.
- Added `api/validateCatalog.ts` with generated-schema matching for both Capability success
  responses and the pure `validateCapabilityList`, `validateCapabilityDetail` and
  `validateEmbeddedCatalog` functions. `api/catalog.ts` retains only protected transport
  and HTTP error mapping.
- Updated `hooks/useCatalog.ts` to own explicit `{ kind: 'online' | 'local', id }`
  selection, independent list/detail loading/error state, manual retry, AbortController
  plus request-token stale isolation, and local-selection cancellation. No detail GET is
  issued for a local case.
- Added `static/useStaticCatalog.ts`. It validates the embedded list/details once, rejects
  the whole catalog on invalid payload or identity association, selects locally by ID and
  reports a listed capability with no bundled detail as an explicit missing state.
- Added `model/catalogPresentation.ts` for the shared controller/state/mode/navigation
  types and static disclosure text. `localCases.ts` remains the only local-case registry
  and was not changed.
- Added `testing/catalogFixture.ts` from the existing `api/catalog.fixture.json`; it is
  explicitly test-only, not a D3 Example and not live discovery.
- Added `testing/static/{index.html,main.tsx}`, `vite.catalog.config.ts`,
  `tsconfig.catalog.json`, `scripts/catalog_static_browser.mjs`,
  `scripts/catalog_static_isolation.test.ts` and npm commands. The harness uses the D1
  hash adapter (`useHashRoute`) for both existing navigation callbacks.
- Extended the shared build-time isolation utility with an explicit composition-module
  allowlist. Catalog allows only the pure `routeInventory` and `hashRoutes` modules in
  addition to shared UI/feature presentation; it still rejects Auth, HTTP, Production
  controllers and sibling features.
- Updated Catalog authority, Demo implementation handoff and root `.gitignore`. No backend,
  producer, OpenAPI, generated artifact, workflow, Explorer, Futures Basis or Backtesting
  change.
- Test-only cross-platform correction: the existing D2-A/D2-B browser scripts normalize
  Windows clipboard CRLF when comparing clipboard text with DOM/download text. Product
  payloads and assertions are unchanged.

## Validation and identity boundary

`validateCapabilityList` matches the generated 200 response for `GET /research/capabilities`;
`validateCapabilityDetail` matches the generated 200 response for
`GET /research/capabilities/{id}`. Both reuse the committed OpenAPI schema and generated
`CapabilityDescription` type; no second DTO or handwritten schema exists. Production uses
the same matcher for success responses and keeps its existing `network`,
`invalid_response`, `unavailable` and `not_found` mapping.

`validateEmbeddedCatalog({ list, details })` requires a structurally valid list and every
bundled detail to be structurally valid. It rejects duplicate list IDs, duplicate detail
IDs and a detail whose ID is not in the list. A listed capability without a detail is
accepted only so the UI can show an explicit missing-detail state; it never becomes a
successful detail result. Inconsistent or invalid embedded data makes the catalog
`invalid`, so no partial payload is presented as ready.

## Static consumption and origin semantics

Static composition calls `useStaticCatalog(embeddedCatalog)` and passes the resulting
controller plus `mode="static"` to the same `ResearchOverviewPresentation` used by
Production. Selection is local; there is no `fetch`, Promise-shaped transport, fake HTTP
200 or retry path. The harness uses `useHashRoute().navigate` for Explorer and Futures Basis;
Production continues to pass its History API `navigate` callbacks from `App.tsx`.

The default static disclosure is `Embedded Capability Example · 静态能力描述，不代表当前服务状态`;
the test harness overrides it with an explicit `静态测试数据 · 非正式 D3 Capability Example ·
非在线发现` label. Tags switch from `在线描述发现` to `嵌入能力示例`, and access text switches
from authenticated HTTP discovery to static embedded description. Published `status` and
`live_readiness` values are displayed unchanged and are never promoted to availability.
Static detail access text identifies authenticated HTTP and Python execution as formal
product instructions rather than Demo operations. Static local-case details add the same
origin clarification without changing `localCases` business facts.

The legal static empty list states that the embedded example is empty and does not imply
that the online service has no published capabilities. Static request failure/retry is not
simulated. Production keeps its existing loading, empty, list error/retry, detail
error/retry and selection-cancellation presentation.

## Verification

Environment: Windows, Node 22.23.2, npm 11.12.1, Poetry 2.3.2, system Google Chrome
157.0.8103.39 via `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH`. Commands ran from `ui_web/`.
Browser evidence is in printed system temporary directories; no evidence log or build
artifact is committed.

| Command | Result |
| --- | --- |
| `npm run test` (default; isolated retry) | **FAIL** — 3 files / 6 existing MO tests reached the 5-second budget; 496 of 502 passed. All six were `Test timed out in 5000ms`, none in Catalog |
| `npm run test -- --maxWorkers=2 --testTimeout=15000` | **PASS** — 61 files, 502 tests |
| `npm run test -- src/features/research_catalog scripts/catalog_static_isolation.test.ts --maxWorkers=1 --testTimeout=30000` | **PASS** — 4 files, 29 tests (23 Catalog feature tests + 6 negative build-isolation tests) |
| `npm run test:catalog-static` | **PASS** — typecheck, Vite build and dependency gate |
| `npm run test:catalog-static-browser` | **PASS** — list/name/status/readiness, matching detail, raw descriptor, local selection, both hash-navigation callbacks, Back, reload and zero non-static requests |
| `npm run build` | **PASS** — Production TypeScript/Vite artifact |
| `npm run lint` | **PASS** — 0 warnings, 0 errors |
| `npm run contract:check` | **PASS** — all consumed OpenAPI/generated artifacts current; no regeneration |
| `npm run test:auth-browser` | **PASS** (exit 0) — real registration/CLI approval/login, `/research/capabilities` reads, seven routes, MO products, reload/logout, Cookie/storage boundaries; required a test-run-only Windows process-tree cleanup hook for orphaned uvicorn pipes |
| `npm run test:research-browser` | **BLOCKED before browser** — fixture generation raises `PublicationUnavailable: publication storage requires POSIX descriptor-relative filesystem operations` on Windows. No D2-C code path was reached; this is the producer's existing platform capability guard |
| `npm run demo:build` | **PASS** — V1 release entry unchanged |
| `npm run test:demo-browser` | **PASS** — V1 six-section reader, Plotly, disclosure, reload, invalid fixture and zero Auth/API |
| `npm run test:static-shell-browser` | **PASS** — D1 shell, seven hashes, history/reload, Explorer leaf and zero non-static requests |
| `npm run test:option-chain-static-browser` | **PASS** — D2-A behavior/isolation; test script only normalized Windows clipboard CRLF |
| `npm run test:premium-static-browser` | **PASS** — D2-B behavior/isolation; test script only normalized Windows clipboard CRLF |
| `git diff --check` | **PASS** |

The default Vitest run was executed first. Its failures are the known resource-sensitive
five-second interaction timeout in existing MO tests, not Catalog assertions. Repository
test configuration and global timeout were not changed. The complete suite passes under
the explicitly adjusted two-worker/15-second invocation.

The static build graph contains the shared presentation, validator, static controller,
`localCases`, OpenAPI schema, shared UI and the D1 hash adapter. It contains no
`shared/http`, `app/auth`, Production `catalog.ts`, `useCatalog`, `ResearchWorkspacePage`,
Research Explorer or Research execution modules. The real built artifact made only static
document/script/stylesheet requests, with empty cookies and zero Auth/API/provider errors.
The negative build tests inject Auth, Production controller, Production HTTP client,
sibling Explorer runtime, indirect dynamic HTTP and an unresolved dynamic import; each
actual build fails for the expected isolation reason.

## Remaining risks and D2-D handoff

- D2-C validates embedded Capability descriptors only. Official D3 capability Examples,
  D4 application composition, Pages release switching and the seven-page V2 runtime remain
  outstanding.
- The valid embedded catalog is exercised in a real browser. Legal empty, invalid
  list/detail and ID-association cases are covered by feature-level static-controller/
  validator tests; a browser fixture-variant framework was deliberately not introduced.
- The Production research browser suite cannot run on this Windows host because the
  existing Publication Store requires POSIX descriptor-relative I/O. Catalog unit tests,
  the Production build and the real Auth browser catalog reads cover the changed controller
  and presentation; this platform gap is not D2-C readiness evidence.
- D2-D should apply the same split to Research Explorer: keep mount/list GET,
  cursor/manifest/analysis/View lazy GET, retry, cancellation and Auth in its Production
  controller; extract the feature-owned Reader/Facts/AnalysisDetails/View composition and
  pure generated-contract validators; let static composition consume a validated embedded
  Publication set or the formal explicit empty state with local cursor/selection and no
  mount GET, Refresh or request retry. Preserve published ordering, null/zero/status/
  provenance and Plotly View semantics; do not add Research execution or reuse Catalog
  DTOs/state. Do not implement D2-D here.
