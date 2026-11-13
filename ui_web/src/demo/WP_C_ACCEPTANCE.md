# WP-C engineering acceptance — 2026-11-13

Required baseline `0412eae0bd2ebb6a5ebe48f53a551e7e8e0163e8`, branch
`feat/github-pages-demo`, initially clean. **WP-C private engineering scope PASS**: both complete frontend repeats and all
required local contract, producer, build, isolation and browser gates pass. This is not
a claim that every unrelated repository suite or remote CI/deployment was executed.
Public rights remain **BLOCKED**. No D7, push, deployment, merge or retained-data deletion.

## Scope and authority

This report owns D5/D6 execution evidence. [Runtime](ARCHITECTURE.md),
[private build](PRIVATE_BUILD.md), [Examples](EXAMPLES.md) and
[authenticity](AUTHENTICITY.md) remain canonical. Feature Presentations, generated
HTTP contracts, producer formulas and admission identities retain their owners.
Original external R2/R3/WP-A handoffs locate retained inputs; none enters Git or CI.
Original WP-C Final HEAD: `e3dce5ebfb48771941e8ac309c18af875d4b60e4`, also recorded
in its delivery response and external handoff. The later D7-P count erratum below
does not change that historical delivery revision.

## Root causes and fixes

| Finding | Evidence / bounded resolution |
| --- | --- |
| Test resource contention | Node 22.23.2 / Vitest 5.0.1 / JSDOM 30.1.0; 12 visible CPUs, default 11 concurrent forks. Sampled busy Node processes used roughly 0.3–0.75 GiB RSS each. No cgroup CPU/memory cap or OOM evidence; this is CPU/accessibility-work contention, not a demonstrated memory exhaustion. Bound to one worker, retain fresh per-file isolation and default 5000ms test timeout. |
| Repeated JSDOM accessibility work | Chain export tests repeatedly discovered the same export group across the entire rendered table/chart/ColorPicker DOM. Scope queries once to its mounted group, including Clipboard wait assertions. All controls, complete CSV/Context comparisons, filenames, null/zero/absence and no-refetch assertions remain. |
| Protected-401 assertion deadline | Baseline App failure was a Testing Library login lookup deadline, distinct from nine 5000ms timeouts. Test now holds the real mocked protected response, verifies authenticated page/request, and resolves 401 inside React `act`; logout-to-login and result removal assertions remain. No Auth runtime change or sleep. |
| Python worker lifecycle | A later full Research repeat exposed five failures: terminal status can precede worker permit release, causing `run_busy` in subsequent tests. Track and join each test-owned worker before `settled` returns and at teardown; assert no thread survives. No process permit reset or production lifecycle change. Focused online tests pass 23/23; complete Research reruns pass 1280 + one existing skip twice (10.26s, 9.75s). |
| Cleanup / state leakage | Historical timer/window errors did not recur in completed current baseline or serial business suite. No timer clearing, listener suppression, broad mock reset or ignored unhandled errors was added. Existing cleanup, AbortController, boundary release, stale-response and StrictMode tests remain enabled. File isolation remains on. |
| Plotly / Ant Design | The slow unit tests mock Plotly; Ant Design DOM and accessibility traversal remain real. Actual Plotly behavior is independently checked in Chromium. No library stub was added to bypass regression. |
| Node-only safety test environment | A new test initially imported a Node file tool through Vite's browser URL transform; switching that test to Node exposed the shared setup's unconditional `window` use. The final test spawns the actual Node CLI functions from the normal test environment, matching existing isolation tests; no application/setup workaround. |
| V1 floating comparison | Only annualized history M1 / 2024-10-22 `y` and its `结果` text differ: `0.0339321720408206` vs `0.03393217204082061` (one ULP). The value already differs before JSON; `report.history_view` uses `repr(outcome.value)`, so serialization faithfully mirrors it. Inputs/fingerprint and every other scientific field agree. |

V1 tracing reaches `construction._contract`: `(365 / 59) * math.log(F_close / S_close)`.
On glibc 2.35 / Python 3.13.15, an 80-digit Decimal `ln` check agrees with the current
binary64 logarithm; the adjacent lower log representation produces the retained value.
The old V1 fixture does not retain its original libm runtime, so the historical platform
cause cannot be proved retrospectively. There is no observed within-process randomness,
serialization rounding or test-only projection change. Cross-platform bit equality was
an invalid regression assumption at this transcendental rounding boundary.

The [V1 authority](futures_basis/ARCHITECTURE.md) now permits at most two ULPs, without
an absolute floor, only for finite annualized-history y values and matching `repr` detail.
Signed zero, all other JSON types/serialization/content, dates, statistics and fingerprint
remain exact. Five negative probes reject eight-ULP financial drift, inconsistent detail,
changed date, fingerprint and statistical structure. Generation and the committed JSON
are unchanged (SHA-256 `cf9709e5abd3f9ff42a25a432e0abcdbab04a54223bc84c526db094a63ddd45a`).
No tolerance changes formal financial production, real admission or Evidence digests.

## Frontend regression evidence

| Run | Actual result |
| --- | --- |
| Initial complete default, 11 workers | FAIL: 574 passed / 10 failed, 75 files, 73.74s; nine test timeouts and one login lookup deadline; no reported unhandled error |
| Clean two-worker experiment | FAIL: 583 passed / one export timeout, 75 files, 138.99s |
| Initial one-worker business suite | All original 584 tests passed; overall FAIL on the new Node safety test import, 76 files, 250.63s |
| Overlapped diagnostic run before final fixes | FAIL: one export timeout and new safety setup error, 77 files, 281.69s; not repeatability evidence |
| Focused final Chain / App / admission / safety | PASS: 72 tests, four files, 38.91s |
| Final complete repeat 1 | PASS: 593 tests / 77 files, 291.75s, no reported unhandled errors |
| Final complete repeat 2 | PASS: 593 tests / 77 files, 250.16s, no reported unhandled errors |

Baseline failures by file: App (1), Chain Page (4), Chain Presentation (1), Premium
Page (2), Premium Presentation (1), Explorer Presentation (1). One early two-worker
attempt was invalidated by dependency reinstallation overlapping the run; its worker
startup errors are retained as an operator-induced invalid diagnostic, not dismissed
as application errors or counted as PASS. A combined Python invocation also failed
collection on duplicate test basenames; an importlib attempt failed namespace loading.
Final Python checks use the established independent module invocation boundaries.
The separate 1275-pass/five-failure Research repeat is retained as the evidence that
triggered the worker-join fix, rather than being hidden by the earlier passing run.

One worker limits inter-file CPU contention; it does not remove in-test asynchronous
ordering, stale/cancelled requests, authentication lifecycle or concurrency assertions.
No timeout increase, skipped failure, deleted assertion or arbitrary sleep was used.

## Python and compatibility gates

Run Python commands at repository root, npm commands in `ui_web`.

| Actual command | Result |
| --- | --- |
| `poetry run pytest market_research/tests -q` | PASS: 1280 passed, one existing skip |
| `poetry run pytest data_lake -q` | PASS: 686 |
| `poetry run pytest data_snapshot/tests -q` | PASS: 287 |
| `poetry run pytest market_backtesting/tests -q` | PASS: 540 |
| `poetry run pytest ui_http/tests -q` | PASS: 589 |
| `poetry run pytest ui_web/scripts/test_export_contracts.py ui_web/scripts/test_private_wpa_examples.py -q` | PASS: 15 |
| `poetry run pytest data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | PASS: 23 |
| `poetry run pytest market_research/tests/test_futures_basis_demo_fixture.py -q` | PASS: 10 |
| `poetry run python market_research/scripts/futures_basis_demo_fixture.py --check` | PASS; retained fixture unchanged |
| `poetry run ruff check market_research` / `poetry run mypy market_research/tests` | PASS / PASS: 49 source files |
| `npm ci` | PASS; lockfile unchanged |
| `npm run contract:check` | PASS: all seven generated HTTP boundaries current |
| `npm run build` / `npm run lint` | PASS / PASS |
| `npm run demo:build` | PASS: original public V1 |
| `npm run test:static-compatibility` | PASS: exhaustive private route type check and actual public/private entry module graphs |
| `npm run test:public-safety` | PASS: tracked payload/credential guards and actual default public files |
| `actionlint` on compatibility and Pages workflows | PASS; existing local actionlint 1.7.12 |

D7-P count erratum: the original table transposed the Snapshot and Backtesting
counts. Retained WP-C raw logs confirm Snapshot **287** and Backtesting **540**;
D7-P independently reproduces both totals. This corrects labels, not historical
execution outcomes or technical acceptance.

## CI and fail-closed feedback

`.github/workflows/demo-compatibility.yml` adds validation only, without deploy/upload
permissions or artifacts. Frontend job runs npm ci, contract check, full Vitest,
production build, lint, default V1 build, static compatibility and public safety.
Python matrix independently runs Research, Backtesting, DataLake, Snapshot, HTTP and
Web-tool tests under the single root Poetry project. No Tushare secret, private package,
Provider acquisition or retained private evidence is needed. The exact commands and
workflow syntax were verified locally. Remote GitHub Actions execution is **NOT RUN**;
pushing this branch would trigger the existing V1 deployment and was not used as a test.

`workspaceRoutes` owns route identity; the actual composition is an exhaustive
`Record<WorkspacePath, ...>`, not a second test-only coverage list. CI compiles it and
builds the real private entry with an empty test-only virtual envelope for graph inspection.
That discarded artifact cannot pass admission and is never a V2 Example or browser claim.
Existing six-feature validators, generated schemas, negative tests and producer tests
cover Result/Profile/View/reference drift. New admission probes cover every Example's
identity, producer, source revision, rights, digest and missing inventory. Original real
negative runner additionally passes 19 rehashed-content and identity rejection probes.

The public scan pins 18 existing synthetic/nonfinancial payloads and rejects new or
changed data files pending explicit review. It checks credential literals, actual V1
fixture/disclosure, private envelope/target-date leakage, local paths, source maps,
public inputs and the actual Pages upload root. Dependency inspection rejects Auth,
HTTP clients and production controllers. These are regression gates, not automatic
rights clearance or a universal secret detector. No new schema framework was introduced.

## Private reproduction and browser acceptance

Use the existing external handoffs to assign `PRIVATE_R2`, `PRIVATE_R3` (package
containing `delivery`), and `PRIVATE_WPA`. All output variables below must be fresh
absolute directories outside every Git worktree and public build input.

```bash
poetry run python ui_web/scripts/private_mo_examples.py verify --output "$PRIVATE_R2"
poetry run python market_research/scripts/futures_basis_report.py verify "$PRIVATE_R3/delivery"
poetry run python market_research/scripts/futures_basis_report.py replay "$PRIVATE_R3/delivery"
poetry run python ui_web/scripts/private_wpa_examples.py verify --output "$PRIVATE_WPA"
poetry run python ui_web/scripts/private_wpa_examples.py replay-w2 --output "$PRIVATE_WPA"
```

All PASS. W2 replay blocks credential, socket and SQLite dependencies. Same R2/R3/WP-A
identities and result versions are retained; the new admission identities equal WP-B's
accepted identities exactly. No provider acquisition, original artifact modification,
cache cleanup, synthetic fallback or build-time financial calculation occurred.

```bash
npm run demo:build:private -- --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" --output "$NEW_PRIVATE_BUILD"
npm run test:private-demo-data -- --r2 "$PRIVATE_R2" --r3 "$PRIVATE_R3" --wpa "$PRIVATE_WPA" --output "$NEW_PRIVATE_NEGATIVES"
npm run test:private-demo-browser -- --build "$NEW_PRIVATE_BUILD" --evidence "$NEW_PRIVATE_BROWSER" --r2 "$PRIVATE_R2" --wpa "$PRIVATE_WPA"
```

New external private build PASS from committed code
`853f8d0be629e3c7e2c15d8f2d7597784af773bc`; the final acceptance commit changes
documentation only. Formal admission reruns all verifiers/replay before
bundling. Actual Chromium 156.0.8078.4 PASS: seven routes, 11 acceptance groups,
21 viewport screenshots plus digest-error screenshot, nine local static requests,
zero page/console errors, zero warnings and no cookies. Root/hash normalization,
shared sidebar/breadcrumb, Back/Forward, deep reload and report sections pass at
1440/1024/390px. Real source/date/window/observed coverage and producer disclosure
remain visible. Chain and Premium preserve all 312 contracts/Points, six expiries,
four IM references and complete Copy Raw / Context JSON / download data after filters.
Downloaded CSV bytes and filenames match the owning feature exporters exactly.

Basis retains six sections and local Slot/time-axis controls; Explorer reads four real
Analyses and all six Views; both M1/Q1 formal return coordinates and genuine Plotly
Hover/Zoom/Pan/Reset pass. Actual Publication has one page: its previous/next boundary
is verified; advancing multiple real pages is **NOT APPLICABLE**. Existing synthetic
local-pagination tests cover that algorithm separately. No replacement market records
were fabricated. Static loading is tested by holding/releasing actual WebCrypto
admission, without a sleep. Corrupt Result digest shows Static Error before business
mounting. No Auth/backend/Provider/XHR/fetch or unexpected origin is allowed. Desktop,
tablet and narrow containment checks pass; representative narrow screenshots were
visually inspected. This is the true private build, not the D2 harness.

## Public/private safety and capacity

Actual public V1 artifact remains four files, carries the original synthetic fixture
and disclosure, and passes credential/private-profile/date/path/source-map scans.
Original Pages workflow, branch trigger and upload root `ui_web/dist-demo` are unchanged.
Private output is a fresh external directory containing only site JS/CSS/HTML and the
repository-relative dependency receipt, plus external admission receipt. Original Raw,
Dataset caches and Publication Source are not bundled; sourcemaps are disabled. The
complete actual file inventories and hashes are retained privately, outside Git/CI.
Independent pre-commit and committed-source site inventories are byte-identical; a
separate final audit verifies every emitted hash, absence of original Publication
Source and private digest leakage into all four public V1 files.

Publication Source is 8,297,891 bytes. Formal Python Reader and safe static export PASS;
HTTP Analysis/View acceptance for this object is **BLOCKED** by the existing 4 MiB
source-verification budget and would return 503 `verification_budget_exceeded`.
This is the explicit [HTTP capacity contract](../../../ui_http/products/research_publication/http-contract.md),
not a new data/identity defect or a promise of arbitrary-size HTTP support. Private
static Reader PASS is not Production HTTP PASS. No MAX_SOURCE_BYTES change, Store
redesign, alternate Publisher or paging framework is justified for this Demo.

## Warnings, reconciliation and remaining D7 work

Known Ant Design List deprecation remains a development diagnostic; it was visible in
baseline Vitest logs, while actual production private Chromium recorded zero warnings.
Vite chunk-size warnings remain informational. Python HTTP tests report the existing
Starlette/httpx deprecation. `npm ci`/local audit reports six existing dependency
advisories (three moderate, three high); dependencies were not upgraded as part of
regression stabilization. Review these before public release; this report makes no
zero-vulnerability claim.

Canonical changes stay narrow: V1 comparison semantics in its fixture authority;
static route/CI/loading rules in Demo authorities; current source-disclosure status in
feature and presentation authorities; implementation navigation points to this report.
No Market Data, Research, Backtesting W2, Snapshot MO, Publication admission, HTTP DTO,
financial formula or generated contract was redesigned. Source, completeness,
execution, integrity and redistribution rights remain separate.

D7 remains blocked on exact source/output/channel rights clearance, public data admission,
exact public V2 artifact review, dependency-security disposition and the independent
release/cutover decision. Public metadata rights also remain BLOCKED. No V2 real payload
was committed or deployed; no trigger change, auto-approval or production declaration.

## Acceptance criteria disposition

| Criteria | Disposition |
| --- | --- |
| 1–2 full frontend / no unhandled test errors | PASS: two complete 593-test repeats |
| 3–7 V1 consistency / relevant Python / contracts / production build / lint | PASS |
| 8–11 dependency isolation / seven private routes / real validators / offline verify-replay | PASS |
| 12–14 Chromium / Copy-Export integrity / actual public V1 asset isolation | PASS |
| 15 CI feedback implementation and local verification | PASS; remote Actions NOT RUN |
| 16–18 no unauthorized public payload / no financial semantic drift / readiness report | PASS within WP-C scope |
| Public rights, public V2 admission and HTTP detailed reads of this oversized Publication | BLOCKED; separate boundaries described above |

## Commit delivery

`5a05c08` — `fix(test): stabilize frontend and legacy fixture regression`

`853f8d0` — `ci(demo): enforce static compatibility and public asset safety`

Original final acceptance commit: `e3dce5ebfb48771941e8ac309c18af875d4b60e4` —
`test(demo): close private v2 engineering acceptance (WP-C)`.
All required WP-C local gates are complete. The final response supplies the last HEAD
and this complete report; the final commit contains documentation only. External
`WP-C-HANDOFF.md` locates private builds, browser receipts, logs, hashes and exact SHA.
