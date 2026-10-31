# Market Research architecture authority

## Mission and authority

`market_research` transforms historical market facts into reproducible empirical
observations and interpreted research evidence. It is the active business organizer,
consuming authorized data contracts and the independent numerical capability of
`market_statistics` under the [repository architecture](../ARCHITECTURE.md).

This authority formally supersedes the previous V1 Component / durable Observation /
Study framework, Shared Component classification and lifecycle, publishing conventions,
`shared.distribution` semantics, Condition-first V2 architecture and roadmap, and the
requirement for V1/V2 coexistence. Their implementations and compatibility contracts
are retired; Git history is the historical reference. No legacy interface survives.

## Functional flow and responsibility boundaries

```text
ResearchPlan → fixed-parameter ObservationJobSpecs
    → Input Preparation → Observation Construction → ObservationSet
    → Research Sample Converter → SampleProjection (Statistics NumericSample + Research binding)
    → market_statistics compute → StatisticalResult
    → Research result association → JobResult / BatchResult → Evidence / Interpretation
```

The independent [Price Segmentation case](descriptive/cases/price_segmentation/ARCHITECTURE.md)
produces a structured observation without the scalar analysis path above. Research also owns
the market-independent [PIP algorithm](algorithm/pip/ALGORITHM.md); the case depends on its
public algorithm boundary, never the reverse. The independent PIP Python boundary is
implemented; the Price Segmentation case remains a future capability, not a generic engine.

Input Preparation acquires validated facts and availability evidence through authorized
upstream public contracts, under the selected case's completeness policy.
Observation Construction owns market indicator formulas and empirical variables derived
from those facts. Research owns sample conversion, single-job and batch execution control,
association of external numerical results, and interpretation with research context.
Executors orchestrate these responsibilities; they do not own financial or statistical
formulas. Generic numerical statistics belong exclusively to Statistics. These responsibilities
do not require a package hierarchy, shared base classes or a generic execution engine.

## Semantic ownership and navigation

These are conceptual responsibilities, not prescribed Python classes or callable names.

| Concept | Ownership |
| --- | --- |
| ObservationJobSpec / ObservationSet | Research observation request, empirical meaning, population, validity and derivation: [Observation authority](descriptive/OBSERVATION.md). |
| Sample Converter / SampleProjection / SampleBinding | Research-owned adaptation: [Sample conversion](descriptive/SAMPLE_CONVERSION.md). |
| Statistics consumption / result association | Research-owned business linkage: [Statistics integration](descriptive/STATISTICS_INTEGRATION.md). |
| Capability discovery / pure plan preview | [Capability publication](descriptive/RESEARCH_CAPABILITY.md); HTTP belongs to ui_http. |
| ResearchPlan / JobResult / BatchResult | Research definition, execution context, control and complete reporting: [Execution authority](descriptive/EXECUTION.md). |
| NumericSample / StatisticalSpec / StatisticalResult / StatisticalFailure | Statistics-owned public numerical contracts: [Statistics contract](../market_statistics/CONTRACT.md). Research consumes them without defining competing types. |

The previous ResearchDefinition / ResearchRun / ResearchReport conceptual inventory is
replaced by these responsibilities, not retained as an additional required model layer.
Research owns research parameters, population selection, business linkage and evidence;
it does not transfer market semantics into the Statistics method parameters or result types.
An ObservationSet can support multiple analyses through explicit conversion. Changing only
statistical parameters does not semantically require new market inputs or observations.
ObservationSets and results are not automatically durable artifacts.
No mandatory SQLite, content addressing, `ensure()` lifecycle, artifact registry or long-term
persistence is required. Reproducibility requires traceable definitions, inputs, derivations,
methods and execution context; a concrete case must explain how it meets that requirement.

## Module and dependency boundaries

Research consumes DataLake / Snapshot public semantic contracts under [UPSTREAM.md](UPSTREAM.md)
and the Statistics [public numerical contract](../market_statistics/CONTRACT.md).
It owns no market-data acquisition infrastructure, provider clients, upstream persistence
or canonical Snapshot Product preparation. DataLake, Snapshot and Statistics never depend
on Research; Statistics also never depends on DataLake or Snapshot and performs no upstream I/O.
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

Current state: the index Trailing Return Observation producer is implemented as an
independent Python capability under `src/market_research/descriptive/`, with public
preparation, pure construction and contract tests. Its public boundary is owned by
[Observation](descriptive/OBSERVATION.md); usage is in [README](README.md).
The reusable scalar [Sample Converter](descriptive/SAMPLE_CONVERSION.md) is implemented
under `market_research.descriptive.conversion`. Independent Result Association is implemented
under `market_research.descriptive.association`, retaining original request/result/projection
and source evidence under its [contract](descriptive/RESULT_ASSOCIATION.md).
Single Job execution is implemented under `market_research.descriptive.execution`,
composing these public components under [its contract](descriptive/JOB_EXECUTION.md).
ResearchPlan / Batch execution is implemented in the same facade, composing Single Job
under the [Batch contract](descriptive/BATCH_EXECUTION.md).
The [capability publication](descriptive/RESEARCH_CAPABILITY.md) and pure preview facade
publish this one case; bounded HTTP delivery belongs to
[ui_http](../ui_http/products/research/http-contract.md). Human/agent usage is in
[USAGE.md](USAGE.md), not a competing semantic authority.
No Research CLI or report renderer is published. The independent Statistics
public API is implemented; deterministic Single Job and
[Batch acceptance](descriptive/BATCH_EXECUTION_ACCEPTANCE.md) are recorded separately
from the [isolated real-market E2E acceptance](descriptive/LIVE_E2E_ACCEPTANCE.md).
Actual verification and live-data limitations are recorded in
[Acceptance](descriptive/ACCEPTANCE.md).
The concrete first case and implementation acceptance gates are reached through the
Descriptive entry; semantic readiness alone does not establish runtime or live acceptance. Agent
execution policy is in [AGENTS.md](AGENTS.md); upstream semantics belong only to
[UPSTREAM.md](UPSTREAM.md).
