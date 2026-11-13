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
