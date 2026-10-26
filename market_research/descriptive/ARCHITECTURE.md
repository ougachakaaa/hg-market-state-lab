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
| First case: formula, public input binding, warm-up, validity and fingerprint | [Trailing Return](cases/trailing_return/ARCHITECTURE.md) |
| Implementation readiness and cross-contract acceptance gates | [ACCEPTANCE.md](ACCEPTANCE.md) |

An ObservationSet may support multiple analyses after conversion. Method parameter changes
do not require upstream acquisition or observation reconstruction as a semantic prerequisite.
Research interpretation must state its population, subject, horizon, historical window,
input/derivation provenance, statistical method and limitations. It consumes computed
results without recalculating statistics or silently filtering the analyzed population.
Descriptive association does not establish causality, predictive validity or a trading signal.

## First case and readiness

[Trailing Return](cases/trailing_return/ARCHITECTURE.md) is the first concrete case,
with CSI1000 as representative target and full canonical index_code as required input.
It owns formula, session alignment, explicit window, public service selection, warm-up,
eligibility and reproducible fact identity. Numerical statistics belong to Market Statistics.
The Observation subject is asset-agnostic; this case binds only Index Daily. Its
missing-tolerant policy preserves calendar candidates and records unavailable facts.
Individual stocks and other series require their own published fact/calendar binding
and price semantics; their gaps do not block the index case. See the capability and
reconciliation matrices in [ACCEPTANCE.md](ACCEPTANCE.md).
Observation production for this case is implemented with independent public preparation
and pure construction. The reusable scalar converter and independent Result Association
are implemented; Job / Batch Executors remain Expected Implementation Gaps. The independent
Statistics public numerical API is implemented by STAT-IMP-01.
[Acceptance gates](ACCEPTANCE.md) distinguish semantic readiness from runtime and live-data
verification. No unresolved implicit default is authorized.

## Deferred scope

Beyond the implemented index Observation slice, Conditional Research and its contracts,
Condition Engine, forward evaluation, backtesting, strategy/model/signal design, generic runner or
pipeline DSL, research database, artifact registry, automatic hypothesis discovery, Web
visualization, full report rendering and new Research CLI are out of scope. No mandatory
durable storage or class hierarchy is required for the first version. Descriptive and
Conditional remain independent under the module invariant; no cross-paradigm framework
or shared execution engine is authorized.
