# D3-R1 real-market feasibility — 2026-11-13

Execution evidence under [Examples](EXAMPLES.md) and [Authenticity](AUTHENTICITY.md),
not financial authority or public-data approval. R1 assessment is complete; R2–R5
Examples, Premium Points, Basis reports and backtest PnL were not generated.

## Baseline and evidence boundary

Branch `feat/github-pages-demo`, initial clean HEAD
`751b0a8b8276f58af95570a70596f805f0951e04`: PASS. No Git remote is configured;
`ougachakaaa/hg-market-state-lab` is the requested identity, not remotely verified.
No ancestry-based cutover, merge, push, data deletion or business-code change.
Root Python 3.13.15 / `.venv`; Token presence PASS via `lab_config`, value undisclosed.
`LAB_RESEARCH_PUBLICATION_ROOT` is unconfigured.

Private evidence set **D3-R1-local-20261113** is outside the resolved Git worktree,
under an owner-only `0700` directory, supplied to scripts with `--output`.
The local handoff gives its location; no machine-private path is committed here.
Existing WP3/WP8 harness practice redirects only Dataset storage placement;
all acquisition uses real public factories/operations and real Source Captures.
No fake Source, direct SQLite query, synthetic data or modified fixture is used.
Default Dataset caches were read only. Isolated Calendar, one-day Futures/Index
caches and the two independent product Raw namespaces remain private.

Isolation PASS: the resolved evidence root is outside every worktree/Vite input;
`vite.demo.config.ts` uses a fixed repository entry and `publicDir: false`.
The only current workflow uploads `ui_web/dist-demo`, not external directories;
there are no private-root imports, symlinks or copy steps. No workflow was changed.
Default CI cannot access this local evidence set. Recheck isolation if build or CI
inputs change; do not copy these artifacts into public assets.

## Source readiness and exact-window coverage

Inclusive window **2026-01-01..2026-11-11 = 315 natural days**. Real Calendar
acquisition proves **206 CFFEX sessions and 206 SSE sessions**, including November 11.
Counts below come from public Coverage/Export, not weekdays or old WP8 results.
`M/P/F` means missing/pending/failed units. Cached means verified cache state,
not a claim of current-provider freshness or independent authentication of old facts.

| Input / identity (export schema) | Existing default cache | Actual isolated acquisition | R1 classification / remaining work |
| --- | --- | --- | --- |
| `tushare_trade_calendar/calendar` (1), CFFEX | 314/315; M/P/F=1/0/0; 205 known opens | 315/315; M/P/F=0/0/0; 206 opens | Available, Cached; default Fetch Required: November 11 |
| Same, SSE | 314/315; M/P/F=1/0/0; 205 known opens | 315/315; M/P/F=0/0/0; 206 opens | Available, Cached; default Fetch Required: November 11 |
| `tushare_equity_index_futures/futures_daily` (2), IM | 205/206 product-days; 820 contract-day rows; M/P/F=1/0/0 | November 11: 1/1 product-day, four actual contract rows; M/P/F=0/0/0 | Available, Cached; full default export still needs November 11 |
| `tushare_index_daily/index_daily` (1), `000852.SH` | 205/206 index-days; 205 rows; M/P/F=1/0/0 | November 11: 1/1 index-day, one row; M/P/F=0/0/0 | Available, Cached; full default export still needs November 11 |
| MO `opt_basic`, target day | No reusable public coverage API asserted | 312 active contracts | Available; Raw retained privately |
| MO `opt_daily`, target day | No reusable public coverage API asserted | 312 unique matching rows for all 312 active contracts | Available; no missing contract or invented row |
| Snapshot CSI1000 `index_daily`, target day | Independent product Captures executed | Each returns one exact row; Premium probe Raw write succeeds | Available; both underlying selected closes validate |
| Snapshot IM `fut_basic` / `fut_daily`, target day | Independent of DataLake coverage | 55 ordinary contracts in lifecycle catalog; four target-day rows | Available; four legitimate expiry references, two legitimate absences |

Initial full-window Futures/Index reads failed with `OperationError` because each
default Calendar lacked November 11. With only the Calendar redirected to the
complete private cache, default market Coverage/Export resolves to 205/206 above.
Missing row dates are November 11 in both exports. This is **Contract Incomplete**
for the initial prerequisite, not a Provider Failed incident. No Provider failure
occurred in the actual probes. Unknown remains explicit where final production
was deliberately not executed.

The isolated one-day successful exports are **not merged** with old exports or
relabeled as a complete 206-day producer snapshot. To prepare an existing default
cache, acquire just two Calendar natural-day units, one IM product-day (four
contract rows) and one index-day. This work is **verified obtainable and already
acquired privately**, but not installed into the default caches. For a wholly
fresh private run, ensure both 315-day Calendars and all 206 IM/index target units
through their public services. Do not copy SQLite contents or hand-stitch proofs.
Provider call count depends on metadata/pagination/batching; units are not API calls.

## Product checks and producer paths

### MO products (R2)

[Chain authority](../../../data_snapshot/src/data_snapshot/products/mo_option_chain/ARCHITECTURE.md)
and [Premium authority](../../../data_snapshot/src/data_snapshot/products/mo_option_premium/ARCHITECTURE.md)
remain separate owners. Fixed identities validate independently:
Chain `target_trade_date=2026-11-11, option_product=MO, price_type=close`;
Premium `as_of=2026-11-11, option_product=MO, price_type=close`.

Both use the five existing shared Captures. Shared source-capture evidence was
written separately into each product's own goal-scoped Raw; neither reads its
sibling Raw or final DTO. Chain's existing input validators confirm active
lifecycle universe, exact daily identity coverage, selected-price legality,
positive underlying and unique legitimate IM matching: six expiries, four matched
references, two legitimate absences. No `build_chain`/read-model payload was generated.

Premium independently completed its canonical `index_daily.capture_observation`
probe and Premium-owned Raw write: one exact observation, admitted. Its own
`basis.construct_basis` validates 312 option observations and the required index/IM
inputs. **Nonempty real Points is Unknown / BLOCKED until R2**: Point Preparation,
Framer and final Plane were intentionally not invoked. A nonempty input basis is
not claimed as a successful Plane. R2 must call the full formal service and verify
nonempty Points and complete HTTP projection.

Formal public production entries are `read_chain_with_api(api, query, raw_root)` /
`read_chain(query)` in `data_snapshot.products.mo_option_chain.service`, and
`read_premium_plane_with_api(api, query, raw_root)` / `read_premium_plane(query)` in
its Premium service. Use explicit private `raw_root` for local work.
Source exceptions mean chain unavailable / `premium_plane_unavailable`;
only a successful empty canonical observation probe proves `date_not_available`.
Admitted-observation downstream failure is never reclassified as date absence.
Regression smoke covers these distinctions; no failure was injected into real data.

### Historical Basis (R3)

[Inputs](../../../market_research/descriptive/cases/futures_basis/INPUTS.md),
[online execution](../../../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md)
and [evidence](../../../market_research/descriptive/cases/futures_basis/EVIDENCE.md)
own the route. Public facade `market_research.descriptive.cases.futures_basis`:
`FuturesBasisRequest` → `preflight_inputs` → later `prepare_inputs` /
`observe_futures_basis` → explicit `ReportRequest` / `compose_report` and reader
projection. R1 invoked only preflight and Dataset Coverage/Export.
Default preflight is `confirm_required`; with private complete Calendars it still
reports Futures/Index `needs_fetch`. No warm-up is required for Basis.
Calendar and Futures must be complete; a **legal partial final Index is allowed**
with honest unavailable-observation accounting. This is not W2's stricter policy.
Offline path: retain `futures_basis_inputs_v1` canonical inputs and the formal
report evidence package; `verify_delivery` verifies and `replay_delivery` replays.
Neither report composition nor replay was run for this new window.

### W2, both profiles (R4)

[Inputs](../../../market_backtesting/cases/futures_roll_long/INPUTS.md),
[Strategy](../../../market_backtesting/cases/futures_roll_long/STRATEGY.md),
[Evidence](../../../market_backtesting/cases/futures_roll_long/EVIDENCE.md) and
[historical WP8](../../../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md)
confirm the existing path. Facade `market_backtesting.cases.futures_roll_long`:
`FuturesRollRequest("IM", start, end, profile)` →
`create_futures_roll_service().preflight` / later `.prepare` / `.run` →
`build_backtest_result`, `validate_backtest_result` → `build_evidence_package` /
`encode_evidence_package` → `reproduce_futures_roll_evidence` offline.

Both `expiry_to_M1_v1` and `expiry_to_Q1_v1` preflights actually ran. Default
Calendar is incomplete, Futures/Index unknown. With private complete Calendar,
Calendar is complete and both markets remain incomplete, 205/206. Neither is ready
for execution from that cache. A public complete Futures export proves lifecycle
and active contract sets; actual Close, multiplier and benchmark checks follow
full `.prepare`. Both profiles initially enter one lot at first-session M1; Q1 is
the expiry roll target, not a different initial-position rule. Benchmark is derived
from public Futures rows; all required inputs must be complete. No Slots, initial
trade, capital normalization, PnL or formal Result were computed here.
WP8's 2024-01-01..2026-10-30 PASS proves an existing execution/replay route only;
it supplies zero new-window coverage. No old Result was trimmed or reused.

### Catalog and Publication (R5)

`market_research.descriptive.capabilities.list_capabilities()` and
`get_capability(id)` were called and agree: exactly
`trailing_cumulative_return_v1`, `status=supported`, `live_readiness=not_probed`.
No new capability/readiness claim was synthesized.

[Publication V1 admission](../../../market_research/PUBLICATION_STORAGE.md)
requires a completed Index Trailing Cumulative Return `BatchResult`, full retained
source evidence and exact provenance/association. Existing formal route:
explicit `ResearchPlan` → `execute_batch` → `retain_source(batch, source_id, path)` →
`publish(batch, source, context, PublicationStore(private_root))` → `list_publications`,
`get_publication_manifest`, `get_analysis`, `get_chart_view`.
R1 checked public symbols and a separate nonexistent private store's empty-list
read (no directory created), plus Publication regression tests. It did **not**
query an existing live Store or create a Batch/Publication.

Production Publication root is unconfigured. R5 must explicitly select subject,
horizon and analyses and retain any required **pre-window H-session warm-up**
separately under [Trailing Return inputs](../../../market_research/descriptive/cases/trailing_return/INPUTS.md).
That extra coverage is Unknown here; a date window alone cannot specify its amount.
Basis Online Report is not a PublishedResearchResult. No admission extension or
canonical authority gap was found; configuration, acquisition and real execution
are the remaining work.

## Publication rights matrix

Reviewed by Codex, 2026-11-13 Asia/Shanghai. Actual origin for market probes is
Tushare; DataLake and Snapshot are acquisition routes, not additional licensors.
Sources reviewed and retained privately with retrieval hashes (E6):
[User agreement](https://tushare.pro/document/1?doc_id=409),
[Data service agreement](https://tushare.pro/document/1?doc_id=405), and
[entitlement table](https://tushare.pro/document/1?doc_id=290).
The public pages show no explicit effective-version date; retained content hashes
identify this review's versions. Service agreement II(2)(5) limits the stated
license to personal, noncommercial viewing/use, subject to valid account rights.
The entitlement table concerns access, not redistribution. No account-specific
public license, exchange/CSI redistribution clearance or derived-output exception
was supplied or discovered. Source attribution does not supply those permissions.

`L` below is a conditional local-access PASS for this bounded personal research
probe using the configured account and successful official endpoint access; account
ownership, special contract and commercial/institutional permissions were not audited.
It is not a general legal clearance. `B` = BLOCKED, rights unresolved, private only.
For derived outputs, local generation is a permitted next development step within
the same personal research scope; it is not recorded as already executed.

| Source / output | Local acquisition / research | GitHub source distribution | Pages static display | Copy / CSV / JSON download | Public derived results / charts | Review basis / release condition |
| --- | --- | --- | --- | --- | --- | --- |
| Calendar, CFFEX/SSE | L | B | B | B | B | Tushare terms; explicit channel-specific permission required |
| IM Futures Daily, including basic metadata | L | B | B | B | B | Same; include exchange-origin facts and retained input scope |
| CSI1000 Index Daily, including identity metadata | L | B | B | B | B | Same; index-provider/exchange rights unresolved |
| MO Option Basic / Daily and complete Chain body | L | B | B | B | B | Same; full-body redistribution/export not cleared |
| Derived Premium Plane | L | B | B | B | B | No reviewed derived-data exception; full body and exports require clearance |
| Basis Report / statistics / Views | L | B | B | B | B | Derivation does not establish public rights; include embedded evidence |
| W2 Result / trades / rolls / Views | L | B | B | B | B | Same; review actual retained facts and downloadable/reachable assets |
| Research Publication / Analysis / ChartViews | L | B | B | B | B | Same; full retained source is an additional distribution surface |
| Capability metadata only | PASS | PASS* | PASS* | PASS* | PASS* | Repository-authored description, root AGPL-3.0 terms; preserve license obligations, no market facts |

`*` Limited metadata review; no new public Example/package was admitted. Repository
source licensing does not relicense third-party market facts. Overall market
Publication Rights **BLOCKED**, not a proven infringement FAIL. Obtain documented
permission covering the exact outputs, raw/derived treatment, channels, attribution
and downloads; then independently review the actual release artifact. Public
BLOCKED does not prevent the lawful private work described above.

## Seven-target acceptance and next-package readiness

`Exact availability` means an execution-ready full formal input proof, not merely a
working API. `Path PASS` means the implementation and smoke path exists, not that
new-window output execution passed. Isolation PASS applies to every row.

| Target | Source access | Exact availability | Formal producer path | Current coverage / additional acquisition | Isolation | Public rights | Next WP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MO Option Chain | PASS | PASS (inputs only) | PASS | 312/312; index 1; IM 4; retain independent Raw and execute full producer | PASS | BLOCKED | R2 may start privately; output/schema gates pending |
| MO Premium Plane | PASS | PASS (inputs only) | PASS | Probe 1, Basis 312; Points nonempty BLOCKED until full R2 production | PASS | BLOCKED | R2 may start privately; no successful Plane asserted |
| IM Historical Basis | PASS | BLOCKED | PASS | Default 205/206; private calendars complete and missing day acquired separately; ensure/export one coherent full input set | PASS | BLOCKED | R3 may start with acquisition; formal output not ready |
| IM Roll Long M1 | PASS | BLOCKED | PASS | Same gaps; strict complete inputs and final lifecycle/Close validation required | PASS | BLOCKED | R4 may start with acquisition; execution not ready |
| IM Roll Long Q1 | PASS | BLOCKED | PASS | Same as M1; separate profile/result/evidence validation | PASS | BLOCKED | R4 may start with acquisition; execution not ready |
| Capability Catalog | PASS (local metadata) | PASS (no market window) | PASS | One actual descriptor and matching detail; no acquisition | PASS | PASS* | Metadata part of R5 can start |
| Publication Explorer | PASS for tested shared sources; warm-up Unknown | BLOCKED | PASS | No new Batch/Publication; root, explicit plan and H-session preparation pending | PASS | BLOCKED | R5 can start preparation; completion blocked on real evidence |

**Technical feasibility PASS; full-window execution/cache readiness BLOCKED;
public market release BLOCKED.** There is no evidenced inaccessible target or
business implementation FAIL. Resolve blockers by producing coherent complete
public exports (R3/R4), verifying nonempty formal Premium Points (R2), and retaining
an admitted completed real-input Batch and linked Publication (R5). None requires
new business semantics, storage compatibility or old-run migration.

Recommended next WP: **D3-R2**, using already captured exact-day real facts through
the two formal producers, preserving separate Raw and private result packaging.
Then R3 restores coherent IM/calendar/index inputs; R4 may reuse legally retained
public facts but produces its own two full executions/evidence packages. R5 handles
metadata plus an explicit admitted Trailing Return plan and its warm-up evidence.
R6 audits private technical results and independently gates public admission.
Stop after this R1 commit; do not automatically execute R2.

## Private evidence index and verification

All E references resolve inside D3-R1-local-20261113, never public assets. Private
scripts accept `--output`; preserve their version and source revision before replay.

| Ref | Private files / meaning |
| --- | --- |
| E1 | `baseline.json`: initial configuration presence, default public coverage/preflights and isolation observations |
| E2 | `provider.json`, `calendar_CFFEX.json`, `calendar_SSE.json`: actual full-window Calendar ensure/export; `probe.py` invocation |
| E3 | `futures_cache_export.json`, `index_cache_export.json`, `target_day.json`, `target_futures_export.json`, `target_index_export.json`: separate existing-cache and fresh target-day proofs; `target_day.py` |
| E4 | `raw/mo-option-chain/2026-11-11/`, `raw/mo-option-premium/2026-11-11/`, `source_capture/`, `input_checks.json`: separate Raw, exact input validators and preflights; `input_checks.py`; no final product payloads |
| E5 | `catalog.json`, `target_day.json`: actual descriptors and isolated empty Publication reader smoke |
| E6 | `rights-sources.json`, `terms-405.html`, `terms-409.html`, `terms-290.html`: reviewed pages and SHA-256 retrieval evidence |
| E7 | `smoke-tests.log`, `verification.json`, `evidence-index.json`: validation outcomes, isolation checks, source revision and retained artifact SHA-256 inventory |

Offline R1 integrity check: hash each retained artifact against `evidence-index.json`,
inspect exact public coverage/envelopes and replay `input_checks.py` against retained
Raw with network disabled. This checks input consistency, not final financial replay
or external authenticity. `probe.py` and `target_day.py` reacquire live inputs and
are separate explicit operations, not an offline integrity command. Their ordinary
JSON diagnostics are not substituted for formal R3/R4 canonical evidence encodings.

Verification: repository/branch/HEAD and private isolation checks PASS;
actual Provider/Coverage/availability checks PASS within the bounds above;
377 selected Dataset/Product/preflight/Publication/topology/architecture tests PASS.
These deterministic tests use controlled inputs and are separate from the actual
Source probes. All 23 local documentation links/anchors and staged diff checks PASS;
offline input validation also passed with socket connections disabled.

Frontend `contract:check`, `build`, `lint`: PASS. Full default `npm run test`:
570 passed / 10 failed (nine timeouts and one missing-login assertion).
`npm run test -- --maxWorkers=1`: all 580 assertions in 74 files passed, but the
command still **FAILS** with two uncaught `window is not defined` timer errors from
React / `@rc-component/util` after `FuturesBasisPage.test.tsx`. This pre-existing
code was not changed; the run is not claimed green. Resolving that regression
gate is separate from R1's successful actual-source and Python checks. A targeted
rerun of `FuturesBasisPage.test.tsx` passed all eight tests (exit 0); it does not
erase the full-suite uncaught-error result.
