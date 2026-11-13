# WP-B private seven-page acceptance — 2026-11-13

Required baseline / initial clean HEAD:
`475dde8783a4b1da341c9a859240c6b23eee4190`, branch `feat/github-pages-demo`.
This delivery combines D3-R6 technical admission, D4 composition and private browser
acceptance. WP-B local technical/browser scope is **PASS**; whole-repository
regression remains **FAIL** as detailed below. Publication Rights remain **BLOCKED** for every real-market output and
Catalog metadata. No public release, push, merge, workflow edit or WP-C execution
is part of this delivery.

## Seven-route acceptance

Every row uses ApplicationShell, AppUiProvider, workspaceRoutes and useHashRoute.
The seven business surfaces reuse their existing formal Presentation; only private
composition and Example admission are new. `/research` is the default.

| Hash route | Formal source / shared surface | Private acceptance |
| --- | --- | --- |
| `/research` | WP-A `research/catalog.json`; ResearchOverviewPresentation | PASS — Genuine Capability/status/not_probed; local Detail |
| `/research/futures-basis` | R3 `delivery/report-data.json`; FuturesBasisPresentation / Report | PASS — Exact IM request; 206 sessions; all six sections, Quantile/Histograms, history, Term Structure, persistence and Evidence |
| `/research/publications` | WP-A `research/embedded-publications.json`; ResearchExplorerPresentation | PASS — Real Publication, four Analyses, all six ChartViews; local selection/pagination |
| `/data` | Shared DailyDataLanding | PASS — Existing descriptions and product navigation; no financial fixture |
| `/data/mo-option-chain` | R2 `chain/response.json`; OptionChainPresentation | PASS — 312 contracts / six Expiries / four IM references / two null; local expiry/viewport, hover and full Copy/Export |
| `/data/mo-premium-plane` | R2 `premium/response.json`; PremiumPlanePresentation | PASS — 312 genuine Points / all 16 coordinates; local side/four metrics/expiry, sparse table, Inspector and full Copy/Export |
| `/backtesting` | WP-A two `w2/*-request.json` / `*-result.json`; BacktestingPresentation / Result | PASS — M1/Q1 local switching; Summary, returns, drawdown, benchmark, Trades/Rolls, Evidence and both V2 Views |

The accepted external package locations remain in the existing local R2/R3/WP-A
handoffs. The final build and browser receipts are located by the local
`WP-B-HANDOFF.md` beside them. No personal path, real Result JSON, screenshot,
Source Evidence or financial value is committed here.

## Reproduction

Run npm commands in `ui_web`. Explicitly assign the existing handoff locations to
shell variables; these are command arguments, never Vite environment inputs.
`PRIVATE_R3` denotes the package containing `delivery/`. Each output must be a new
absolute external directory under an existing external parent.

```bash
npm run demo:build:private -- \
  --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" \
  --output "$NEW_PRIVATE_BUILD"

npm run test:private-demo-data -- \
  --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" \
  --output "$NEW_PRIVATE_NEGATIVES"

npm run test:private-demo-browser -- \
  --build "$NEW_PRIVATE_BUILD" --evidence "$NEW_PRIVATE_BROWSER" \
  --r2 "$PRIVATE_R2" --wpa "$PRIVATE_WPA"
```

Serve only `$NEW_PRIVATE_BUILD/site` on loopback to review interactively; open
`/#/research`. The browser command serves those actual files automatically and
closes its loopback server afterward. It does not use a backend or test fixture.
The build parent contains the private admission receipt; screenshots and browser
logs remain in the separately specified acceptance directory.

## Admission, provenance and isolation

[Private build authority](PRIVATE_BUILD.md) owns the boundary. The builder runs the
existing R2 complete verifier, R3 formal Verify and Replay, and WP-A complete
verifier (including guarded W2 reproduction, formal Python Publication Reader,
safe export equivalence and genuine Capability facade). No acquisition operation
is callable. Formal offline replay verifies retained inputs before bundling; the
Vite build itself performs no financial calculation or market acquisition.

All package profiles/revisions/origins/rights, sealed inventories and explicit
R2/R3 links must agree. Selected projections are rechecked against retained result
digests/inventories. Browser admission repeats SHA-256, complete Example Identity,
fixed request, coverage and all existing Feature validators. R3/W2 input
fingerprints and Publication Source SHA agree with their verified identities.
Missing or invalid data fails closed, before business mounting, with Static Error;
there is no previous-result, Synthetic, Provider or HTTP fallback.

The browser receives exactly seven complete presentation projections: Catalog,
Basis reader, safe Publication export, Chain, Premium, M1 and Q1. It receives no
DataLake, Raw Capture, original Publication Source or source-evidence copy. The
8,297,891-byte Publication Source remains private. Its safe export was verified by
the formal Python Reader; this is **not** a claim of HTTP Analysis/View 200.
The online 4 MiB budget and permissions are unchanged.

```text
Explicit external R2 / R3 / WP-A
  → formal offline verification / replay
  → inventory-bound safe Result projections
  → virtual private Vite module + independent external output
  → browser digest / identity / Feature validation
  → shared Shell + Feature Presentation + local state
  → shared Ant Design theme / Plotly / local Clipboard and downloads
```

The build graph excludes Auth gate/client, protected HTTP, Production Page/Query/
Run controllers, Preflight, Submit, polling, Provider and test fixtures. The
emitted `presentation-dependencies.json` lists actual repository-relative runtime
modules, including otherwise tree-shaken imports. Package and output paths are
resolved against every Git worktree and repository symlink aliases; inputs/output
cannot overlap. New output only; no retained data or cache was deleted.

`npm run demo:build`, V1 fixture, `vite.demo.config.ts`, `dist-demo` and Pages upload
remain unchanged. No private environment-variable loader or CI input exists.
Private output is never a Pages input. Default-public artifact scans and Git diff
review independently check that no private Result/Publication identity, fingerprint,
Source payload or personal path entered public assets or tracked files.

## Origin and local interactions

Verified UI metadata separates static delivery, real-market source, historical
embedded formal execution and private / public-BLOCKED rights. Catalog uses the
formal metadata facade rather than claiming historical quotations. Market pages
retain Tushare, exact day/window, actual observations, formal Producer and research
limitations. Basis and Backtesting propagate disclosure into shared Evidence;
Synthetic defaults and Production/Offline evidence remain separately tested.
Disclosure does not modify any business DTO, Raw JSON, Context V1 or CSV.

Actual browser Copy Raw/Context and downloaded Context JSON match the complete
formal R2 payload after local filters. Each CSV retains 312 data rows; Premium
retains all 16 metric leaves and genuine sparse semantics. Hidden expiries and
out-of-viewport contracts remain in exports. Inspector repeats the source note.
No Backtesting export or execution lifecycle was invented.

## Browser and technical gates

Final production Chromium **156.0.8078.4** recorded seven routes, ten acceptance
groups, nine static document/script/stylesheet requests, **zero errors and zero
warnings**. There were no Auth/API/Provider requests or cookies.

The browser runner compares coverage to the canonical route inventory; future
unhandled routes fail acceptance. Actual Chromium checks all seven pages at
1440px, 1024px and 390px, shared breadcrumb/sidebar links, hash navigation,
Back/Forward, deep reload, route-safe report section jumps, Catalog Detail, both
MO products, all Explorer details and both W2 strategies. Genuine hover and
Plotly drag Zoom / Pan / Reset are exercised. Only local static asset GETs are
permitted; Auth/API/Provider/XHR/fetch requests fail the gate. A response-only
corrupted Result digest must display Static Error without mounting a business
page or falling back. No build file is altered by this negative browser probe.

The known Ant Design List deprecation diagnostic is retained as a warning, even
though Ant Design writes it through console.error. Every other console error,
unhandled page error and unsuccessful/forbidden request fails acceptance. No
warning was suppressed in the application or dependency. An intermediate development-JSX build was rejected by the final safety audit
because SSR left Vite in development mode and JSX source filenames exposed local
source paths. The builder now explicitly sets production compilation after SSR
and scans every emitted asset before a PASS receipt; the delivered production
artifact is independently rescanned. This fix also removes development diagnostics
from the final production bundle. Earlier private diagnostic artifacts were never
published. Build chunk-size warnings
remain informational; no library, financial method or timeout was changed.

| Gate | Result |
| --- | --- |
| R2 full private verifier / both formal Product validators | PASS |
| R3 formal Verify / Replay / Embedded Report validation | PASS |
| WP-A full verifier / guarded M1 and Q1 reproduction | PASS |
| Safe Publication export / Catalog / Embedded validators | PASS |
| Private identity, digest, fingerprint and fail-closed negative probes | PASS: 19 rejection probes |
| Existing six Feature suites + private isolation, one worker | PASS: 338 tests / 50 files |
| Shared reader/origin and private boundary focused rerun | PASS: 19 tests / 3 files |
| Existing static Shell / six Feature dependency isolation | PASS: 37 tests / 7 files |
| `npm run contract:check` | PASS; seven generated boundaries current |
| `npm run build` / `npm run lint` | PASS / PASS |
| `npm run demo:build` | PASS; V1 behavior preserved |
| Private build / actual seven-page browser | PASS / PASS; all seven routes, 21 viewport screenshots and corrupt-digest browser rejection |
| `git diff --check` | PASS |
| Whole default Vitest regression | FAIL: final 569 passed / 15 default-timeout failures in 75 files |
| Historical Python V1 fixture check | FAIL: same 2 drift failures, 3 passed |
| Public market/Catalog rights / public admission | BLOCKED / BLOCKED |

## Regression and WP-C readiness

The first full default Vitest run returned **573 passed / 7 failed** in 74 files;
all seven failures were default 5000ms timeouts in MO and Explorer tests. The final
default run (including the four new tests) returned **569 passed / 15 failed** in 75 files; every failure was a 5000ms timeout in App, Backtesting, MO
or Explorer tests. None of the new tests failed. The
six-Feature single-worker run passed all 338 tests, without changing
an assertion, fixture or timeout. The App suite also passed **27/27** in an
isolated rerun. The final origin/boundary focused rerun passed **19/19**. WP-A's
intermittent protected-401 login assertion
and earlier timer/window diagnostics remain historical WP-C evidence; do not
misreport them as a passing whole-repository regression gate.

The isolated Python fixture check reproduces the two R3/WP-A V1 binary64 drift
failures. Producer code and the committed Synthetic fixture are unchanged. No
whole Python suite was rerun for this frontend-only work; the earlier module-wide
results remain attributed to R3/WP-A.

WP-C can start from a complete private seven-page workspace with external admission,
browser receipts and isolated regression diagnostics. WP-C and D7 have not started.
Public release still needs an independent exact-artifact rights/safety review;
technical acceptance grants no permission to redistribute market or derived data.

## Changed-file inventory

- `package.json`, `tsconfig.private.json`: explicit private commands and independent type check.
- `scripts/build_private_demo.mjs`, `private_demo_boundary.mjs`,
  `private_demo_projection.mjs`, `private_demo_isolation.mjs`: admission, safe
  projection, external-output checks and complete build graph guard.
- `scripts/private_demo_browser.mjs`, `private_demo_negative.mjs`,
  `private_demo_isolation.test.ts`: real acceptance and negative checks.
- `src/demo/private/{index.html,main.tsx,virtual.d.ts,admission.ts,PrivateWorkspace.tsx}`:
  isolated entry, verified presentation metadata and shared seven-page composition.
- `src/features/backtesting/{ARCHITECTURE.md,components/Result.tsx,
  page/BacktestingPresentation.tsx,page/BacktestingPresentation.test.tsx}`:
  explicit Evidence origin propagation and regression coverage.
- `src/features/futures_basis_research/{ARCHITECTURE.md,
  page/FuturesBasisPresentation.tsx,report/Report.tsx,report/Report.test.tsx}`:
  explicit reader Evidence origin propagation and Synthetic/real separation checks.
- `src/features/research_catalog/page/ResearchOverviewPresentation.tsx`:
  long readiness label wraps on narrow screens.
- `src/demo/{ARCHITECTURE.md,PRIVATE_BUILD.md,IMPLEMENTATION.md,WP_B_ACCEPTANCE.md}`:
  navigation, narrow private build authority and delivery evidence.
