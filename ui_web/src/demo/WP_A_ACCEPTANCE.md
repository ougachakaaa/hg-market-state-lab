# WP-A private real research examples — 2026-11-13

Execution evidence under [Examples](EXAMPLES.md) and [Authenticity](AUTHENTICITY.md).
Required baseline `69cd25f15dd35d086582726439236ebe472f36d3`, branch
`feat/github-pages-demo`; initial worktree was clean. Producer business source remains
unchanged. Technical checkpoints and public rights are independent; market and output
Publication Rights remain **BLOCKED**. No D4 composition or public release is accepted.

## W2 checkpoint

Both formal `futures_roll_long_v1` / IM requests retain the inclusive
`2026-01-01..2026-11-11` window. Each independently ran
`create_futures_roll_service().run(request)`, Result construction/validation and
portable Evidence construction/encoding. The tool redirects only Dataset storage
placement using WP8's existing isolation pattern. No existing cache or R3 Export
supplies W2's proof, and no Dataset tables are queried or assembled by the tool.

| Check | M1 | Q1 |
| --- | --- | --- |
| Strategy | `expiry_to_M1_v1` | `expiry_to_Q1_v1` |
| Actual observed sessions | 206; January 5–November 11 | 206; January 5–November 11 |
| Execution legs / rolls | 20 / 9 | 8 / 3 |
| Final Flat, daily accounting, actual expiry/Close bindings | PASS | PASS |
| Complete Result, returns/drawdown V2 Views and full Evidence | PASS | PASS |
| Formal guarded offline reproduction | PASS | PASS |
| Existing Embedded Result validator | PASS | PASS |

Final Exports prove 315/315 CFFEX natural days, 206/206 IM product-days with 824
Contract-day facts, 315/315 auxiliary SSE natural days, and 206/206 CSI1000 Index
sessions. Missing/pending/failed counts are zero. SSE remains auxiliary, outside
the official three-export fingerprint. Both strategies consume identical input
fingerprint `c7e9bdadf1881be9d6a60256d50e857a579de7f7cec40938bdb876e4a2657631`.
Result/definition profiles remain `futures_roll_long_result_v1` /
`futures_roll_long_definition_v1`.

Separate Results retain full PnL, equity, return, benchmark, drawdown, Trades/Rolls,
limitations and producer Views privately. No financial values are copied here.
Offline reproduction runs in a separate process with credential lookup, socket
connections and SQLite connections forbidden. Complete reproduced Results match the
retained JSON. Eight negative frontend probes reject Profile, window, missing View
and Strategy mismatches. The existing validator returns the producer payload unchanged.

Private tooling is [the explicit runner](../../scripts/private_wpa_examples.py) and
[the validator runner](../../scripts/validate_private_wpa.mjs). Neither is a build input.
The complete private handoff and final regression matrix are recorded below.

## Research checkpoint

The exact Python `ResearchPlan` preview expanded two Jobs and four analysis attempts.
Both Jobs executed through `execute_batch`, independently preparing their own public
inputs/observations. Fixed scope is `000852.SH`, `trailing_cumulative_return_v1`,
explicit `{}` parameters, the unchanged 2026 request window, Horizons `[20, 60]`,
`on_job_failure="continue"`. `quartiles` uses `[0, .25, .5, .75, 1]`;
`distribution` uses `[-.5, -.2, -.1, -.05, 0, .05, .1, .2, .5]` in `decimal_ratio`.
These are this Example's choices, not Research defaults.

| Horizon | Candidate / Eligible / Unavailable / Excluded | Warm-up facts | Total Index facts |
| --- | --- | --- | --- |
| 20 trading sessions | 206 / 206 / 0 / 0 | 20/20; 2025-12-04–2025-12-31 | 226/226 |
| 60 trading sessions | 206 / 206 / 0 / 0 | 60/60; 2025-10-09–2025-12-31 | 266/266 |

Both sample fact coverages are 206/206; every candidate anchor lies within the fixed
2026 window. Calendar discovery follows the official adjacent/doubling backward
requests; all Calendar slices are complete. Warm-up rows are preparation dependencies,
never Demo observations. Source is real Tushare Calendar/Index through unchanged
DataLake public services; original exports, attempts, endpoint dependencies, sample
bindings, numeric results and coverage remain in formal retained source evidence.

Input profile is `trailing_return_inputs_v2`. Fingerprints:

- H20: `80e0c40917c6ff9d82c67b4d003be412bbbc84e30f77095dfe767adabc68d124`.
- H60: `01dd98be249e10534584b94ab5f5fc50637a9f48d554b322de48c52146bdf6e2`.

Actual Batch status **success**, two `Success` Jobs and four successful analyses.
The original in-memory Batch passed `retain_source` and `publish`; no Workbench JSON
was ingested or reconstructed as a Batch. Final private Publication ID is
`30f752900ee24f0a8fda7f7b70328ed9`. A newly opened `PublicationStore` reads its
Manifest, all four associated Analyses and all six referenced ChartViews. Original
ordering, exact IDs, specs, units, status, source integrity and linkage pass.
Source SHA-256 is `961945b19d02909a17c0c5dd31c1c54e684281fd94a8a203478d7986b7d0fbee`;
size is 8,297,891 bytes. Statistics and market values stay private.

The actual source exceeds HTTP's unchanged 4 MiB detailed-verification budget.
An HTTP Analysis/View read therefore returns 503 `verification_budget_exceeded`;
this is **not** live HTTP acceptance. Python Reader access and static export have no
HTTP execution requirement. The adapter's existing allowlisted Analysis projection
was extracted as `project_analysis`, shared with the unchanged bounded HTTP route.
Private export uses the actual verified Python Reader plus that projection and
existing DTOs; it neither raises HTTP limits nor emits raw internal manifests.
Projection equivalence tests cover success, failure, not-attempted and private-field
redaction; existing HTTP budget tests remain intact.

`validateEmbeddedPublicationSet` accepts the complete safe Reader export, with
additional required-detail checks for all selected Analysis/View references. Three
negative probes reject foreign Publication, unpublished View and invalid Job/Analysis
association. `list_capabilities()` / `get_capability(id)` supply the real Catalog,
including `supported` and `live_readiness="not_probed"`; `validateEmbeddedCatalog`
passes and rejects an unlisted detail identity. No fake readiness probe occurred.

## Private handoff and reproducibility

The accepted owner-only external package is located through the local
`WP-A-HANDOFF.md`, beside the existing R2/R3 handoffs, outside Git and every build
input. Its index uses `wp-a-private-example-index-v1`, revision 1, `real_market`.
It inventories 45 files with SHA-256/byte lengths, references the two original W2
Results/Evidence, complete Research source/Publication Store, safe Reader export,
Catalog, runtime, acquisition/placement audits and validation receipts. No generic
financial artifact store, serialization or business schema is introduced.

```text
runtime.json  acquisition.json  placement-audit.json
w2-stage.json  research-stage.json
w2/{strategy}-request.json / -result.json / -evidence.json
w2/acceptance.json  frontend-validation.json  offline-reproduction.json
research/preview.json  batch-summary.json  source.json  source-reference.json
research/publications/             # unchanged formal PublicationStore layout
research/embedded-publications.json  catalog.json
research/acceptance.json  frontend-validation.json
tooling/                           # accepted helper source snapshots
r2-verification.json  r3-verification.json
example-index.json  example-index.sha256
```

The index's detached checksum is
`d368f2a05c7eb552ba20c3b95b74a98d97a16c18bea2753fb56fa93d3775bbeb`.
R2's existing full private verifier and R3's formal Evidence verifier passed again;
their original identities/manifests are referenced without copying or replacing
business evidence. W2's strict proof remains independent of R3's Basis proof.

Final acquisition ran **2026-11-13 11:55:03–11:56:32 Asia/Shanghai**. The 48 public
service operation records retain exact requests, start/end timestamps, statuses,
final coverage and row counts. These are service-operation timestamps, not claims
of exchange-side timestamps or simultaneous Source snapshots. All audited SQLite
connections stayed under the new private Dataset root. Default caches were never
opened by this tool; no historical Publication/Run or DataLake cache was deleted.

Producer baseline, clean business-source state, helper digest, dependency-lock
digests, Python 3.13.15, NumPy 2.5.3, Pydantic 2.13.5 and Tushare 1.4.29 are retained.
The handoff records Node 22.23.2 and the delivery source revision. The helpers were
developed during this work; source snapshots and digests distinguish them from the
unchanged baseline business producers. Earlier private attempts remain diagnostics.

From repository root, set `PRIVATE_WPA` to the accepted external location:

```bash
TUSHARE_TOKEN='' poetry run python ui_web/scripts/private_wpa_examples.py verify --output "$PRIVATE_WPA"
TUSHARE_TOKEN='' poetry run python ui_web/scripts/private_wpa_examples.py replay-w2 --output "$PRIVATE_WPA"
node ui_web/scripts/validate_private_wpa.mjs "$PRIVATE_WPA" w2
node ui_web/scripts/validate_private_wpa.mjs "$PRIVATE_WPA" research
```

`verify` is read-only: it validates the full accepted inventory, prior-package
references, both complete W2 reproductions, formal Publication Reader export and
actual Capability facade equivalence, then invokes the existing frontend validators.
Python credential lookup, socket connections and SQLite connections are forbidden.
An independent temporary copy containing the sealed package but no Dataset cache
also passed complete verification, both formal W2 reproductions and all three
frontend validators. Its read-only verification receipt is retained beside the handoff.
Digests and reproduction establish integrity relative to retained facts, not external
market authentication or redistribution rights. Research source verification uses
its official Reader; no new Research replay engine is claimed.

Explicit fresh production uses `w2 --output "$NEW_PRIVATE_WPA"`, then
`research --output "$NEW_PRIVATE_WPA"`; both may acquire facts. Output/stages cannot
overwrite existing results. `handoff` requires explicit accepted `--r2` and `--r3`
paths and seals the index only after both stages pass. `export-research` is an
explicit recovery for a genuinely committed Publication whose offline export failed;
it uses the formal Reader, never reconstructs a Batch or reacquires data, and rejects
already accepted/sealed output. Failure markers cannot inherit an earlier PASS.

## Verification and remaining work

| Check | Actual result |
| --- | --- |
| W2 full Python suite | PASS: 540 tests |
| Research Plan/Batch/Job/Publication focused suite | PASS: 244 passed, 1 platform-specific skip |
| Research full suite | FAIL: 1273 passed, 1 skipped, 2 known V1 Synthetic fixture drift failures |
| DataLake full suite | PASS: 686 tests |
| HTTP full suite after projection extraction | PASS: 589 tests |
| Architecture/topology | PASS: 23 tests |
| New private-tool boundary tests | PASS: 10 tests |
| Backtesting/Catalog/Explorer frontend tests | PASS: 154 tests |
| Actual W2/Publication/Catalog validators | PASS; 12 negative rejection probes |
| Complete cacheless copy verification / R2–R3 references | PASS / PASS |
| Rehashed wrong Strategy / missing Evidence / corrupted stored Source | PASS: all three rejected |
| Backtesting/Research/HTTP Ruff | PASS |
| Backtesting / HTTP / Research-tests mypy | PASS: 50 / 62 / 49 files; separate invocations |
| `npm run contract:check` | PASS; all seven generated boundaries current |
| `npm run build` / `npm run lint` | PASS / PASS |
| Full Vitest default suite | FAIL: 567 passed, 13 failed in 74 files |

The Python failures are the same unchanged V1 Synthetic binary64/report fixture
drift recorded in [R3](R3_ACCEPTANCE.md). Frontend full-suite failures comprise 12
5000ms timeouts and one protected-401 login-button assertion. That assertion failed
on its first isolated rerun, passed on a second isolated rerun, and passed in a
temporary extraction of the exact required baseline using the same installed
dependencies. All frontend business source remains byte-identical to the baseline.
Keep these timing/fixture diagnostics for WP-C; the repository-wide regression gate
is **FAIL**, not waived. No formula, assertion, fixture or global timeout was changed.
Private logs retain all runs. An initial combined mypy command hit duplicate test
module names; the required module checks passed separately.

The first local attempt's URI placement audit rejected a legitimate read-only
SQLite URI; a test now covers that case. An earlier genuine Research publication
hit the unchanged HTTP verification budget during export; the shared pure projection
resolved offline delivery. A separate cacheless-check launcher initially dereferenced
the venv Python symlink and used an interpreter without dependencies; it was corrected
to the root runtime's `sys.executable`. These were tooling diagnostics, not altered
market facts or financial Producer failures.

| Technical gate | W2 M1/Q1 | Research Publication | Catalog |
| --- | --- | --- | --- |
| Real Source / formal origin | PASS | PASS | PASS: formal metadata facade |
| Formal Producer | PASS | PASS | PASS |
| Contract / identity / integrity | PASS | PASS | PASS |
| Coverage | PASS | PASS, Warm-up separately retained | PASS: metadata scope |
| Publication Rights | BLOCKED | BLOCKED | BLOCKED: separate metadata review |
| Admission to public data assets | BLOCKED | BLOCKED | BLOCKED |

Git/worktree/symlink checks and build asset scans found no private package references,
real Result bodies or Publication payloads in public inputs or built assets. Vite Demo
still has `publicDir: false`; Pages still uploads only `ui_web/dist-demo`. No deployment
workflow, static page composition, generated contract, financial calculation or
business admission range changed. Safe source/documentation changes pass the public
data-safety inspection; this does not approve real-data inclusion or a new release.

D4 has both full W2 Results, real Explorer records, genuine Catalog and verified R2/R3
references for private consumption through existing shared presentations. It must
preserve request/coverage/limitations, distinguish real-market origin from historical
Synthetic wording and avoid HTTP Run fabrication. Actual public consumption remains
blocked pending independent rights clearance. WP-B can use this private input set;
its acceptance is not claimed here. No D4–D6, Pages release, push or merge was executed.
