# INT-1 integration acceptance — 2026-11-13

## Candidate and review boundary

Integration branch: `integration/demo-v2-into-develop`.
[Draft PR #6](https://github.com/ougachakaaa/hg-market-state-lab/pull/6) targets `develop`;
it must not be auto-merged. Public V2 / Publication Rights remain **BLOCKED**.

Fixed inputs and actual merge:

| Identity | Commit |
| --- | --- |
| Target / first parent | `389abc742938043bd253702aec0d27bbc0f08981` |
| Source / second parent | `d6e813a93e5b0a1fc71c985f7798f6d546c5d62f` |
| Two-parent Merge Commit | `1517ab1391d1669f7ea56ac7f7836a44737c38fc` |
| Final implementation and browser-tool commit | `c12d5f99ff07bd074e5842bfbec34120fc4b18f2` |
| Research rebuild / initial private build code | `d2257d0e659ce0c2a6a73d2ba32a9d5c39f6e1b5` |

Final delivery adds only documentation after the implementation commit above. Its exact
HEAD is supplied in the delivery response and external INT-1 handoff; a document cannot
contain its own commit hash. The PR's current head is the final review candidate.
Both fixed inputs remain ancestors. Fetch and subsequent remote preflight confirmed
`develop` still at the fixed target; no newer develop changes were silently included.
The original develop worktree was clean and remains on its original branch. A new
sibling worktree owns integration. No reset, squash, force-push or main/develop update
was performed. Source history and the real two-parent merge are retained.

## Actual conflicts and Authority Resolution Matrix

Exactly four paths were unmerged after the real Git Merge. Thirteen overlapping
change regions found in read-only exploration were not thirteen actual conflicts.

| Actual conflict | Resolution / canonical owner |
| --- | --- |
| `features/backtesting/components/Result.tsx` | Retain develop's memoized observed-session domain and shared DateAxisControl; use Demo's transport-free Result type and origin-aware Evidence. [Backtesting](../features/backtesting/ARCHITECTURE.md), [date axis](../../DATE_AXIS_PRESENTATION.md). |
| `features/backtesting/page/BacktestingPage.tsx` | Retain Demo's shared Presentation composition; inject develop's friendly readiness, cache refresh wording and pure Failure guidance from the Production controller. Static never imports that controller. |
| `features/futures_basis_research/report/Report.tsx` | Use the single shared DateAxisControl with develop's mode values, keeping Demo's local section navigation, origin disclosure and narrow-width chart containment. [Basis](../features/futures_basis_research/ARCHITECTURE.md). |
| `features/research_explorer/ARCHITECTURE.md` | Preserve both the generic published-View calendar boundary and shared Static/Production reader ownership. Explorer does not invent a trading calendar. |

Additional semantic reconciliation, including clean textual merges:

| Concern | Decision / verification |
| --- | --- |
| Publication / W1 / W2 storage | develop's formal SQLite implementations are byte-identical to the target. Independent databases, integrity, portable paths, owner isolation, lifecycle and failure categories remain owned by their existing storage authorities. |
| Publication HTTP | Keep the shared pure `project_analysis` adapter after the existing bounded HTTP Reader. [HTTP contract](../../../ui_http/products/research_publication/http-contract.md) retains source-verification and response limits; generated wire contracts did not change. |
| Private WP-A generation | Audit Dataset placement during public Batch execution; publish afterwards through the independent SQLite PublicationStore. No legacy migration or direct insertion into SQLite. |
| Private offline verification | Permit only the explicitly selected package Publication database, force SQLite `mode=ro` and `query_only`. Block Dataset/Run SQLite, network and credentials. Nested W2 replay still rejects every SQLite connection. Tests assert attempted writes fail and the complete file inventory remains byte-identical. |
| Mixed-age private evidence | Rebuilt Research acceptance records its actual code revision; Catalog/Publication origin consumes that revision. Reused W2 retains the original runtime revision and unmodified Evidence. [Private build](PRIVATE_BUILD.md) owns this packaging detail. |
| W2 validator / CI | Retain develop's portable Node/Vitest invocation and Demo's conditional Node/npm setup in the Backtesting Python job. Preserve bounded frontend workers and upstream timer cleanup. |
| Authority topology | Existing specialized storage, date-axis, feature and private-build contracts retain ownership. This report is execution evidence, not a combined replacement Authority. |

No business financial implementation or second business schema was introduced. No
HTTP source budget, production Run semantics or public release gate was relaxed.
All four unmerged paths were resolved; conflict-marker and full diff checks pass.

## Private evidence and SQLite Publication

The initially unknown paths were found through a bounded search in the application's
external local-data directory. Original R2/R3/WP-A Handoffs were read before consumption.
Absolute paths, new Publication ID, sealed inventories, source/result digests, commands,
logs and screenshots remain in the external INT-1 handoff and private receipts.
No real result, cache, Source, screenshot or private package path is committed here.

| Gate | Actual result |
| --- | --- |
| R2 formal Verify / frontend validators | **PASS**, original accepted MO Chain/Premium package and manifest unchanged. |
| R3 formal Verify / Replay | **PASS**, original IM report, six sections, 206 observed CFFEX sessions and retained fingerprint unchanged. |
| Original WP-A W2 Replay | **PASS**, both M1/Q1 under credential/network/all-SQLite guard. |
| Original WP-A Publication verification | **Expected rejection**: legacy file-store directory lists no current SQLite Publication. No migration or modification of the old package. |
| New Publication | **PASS**, new external package and new genuine Publication ID through fixed ResearchPlan → execute_batch → retain_source → publish → PublicationStore. |
| Rebuilt research identity | `000852.SH`, 2026-01-01..2026-11-11, H20/H60, original Quantile/IntervalCount parameters; two successful Jobs, four Analyses and six Views. |
| Source reuse | **PASS**, copied legally retained DataLake cache files to the new external package, consumed only public services, blocked credentials and socket access throughout Batch execution. Cache bytes before/after are identical; no Provider acquisition. |
| Financial / provenance association | **PASS**, old/new scope and all projected statistical results are exactly equal. W2 files are reused byte-for-byte; original producer revisions and original acquisition evidence are retained. |
| New WP-A Verify / W2 Replay / Reader export / frontend validators | **PASS**, new sealed index, actual digests/revisions, current SQLite Reader and original R2/R3 references. |
| Private static build / negative admission | **PASS**, rebuilt from integration code; 19 negative probes, with no synthetic replacement of a real Example. |

Current public facade has no supported decoder for reconstructing an executable Batch
from a retained Publication Source. Therefore Research Batch was rerun through public
services over the retained genuine cache, rather than importing private deserialization
or converting legacy storage. No old Publication ID was forced.

The new retained Source is 8,549,306 bytes. Python Reader and safe static export **PASS**.
An actual invocation of the bounded Analysis delivery endpoint returns **503
`verification_budget_exceeded`**, with the unchanged 4 MiB limit. This is an existing
HTTP capacity boundary, not Production detailed-read PASS; no private shortcut was added
to HTTP. Synthetic HTTP regression verifies the ordinary bounded read contract separately.

## Integrated browser and engineering verification

Environment: Linux / WSL2, Python 3.13.15, Node 22.23.2, npm 10.9.8,
Playwright 1.64.1, actual Chromium 156.0.8078.4. Each worktree has its own root `.venv`;
Poetry installs from the repository root. Frontend commands run in `ui_web`.

The final private build records code `c12d5f9`; an independent hash audit confirms its
entire site inventory is identical to the first integrated `d2257d0` build. The final
Chromium run consumes the new build, never an old branch's dist. All seven routes
pass at 1440, 1024 and 390px:

| Route | Result |
| --- | --- |
| `#/research` | **PASS**, genuine capability descriptions, status and local details. |
| `#/research/futures-basis` | **PASS**, six sections, observed coverage, local section navigation, distribution Slot and shared date-axis switching across history charts. |
| `#/research/publications` | **PASS**, rebuilt SQLite Publication export, four Analysis selections and all six Views; one-page boundaries, with no invented real pagination records. |
| `#/data` | **PASS**, shared overview and product links. |
| `#/data/mo-option-chain` | **PASS**, complete genuine payload, local expiry filtering, Copy Raw/Context and exact CSV/JSON. |
| `#/data/mo-premium-plane` | **PASS**, complete genuine payload/Points, expiry filtering, Copy/Export and actual Plotly hover. |
| `#/backtesting` | **PASS**, M1/Q1 selection, exact return coordinates, shared Trading/Calendar Days for both charts, default reset on strategy switch, evidence and Plotly Zoom/Pan/Reset. |

Actual private browser evidence: seven routes, eleven acceptance groups, 21 viewport
screenshots plus a digest-error screenshot, nine local static requests, no cookies,
zero page/console errors and zero warnings. Sidebar, breadcrumbs, Back/Forward, deep
reload, actual admission loading and fail-closed corrupt-digest handling pass. No Auth,
backend API, Provider, XHR/fetch or unexpected-origin request occurs. Representative
narrow/tablet screenshots were visually inspected; static origin and historical
real-market/rights disclosures are visible without document overflow.

Production Backtesting Chromium **PASS**: actual Auth → Vite → FastAPI → worker →
SQLite Run Store, M1/Q1, readiness, failures, safe retries, owner/unknown identity,
requested-versus-observed windows, date-axis alignment/hover/spacing/legend, no extra
request on axis change, refresh, history and logout. Production Basis Chromium **PASS**:
real authentication, submit/poll/read, complete/partial and failure states, charts,
shared historical date axes, section navigation, two viewports and logout. These use
explicit synthetic public-service fixtures for engineering regression, separate from
the genuine private seven-page acceptance above. Static Backtesting harness **PASS**
with its test-only producer fixture and shared date axes; it is not a real-market gate.

| Root Python command | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | **PASS**, 1290 passed / 4 Windows-only skips. |
| `poetry run pytest market_backtesting/tests -q` | **PASS**, 595 passed. |
| `poetry run pytest data_lake -q` | **PASS**, 686 passed. |
| `poetry run pytest data_snapshot/tests -q` | **PASS**, 287 passed. |
| `poetry run pytest ui_http/tests -q` | **PASS**, 590 passed. |
| `poetry run pytest ui_web/scripts -q` | **PASS**, 17 passed, including real SQLite tool/readonly/export regressions over synthetic inputs. |
| Relevant topology / architecture tests | **PASS**, 23 passed; also included in owning full suites. |
| Explicit Publication/W1/W2/HTTP portable SQLite selection | **PASS**, 146 passed / 4 Windows-only skips. Native Windows is **NOT RUN** here. |
| V1 formal fixture regeneration `--check` | **PASS**, unchanged committed fixture. |
| Ruff: Research, Backtesting, DataLake, Snapshot, HTTP, Web Scripts | **PASS**. |
| Mypy: Research tests, Backtesting, HTTP, DataLake, Snapshot | **PASS**. |
| actionlint: compatibility and Pages workflows; `git diff --check` | **PASS**. |

| Frontend command | Result |
| --- | --- |
| `npm ci` | **PASS**, Demo's repaired lockfile preserved. |
| `npm run contract:check` | **PASS**, all generated HTTP boundaries current; no unnecessary generation. |
| `npm test` | **PASS**, 607 tests / 82 files, no reported unhandled errors. |
| `npm run build` / `npm run lint` | **PASS / PASS**. |
| `npm run demo:build` | **PASS**, existing Synthetic Public V1. |
| `npm run test:static-compatibility` | **PASS**, exhaustive private route typing and actual static module graph. |
| `npm run test:public-safety` | **PASS**, actual four-file V1 artifact and tracked payload/credential guards. |

Retained diagnostics: initial Ruff caught two formatting issues in the new regression;
corrected and rerun PASS. The historical static harness initially rejected the newly
shared axis radio inputs as query controls; it now separately prohibits editable query
inputs, Submit and refresh, while testing both real axis modes. An exploratory portable
selection referenced retired test filenames and collected nothing; the corrected current
selection above ran 146 tests. No assertion was removed to hide financial drift, no
skip/timeout increase or static isolation waiver was introduced. Existing Vite chunk-size,
Ant Design List deprecation and Starlette/httpx diagnostics remain; Production dev
scanning can log the private virtual-entry prebundle warning, while browser assertions
and all production/private builds pass. Actual private production assets log no warnings.

## CI, isolation and merge recommendation

The independent PR compatibility workflow has read-only contents permissions and no
Pages deployment/upload job. The existing Pages workflow and its feature-branch trigger,
V1 entry/assets and upload root are unchanged from the Demo baseline. Private files do
not enter Git, CI inputs/artifacts, `public`, `dist` or `dist-demo`. The actual public
four-file output contains no private result digest, private root or source map; final
external audit verifies every private emitted hash and original WP-A sealed file.
No Source evidence or cache is bundled into the site. No retained package or default
store/cache was deleted or reset; browser harnesses clean up only their own temporary
Auth/Run test state.

[Implementation CI run](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43401957699)
validates implementation commit `c12d5f9`: **all seven Jobs PASS remotely**
(Frontend plus six Python suites). Backtesting's Node dependencies, generated contracts,
worker stability, static graph and public safety all passed on that exact candidate.
Documentation-only delivery commits trigger their own checks; the final delivery and
PR checks record their separate status.

Local integration, actual private evidence, SQLite rebuild and browser gates are complete.
The implementation is technically ready to merge into develop, subject to the user's
overall review and the latest documentation-only PR checks. There is no missing
private-evidence blocker now. GitHub reports the Draft PR mergeable; no merge was performed.
Known separate boundaries remain: oversized Publication HTTP detailed reads are **BLOCKED**,
native Windows was **NOT RUN** in this environment, and real public V2 redistribution /
release remain **BLOCKED** pending their independent gates. This task neither changes
those boundaries nor publishes or declares production.

### Reproduction

Resolve `PRIVATE_R2`, `PRIVATE_R3` and `PRIVATE_WPA` from the external INT-1 Handoff.
Use its newly sealed SQLite WP-A package, not the original file-store package.
All build/negative/browser outputs must be new absolute directories outside every
worktree and public input. From the repository root:

```bash
poetry run python ui_web/scripts/private_mo_examples.py verify --output "$PRIVATE_R2"
poetry run python market_research/scripts/futures_basis_report.py verify "$PRIVATE_R3/delivery"
poetry run python market_research/scripts/futures_basis_report.py replay "$PRIVATE_R3/delivery"
poetry run python ui_web/scripts/private_wpa_examples.py verify --output "$PRIVATE_WPA"
poetry run python ui_web/scripts/private_wpa_examples.py replay-w2 --output "$PRIVATE_WPA"
```

From `ui_web`:

```bash
npm run demo:build:private -- --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" --output "$NEW_PRIVATE_BUILD"
npm run test:private-demo-data -- --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" --output "$NEW_PRIVATE_NEGATIVES"
npm run test:private-demo-browser -- --build "$NEW_PRIVATE_BUILD" --evidence "$NEW_PRIVATE_BROWSER" --r2 "$PRIVATE_R2" --wpa "$PRIVATE_WPA"
```

The build invokes the formal current Publication Reader as part of WP-A admission.
Its PASS remains distinct from authenticated HTTP detailed-read capacity acceptance.
