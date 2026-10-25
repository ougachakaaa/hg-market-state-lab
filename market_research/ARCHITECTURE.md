# Market Research architecture authority

## Mission and authority

`market_research` transforms historical market facts into reproducible empirical
observations and interpreted research evidence. It is the active business organizer,
consuming authorized data contracts and the independent numerical capability of
`market_analyze` under the [repository architecture](../ARCHITECTURE.md).

This authority formally supersedes the previous V1 Component / durable Observation /
Study framework, Shared Component classification and lifecycle, publishing conventions,
`shared.distribution` semantics, Condition-first V2 architecture and roadmap, and the
requirement for V1/V2 coexistence. Their implementations and compatibility contracts
are retired; Git history is the historical reference. No legacy interface survives.

## Functional flow and responsibility boundaries

```text
ResearchPlan → fixed-parameter ObservationJobSpecs
    → Input Preparation → Observation Construction → ObservationSet
    → Research Sample Converter → Analyze NumericSample
    → market_analyze public API → Analyze AnalysisResult
    → Research result association → JobResult / BatchResult → Evidence / Interpretation
```

Input Preparation acquires complete facts through authorized upstream public contracts.
Observation Construction owns market indicator formulas and empirical variables derived
from those facts. Research owns sample conversion, single-job and batch execution control,
association of external numerical results, and interpretation with research context.
Executors orchestrate these responsibilities; they do not own financial or statistical
formulas. Generic numerical statistics belong exclusively to Analyze. These responsibilities
do not require a package hierarchy, shared base classes or a generic execution engine.

## Semantic ownership and navigation

These are conceptual responsibilities, not prescribed Python classes or callable names.

| Concept | Ownership |
| --- | --- |
| ObservationJobSpec / ObservationSet | Research observation request, empirical meaning, population, validity and derivation: [Observation authority](descriptive/OBSERVATION.md). |
| Sample Converter / result association | Research-owned outbound adaptation and business linkage: [Analyze integration](descriptive/ANALYZE_INTEGRATION.md). |
| ResearchPlan / JobResult / BatchResult | Research definition, execution context, control and complete reporting: [Execution authority](descriptive/EXECUTION.md). |
| NumericSample / AnalysisSpec / AnalysisResult / AnalysisFailure | Analyze-owned public numerical contracts: [Analyze contract](../market_analyze/CONTRACT.md). Research consumes them without defining competing types. |

The previous ResearchDefinition / ResearchRun / ResearchReport conceptual inventory is
replaced by these responsibilities, not retained as an additional required model layer.
Research owns research parameters, population selection, business linkage and evidence;
it does not transfer market semantics into Analyze's method parameters or result types.
An ObservationSet can support multiple analyses through explicit conversion. Changing only
statistical parameters does not semantically require new market inputs or observations.
ObservationSets and results are not automatically durable artifacts.
No mandatory SQLite, content addressing, `ensure()` lifecycle, artifact registry or long-term
persistence is required. Reproducibility requires traceable definitions, inputs, derivations,
methods and execution context; a concrete case must explain how it meets that requirement.

## Module and dependency boundaries

Research consumes DataLake / Snapshot public semantic contracts under [UPSTREAM.md](UPSTREAM.md)
and Analyze's [public numerical contract](../market_analyze/CONTRACT.md).
It owns no market-data acquisition infrastructure, provider clients, upstream persistence
or canonical Snapshot Product preparation. DataLake, Snapshot and Analyze never depend
on Research; Analyze also never depends on DataLake or Snapshot and performs no upstream I/O.
Modeling remains a sibling, not a required downstream runtime stage; current repository
rules grant it no Research import permission. Any eventual Modeling or UI consumption of
published Research outputs requires its own authorized public boundary.

Research does not depend on inbound adapters (`ui_cli`, `ui_http`, `ui_web`), HTTP DTOs or
frontend types. It owns empirical meanings and evidence, not UI presentation, production
market-state models, forecasts, trading signals, recommendations or strategies. Findings
can inform a human/agent semantic decision and authority update; they do not automatically
become authoritative models or signals.

## Paradigm, status and extensibility

[Descriptive Research](descriptive/ARCHITECTURE.md) and Conditional Research are independent
paradigms that may evolve in parallel. Neither may import the other or require it to run
first. Shared Research/Observation base classes or execution engines must not create hidden
coupling. A person may use descriptive findings to formulate a condition hypothesis; that
human research workflow grants no program dependency. Only Descriptive is detailed here;
no Conditional contract, directory scaffold or implementation is introduced.

Current state: semantic foundation only, with architecture/integration checks. No Research
execution package, case implementation, CLI, HTTP service or report renderer is published.
Observation Producer, Sample Converter and Job / Batch Executor are Expected Implementation
Gaps, not runtime capabilities. Analyze's statistical API is likewise authority-only.
The first intended case remains illustrative in the descriptive authority. Agent execution
policy is in [AGENTS.md](AGENTS.md); upstream semantics belong only to [UPSTREAM.md](UPSTREAM.md).
