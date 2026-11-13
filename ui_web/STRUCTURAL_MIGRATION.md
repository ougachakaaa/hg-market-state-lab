# Structural consolidation — WP0 audit and migration

## Baseline and status

Audited 2026-11-13 at `4872508fb7b7f47b2d8f8977942246a3068c0e2c` on branch
`chore/ui-web-structural-consolidation`, created directly from that commit. At audit time local
`develop`, `main` and HEAD matched this baseline; this does not assert remote freshness or live Pages
state. Worktree was clean. [Directory ownership](STRUCTURE.md) is the target contract; this document
owns the transition and executable work-package gates. WP0 performs no runtime/configuration change,
file movement, deletion, deployment, permission change or data generation.

## Findings and priorities

| Priority | Observed baseline | Consequence |
| --- | --- | --- |
| P0 | `demo:dev/build/preview` use `vite.demo.config.ts`, rooted at `src/demo/futures_basis`; `test:demo-browser` uses `futures_basis_demo_browser.mjs` | Default Demo is V1, not the current seven-page public composition |
| P0 | `build_private_demo.mjs` invokes four Python verify/replay operations before Vite, using `.venv/bin/python` | Violates target build boundary and embeds a Unix-only runtime path; move verification/generation out of build |
| P0 | Pages workflow extracts V1 archive on every release and restores it after failed online acceptance | V1 archive, inventory and verification scripts have active production-path references; retire together at WP4 |
| P1 | `public_asset_safety.mjs` requires the original V1 fixture and Synthetic disclosure in `dist-demo`; compatibility also builds V1 | Replacing runtime without replacing these assertions fails gates or preserves obsolete semantics |
| P1 | Public/private and all specialized TSConfigs extend `tsconfig.demo.json`, which targets V1 | Establish independent target includes before retiring V1 config |
| P1 | Root `tsconfig.app.json` includes all `src`; current Vitest setup is `src/test/setup.ts`; node config includes root Vite config/test | Moving files can silently remove test/type coverage; explicitly check discovery and static entry typing |
| P1 | Eight specialized Vite configs, many scripts and six feature testing/static directories surround shared source | Path updates span config, HTML, imports, browser helpers, isolation allowlists and npm scripts |
| P1 | `dist*` outputs occupy module root; TS build caches use `node_modules/.tmp`; compatibility creates OS-temp builds | Put all build outputs/caches under `.build/` and update every consumer, including safety checks and local deployment |
| P1 | Runtime Authority still describes uncompleted D7/feature-branch publication; actual workflow triggers main and has public admission | Reconcile present state with D7 acceptance; preserve historical records rather than treating old prose as current |
| P1 | Python example generators directly call Snapshot/Backtesting/Research services and HTTP projections | Existing results are not proof of generation through formal HTTP; endpoint feasibility is a WP2 gate |
| P2 | `src/demo/public/examples/package.json` is data, while root package.json owns npm | Name the target Manifest unambiguously; retain one npm project, not a nested package |

### Actual invocation chains

- `.github/workflows/demo-compatibility.yml`: push to feature/develop/main, PR and reusable workflow;
  contract check → frontend tests/build/lint → V1 demo build → static compatibility → public build/browser/
  artifact verification → public safety. Independent Python matrix includes `ui_web/scripts`, plus
  Research's `futures_basis_demo_fixture.py --check`. These are active V1 references.
- `.github/workflows/deploy-demo-pages.yml`: main only; same-revision compatibility → admission status →
  read protected environment → extract/verify/upload V1 rollback → admitted public build/browser/receipt →
  protected deploy → online verification → V1 recovery on failure. Preserve permissions and environment
  checks. WP0 neither pushes main nor runs this workflow.
- `.github/workflows/release-preflight.yml`: PRs targeting develop/main read environment and branch
  policies, upload inspection evidence; no build. Keep inspection independent from Demo implementation.
- `demo:build:private`: explicit external R2/R3/WPA → Python verification/replay → projection/admission →
  virtual private envelope → private entry → shared `StaticWorkspace`. Public build loads tracked package
  and evidence → independent public admission → virtual public envelope → the same workspace. Public
  isolation currently imports `private_demo_isolation.mjs`; shared checks must outlive private entry removal.
- `extract_v1_rollback.mjs` reads tracked `rollback-v1.tar.gz` and `rollback-inventory.json`;
  `verify_v1_rollback.mjs` and `verify_v1_online.mjs` are active workflow consumers. V1 fixture generator
  and `market_research/tests/test_futures_basis_demo_fixture.py` also retain cross-module references.
- Historical browser tests remain runnable npm commands even when absent from CI. Feature testing
  acceptance files cite V1 `test:demo-browser`; those citations are historical evidence, not active runtime
  imports. Preserve their original outcomes and identify superseding coverage.

## Migration matrix

Paths below are relative to `ui_web/` unless explicitly repository-relative. Each row names a complete
file family; [baseline inventory](STRUCTURAL_INVENTORY.md) expands every tracked tooling/config/Demo file
and every npm command. KEEP does not preclude correcting imports after another owner moves.

| Current object | Action / target | WP | Dependencies and deletion/move gate |
| --- | --- | --- | --- |
| `src/app`, feature production code, shared Presentation, generated contracts, formal offline reader | KEEP `src/` | all | Preserve boundaries, types, HTTP contracts and Online behavior; no duplicate JSX/projections |
| Feature unit tests, local Authority, `src/test/setup.ts` | KEEP co-located | 1 | Verify discovery and lifecycle setup after root include changes |
| Six `src/features/*/testing/static` trees | MOVE `tests/static/<feature>/` | 1 | Update HTML/import/config/browser roots and isolation graphs; keep testing Authority with feature |
| `visualization-harness.html`, `src/shared/visualization/FixtureHarness.tsx` | MOVE `tests/visualization/` | 1 | Rewrite harness entry, browser script and Vite harness handling together |
| `src/demo/shell/StaticShellHarness.tsx`, main/index | MOVE `tests/static/shell/` | 1 | Preserve shell regression; shared `hashRoutes.ts` moves with runtime in WP3, not into test-only ownership |
| Root specialized Vite/TSConfigs (shell, option-chain, premium, catalog, explorer, futures-basis, backtesting) | MOVE `tests/config/` | 1 | Fix extends/includes/outDir and npm flags; retain all seven specialized suites |
| Root Online Vite config/test and app/node/root TSConfigs | KEEP; UPDATE paths/output only | 1 | Online `.build/online`; cache `.build/cache`; retain explicit typing/discovery |
| Browser, isolation and acceptance helpers in scripts | MOVE `tests/browser/`, `tests/isolation/`, `tests/fixtures/` | 1 | Move imported helpers together, update Python subprocess paths and CI pytest collection |
| `export_contracts.py`, `contract_types.mjs`, `test_export_contracts.py`, report packager | KEEP general tools; MOVE tool test to `tests/` | 1 | Contract semantics unchanged; package report's generated output under `.build/reports/` |
| `src/demo/static`, shared hash routing; public/private entry/admission | MERGE `demo/runtime/` | 3 | One entry and runtime, shared formal Presentation, preserved static error/disclosure and validation |
| Public `examples/package.json` and evidence | MERGE `demo/bundles/manifest.json`, per-result Bundle files and evidence | 2 | Split existing envelope without editing results; bind exact Bundle hashes; evidence review is separate from Build admission |
| Private Python generators, validators, `private_demo_projection.mjs` | MERGE generation/admission tooling in `demo/build/` | 2 | Explicit formal local HTTP, root Python environment, no business/projection internals; legacy profiles retire only after equivalent checks |
| `build_public_demo.mjs`, `build_private_demo.mjs` | MERGE `demo/build/` | 2–3 | One offline Vite build, no Python/HTTP; preserve failure checks; remove private command after cutover |
| `vite.demo.config.ts`, Demo/private/public TSConfigs | MERGE `demo/build/` config | 2–3 | Separate from V1 includes first; default demo commands select sole runtime after WP3 |
| `static_compatibility`, `private_demo_isolation`, staticPresentationIsolation and negative/data tests | MERGE retained checks in `tests/` and build isolation in `demo/build/` | 1–3 | Reject Online/Auth/business-network imports using actual build graph; replace V1-specific expectations |
| `public_asset_safety` and reviewed payload inventory | MERGE safety checks in build; tests in `tests/` | 2–4 | Preserve secret/exact-byte scans and independent reviewed-payload coverage; remove stale inventory entries only with their payloads |
| `public_release.mjs` | SPLIT by MERGE: input verification in `demo/build/`, release receipt/transfer verification in `deploy/pages/` | 4 | Build must not import deployment code; deployment must not invoke build or generation |
| Public admission status, artifact/Pages-environment checks, public browser online runner | MOVE `deploy/pages/`; reusable browser assertions `tests/browser/` | 4 | Same-SHA verification, protected environment and full inventory survive path change |
| `deploy.ps1`, config template, `publish.py`, README, test_publish.py | KEEP deploy support; MOVE test to `tests/deploy/` | 1,4 | BuildOutput becomes `.build/online`; unit-test local publish without contacting WSL/site |
| `src/demo/futures_basis` runtime, fixture, CSS, archive, inventory | RETIRE executable/payload files | 3–4 | V1 build/tests superseded in WP3; archive removed only with WP4 workflow recovery removal; keep formal historical evidence |
| V1 extraction/verification/online scripts and V1 browser script | RETIRE | 3–4 | Replace effective safety/browser assertions first; zero active workflow/npm/code references |
| Repository Research V1 generator/test | RETIRE Demo-only path or MERGE useful assertions | 4 | Read Research local policy/authority, remove Python CI --check and producer-test references; preserve unrelated report functionality |
| `dist`, `dist-demo`, `dist-demo-shell`, six `dist-*-test`, `dist-ssr`, `dist-demo-public`, caches and generated receipts | MOVE output policy to `.build/online`, `demo`, `tests/<suite>`, `reports`, `cache` | 1–4 | No copying history required; verify producer/consumer paths and ignored status; remove identified stale local outputs in WP4 only |
| Root package/lock, node_modules, lint config | KEEP one project | all | Update scripts/paths without second install boundary or unnecessary dependencies |
| Three repository workflows | KEEP location, UPDATE paths/gates | 1–4 | Permissions/triggers/protection unchanged; no deploying as part of these WPs |

## WP1–WP4 execution and acceptance

Each WP updates narrow Authority first, implements its bounded change, reviews the full diff and
records acceptance before the next starts. WP0 ends with its documentation commit.

### WP1 — placement and generated-output boundary

Move specialized harnesses/configs, test scripts and fixture helpers as mapped above. Keep Online and
feature source ownership. Move current outputs under `.build/` including temporary compatibility
builds and TS caches; add ignored root. Existing V1/public entry identities remain temporarily.
Update all package scripts, relative imports, scanner allowlists, local deployment defaults and CI
collection paths together. Preserve feature static hooks in `src/`: they own Presentation state.

Acceptance: contract:check, complete Vitest, Online build, lint; type/build all seven specialized
entries and their browser suites; static graph/negative checks; Python tooling and deploy unit tests.
Compare discovered suites/entries with baseline inventory. `git status --ignored` proves generated
outputs stay ignored and no build writes new `dist*`/OS-temp/node_modules cache outputs.

### WP2 — single Manifest and explicit generation

Before implementation inspect each feature's published HTTP contract for complete Results and local
auth/run/publication acquisition. Record endpoint/response association for Basis, both MO products,
Backtesting, catalog descriptors and Explorer manifest/analysis/Views. Use formal workflow including
polling only in explicit generation, never browser/build. Missing capabilities block that item and
must be reported; do not design new APIs here. Implement Python explicit capture and one Manifest
with one complete Result per Bundle, exact SHA-256; seven Examples are seven Bundles even when a Result requires multiple HTTP requests.
Private evidence remains external; never copy raw sources or automatically commit generated results.

Acceptance: generate only on explicit invocation against local formal authenticated HTTP; failure
does not publish incomplete Manifest. Offline Node/Vite Bundle admission validates only the Manifest and Bundle SHA-256.
Business DTO/Result validation, static isolation and deployment Artifact Verification are separate;
legacy Publication Rights Gates, Evidence Review and independent review records are not Build prerequisites. Tests reject missing/tampered/traversal/unsupported/mismatched
bundles and dangling Explorer references. Run build with Python unavailable and business network
blocked; it must succeed from admitted existing inputs. No financial/result recomputation.

### WP3 — sole formal Demo runtime

Move shared static workspace/routing into `demo/runtime`, merge admission/loading with retained
validators and origin disclosure. Root demo dev/build/preview commands select this runtime. Remove
V1 runtime and separate Private/Public runtime entries once superseded. Temporary legacy rollback
archive remains solely for WP4 removal; no V1 runtime build remains. Remove compatibility's V1 build
and replace safety checks that require Synthetic fixture presence. Keep effective historical assertions
as clearly test-only fixtures where needed, never a second formal Demo.

Acceptance: seven routes match canonical route inventory, base/hash reload/back/forward/unknown route,
desktop/mobile, full Basis sections, charts/local selectors/Copy/Export and static validation errors.
No Auth/API/Provider/browser execution; actual static build graph excludes Online controllers. All
Online regressions, contract check/build/lint pass. Admission/negative tests continue to reject restricted
or unreviewed input. No runtime import points to retired entries.

### WP4 — deployment separation and hard retirement

Separate build input validation from deployment receipt/transfer verification. Workflows consume
`.build/demo` verified bytes, with no regeneration or deployment-side rebuild. Preserve same-SHA gates,
permissions, environment inspection, exact assets and post-deploy checks. Remove V1 automatic recovery
steps and support files. Failure stops with failed acceptance; do not add previous-generation rollback
or build-history retention. Ordinary current-run transfer/diagnostic artifacts are not a retained Demo
generation. Preserve local Online publish behavior independently.

Read Research policy before removing its Demo-only generator/tests. Reconcile payload inventories,
CI matrix paths, documentation and npm scripts. Enumerate and resolve actual local build roots inside
ui_web before cleanup; delete only identified derived outputs, never source/formal evidence/data.

Acceptance: zero active V1/private-entry references (historical evidence explicitly exempt), all root
checks and relevant producer/consumer tests pass; workflow inspection verifies unchanged triggers,
permissions and protected environment. Run local artifact tamper/transfer verification and publish
unit tests; no main merge, workflow dispatch, protected-settings update or live publish. Report exact
deleted paths and distinguish local verification from unperformed live acceptance.

## Authority reconciliation register

Current live contracts govern until the assigned WP implements replacement. Target structure and
hard-cutover decision are authoritative for this migration; historical acceptance is never rewritten
to claim new success. Documentation moves repair relative links and inbound navigation atomically.

| Owner / affected content | Required disposition |
| --- | --- |
| Module ARCHITECTURE, AGENTS | WP0 route structure/audit; WP3 replace Demo entry links and remove stale D7 status descriptions |
| presentation-architecture, application, workspace, contracts | WP1 harness/config references; WP3 new Demo links and single runtime wording; retain Online/feature invariants |
| Demo ARCHITECTURE | WP0 mark stale current-status statements; WP3 move to `demo/ARCHITECTURE.md`, remove permanent V1/private branches; WP4 reconcile release/recovery wording |
| EXAMPLES | WP2 move to `demo/EXAMPLES.md`, replace envelope/multiple indices/direct producer generation with Manifest/Bundle/local HTTP; keep targets and result semantics |
| AUTHENTICITY | WP0 distinguish current user-directed decision from historical gates; WP2 move to `demo/AUTHENTICITY.md`, preserve distribution decision/provenance/security; no new rights claim |
| PRIVATE_BUILD, PUBLIC_BUILD | WP2–3 merge current build contract into `demo/build/ARCHITECTURE.md`; retire competing private/public build authorities after replacing checks |
| RELEASE | WP4 move to `deploy/pages/ARCHITECTURE.md`; replace V1 recovery and previous-generation retention with hard cutover; retain admission and permission constraints |
| IMPLEMENTATION | WP3 retire live D/R/WP-A–C handoff sections superseded by this migration; preserve original as historical evidence with explicit scope note |
| D7_READINESS | WP3 retire current-status role in favor of actual WP acceptance; preserve historical findings |
| R1_FEASIBILITY, R2/R3, WP_A/B/C, INTEGRATION, D7_RELEASE acceptance; shell ACCEPTANCE | RETIRE superseded Demo documents after extracting valid Authority; preserve history in Git, not demo/history; preserve independent business evidence |
| futures_basis ARCHITECTURE/README/ACCEPTANCE/DEPLOYMENT_ACCEPTANCE | WP3 retire active V1 contracts; preserve history in Git after extracting valid Authority; WP4 remove executable archive references from current owners |
| public/examples README and evidence/review | WP2 reconcile Manifest paths separately from evidence review, keep Authenticity sole publication-decision owner |
| Six feature testing ACCEPTANCE; feature architecture/static references; offline reader authority | WP1 update active paths only; WP3 annotate superseding Demo coverage; preserve old command results |
| deploy README/config documentation | WP1 `.build/online`; WP4 artifact-only Pages boundary, no permission/WSL infrastructure changes |
| Root DEVELOPMENT and navigation; Research fixture-related Authority | Change only discovered affected references in assigned WP; enter Research local policy before producer retirement |

## Blockers, limitations and verification

WP0 has no blocker to documenting the target. Formal HTTP coverage and generation credentials/data
availability require WP2 feasibility checks; neither prior private success nor a committed public
package proves those checks. Existing payload inventory binds exact files: renaming/splitting requires
intentional review updates, not disabling safety. Removing private tooling must retain its useful
negative checks. Hard cutover removes automatic recovery; an online acceptance failure remains a
failed release and may leave the newly deployed site present. This is the selected policy, not a
promise of uninterrupted availability.

WP0 validation: check local Markdown file/anchor navigation for every new/modified Authority;
check complete inventory coverage against baseline tracked files and npm scripts; review diff for
documentation-only changes. Module default checks are contract:check, test, build and lint, run from
ui_web; report environment/test failures explicitly without changing runtime to fix unrelated issues.
No remote freshness, live deployment or external/private data validation is claimed.

### WP0 execution results — 2026-11-13

| Check | Outcome |
| --- | --- |
| Baseline inventory coverage | PASS: 174 explicitly inventoried tracked files and all 40 npm commands; remaining src ownership covered by KEEP family |
| Local Markdown navigation | PASS: 63 file/anchor references across all six new/modified documents, no missing target |
| `npm run contract:check` | PASS: all seven OpenAPI and generated TypeScript products current |
| `npm run build` | PASS: existing Online build; existing large-chunk warning remains; output uses current ignored dist, not the unimplemented target |
| `npm run lint` | PASS |
| `npm run test` | INCOMPLETE: Vitest 5.0.1 printed RUN only; no suite/assertion result after approximately three minutes. Terminated this invocation and its worker; no test pass is claimed and no runtime/config fix attempted |
| Diff and scope | PASS: Markdown-only changes; no implementation/config/workflow changes, historical data deletion or deployment |

The incomplete full-suite run is a verification limitation for WP0 and must be resolved/rechecked
before WP1 implementation acceptance. Contract, build and lint success does not substitute for tests.
