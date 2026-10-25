# Descriptive observation authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). It owns
`ObservationJobSpec`, `ObservationSet` and market observation construction. Public input
selection, completeness and upstream failure semantics remain in [UPSTREAM.md](../UPSTREAM.md).
Numerical statistical methods belong to [Analyze](../../market_analyze/CONTRACT.md).

## Fixed observation request

An `ObservationJobSpec` fixes one subject, one metric definition, one horizon, one historical
sample window and the business parameters required by that metric. `JobSpec` is only a
contextual shorthand for this request, not a second competing model. Research owns the
question and stable methodological choices as well as their actual execution binding.

- Horizon describes the span covered by one observation; in the illustrative return case
  it is a number of trading sessions, not the full historical research period.
- Historical sample window identifies which historical dates belong to the research
  population. The case must define the date reference and inclusion boundaries.
- Metric parameters define the market variable and its derivation. Analysis parameters
  such as quantile points or count intervals belong to Analyze's `AnalysisSpec`.

Changing observation parameters changes the empirical request. Changing only statistical
method parameters is a different semantic change and does not require rebuilding observations.
The conceptual operation is `observe(ObservationJobSpec) -> ObservationSet`; it prescribes
neither a Python signature nor synchronous/asynchronous execution.

## ObservationSet and construction

An `ObservationSet` is a coherent Research-owned empirical collection. It is neither an
Analyze input/result nor an automatically persisted artifact. A concrete case must define:

| Responsibility | Required semantics |
| --- | --- |
| Grain and identity | What one observation represents, its key and the meaning of duplicates. No universal row schema or asset hierarchy is imposed. |
| Market variable | Metric definition, financial formula, units and required business parameters; Research owns their calculation from prepared facts. |
| Temporal meaning | Observation reference date, horizon, historical window, alignment, lookback and any required facts outside that window. |
| Population and validity | Intended population, valid/invalid observations, legitimate absence/null, explicit eligibility/exclusion rules and reasons. |
| Provenance | Actual input references, request context, derivation definition and association back to the fixed observation request. |

Input Preparation acquires and validates complete authorized market facts. Observation
Construction consumes those prepared facts and does not acquire data through hidden helpers.
Construction cannot silently shift dates, replace required history, impute facts or copy
canonical Snapshot Product preparation into Research contrary to UPSTREAM.

Required input completeness and statistical admissibility are different concerns. An
upstream failure must fail explicitly; it cannot be relabeled as an ineligible observation.
Any legitimate observation exclusions must be declared and retain their reasons. Account
for constructed and eligible observations so conversion can reconcile analyzed counts.
Research selects business populations; Analyze does not learn subject or horizon semantics
to make those selections. Method-specific numerical validity remains Analyze-owned.

## Reuse, traceability and readiness

One ObservationSet can support multiple requested analyses through the
[Research-owned conversion boundary](ANALYZE_INTEGRATION.md). Observation construction
does not own Quantile or IntervalCount algorithms or their defaults.

Preserve enough source and derivation references to explain what facts and calculations
actually produced the observations. A re-fetchable historical window or mutable upstream
cache does not prove identical historical inputs. Concrete cases must choose a sufficient
input retention/reference strategy under UPSTREAM; no universal provenance envelope,
mandatory SQLite lifecycle or artifact registry is introduced.

The first case's exact index/public contract binding, return formula, historical interval,
boundary history and population rules remain case decisions. Its Observation Producer is
an Expected Implementation Gap. No legacy observation package or persistence contract is restored.
