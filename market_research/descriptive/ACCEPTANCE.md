# Descriptive implementation acceptance authority

This document specializes the [Descriptive entry](ARCHITECTURE.md). It owns readiness,
reconciliation and cross-contract acceptance gates; detailed contracts remain with their
linked owners. Implementation Ready means no further business decision is required for
the stated scope, not that runtime or live-data acceptance exists.

## Implementation readiness matrix

| Work package / case | Semantic readiness | Runtime / remaining limitation | Canonical owner |
| --- | --- | --- | --- |
| Asset-agnostic scalar Observation | Implementation Ready as abstract contract | No producer; each new series needs explicit fact/calendar/metric binding | [Observation](OBSERVATION.md) |
| Index Trailing Return, complete or legal partial facts | Implementation Ready with explicit canonical index_code, dates and H | No implementation; live CSI1000 identity and data acceptance unperformed | [Case](cases/trailing_return/ARCHITECTURE.md), [inputs](cases/trailing_return/INPUTS.md), [identity](cases/trailing_return/INPUT_IDENTITY.md) |
| Converter / association with missing and coverage context | Implementation Ready | No converter/association; zero eligible fails conversion | [Integration](ANALYZE_INTEGRATION.md) |
| Single Job / Batch | Implementation Ready | No executors; final Success still requires every declared analysis/association | [Execution](EXECUTION.md) |
| Analyze NumericSample, Quantile, IntervalCount | Existing contracts remain Implementation Ready | No package or installed statistical API; no market missing-value responsibility | [Public contract](../../market_analyze/CONTRACT.md), [Quantile](../../market_analyze/QUANTILE.md), [IntervalCount](../../market_analyze/INTERVAL_COUNT.md) |
| Individual-stock return Observation | Abstractly allowed; not ready as concrete case | Upstream Capability Gap: no stock daily Public Service in current DataLake catalog. Semantic Gap: identity/calendar binding and raw versus adjusted return/corporate-action convention require formal case decisions | [Subject contract](OBSERVATION.md), [published catalog](../../data_lake/DATASETS.md), [selection policy](../UPSTREAM.md) |
| Index futures, commodity futures, other market series | Abstractly allowed; no return case declared | Existing index-futures Dataset alone does not decide contract selection/roll/price-return/calendar semantics. Commodity/other bindings unreviewed, not claimed supported | [Subject contract](OBSERVATION.md), [selection policy](../UPSTREAM.md) |

Stock fact-service capability belongs to DataLake; stock research price/calendar binding
belongs to its future Research case. No private Tushare/SDK/SQLite workaround or stock
service implementation is authorized here. These gaps do not block the index case.
Required caller inputs are not missing semantic defaults. Conditional, new metrics/sample
shapes, optional analyses, retries, adjustment engines and durable outputs are outside scope.

## Mandatory scenarios A-H

These are implementation acceptance specifications, not behavior tests already executed.
Each successful construction verifies unique ordered keys, exactly one outcome per
candidate, all missing dependencies and derived counts/ratios.

| Scenario | Fixture and expected behavior |
| --- | --- |
| A — Complete time series | Complete Calendar and legal positive prices: every candidate Eligible; observation coverage 100%, unavailable/excluded ratios 0; verify returns, H, keys, provenance and v2 identity. |
| B — Missing intermediate price | Six open sessions D0..D5, closes [100,110,missing,90,120,130], H=2, anchors D2..D5. D2 Unavailable (anchor D2); D3 Eligible (90/110-1); D4 Unavailable (lookback D2); D5 Eligible (130/90-1). Counts 4=2+2+0; observation coverage 50%, unavailable 50%, excluded 0%; fact coverage 5/6, warm-up 2/2, sample 3/4. Never substitute another date for D2. |
| C — Weekend / holiday | Complete Calendar includes closed dates between opens. Closed dates are neither candidates nor missing Index units; H follows the open-session sequence. No artificial fact-coverage gaps. |
| D — Missing warm-up price | Complete calendar resolves lookbacks, but some required pre-window daily rows are absent under valid proof: affected anchors Unavailable; other computable anchors Eligible; fixed H and independent warm-up fact coverage retained. Unknown history/calendar instead fails preparation. |
| E — Incomplete Calendar | Final Calendar cannot prove full sample/discovery date population: input_preparation fails, no guessed candidate universe or observation coverage; no price-row/weekday inference and no Analyze attempt. |
| F — All market facts missing | Complete Calendar, positive candidate population, valid Index Export with zero success and empty records: all candidates Unavailable, Eligible=0, 0% fact/observation coverage, unavailable ratio 100%. Valid ObservationSet retained; conversion fails NoEligibleObservations, Job Failed, every analysis not_attempted. No successful empty NumericSample. |
| G — Invalid public facts | Wrong scope/schema/identity, duplicate/conflicting/illegal rows or inconsistent coverage: InvalidPublicInput at input_preparation; no silent dropping or ordinary Missing. OperationError is UpstreamFailure, not availability. |
| H — Individual stock capability | Subject abstraction represents stable identity, metric, calendar basis, H/window without changing the general model. Current catalog has no stock daily service; report Upstream Capability Gap and undefined price/adjustment binding, never fake a public API or claim reliable economic returns. |

## Additional implementation gates

| Boundary | Required checks |
| --- | --- |
| Outcome precedence | Two missing endpoints retain two dependencies but one Unavailable. A shared missing fact affects every dependent anchor. Missing plus non-positive endpoint is Unavailable; both available and any non-positive is Excluded non_positive_close, preserving all offending endpoints. |
| Coverage | Non-positive but legal facts count available; positive candidate zero eligible has 0% observation coverage. Zero candidates yield Not Applicable ratios; no-candidate Index not requested. Keep upstream coverage unchanged and Calendar/Index units separate. |
| Public invocation | Export-first; validate partial envelope before ensure; at most one ensure for each incomplete range, then validate final Export. Partial EnsureResult plus valid final partial Index view can construct; OperationError and invalid views fail. Complete final Calendar mandatory. |
| History | One-day sample, adjacent backward doubling, date.min exhaustion, missing Calendar block and legal missing warm-up quotations; no arbitrary cutoff, list_date trimming, suffix guessing or snapshot fallback. |
| Formula / fingerprint | Exact fixtures in case authority; positive-endpoint overflow fails construction; v2 deterministic bytes and sensitivity from identity contract, no-candidate versus empty Index distinction, old v1 not reinterpreted. |
| Converter / association | All Eligible values once in order; preserve equal-valued distinct keys, exact units, missing/excluded records, full coverage/evidence and dependence context; no I/O or second screen. Invalid accounting/unmappable scalar fails. Only NumericSample crosses Analyze boundary. Wrong method/spec/count/unit fails association with raw result preserved. |
| Partial successful Job | Valid partial ObservationSet with at least one Eligible plus all required analyses/associations successful yields Job Success with honest coverage. An analysis failure still fails Job; zero Eligible fails conversion with diagnostics preserved. |
| Plan / Batch | Whole-plan preflight before I/O, exact Cartesian order/identity, required analysis order, no analysis dimension expansion, continue and stop accounting per execution contract. |
| Analyze | Existing owner fixtures for types, empty/non-finite sample, duplicates, immutability, unit, quantile estimator/extreme arithmetic and interval endpoints/count conservation remain required. |
| Live data | Explicit metadata-verified CSI1000 code, dates/H and both method parameters; independently check input pairing/returns, sample/binding, analyses/associations and retained fingerprint through authorized public services. No experiments on real user caches. |

## OBS-02 authority reconciliation report

Baseline reviewed: d158b1f5879491a78a3c3afda807606014632a78. The following classification
records reconciliation of the frozen decisions; linked current authorities are canonical,
and superseded rules are not alternate valid policies.

| Existing decision | Classification | Resolution / owner |
| --- | --- | --- |
| ObservationJobSpec fixed subject/metric/parameters/H/window, scalar grain and deterministic keys | Remain Valid | Observation and execution retain the core request and identity separation. |
| First case's subject is canonical index_code | Needs Specialization | It remains the index case binding; the general subject is asset-agnostic with case-owned identity/time/public-source obligations. |
| Every required Index unit must succeed or whole Job fails | Superseded | Only this declared missing-tolerant case accepts validated partial Export; retain all calendar candidates and explicit Unavailable dependencies. Other consumption remains fail-closed. |
| Eligible/Excluded-only conservation | Superseded | Observation adds Unavailable and three-way derived accounting; coverage has fixed candidate denominator. |
| H-session SSE basis and adjacent backward discovery | Remain Valid | Input authority preserves exact discovery and calendar offsets, independent of missing price rows. |
| Required input validation and failure rules | Needs Specialization | Calendar/illegal public input/operation failures still fail; legal missing daily units are availability evidence. Normal partial EnsureResult is retained, then final Export validated. |
| Public source selection, no private access/fallback, DataLake complete semantics | Remain Valid | UPSTREAM narrowly permits the case policy; no DataLake authority or implementation changes. |
| Non-positive endpoint business exclusion | Remain Valid | Available legal endpoints retain exclusion rule; missing-first precedence is now explicit. |
| Complete-input trailing_return_inputs_v1 hash | Superseded | New construction uses explicit v2 profile with final coverage, expected/absent keys and endpoint requirements; historical v1 semantics unchanged. |
| Converter maps every eligible scalar, Analyze pure and market-agnostic | Remain Valid | Integration specializes SampleBinding to retain missing/coverage context; no NumericSample change. |
| Valid zero-eligible set versus successful analysis / Job | Remain Valid | All-unavailable is newly admissible construction; zero-eligible conversion failure and all-required-analysis Success rule stay independent. |
| Research producers/converters/executors and Analyze API | Implementation Gap | Authority-only; no runtime added. Stock and other-asset gaps are scoped separately in the readiness matrix. |

## Authority topology and handoff

The root module boundary is unchanged. Research entry leads to Descriptive and the
Observation/integration/execution/acceptance owners. The case entry retains identity,
formula and eligibility, and routes separately to public preparation/coverage and input
identity contracts. These are independently consumed stable concerns; each has one owner
and inherits upper invariants. No duplicate Observation framework or generic financial
object framework is introduced. Earlier statistical/research retirement decisions remain
valid; Conditional stays independent and unimplemented.

Repository checks establish navigation, boundary and tooling consistency only; they do
not prove missing-aware runtime, numerical correctness or live-data success. Report actual
check outcomes at handoff. Stop after semantic encoding and reconciliation; implementation
requires a separate task.
