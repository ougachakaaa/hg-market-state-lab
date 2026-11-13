# D3-R2 private real MO Examples — 2026-11-13

Execution evidence under [Examples](EXAMPLES.md) and [Authenticity](AUTHENTICITY.md).
Technical acceptance **PASS**; market Publication Rights **BLOCKED** under the
retained R1 review. This does not approve Git/Pages redistribution or D4 composition.

Baseline/source revision: `df1ea10054931f0cc5994ebd039eabf0d9a4f6f6`, branch
`feat/github-pages-demo`, initially clean. Product, HTTP projection, generated schema,
V1/D2 fixtures and deployment workflow are unchanged. No data was deleted.

## Actual execution and coverage

R1 evidence `D3-R1-local-20261113` was located through the local evidence directory
and README handoff; retained references passed its SHA-256 index. R2 independently
reacquired each Product's inputs through a real configured Tushare client, using
root Poetry and explicit external Raw roots. R1 Raw was retained for comparison,
never injected as a Source API or substituted for either Service's new captures.

| Gate / actual coverage | Chain | Premium |
| --- | --- | --- |
| Real Source acquisition | PASS; eight actual endpoint calls | PASS; eight actual endpoint calls |
| Owning application entry | `mo_option_chain.service.read_chain_with_api` | `mo_option_premium.service.read_premium_plane_with_api` |
| Fixed request | 2026-11-11 / MO / close | 2026-11-11 / MO / close |
| Product execution | PASS; complete OptionChain | PASS; complete PremiumPlane |
| Active contract / exact-day daily coverage | 312 / 312 | 312 / 312 |
| Actual Points | 312 option records | 312 genuine analytical Points |
| Expiries | 6 | 6 |
| Legitimate IM references / absences | 4 / 2 | 4 / 2 |
| Selected option nulls / zeros in this capture | 0 / 0 | 0 / 0 |
| Official HTTP projection + Python DTO | PASS; `to_chain_dto` | PASS; `project_plane` |
| Existing frontend generated-schema validator | PASS; `validateOptionChain` | PASS; `validatePremiumPlane`, including nonempty Points |
| Private package offline verification | PASS | PASS |
| Public source / Pages / downloads / derived output rights | BLOCKED | BLOCKED |

Acquisition intervals (Asia/Shanghai): Chain **10:57:41–10:57:43**, Premium
**10:57:43–10:57:45**, 2026-11-13. Full timezone-aware UTC timestamps and per-call
start/end/status/query/row counts are retained privately. Endpoints are `opt_basic`,
`opt_daily`, `index_daily`, `fut_basic`, `fut_daily`; retained Capture identities are
`mo_option_basic`, `mo_option_daily`, `index_daily`, `im_futures_basic`,
`im_futures_daily`. The underlying is the required exact CSI1000 observation.

Both Services ran their complete canonical pipeline. Premium's successful Service
executes observation probe → independent captures/Raw → OptionMarketBasis → Point
Preparation → PremiumPlaneFramer → PremiumPlane. HTTP serialization uses Pydantic
`by_alias=True`, preserves `yield`, all 16 metric coordinates per Point and all nulls.
No financial calculation, repair, fabricated cell, server Run or browser metric
computation was introduced. The frontend validators return the original payload;
Premium's rawPayload and plane reference that same object. An explicit empty-Points
negative check rejects success. Source/result identity, strike, selected Close,
reference coverage and ordering comparisons pass independently for each Product.

R1 comparison: no added/removed contract identities, unchanged 312 contracts/six
expiries, and all five corresponding Raw files byte-identical within each Product.
Counts were observed, never forced. Genuine null/zero cases are absent in these
captures; existing controlled regression tests cover their semantics.

## Private package and verification

Private identity **D3-R2-local-20261113-v1**, profile `d3-r2-private-mo-v1`, Example
revision 1. The exact external location is in the local `D3-R2-HANDOFF.md`, outside
Git and build inputs; it is intentionally not committed. Package layout:

```text
manifest.json + manifest.sha256
chain/response.json + source-calls.json + r1-comparison.json
chain/raw/mo-option-chain/2026-11-11/*.json
premium/response.json + source-calls.json + r1-comparison.json
premium/raw/mo-option-premium/2026-11-11/*.json
r1-index.json + r1/{provider.json,input_checks.json,raw/...}
frontend-validation.json
tooling/{private_mo_examples.py,validate_private_mo.mjs}
```

The manifest inventories 32 files with byte lengths/SHA-256, binds separate Example
identities, source revision, acquisition times, Raw/result references, official
projection, coverage, limitations and blocked rights. These are **Demo provenance
digests**, not a new official Product input fingerprint. The detached manifest
checksum detects accidental changes; neither hashes nor locally retained provider
facts independently authenticate an exchange or grant redistribution rights.

Before execution, the owner-only external directory was checked against all Git
worktrees and repository symlinks. Vite's fixed Demo entry has `publicDir: false`;
Pages uploads only `ui_web/dist-demo`. No private package is imported or copied to
Vite/build/public/test/CI assets. Build-config/workflow hashes are recorded privately.
Credentials are loaded only by the canonical Source factory through `lab_config`;
only endpoint queries, timestamps, statuses and row counts are logged.

From repository root, set `PRIVATE_R2` to the handoff's existing absolute package
path, then run this credential-free, read-only operation:

```bash
poetry run python ui_web/scripts/private_mo_examples.py verify --output "$PRIVATE_R2"
```

It verifies manifest association, complete file inventory, hashes, retained R1
references, published Python DTOs, fixed requests, complete option identities,
source Close/strike/context, legitimate IM references, deterministic ordering and
actual coverage. It invokes the existing TypeScript validators through Vite SSR
without an HTTP listener. Python network connections are disabled during verify;
no token lookup or live acquisition occurs. It also passed with `TUSHARE_TOKEN`
unset. Verification detects modified manifests/results, missing source artifacts,
wrong queries, missing Points, changed prices even after rehashing, and cross-Product
Raw references (seven private negative checks).

Financial metrics are protected by complete producer payload hashes and the
published schema; offline verification does **not** recompute their formulas or
replay the observation probe. The current public Services require a Source client;
no pure offline replay API is published. Full financial reproduction uses an
explicit new live acquisition and may not be byte-identical to retained facts:

```bash
poetry run python ui_web/scripts/private_mo_examples.py acquire \
  --output "$NEW_PRIVATE_R2" --r1 "$PRIVATE_R1"
```

Both arguments must identify external absolute locations; output must not already
exist. Acquisition never overwrites a retained package. Incomplete tooling attempts
remain private and are not accepted packages. An initial evidence check incorrectly
expected `opt_code=MO`; it was corrected to the existing Capture's Source identity
`OP000852.SH`. A Vite optimizer log initially interrupted receipt parsing; the
validator runner now suppresses Vite informational logs. Neither issue changed a
Product or its financial output. The final package was independently reacquired,
sealed and verified using the corrected tooling.

## Regression and next consumption boundary

| Check | Actual result |
| --- | --- |
| `poetry run pytest data_snapshot/tests ui_http/tests -q` | PASS: 875 tests |
| `poetry run ruff check data_snapshot ui_http` | PASS |
| `poetry run mypy data_snapshot ui_http` | PASS: 118 source files |
| `poetry run ruff check ui_web/scripts/private_mo_examples.py` | PASS |
| `npm run contract:check` | PASS; all seven generated boundaries current |
| `npm run test -- src/features/mo_option_chain src/features/mo_option_premium` | PASS: 123 tests / 21 files |
| `npm run build` / `npm run lint` | PASS / PASS |
| `npm run test` | FAIL: 569 passed, 11 default 5000ms timeout failures / 74 files |
| Full single-worker frontend rerun | NOT RUN in R2; R1's 580 assertions plus uncaught React timer/window errors remain a recorded FAIL |
| Private frontend acceptance / offline verification / seven negative checks | PASS / PASS / PASS |
| D4/browser composition / deployment | NOT RUN; outside R2 |

No unrelated assertion or timeout was relaxed. The full-suite failures are reported
separately from the successful real-data acceptance. See [R1](R1_FEASIBILITY.md)
for the historical default-timeout and single-worker uncaught-error evidence.

D3-R3 historical Basis and D3-R4 W2 production remain separate work. D4 must consume
these complete validated Results through the existing shared presentations, retain
fixed request/source/coverage disclosure, preserve full Raw/Copy/Export and all
Premium coordinates, and introduce no Product logic or HTTP Run lifecycle. Public
consumption additionally requires independent documented rights clearance and
review of actual release assets. Seven-page composition, R5 and deployment are not
started here. Stop after D3-R2 for review.
