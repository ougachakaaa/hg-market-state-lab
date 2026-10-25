# Market Research architecture authority

## Mission and authority

`market_research` transforms historical market facts into reproducible empirical
observations, statistical analyses and research evidence. It remains an independent
bounded module under the [repository architecture](../ARCHITECTURE.md).

This authority formally supersedes the previous V1 Component / durable Observation /
Study framework, Shared Component classification and lifecycle, publishing conventions,
`shared.distribution` semantics, Condition-first V2 architecture and roadmap, and the
requirement for V1/V2 coexistence. Their implementations and compatibility contracts
are retired; Git history is the historical reference. No legacy interface survives.

## Functional flow and responsibility boundaries

```text
ResearchDefinition
    → Input Preparation
    → Observation Construction → ObservationSet
    → Descriptive Analysis → AnalysisResult
    → Research Evidence / Report
ResearchRun records actual execution context and input provenance.
```

Input Preparation acquires complete facts through authorized upstream public contracts.
Observation Construction derives explicit empirical variables and collections from those
facts. Analysis computes over a defined observation population without acquiring facts
or mutating observations. Reporting assembles computed evidence without recalculating
statistics or redefining populations. These are functional responsibilities, not mandatory
packages, services, abstract base classes or orchestration stages.

## Core conceptual models

These six models define semantic responsibilities, not a requirement for six Python classes.

| Concept | Ownership |
| --- | --- |
| ResearchDefinition | Research question, variable definitions, requested AnalysisSpecs and stable methodological choices; separate from execution-time data binding. |
| ResearchRun | One execution: definition reference, historical evaluation window, actual upstream input references, input/execution provenance and execution status. No generic workflow framework is implied. |
| ObservationSet | Central research data boundary: coherent empirical collection with explicit grain, variable meaning and units, temporal semantics, population/observation validity, source and derivation provenance. Schema and grain may vary by case. |
| AnalysisSpec | Target variables, statistical population, grouping dimensions, methods and parameters. It hides neither input acquisition nor observation construction. |
| AnalysisResult | Actual calculation: analysis definition reference, observation input reference, sample counts, statistics, diagnostics and relevant evidence. It is separate from the ObservationSet. |
| ResearchReport | Assembled deliverable: definition reference, execution context, analysis results, evidence, findings and limitations. It consumes computed evidence; it conducts no statistical calculations. |

A definition may request several analyses. A run binds actual inputs and constructs an
ObservationSet; multiple AnalysisSpecs can consume that same set without reconstruction.
Each produces a separate AnalysisResult. A ResearchReport assembles those results with
run and definition context. ObservationSets are not automatically durable artifacts.
No mandatory SQLite, content addressing, `ensure()` lifecycle, artifact registry or long-term
persistence is required. Reproducibility requires traceable definitions, inputs, derivations,
methods and execution context; a concrete case must explain how it meets that requirement.

## Module and dependency boundaries

Research consumes DataLake / Snapshot public semantic contracts under [UPSTREAM.md](UPSTREAM.md).
It owns no market-data acquisition infrastructure, provider clients, upstream persistence
or canonical Snapshot Product preparation. DataLake and Snapshot never depend on Research.
Modeling remains a sibling, not a required downstream runtime stage; current repository
rules grant it no Research import permission. Any eventual Modeling or UI consumption of
published Research outputs requires its own authorized public boundary.

Research does not depend on inbound adapters (`ui_cli`, `ui_http`, `ui_web`), HTTP DTOs or
frontend types. It owns empirical meanings and evidence, not UI presentation, production
market-state models, forecasts, trading signals, recommendations or strategies. Findings
can inform a human/agent semantic decision and authority update; they do not automatically
become authoritative models or signals.

## Paradigm, status and extensibility

[Descriptive Research](descriptive/ARCHITECTURE.md) is the initial paradigm. Conditional
Research may later be a separate paradigm; its contract and implementation are out of scope.
Distribution, time-series and relationship analyses are capability directions, not an
instruction to build a universal statistics library. Shared abstractions must be justified
by concrete cases, not asset names or the six conceptual models.

Current state: semantic foundation only, with architecture/integration checks. No Research
execution package, statistical engine, case implementation, CLI, API or report renderer
is published. The first intended case is specified only as direction in the descriptive
Authority. Execution policy is in [AGENTS.md](AGENTS.md); upstream semantics belong only
to [UPSTREAM.md](UPSTREAM.md), paradigm details only to the descriptive authority.
