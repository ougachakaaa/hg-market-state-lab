# D3-R3 private real IM Historical Basis — 2026-11-13

Execution evidence under [Examples](EXAMPLES.md) and [Authenticity](AUTHENTICITY.md).
D3-R3 technical acceptance **PASS**; market Publication Rights **BLOCKED** under
[R1's retained review](R1_FEASIBILITY.md). Regression failures below remain open.
This accepts private evidence preparation, not D4 composition or public release.

## Identity and acquisition

Clean source/baseline `310cfa14e62788b97fc2104769d52c326a8283a3`, branch
`feat/github-pages-demo`. Exact immutable request: `futures_basis_v1`, `IM`,
inclusive `2026-01-01..2026-11-11`, `r01a_standard_v1`.
Formal `ReportRequest`, `QuantileSpec` and three `IntervalCountSpec` values match
[the published standard profile](../../../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md)
exactly; no changed formula, Slot resolution, statistical range or annualization.

R1's private handoff and acquisition configuration were inspected. Current public
factories have no consumer-configurable Dataset storage root. The existing WP3
`futures_basis_live_acceptance.isolated_storage` harness redirected only Dataset
composition placement to fresh external Dataset-owned SQLite files. This is the
existing isolated development environment pattern, not a second cache implementation,
Source substitute or new runtime configuration API. Real public `export` → `ensure`
→ final `export` ran through the unchanged official Producer. Both calendars were
prepared before Futures and its mapped Index. No R1 single-day export, old cache
rows or SQLite tables were copied, queried or stitched into the final inputs.

Acquisition/production interval: **2026-11-13 11:26:39–11:27:23 Asia/Shanghai**
(full UTC timestamps retained in `acquisition.json`). Actual provider is Tushare;
Dataset identities and schema versions below come from the final public Exports.
These are separately retained snapshots, not a claim of simultaneous freshness.
SQLite connection auditing confined every connection to the three private Dataset
files; default cache size/mtime remained unchanged. No data was deleted.

| Final input | Schema | Requested / successful units | Rows | Missing / pending / failed |
| --- | --- | --- | --- | --- |
| `tushare_trade_calendar/calendar`, CFFEX | 1 | 315 / 315 natural days | 315; 206 open | 0 / 0 / 0 |
| `tushare_trade_calendar/calendar`, SSE | 1 | 315 / 315 natural days | 315; 206 open | 0 / 0 / 0 |
| `tushare_equity_index_futures/futures_daily`, IM | 2 | 206 / 206 product-days | 824 Contract-days | 0 / 0 / 0 |
| `tushare_index_daily/index_daily`, `000852.SH` | 1 | 206 / 206 sessions | 206 | 0 / 0 / 0 |

All four final Exports are complete. Every Futures row agrees on the actual
underlying `000852.SH`. Observed candidate dates are `2026-01-05..2026-11-11`;
request boundaries remain January 1 and November 11. Closed natural days have no
invented quotations. Input policy remains the Basis policy: a legal partial Index
would be retained as unavailable facts, rather than applying W2's strict policy.

## Formal report and consumer

Unchanged `market_research/scripts/futures_basis_report.py` executed directly through
its existing script entry under the isolation harness. It called formal
`observe_futures_basis`, composed the report and invoked the official HTML packager.
There is no HTTP Run ID, server lifecycle, preflight or new financial engine.
Producer runtime records clean source revision, Python **3.13.15**, Node **22.23.2**,
NumPy **2.5.3**, React **19.3.0**, Ant Design **6.6.5**, Plotly **4.1.1**, Vite **8.3.0**,
all installed package versions and both dependency-lock digests.

Report status **complete**; no failed statistical methods. All 12 distributions
and 18 paired term comparisons retain original Mean, Quantile and IntervalCount
results, common-date bindings and dropped outcomes. All four persistence summaries
retain complete and censored runs separately. Original `index_points` and
`decimal_ratio` units, nulls, statuses and reasons remain unchanged.

| Slot | Candidates per metric | Basis Value / Ratio eligible | Annualized eligible / not applicable | Unavailable / excluded | Complete / censored discount runs |
| --- | --- | --- | --- | --- | --- |
| M0 | 206 | 206 / 206 | 196 / 10 | 0 / 0 | 18 / 1 |
| M1 | 206 | 206 / 206 | 206 / 0 | 0 / 0 | 3 / 2 |
| Q1 | 206 | 206 / 206 | 206 / 0 | 0 / 0 | 0 / 1 |
| Q2 | 206 | 206 / 206 | 206 / 0 | 0 / 0 | 0 / 1 |

M0's ten expiry-day annualized values are Not Applicable, never zero-filled.
Censored durations remain lower bounds. Slot roles share dates/underlyings; these
are descriptive findings without independence, forecasting or investment claims.
The full producer limitations are retained privately in the reader and index.

The existing `validateEmbeddedReport` accepted the exact immutable request plus
complete `report-data.json`, returning the original payload unchanged. The small
local-only [validator runner](../../scripts/validate_private_basis.mjs) loads the
existing validators via Vite SSR without an HTTP listener. It checks the fixed
profile's explicit parameters, definition, manifest fingerprint and identical Views,
plus complete section payloads. Six negative probes reject request mismatch,
unsupported analysis/reader profiles, invalid status/View and a missing section.
It defines no business DTO or financial validation/calculation policy.

Offline Chromium **156.0.8078.4**, with networking disabled, passed the existing
formal report browser gate against the actual report: six rendered sections,
exact embedded producer payload, three V2 history Views with four Slot bindings,
all transitions/finite points, 24 V1 count/frequency histogram Views, hover,
Zoom/Pan/Reset, Trading/Calendar Days, paired population and evidence access,
1440×900 and 1024×768 containment. Zero external requests and zero browser errors.
This is the standalone Reader gate; no D4 static page was composed. Its pending
V2 origin-label work remains a D4 dependency, as recorded in the implementation handoff.

## Private package and replay

Private identity **D3-R3-local-20261113-v1**, Example profile
`d3-r3-private-basis-v1`, revision 1, classification `real_market`.
The owner-only external package location is recorded in the local
`D3-R3-HANDOFF.md`, outside Git and all build inputs. Structure:

```text
delivery/
  inputs.canonical.json  evidence.json  views.json  associations.json
  report-data.json  report.html  manifest.json  SHA256SUMS  REPRODUCE.md
dataset-cache/                 # three normal Dataset-owned databases
acquire.py  acquisition.json   # explicit acquisition invocation and audit
verify.json  replay.json  offline_guard.py  offline-guard.json
frontend-validation.json  tooling/validate_private_basis.mjs
browser/acceptance.json        # private screenshots and browser evidence
example-index.json  example-index.sha256
```

The lightweight index references the official Evidence Package, coverage,
provider/Datasets, acquisition, runtime, limitations, validation receipts and rights.
It does not redefine financial evidence or reuse MO's separate manifest format.
The official manifest/SHA256SUMS remain canonical for the report package.

- Input fingerprint: `8b939aa831373d7860c7c4d8d433e8d85bb2a9753ff596e66eba446a3c9e90ef`.
- Official manifest SHA-256: `4ae23a10760ffd314a6555819931d2e3e81dfceabd53cf2057096b54fadeb9c5`.
- Reader result SHA-256: `66d0b9f330312b17c1aabc3c09843c225aa6666b509d9383d2015f0e05ce58b7`.

From repository root, set `PRIVATE_R3_REPORT` to the handoff's `delivery` directory:

```bash
TUSHARE_TOKEN='' poetry run python market_research/scripts/futures_basis_report.py verify "$PRIVATE_R3_REPORT"
TUSHARE_TOKEN='' poetry run python market_research/scripts/futures_basis_report.py replay "$PRIVATE_R3_REPORT"
node ui_web/scripts/validate_private_basis.mjs "$PRIVATE_R3_REPORT"
```

Formal Verify **PASS** and Replay **PASS**, including canonical fingerprint,
Manifest/Views/Associations linkage and deterministic scientific result comparison.
Both commands also passed with credential lookup, socket connections and SQLite
connections replaced by immediate failures. Neither Token, market network nor
DataLake cache is needed. An initial local guard named a nonexistent config helper;
it was corrected to the actual `lab_config.tushare_token` before this successful
execution. No producer or evidence content was changed to obtain PASS.

Isolation checks passed against every Git worktree and repository symlink. Demo
Vite has `publicDir: false`, fixed repository inputs, and Pages uploads only
`ui_web/dist-demo`. No private-root import/copy/build step or workflow change was
introduced. Only this documentation and the validator tool are committed.
Hashes establish retained integrity, not independent exchange authentication or
redistribution rights. Market Publication Rights remain independently **BLOCKED**.

## Regression and remaining work

Actual command outcomes are recorded below. No assertion, numerical method,
global timeout, historical synthetic fixture or generated contract was changed.

| Check | Actual result |
| --- | --- |
| Six core Futures Basis Python test files (observation, Slots, statistics, report, online, preflight) | PASS: 223 tests |
| `poetry run pytest data_lake -q` (all public-service/core/provider/Dataset tests) | PASS: 686 tests |
| `poetry run pytest market_research/tests data_lake data_snapshot/tests/test_authority_topology.py ui_http/tests/test_architecture.py -q` | FAIL: 1982 passed, 1 skipped, 2 historical V1 synthetic fixture consistency failures |
| Isolated `test_futures_basis_demo_fixture.py` rerun | FAIL: same 2 failures, 3 passed; producer/fixture files identical to required baseline |
| Architecture/topology checks in Snapshot and HTTP | PASS: 23 tests |
| Research Ruff / mypy tests | PASS / PASS: 49 source files |
| Embedded validator / static controller / report frontend tests | PASS: 22 tests in 4 files |
| Private validator negative probes | PASS: 6 rejection checks |
| Formal Verify / Replay / guarded offline Verify and Replay | PASS / PASS / PASS |
| Actual private report offline browser gate | PASS; zero network requests/errors |
| `npm run contract:check` / `npm run build` / `npm run lint` | PASS / PASS / PASS |
| `npm run test` full default suite | FAIL: 572 passed, 8 failed in 74 files; 5000ms timeout failures |
| Full single-worker rerun | NOT RUN in R3; R1's prior uncaught timer/window failures remain historical evidence, not a new R3 result |

The two Python failures compare the unchanged committed V1 synthetic fixture with
current regeneration: one annualized history point differs in its binary64 y value
and matching detail text (`0.0339321720408206` versus `0.03393217204082061`). They
reproduce independently of acquisition. Real R3 scientific replay passes. Existing
R1/R2 full frontend timeout failures remain a separate regression issue; this run
has eight timeout failures and no reported uncaught `window` error. The complete
logs are retained privately. These failures prevent claiming the whole repository
regression suite green; they do not invalidate the thirteen D3-R3 technical gates.

D3-R4 still needs independent formal M1 and Q1 W2 executions under its own strict
input policy; R3 grants no backtest acceptance. R5 still needs an explicit admitted
Trailing Return plan, warm-up and real Publication evidence. R6 must audit the
Examples and independently clear public rights. D4 must compose all seven shared
surfaces, use this unchanged validated reader, preserve request/coverage disclosure
and correct real-market origin wording (current `mode="demo"` still has historical
Synthetic wording). No D4, R4/R5, merge, push or deployment work was started.
Stop after this commit for review.
