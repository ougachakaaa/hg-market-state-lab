# Descriptive Research authority

This is the initial research paradigm under the [module authority](../ARCHITECTURE.md).
Public fact acquisition follows [UPSTREAM.md](../UPSTREAM.md). Descriptive Research owns
the empirical meaning and interpretation of historical observations, sample conversion
and research execution. Generic numerical statistics are delegated to the independent
[Analyze module](../../market_analyze/ARCHITECTURE.md).

## Main flow and authority navigation

```text
ObservationJobSpec → complete prepared facts → ObservationSet
    → Research Sample Converter → Analyze NumericSample
    → Analyze API (Quantile / IntervalCount) → Analyze AnalysisResult
    → Research association → JobResult → BatchResult / Evidence
```

| Concern | Canonical owner |
| --- | --- |
| Fixed observation request, grain, population, validity, market derivation and provenance | [OBSERVATION.md](OBSERVATION.md) |
| ObservationSet → NumericSample and statistical result → research association | [ANALYZE_INTEGRATION.md](ANALYZE_INTEGRATION.md) |
| ResearchPlan, single Job / Batch control, statuses and results | [EXECUTION.md](EXECUTION.md) |
| Numerical input, method parameters, results and failures | [Analyze CONTRACT.md](../../market_analyze/CONTRACT.md) |

An ObservationSet may support multiple analyses after conversion. Method parameter changes
do not require upstream acquisition or observation reconstruction as a semantic prerequisite.
Research interpretation must state its population, subject, horizon, historical window,
input/derivation provenance, statistical method and limitations. It consumes computed
results without recalculating statistics or silently filtering the analyzed population.
Descriptive association does not establish causality, predictive validity or a trading signal.

## First intended case and readiness

**CSI1000 Trailing Cumulative Return Distribution** illustrates the ownership and flow:

```text
subject = CSI1000
metric = trailing_cumulative_return
horizon = 2 trading sessions
sample_window = 2020-01-01 ... 2025-12-31

Authorized historical index facts → fixed-horizon return ObservationSet
    → Research Converter → NumericSample → Quantile and IntervalCount
    → Research JobResult association → interpreted evidence
```

The dates and horizon are examples, not approved production defaults. A ResearchPlan can
expand multiple subjects, horizons and windows into independent fixed-parameter Jobs under
an explicitly declared expansion rule. Before implementation the concrete case must settle
the index code and public upstream binding, return formula/units, actual historical window,
boundary inputs, population/validity and reproducibility strategy. Statistical choices
belong to Analyze's method authority; no quantile algorithm or interval buckets are selected
here. These case and statistical choices remain unresolved semantic decisions. The
Observation Producer, Converter and Executors are Expected Implementation Gaps, not
runnable capabilities.

## Deferred scope

No case is implemented by this authority encoding. Conditional Research and its contracts,
Condition Engine, forward evaluation, backtesting, strategy/model/signal design, generic runner or
pipeline DSL, research database, artifact registry, automatic hypothesis discovery, Web
visualization, full report rendering and new Research CLI are out of scope. No mandatory
durable storage or class hierarchy is required for the first version. Descriptive and
Conditional remain independent under the module invariant; no cross-paradigm framework
or shared execution engine is authorized.
