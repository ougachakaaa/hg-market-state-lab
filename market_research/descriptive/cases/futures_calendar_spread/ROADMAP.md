# Calendar Spread L1 work packages and reconciliation

Specializes [the case](ARCHITECTURE.md). This document owns delivery sequencing,
acceptance and WP0 reconciliation, not competing financial or numerical formulas.

## Baseline and status

WP0 starts on `develop` at `f63327fe887d154f68a85dcc479c24844564baec`, exactly the
requested baseline, with a clean worktree. Only Authority and navigation Markdown
are changed. WP0 performs no business tests, dependency installation, generated
contract update, cache mutation, build or publication. Commit identity is reported
in the task report/Git history rather than self-embedded in the commit's contents.

WP0 semantic and navigation review is complete as recorded below. WP1 delivers
the public pure financial API after baseline
`303c34ce6352073f76370b9f25e919b2bbd4a2e3` on the existing `develop` branch.
WP1 verification and closure are recorded below. WP2 implements read-only input
preparation and pure Pair-day construction after baseline
`cb9f778ae72cb5a331ea890b61bda99c8d8777d8` on the existing `develop` branch.
WP3 implements the Statistics method after baseline
`b83ef47672d8f58a9490335fb1500d58def287f1` on the existing `develop` branch.
WP4 implements independent Python Daily / Historical Relative Value queries after
baseline `f957342039b4137d224b0c9cc2eee9cd44623c5b` on `develop`.
WP5–WP7 remain **NOT IMPLEMENTED / NOT VERIFIED** for this case.

## Implementation work packages

| WP | Deliverable and boundary | Acceptance criteria |
| --- | --- | --- |
| WP1 | New case public pure financial calculation, immutable named result and explicit failures, under [Definition](DEFINITION.md) and [Application](APPLICATION.md) | Same inputs yield the same three metrics; verify positive/negative/zero spread, units/version, logarithmic formula versus linear, actual expiry spacing versus near DTE, equal/reversed expiry rejection, date-only types, finite positive prices, bool/nonfinite rejection and overflow/underflow failure. No upstream I/O, Basis formula change or frontend calculation. |
| WP2 | Read-only Input Preparation and Pair-day Observation, consuming the existing public Slot resolver | Verify complete Calendar/Futures proof, schema/scope/window/counter/row validation, missing-proof/incomplete-export failures, no ensure/fallback, six-pair accounting, true identities across transitions, closed day versus proven-empty open day, nonpositive exclusions, stages at DTE 0/7/8/21/22 and retained full public input evidence. Synthetic tests use injected public services, not real cache. |
| WP3 | Statistics public EmpiricalPercentile Spec/Result, root facade dispatch and numerical backend integration | Satisfy [method fixtures](../../../../market_statistics/EMPIRICAL_PERCENTILE.md), especially ties/all-equal/singleton, exact counts, query order, unchanged units, validation precedence, immutability and backend-result failure. Existing Quantile/IntervalCount/Mean contracts remain unchanged. No Research/domain imports or new dependency. |
| WP4 | Independent Daily and Historical Relative Value Python queries sharing WP1/WP2 and consuming Statistics | Verify all six pairs and three metric choices; strict pre-evaluation cutoff, history_start boundary, product/pair/stage isolation, stage and all-stage linkage, repeated-value multiplicity, empty and 1/29/30 sample behavior, unavailable current observations, optional explicit-edge histograms and outside counts, unit/method/sample association and propagation of statistical failures. Compare both products' current metrics from the same retained inputs. |
| WP5 | Two independent formal HTTP products, DTO projection, composition and OpenAPI | Verify actual query delegation, strict parsing and classified error mapping under each HTTP plan, existing authentication/same-origin requirements, no-store, complete finite projection, ordering/null/zero, successful empty/small outcomes and absence of writes/Run lifecycle. Publish actual OpenAPI; no HTTP formula or DataLake import. |
| WP6 | Two independent Web consumers and shared public Presentation | Generate each consuming feature's types from delivered OpenAPI. Verify explicit controls, query versus local pair selection, current/historical labels and units, empty/small/excluded states, histogram outside values, request cancellation/stale-result handling and preserved financial/source limitations. Register routes/cards only with actual consumers; no frontend metric/statistical computation. |
| WP7 | Formal HTTP Demo captures, two Bundles, static composition and content requirements | Use explicit real available Presets, complete formal Results and existing admission/transaction/build machinery. Verify request/Result associations, hash/Manifest membership, invalid/missing rejection, failed capture preserving active data, shared Presentation and an actual offline build artifact. Do not invent results or Run identities. No publication/merge is implied. |

Dependencies: WP2 consumes WP1; WP3 is numerically independent and can run alongside
WP1/WP2; WP4 depends on WP1–WP3; WP5 depends on WP4; WP6 depends on WP5; WP7 depends
on WP5–WP6. These are sequencing permissions, not instructions to delegate work.
Each implementation package follows root scoped verification: select directly
changed cases/files, never restore full-module, browser-matrix or full-repository
gates. Real-data, browser, platform and publication claims require separately
requested, actually executed evidence. WP7's actual new Demo build is necessary
to establish its own artifact delivery, not a WP0 check.

## Reconciliation: authority and current code

Review basis: repository/module authorities; Futures Basis definition, Inputs and
Slot Resolution; DataLake Calendar/Futures public services and Futures facts;
Statistics public contract/methods/backend; HTTP product catalog and Basis delivery
boundary; Web Workspace/Feature/Presentation and Demo Bundle/Build/Release authorities.
Public exports and Slot resolver/Statistics dispatch source were inspected read-only.

| Concern | Finding and decision | WP0 result |
| --- | --- | --- |
| Independent Case | Research/Descriptive permit independent no-Horizon cases. New case specializes those boundaries without changing scalar dispatch or admitting a Plan/Batch/Publication. | PASS — authority reconciliation |
| DataLake sufficiency | Calendar schema 1 and Futures schema 2 publish candidate dates, Close, identity and delist_date (last trading day), with complete product-day proof. No Index/Snapshot or DataLake extension is needed. | PASS — public capability review |
| Slot reuse | Existing facade exports `ContractMetadata`, `DailyUniverseEvidence`, `DailySlotResolution` and `resolve_daily_slots`; implementation is pure and accepts complete metadata/evidence. New caller permission is explicit in the existing Slot authority. No private imports or duplicate resolution. | PASS — source/contract review |
| Basis independence | Existing preparation also fetches SSE/Index facts and its financial/statistics/run contracts are case-specific. Do not reuse those workflows, carriers or formula by masquerading as Basis. | PASS — boundary reconciliation |
| Shared metrics | No existing Calendar Spread public financial capability was found in reviewed public surfaces. WP1 adds it under the new case; both products consume it. | NEW IMPLEMENTATION — not runtime PASS |
| Quantile and Histogram | Root `market_statistics` exports NumericSample, QuantileSpec, IntervalCountSpec, results, compute and validate_spec. Reuse unchanged Type 7 and explicit-edge interval accounting. | PASS — public API reuse review |
| Empirical percentile | Current Statistics union/dispatch has Quantile/IntervalCount/Mean only. Existing extension rules require a separate numerical method contract. WP0 adopted midrank semantics as its statistical method design, not an explicitly confirmed user ties choice; WP3 still must implement/export it. | AUTHORITY RESOLVED; runtime OPEN until WP3 |
| Historical relative value | New Pair-day population, expiry stages, cutoff, sample-size interpretation and two assessment bindings belong to Research. No current Basis statistics adapter is reused. | NEW IMPLEMENTATION — WP2/WP4 |
| HTTP | Existing composition permits Research public case facades. Planned products use that boundary and existing Auth; no adapter-owned business rules or new server identity. | AUTHORITY RESOLVED; runtime OPEN until WP5 |
| Web | Two planned independent features fit Daily Data and Research. Feature catalogs distinguish planned authority from implemented routes/cards; no sibling semantic state is shared. | AUTHORITY RESOLVED; runtime OPEN until WP6 |
| Demo | Existing required membership remains seven Bundles. Future two-product cutover is separately planned and consumes complete formal HTTP Results, with no claim of existing data/build/release readiness. | AUTHORITY RESOLVED; runtime OPEN until WP7 |
| W2 and future levels | W2 Position-Driven Core/Policy, Futures Basis identity/formulas and L2/L3 remain untouched. No future framework or empty implementation is created. | PASS — scope review |
| Point-in-time limit | DataLake does not promise historically known metadata. Historical date cutoff excludes future observations but cannot establish point-in-time metadata. Retain the producer limitation in results and disclosure. | KNOWN LIMITATION — not a WP1 blocker |

## WP0 acceptance and open issues

Diff review confirms Markdown-only changes, separate canonical ownership of financial,
observation, statistical, transport, Presentation and Demo concerns, and no change
to current runtime behavior. Directed navigation review follows Research module →
Descriptive → case → specialized contracts, Statistics entry → percentile contract,
HTTP catalog → planned products, Web catalog/Workspace → planned features and Demo
entry → future integration. Links added/changed by WP0 are checked locally; no
whole-repository link scan or business tests are required.

The confirmed L1 choices include annualized ratio as default metric,
explicit historical start, retained small-sample numbers with warning, and the
limited favorable-direction interpretation. Midrank ties are the statistical method
design adopted by WP0; the prior discussion did not explicitly confirm this ties
rule as a user choice. Statistics remains unimplemented pending WP3; WP1 does not
change its mathematical definition. Stage boundaries, default quantile
points, threshold 30, optional explicit-edge Histogram and read-only synchronous
query behavior are the recorded L1 defaults. No unresolved business decision needs
user adjudication before WP1. Runtime gaps in the table are assigned work, not
authority contradictions or evidence that an unimplemented capability passed.

WP0 ended at its independent documentation commit; WP1 ended at its separate
financial-core commit. Each task stopped at its own package boundary.

## WP1 reconciliation and acceptance

The WP1 API specializes Application without changing Definition formulas, sign,
units or written binary64 operation order. Exact built-in int/float input acceptance,
strict date-only validation and separate validation/calculation exception types
are now explicit. No blocking financial semantic conflict was found. Basis formulas,
public APIs and private modules are neither reused nor changed.

Directed acceptance uses only `market_research/tests/test_futures_calendar_spread_financial.py`;
PASS — 71 deterministic cases cover signs/zero, logarithmic annualization, real
last-trading-date spacing, cross-year/leap-day/one-day dates, finite extreme values,
strict validation, numerical overflow/ratio underflow, metric identity/units/version,
immutability, deterministic execution and prohibited network access.

With this directed acceptance, WP1 is **READY TO CLOSE** and WP2 Input Preparation
& Pair-day Observation is **READY FOR IMPLEMENTATION**. No blocking financial
authority drift was found. At WP1 closure, WP2 and all later WPs remained
unimplemented/unverified; current WP2 status is recorded below.
Basis formulas/API and unrelated modules are unchanged by complete diff review.
No full regression, architecture scan, browser, live-market or deployment checks
were run; those are NOT VERIFIED and not WP1 acceptance requirements.

Deferred reconciliation items, outside WP1: review synchronous query delivery and
its operational constraints in WP4/WP5; reconcile Ensure interaction and read-only
input availability in WP2/WP4 (WP2 findings below); reconcile the formal Release Gate
before actual WP7 publication. Existing authority remains in force pending those reviews;
WP1 creates no query, Ensure or release behavior.

## WP2 reconciliation and acceptance

WP2 publishes immutable preparation, retained public evidence, ordered day/pair
outcomes, accounting and classified exceptions under Application / Inputs /
Observation. These details belong to those existing narrow contracts; no new
framework, storage or authority layer is needed. Financial Definition and WP1
API are unchanged. Only public DataLake Calendar/Futures interfaces and the
existing public Slot resolver are consumed; no Basis preparation, Index/SSE,
private upstream dependency or second financial formula is introduced.

PASS — 136 synthetic public-service cases in
`market_research/tests/test_calendar_spread_inputs.py` and
`market_research/tests/test_calendar_spread_observations.py` verify final-export
proof/payload validation, exact requests/read-only order, error classification,
retained immutable evidence, six-pair ordering/accounting, signs/zero, financial
and Slot delegation, expiry-day / next-open-day transitions, month/quarter/year
boundaries, stages 0/7/8/21/22, closed/empty/excluded outcomes, malformed retained
inputs and numerical/Slot failures. Construction is tested with network, file,
service factory and clock access forbidden. Unexpected service/Slot programming
exceptions propagate instead of being labeled incomplete inputs.

WP2 is **READY TO CLOSE** by deterministic synthetic acceptance and source/diff
review. This is not real-market acceptance. Real cache/provider integration,
real market metadata, platform/browser/deployment and broad regression are
**NOT VERIFIED**, deliberately not executed. No live caches were accessed or
changed and no acquisition, merge or publication was performed.

Read-only/no-ensure impact: missing, pending or failed cache units cause explicit
preparation failure; this API cannot make absent facts available. Operators must
prepare the selected caches separately through existing DataLake public operations.
Independent Exports have no shared acquisition-time/freshness guarantee. Complete
product-day coverage is trusted as producer proof of empty vs full universes;
Research does not independently recreate the catalog. Retained metadata is not
asserted to be known on the historical trade date. These are existing boundaries,
not authority defects requiring new upstream behavior. WP2 resolves the scoped
Ensure review without enabling Ensure; query-operation review remains for WP4/WP5,
and the formal Release Gate remains for WP7.

At WP2 closure, WP3 was independent of WP2 and ready for its separately scoped
numerical implementation; the WP0 Midrank design attribution is unchanged. WP4 then had its
WP1/WP2 financial/input/Observation dependencies available, but remained **NOT READY
for complete implementation/closure until WP3 is delivered**. Do not begin WP3 or
WP4 as part of WP2.

## WP3 reconciliation and acceptance (2026-11-16)

**IMPLEMENTED** — the Statistics root facade exports EmpiricalPercentileSpec,
EmpiricalPercentileResult and immutable EmpiricalPercentileQueryResult. The public
Spec/Result unions, sample-free validate_spec and sole public numerical operation
compute include `empirical_percentile`, estimator `midrank_v1`. Generic formulas,
DTO semantics and backend conformance remain owned by Statistics, not this case.
WP0's design attribution is retained as history; WP3's execution request explicitly
freezes Midrank V1. No remaining numerical decision blocks this method.

PASS — 94 directed cases in `market_statistics/tests/test_empirical_percentile.py`
and `market_statistics/tests/test_public_api.py` cover exact L/E/G and standard
fractions, ties/all-equal/singleton, negatives/signed zero, exact binary64 ties,
query order/repeats/outside range, unit propagation, invalid inputs, sample-first
precedence, standalone validation and compute revalidation, public typed dispatch,
immutability/determinism and malformed backend values/shapes/counts. Scoped backend
exceptions, warnings and floating-point errors fail explicitly. Existing three
public method dispatch examples pass; their implementations and formulas are unchanged.

WP3 is **READY TO CLOSE**. WP4 is **READY FOR IMPLEMENTATION** with WP1–WP3
available through their public boundaries. WP4 Research queries are not delivered
or started. Source association, read-only/no-ensure availability and synchronous
query-operation concerns remain WP4/WP5 tracking items; WP3 changes none of them.
No Research runtime, HTTP, Web, Demo, W2, dependencies, persistence, caches or
market data were changed. Broad regression, architecture scans, real-market,
browser, platform, build and deployment checks were not run and are **NOT VERIFIED**.

## WP4 reconciliation and acceptance (2026-11-16)

**IMPLEMENTED** — the public case facade publishes `query_daily_spreads` and
`query_historical_relative_value`, immutable explicit requests/results and nested
analysis carriers, plus `CalendarSpreadQueryError`. [Application](APPLICATION.md)
owns operations; [Query Results](QUERY_RESULTS.md) owns the independent result and
association contract; [Relative Value](RELATIVE_VALUE.md) retains sole population
policy. No financial formula, Statistics contract or WP2 construction is changed.

Both queries call the existing preparation/construction once. Historical derives
all six pairs × four groups and the current snapshot from one inclusive-window
ObservationSet. A strict `< evaluation_date` cutoff excludes the current day from
every historical sample. Results retain ordered dated values, real contract rows,
stages and source evidence for future curves and inspection. Stage/all-stage
projections share immutable sample points. Quantile Type 7, optional explicit-edge
IntervalCount and Midrank V1 are consumed through root Statistics, with concrete
Spec/Result/sample associations and no consumer numerical algorithms.

PASS — 98 WP4 synthetic cases in `market_research/tests/test_calendar_spread_queries.py`
across two scoped runs (97 initially, then the additional historical-exclusion /
all-closed case). Seven selected existing public API cases also pass: WP1 identity /
units; WP2 exact read-only preparation (four products) and financial/Slot delegation;
WP3 standard midrank fixture. Total: **105 passed**, no full-module regression.

Acceptance includes all four products and three metrics/units, six pairs/four
stages, exact one-preparation/one-construction delegation, fixed quantile parameters,
actual WP3 calls, duplicates, date cutoff/start inclusion, and true identities
across contract rolls without artificial continuous returns. An extreme evaluation
price leaves historical distributions, quantiles, sample counts and percentile
reference samples unchanged. N=0/1/29/30 gives the required statuses, preserving
small-sample numbers/warnings. A missing matching-stage sample stays empty even
with an available all-stage sample. Closed/empty/excluded current observations,
legitimate zero, histogram not-requested/outside counts, invalid-before-I/O,
statistical failures/mismatches, seven failure categories, retained evidence,
immutability, determinism and no extra I/O/Ensure are covered.

Changed source/test Ruff and diff review pass. A targeted mypy invocation reports
two existing imported-source diagnostics: WP2 `validation.py`'s CoverageResult
argument shape and Futures Basis `statistics.py`'s handling of the WP3-extended
Statistics union. No new-file type diagnostic was reported, but the invocation
is **NOT PASS**. These adjacent typing issues are unchanged and were not repaired
or suppressed as part of WP4.

Source reconciliation: WP2's `prepared_inputs.futures_export` reference resolves
through each full query result's `prepared_inputs` projection to the one complete
retained final Export, including its request/proof; tests confirm actual row links.
No digest, fabricated provenance, arbitrary reference evaluation or second raw
collection is introduced. Result identity is operation + case/definition + exact
echoed request, suitable for later formal projection; it is not a Run identity.

Read-only/no-Ensure reconciliation is complete for the Python queries: missing,
pending or failed cache units fail explicitly, never auto-acquire or become empty
samples. Operators prepare caches separately. Independent snapshot freshness and
historical metadata limits are disclosed in returned SourceContext. WP5 still
must assess synchronous window-size memory/latency, concurrency, response volume,
transport limits and safe DTO/error projection. No arbitrary limit, asynchronous
execution or persistence is added by WP4.

WP4 is **READY TO CLOSE** by this directed synthetic acceptance and complete
source/diff review. WP5 HTTP Delivery is **READY FOR IMPLEMENTATION**, without
claiming HTTP delivery or operational/performance readiness. WP5 is not started.
Real-cache/provider integration, true-market results, workload performance,
platform/browser/deployment and broad regression remain **NOT VERIFIED**.
No cache/data changes, dependencies, HTTP/Web/Demo, Publication, W2, merge or
publication occurred; work stops at WP4.
