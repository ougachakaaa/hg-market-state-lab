# Descriptive Research authority

This is the initial research paradigm under the [module authority](../ARCHITECTURE.md).
Public fact acquisition follows [UPSTREAM.md](../UPSTREAM.md). This document owns
observation, population, analysis and evidence semantics for descriptive research;
concrete case definitions must specialize these boundaries before implementation.

## Observation and population

An ObservationSet is a coherent empirical collection, not an AnalysisResult or an assumed
stored artifact. Before constructing one, specify observation grain/key, variable meaning,
units, derivation, temporal reference/window/alignment, population scope, validity rules,
handling of legitimate null/absence, and source/derivation provenance. Different cases
can have different schemas and grains; no universal row schema or asset hierarchy is required.

Distinguish required input completeness from admissibility for a statistical population.
An upstream failure cannot be disguised as an excluded observation. Define valid/invalid
observations and any exclusions explicitly, preserve their reasons, and account for the
constructed, eligible and analyzed counts. Grouping or method-specific eligibility belongs
to the AnalysisSpec and must remain traceable to the original ObservationSet.
Window boundaries, lookback requirements and use of facts outside the evaluation window
must be explicit; construction cannot silently shift dates or discard required history.

## Analysis and evidence

An AnalysisSpec defines target variables, population, grouping, statistical method and
parameters. Analysis reads the prepared ObservationSet without mutating or reconstructing
it and without upstream I/O. Multiple analyses can reuse exactly the same observation
collection. AnalysisResult identifies that collection and spec, reports sample counts,
calculated statistics, diagnostics and evidence. Empty/insufficient populations and
undefined statistics must be handled explicitly by the case/method contract, not guessed
or silently converted to numeric results.

Method definitions must settle units, estimator conventions, quantile interpolation,
histogram boundaries, tail definitions and other relevant parameters before calculation.
No historical `shared.distribution` defaults are inherited. Applicable choices belong
to the concrete analysis contract; this foundation chooses no formulas or defaults.

ResearchReport assembles computed evidence, findings and limitations with definition/run
context. It does not recalculate statistics, filter populations or turn descriptive
associations into causality, predictive validity or authoritative trading signals.
Interpretation must state the population and limitations supporting the claim.

## Capability directions

| Family | Intended directions, subject to concrete case contracts |
| --- | --- |
| Distribution | Descriptive statistics, quantiles, empirical distributions, histograms, tail frequencies |
| Time-series | Rolling statistics, temporal variation, historical period comparisons |
| Relationship | Joint distributions, correlations, group comparisons |

These directions authorize no complete statistical library or universal engine.

## First intended case and readiness

CSI1000 historical daily return distribution is the first intended case:

```text
Authorized index daily facts → daily return observations
    → population validation → distribution analysis → reproducible evidence
```

Daily returns, volatility, quantiles, tails and historical period variation are eventual
questions, not implemented capabilities. The separate case task must decide the exact
index/public upstream binding, return definition/units, historical window and boundary
inputs, validity/population, initial AnalysisSpec and reproducibility strategy. Start with
the smallest executable descriptive slice; do not infer unresolved choices from legacy
code. IM basis, MO option premiums and variable relationships are possible future cases,
not reasons to create shared asset abstractions now.

## Deferred scope

No case is implemented by this reset. Conditional Research and its contracts, Condition
Engine, forward evaluation, backtesting, strategy/model/signal design, generic runner or
pipeline DSL, research database, artifact registry, automatic hypothesis discovery, Web
visualization, full report rendering and new Research CLI are out of scope. No mandatory
durable storage or six-class hierarchy is required for the first version.
