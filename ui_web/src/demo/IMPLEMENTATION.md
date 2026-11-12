# D0 reconciliation and implementation handoff

Execution guidance under [Demo Runtime authority](ARCHITECTURE.md) and
[Example contract](EXAMPLES.md); feature semantics remain with their canonical owners.
D0 is authority-only. The following gates are future implementation acceptance criteria,
not claims that V2 has passed. Stop after D0; D1 is a separate task.

## Inspected baseline

- Branch `feat/github-pages-demo`; clean working tree; HEAD/expected baseline
  `bdda39ca2ab17f1248e78b29502133112da6ce07`.
- Local `develop` was `c68ba9af4194a51ceb3f7e06fd8f445d18d7dab6`; it is an ancestor,
  with zero develop-only and two Demo-only commits (`2c1ed5b`, `bdda39c`). The fixture
  commit `c68ba9a` is already on develop. No later commit implements D0.
- Comparison is of local refs, without fetching, resetting, rebasing or merging.

## Actual composition and extraction boundaries

| Inspected implementation | Actual dependency/behavior | Required shared boundary |
| --- | --- | --- |
| `src/main.tsx` → `app/App.tsx` | AppUiProvider wraps AuthenticationGate; gate mounts shell only after `useAuthentication` succeeds | Keep production gate/lifecycle; extract shell presentation and inject content/header actions |
| `app/App.tsx` ApplicationShell | Requires `CurrentUser` and `signOut`; owns username/logout JSX, route selection, direct imports of all six online feature Pages and Daily Landing | Shared layout/menu/breadcrumb/Landing must not import Auth, online Pages or request controllers; production composition supplies them |
| `app/routes.ts` | Seven private `knownPaths`; pathname + history/popstate; navigation drops search when changing page | Share route identities/discovery without browser side effects; preserve production search/Run semantics and separate Demo hash adapter |
| `demo/futures_basis/main.tsx` + `vite.demo.config.ts` | Independent one-page shell/theme, dynamically imported validated fixture, Report error boundary; no router/auth/backend; fixed Pages base | Preserve disclosure/validation/error behavior; replace V2 shell/business layout with canonical shared presentation |
| OptionChainPage → `useOptionChain` | Page calls hook directly; hook combines date-triggered HTTP query, expiry/color/viewport state and projection | Keep production query/cancellation; expose shared feature presentation and applicable local state/projections over validated Example |
| PremiumPlanePage → `usePremiumPlane` | Direct hook; date/price change fetches; hook combines query and local metric/expiry projection; retains raw payload | Separate query from shared controls/table/local projection; fix query in Demo and preserve complete Example payload |
| ResearchWorkspacePage → `useCatalog` | Mount reads capability list; selection reads detail; local selection/localCases and CapabilityDetails JSX live in Page | Share overview/details; production GET controller and static descriptor/local selection controller are separate |
| ResearchExplorerPage → `useExplorer` | Mount list GET; cursor/selection drives lazy manifest/analysis/View GETs and retry; Page owns Facts, AnalysisDetails and View presentation | Extract shared reader composition; Demo uses embedded records or honest empty state without mount GET/Refresh |
| FuturesBasisPage → `useFuturesBasis` + `usePreflight` | Form/admission, preflight, Submit, URL Run restore, polling and Run status cards bound directly to Page | Share title/fixed request/result regions; production owns execution widgets; static controller bypasses no production gates and creates no Run |
| BacktestingPage → `useBacktesting` + `usePreflight` | Four-field form, advisory readiness, Submit, URL restore/status polling/result validation | Same separation; shared request/readout with capability-aware execution area; no fake completed Run |

All six feature `api/` boundaries currently combine runtime schema validation with
`protectedRequest`. Catalog/Explorer schemas are Ajv-based; MO schemas are also Ajv-based
and Premium additionally rejects a successful body with no Points. Research validates
reader data and request/status association; Backtesting validates request agreement and
both V2 Views. Pure validation can be extracted within each owning feature and reused;
importing runtime API functions into static presentation is not an isolation solution.

Directly reusable result presentation includes:

- `features/futures_basis_research/report/Report.tsx`, reader validation/types and
  shared ChartView: already online/offline/Demo shared, with six sections and local
  metric/Slot/time-axis controls. Preserve offline packaging and evidence-mode behavior.
- `features/backtesting/components/Result.tsx`: consumes `BacktestResult` via a type-only
  import; renders Summary, return/drawdown Views, Trades, Rolls, Evidence. The current
  “online evidence summary” sentence needs origin-aware wording for static reuse.
- MO `OptionChainResults`, `OptionChainVisualization`, controls, CopyActions, charts/models;
  Premium `PremiumResults`, `PremiumControls`, CopyActions, models and Inspector. Their
  results need no second financial projection; query controls and origin wording need separation.
- Catalog `CapabilityDetails` and Explorer `AnalysisDetails`/`Facts` are reusable JSX
  currently inside their online Pages; extract within their feature, not into sibling/shared
  business ownership. Explorer's Plotly adaptation must remain within feature/chart boundaries.

## Reconciled authority conflicts

| Previous statement | D0 resolution / canonical owner |
| --- | --- |
| Module directs every public Demo task to one Futures Basis page | Module now routes to Demo Runtime, then Example and V1 fixture contract |
| Application/shell implicitly requires Auth for every composition | Production authentication remains mandatory; anonymous static composition is separate, with shared shell presentation |
| Presentation flow assumes every Page acquires data through online hooks | Explicit composition → production/static controller → same feature presentation; no sibling/shared DTO transfer |
| Workspace says every anonymous deep link uses Auth | Scoped to Production; Demo uses Pages hash navigation and no Auth imports |
| Explorer has no Sidebar leaf | Target shared navigation includes explicit Explorer leaf in both runtimes; implementation deferred to D1 |
| V1 says one page/no router and eventual WP5 main trigger | Historical V1 facts retained; V2 seven-page hash routing and D7 main-release target supersede those plans |
| MO Copy/Export and Premium Inspector require an actual received HTTP body | Production unchanged; validated complete static Example is allowed in Demo with explicit origin labels and unchanged raw/context/CSV formats |
| Feature authorities describe protected queries/Run lifecycle as the entry path | Those clauses apply to production controllers; shared result presentation also consumes validated static Examples, never simulated lifecycle |

Historical `ACCEPTANCE.md` and `DEPLOYMENT_ACCEPTANCE.md` under `futures_basis/` remain
untouched. D0 changes neither Auth/HTTP contracts, generated artifacts nor workflow triggers.

## Bounded implementation work

D1–D6 below are a bounded implementation sequence; they grant no permission to alter
producer semantics or implement future financial features. Read each owning local policy
before code work. If the actual next task chooses a different package split, retain every
boundary and gate here.

| Package | Allowed scope | Completion evidence |
| --- | --- | --- |
| D1 Shared Application Shell | `src/app/` shell/composition/routes, public feature entry wiring, existing AppUiProvider/theme consumption; Demo shell composition as needed | Shared shell in Production and a static shell harness; all seven route identities and Explorer menu leaf; production regression and static isolation gates below |
| D2 Shared Feature Presentation | Six feature Page/hooks/components/model boundaries, pure validators and public presentation exports; shared infrastructure only where domain-neutral | Both controllers compose the same feature JSX; production query/Run/auth behavior unchanged; no copied Demo page or financial projection |
| D3 Static Examples | Demo manifests/assets/loaders; producer-backed fixture generation tooling under owning-module policy and root Python environment | Required Example coverage/windows, formal validation and deterministic reproduction; disclosure and public-data review; no hand-edited outputs |
| D4 Full Static Composition | Demo entry/static controllers, hash adapter/base config, fixed query/capability wiring and local state | Seven actual shared business surfaces, both overviews, anonymous reload/navigation, fixed parameters, no execution actions/network |
| D5 Automated Compatibility Gates | `ui_web/scripts`, feature/fixture tests, npm scripts and CI validation as required | Route omission, invalid fixture/profile/request/View and contract drift fail; production regression and browser isolation pass |
| D6 Integration/Acceptance | Runtime wiring, presentation-origin wording, browser scripts and acceptance records needed to close observed gaps | Desktop/narrow navigation/readers/interactions, local Copy/Export, negative isolation and offline Reader regression; record actual outcomes and unresolved gaps |

D7 alone changes Pages trigger to `main` and completes release automation. D0 implements
none of these packages. D1–D6 cannot modify backend financial semantics, producer result
contracts, W2 strategy/Core models, business module dependency permissions, Auth security,
HTTP routes/DTOs, root runtime ownership or generated schemas merely for Demo convenience.
Necessary producer fixture tooling is not a second business implementation. A genuine
contract gap requires explicit reconciliation at its canonical owner before implementation.

## D1 ready-for-implementation handoff

D1 is ready: no additional financial decision is needed to extract the shell. Keep scope
small; do not simultaneously split all feature Pages or generate new Examples.

1. Extract the current ApplicationShell layout/menu/breadcrumb into a presentation entry
   in `src/app/`. Accept route/navigation, rendered feature content and header identity/actions
   through explicit composition. Keep responsive/collapse state local to the shared shell.
   Extract/reuse Daily Landing rather than copying it. Keep AppUiProvider/theme shared.
2. Leave `App.tsx` as production composition: AuthenticationGate/useAuthentication and
   protected feature selection supply the shell. No fake user for Demo, no weakening of
   checking/logout/401 unmount or request-boundary installation/closure.
3. Expose one side-effect-free canonical route inventory from `routes.ts` or a nearby
   app-owned module. Keep production pathname adapter and add the static hash adapter at
   the appropriate composition boundary. Navigation and breadcrumbs receive correct hrefs
   for both runtimes. Add Explorer as a Research leaf and remove its no-leaf workaround.
4. Prove static shell composition with shared Landing/neutral test content; D1 need not
   mount any of the current online feature Pages or claim full V2 product coverage.
   V1 may remain the shipped entry until later packages complete. A test harness is not
   a second Demo page or proof that D4 has finished.

Key existing files: `src/app/App.tsx`, `src/app/routes.ts`, `src/app/AppUiProvider.tsx`,
`src/app/auth/useAuthentication.ts`, `src/shared/ui/theme.ts`, `src/demo/futures_basis/main.tsx`,
`vite.demo.config.ts`, `tsconfig.demo.json`, `src/app/App.test.tsx` and existing browser scripts.
Exact new component/prop filenames remain implementation choices.

Required dependency direction:

```text
Production entry → AuthenticationGate + production route/controller composition
                                      ↓
                              Shared Shell → injected feature content
                                      ↑
Static entry → hash route + Example composition
```

Shared Shell imports neither Auth nor feature request controllers. Features do not depend
on `demo/`, Auth or application route implementations. Demo composes feature public
presentation entries; DTO/validator/projection ownership stays within the owning feature.
No generic feature runtime, registry or plugin/DI framework is needed.

**Production Regression Gate:** after D1, run the existing module contract/test/build/lint
checks and `test:auth-browser`; cover route selection, collapsed navigation, new Explorer
leaf, breadcrumb and deep-link Back/Forward. Verify one `/auth/me` per mounted lifecycle,
no business mount while checking, login/deep-link behavior, 401 including late responses,
logout pending/failure/success and stale-result isolation. Feature Run identity/polling
and offline Reader semantics must not change. Broaden feature browser checks only if
D1 actually affects their behavior; later controller extractions require relevant gates.

**Static Runtime Isolation Gate:** build/import the shared shell in a Demo composition
without Production App/Auth, business API transport or query/Run/preflight hooks in its
transitive runtime graph (include dynamically reachable imports; generated type-only
imports are allowed). Serve only static files under the Pages base. Record all browser
requests during initial load, route navigation, reload/history and shell interactions;
only bundled static assets may load, with zero Auth/API/provider/network execution calls.
Route/href assertions must prove that shell links stay under the Pages base. A disabled
button test alone fails this gate. In D1 this gate proves shell isolation only; D4/D6 must
repeat it across actual seven-page content, fixed controls, keyboard submits and all local
interactions.

## Stable command capabilities

Existing `demo:dev`, `demo:build`, `demo:preview`, `test:demo-browser` remain the command
names; evolve their implementation to V2 without a second long-term script family.
Plan `demo:check` for route coverage, Example validation and static dependency checks,
and `demo:fixtures:update` for explicit deterministic producer generation. These two
commands do not exist at D0. `demo:fixtures:update` may delegate to root Poetry; release
`demo:build` must remain npm-only and consume committed Examples. `contract:check` remains
the independent all-product freshness check, not silently replaced by Demo validation.
Browser acceptance uses the existing Playwright stack and must exercise the built static
artifact. No D0 npm, dependency, workflow or business-test changes are required.

## Remaining implementation risks and D0 verification

The current Shell still imports all online Pages; extracting JSX alone can accidentally
retain Auth/transport through barrels or runtime imports. MO local state is private inside
combined query hooks; Catalog/Explorer reader JSX lives inside querying Pages. Pure schema
validation is currently coupled to transport. These require dependency and behavior checks,
not only component snapshots. Hash routes also compete with the V1 report disclosure/section
anchors. New target-window Examples, all-page coverage checks and V2 browser evidence do
not yet exist. The current feature-branch deployment trigger remains active until D7.
These are bounded implementation risks; none blocks D1 shell extraction.

D0 verification is documentation-scoped: reviewed the complete changed Markdown content
and diff, checked all 142 local Markdown links across the 17 changed/new files (including
heading anchors), and ran `git diff --check`. No repository Markdown-specific check command
was found in the existing npm scripts, Python tooling or workflows. No business code,
dependencies, generated contract, workflow or historical acceptance record changed;
production/fixture/browser suites were not rerun for this authority-only package.

## D1 shell implementation boundary

D1 extracts `app/ApplicationShell.tsx`, `app/DailyDataLanding.tsx` and pure
`app/routeInventory.ts`. Production `App.tsx` retains Auth and online Page composition;
`app/routes.ts` retains the pathname/history adapter and server query behavior.
`demo/shell/` is a verification harness using the same Shell/theme/Landing and an
independent hash adapter. All other content is explicitly neutral verification content,
not business Presentation or V2 page readiness. Hash route queries, including server
`run_id`, normalize away; report section scrolling remains D2/D4 work and must not
replace a route hash.

The harness uses `vite.shell.config.ts`, inheriting the V1 Vite settings with a separate
entry/output. Its build rejects nonliteral dynamic imports in project code and checks
all loaded project modules and their static/dynamic edges before tree shaking against
an explicit shell-only allowlist. The emitted dependency evidence and real static-file
browser checks are D1 shell isolation evidence only. `demo:build`, V1 fixtures and Pages
workflow remain unchanged. Harness commands: `test:static-shell` (typecheck/build/import
graph) and `test:static-shell-browser` (build plus Chromium against static files).

D1 implementation results and remaining handoff: [Shell acceptance](shell/ACCEPTANCE.md).

## D2-A Option Chain implementation handoff

Option Chain now exposes its feature-owned `presentation.ts` entry: shared page layout,
local `useOptionChainPresentation(validatedResult)` and pure `validateOptionChain`.
Production still composes its own request/cancellation/stale-response controller;
static composition supplies fixed query identity, disclosure and a `ready` result without
loading that controller. The test-only static harness uses existing regression data,
not the D3 Example target, and does not change the V1 release entry or D1 shell harness.
Implementation and actual verification: [D2-A acceptance](../features/mo_option_chain/testing/ACCEPTANCE.md).

D2-B should apply the same feature-local split to Premium: preserve its full raw payload
and existing nonempty-Points validation, separate request lifecycle from metric/expiry
presentation state, and expose a transport-free presentation entry. Reuse its existing
serializers/Inspector and keep source disclosure adjacent to them. Do not import Option
Chain state/DTOs or introduce a generic feature runtime. D2-B, official Examples and full
static composition remain separate work.
