# Market Analyze architecture authority

## Identity and ownership

`market_analyze` is an independent numerical statistics bounded module under the
[repository architecture](../ARCHITECTURE.md). It owns generic numerical inputs, method
parameters, calculated statistical results and statistical failure semantics. Its first
capability directions are Quantile and IntervalCount only.

The [public numerical contract](CONTRACT.md) is the canonical owner of `NumericSample`,
`AnalysisSpec`, `AnalysisResult`, `AnalysisFailure` and the conceptual `analyze` operation.
Its public API is a Python semantic boundary; it does not imply an HTTP service or a
separately deployed application. Method contracts specialize it:
[Quantile](QUANTILE.md) and [IntervalCount](INTERVAL_COUNT.md).

## Boundaries and dependency direction

Consumers adapt their own data into Analyze's public numerical contract. Analyze does
not consume Research ObservationSets or own their conversion, result association or
interpretation. It does not understand consumer business identities, financial formulas,
or Research Jobs, Batches and Executors.

```text
market_research → market_analyze public API
```

Analyze must not depend on `market_research`, `data_lake` or `data_snapshot`. It does not
acquire market inputs, access upstream storage, or perform upstream I/O. Generic numerical
results do not automatically become market findings, production states or trading advice.
Consumers retain business meanings and interpretation; Analyze owns statistical legality
and calculation under explicitly defined method contracts.

## Authority and runtime status

This module currently contains authority only. The intended future Python namespace is
`market_analyze`, but no Python package, callable public API or statistical implementation
is published or installed. NumericSample, both methods, validation and failure semantics
are Implementation Ready; the statistical API is an Expected Implementation Gap.

The [repository runtime invariant](../ARCHITECTURE.md#3-python-runtime-与-module-boundary)
continues to apply: one root Python project, dependency graph and worktree-local `.venv`.
Authority creation adds no package registration, module-local tooling or independent runtime.
No statistical DSL, universal engine, registry, framework or legacy `shared.distribution`
implementation is introduced or inherited.

Agent reading and verification rules are in [AGENTS.md](AGENTS.md). Method decisions must
be made in the narrow statistical authority before implementation; authority readiness
does not claim runtime readiness.
