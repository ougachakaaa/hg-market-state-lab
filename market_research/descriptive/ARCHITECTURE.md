# Descriptive Research authority

This is the initial research paradigm under the [module authority](../ARCHITECTURE.md).
Public fact acquisition follows [UPSTREAM.md](../UPSTREAM.md). Descriptive Research owns
the empirical meaning and interpretation of historical observations, sample conversion
and research execution. Generic numerical statistics are delegated to the independent
[Statistics module](../../market_statistics/ARCHITECTURE.md).

## Main flow and authority navigation

```text
ObservationJobSpec → validated prepared facts / availability evidence → ObservationSet
    → Research Sample Converter → SampleProjection (NumericSample + Research SampleBinding)
    → Statistics compute (Quantile / IntervalCount) → StatisticalResult
    → Research association → JobResult → BatchResult / Evidence
```

| Concern | Canonical owner |
| --- | --- |
| Fixed observation request, grain, population, validity, market derivation and provenance | [OBSERVATION.md](OBSERVATION.md) |
| ObservationSet → SampleProjection / SampleBinding | [SAMPLE_CONVERSION.md](SAMPLE_CONVERSION.md) |
| Statistics consumption and result association | [STATISTICS_INTEGRATION.md](STATISTICS_INTEGRATION.md) |
| AnalysisRequest, immutable evidence, exact result linkage and association failures | [RESULT_ASSOCIATION.md](RESULT_ASSOCIATION.md) via Statistics integration |
| ResearchPlan, single Job / Batch control, statuses and results | [EXECUTION.md](EXECUTION.md) |
| Numerical input, method parameters, results and failures | [Statistics CONTRACT.md](../../market_statistics/CONTRACT.md) |
| PIP numerical algorithm | [PIP algorithm](../algorithm/pip/ALGORITHM.md) |
| Independent structured segmentation observation | [Price Segmentation](cases/price_segmentation/ARCHITECTURE.md) |
| Independent same-day Futures Basis, relative Slots and case-owned numerical adaptation | [Futures Basis / R01-A](cases/futures_basis/ARCHITECTURE.md) → [work packages/readiness](cases/futures_basis/ROADMAP.md) |
| Online Futures Basis application, standard profile, run lifecycle and read boundary | [R01-A online application](cases/futures_basis/ONLINE_APPLICATION.md) |
| First case: formula, public input binding, warm-up, validity and fingerprint | [Trailing Return](cases/trailing_return/ARCHITECTURE.md) |
| Admitted capability publication and pure preview | [RESEARCH_CAPABILITY.md](RESEARCH_CAPABILITY.md) |
| Implementation status, cross-stage acceptance scenarios and validation evidence | [ACCEPTANCE.md](ACCEPTANCE.md) |

An ObservationSet may support multiple analyses after conversion. Method parameter changes
do not require upstream acquisition or observation reconstruction as a semantic prerequisite.
For the scalar analysis path, Research interpretation must state its population, subject, horizon, historical window,
input/derivation provenance, statistical method and limitations. It consumes computed
results without recalculating statistics or silently filtering the analyzed population.
Descriptive association does not establish causality, predictive validity or a trading signal.

The [Price Segmentation case](cases/price_segmentation/ARCHITECTURE.md) independently
observes one complete price series and does not require horizon, scalar ObservationSet,
conversion or Statistics. Its independent Python observation API is implemented and
[real-market validation](ACCEPTANCE.md#real-market-validation-evidence) is recorded separately;
the existing scalar runtime remains unchanged.

The independent [Futures Basis case](cases/futures_basis/ARCHITECTURE.md) defines
Contract-day and Slot-day observations with no Horizon. It uses its own population,
adaptation and result association while consuming the Statistics public numerical
contract. Its authority does not admit it to the current scalar runtime or public
capability facade. Implementation readiness is tracked in its own roadmap. Its
[online application authority](cases/futures_basis/ONLINE_APPLICATION.md) is a
separate case-specific interactive boundary; it does not extend the scalar runtime,
create a generic execution engine or change this paradigm's contracts.

## First case and readiness

[Trailing Return](cases/trailing_return/ARCHITECTURE.md) is the first concrete case,
with CSI1000 as representative target and full canonical index_code as required input.
It owns formula, session alignment, explicit window, public service selection, warm-up,
eligibility and reproducible fact identity. Numerical statistics belong to Market Statistics.
The Observation subject is asset-agnostic; this case binds only Index Daily. Its
missing-tolerant policy preserves calendar candidates and records unavailable facts.
Individual stocks and other series require their own published fact/calendar binding
and price semantics; their gaps do not block the index case. See the capability and
readiness matrix in [ACCEPTANCE.md](ACCEPTANCE.md).
Observation production for this case is implemented with independent public preparation
and pure construction. The reusable scalar converter and independent Result Association
are implemented. The [Single Job Executor](JOB_EXECUTION.md) composes them through public
boundaries. [ResearchPlan / Batch](BATCH_EXECUTION.md) composes Single Job with whole-plan
preflight and deterministic continue/stop accounting; the Batch contract and
deterministic tests record actual verification. The independent Statistics public
numerical API is implemented by STAT-IMP-01.
[Acceptance](ACCEPTANCE.md) records current readiness and bounded real-market validation.
No unresolved implicit default is authorized.

## Deferred scope

Beyond the implemented index Observation slice, Conditional Research and its contracts,
Condition Engine, forward evaluation, backtesting, strategy/model/signal design, generic runner or
pipeline DSL, research database, artifact registry, automatic hypothesis discovery, Web
visualization within Research, general report rendering and new Research CLI are out of scope.
The narrowly defined [R01-A offline report](cases/futures_basis/DELIVERY.md) is
implemented WP5 delivery; Research owns business projection/evidence and ui_web
owns rendering. [R01-A online application](cases/futures_basis/ONLINE_APPLICATION.md)
is WP6 authority for WP7–WP9 runtime; it remains HTTP/Web transport, not a new
Research engine or capability. Execution requires no mandatory
durable storage or class hierarchy; separate opt-in [publication](../PUBLICATION.md)
owns its own persistence and does not alter execution. The case-specific online run
store is disposable runtime state, not Publication or generic Research durability.
Descriptive and Conditional remain independent under the module invariant; no
cross-paradigm framework or shared execution engine is authorized.
