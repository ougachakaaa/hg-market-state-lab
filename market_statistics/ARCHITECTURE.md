# Market Statistics architecture authority

## Identity and ownership

`market_statistics` is an independent, business-agnostic, contract-driven numerical
statistics bounded module under the [repository architecture](../ARCHITECTURE.md).
It owns statistical sample legality, method parameters, computation contracts, typed
results, numerical failure semantics and validation of statistical backend results.
V1 contains Quantile and IntervalCount only. This is the canonical identity decision
STAT-01; the former authority namespace is retired without a compatibility alias.

The [public numerical contract](CONTRACT.md) is the canonical owner of `NumericSample`,
`StatisticalSpec`, `StatisticalResult`, `StatisticalFailure`, `compute` and `validate_spec`
(STAT-02 and STAT-03). Its public API is a Python semantic boundary; it does not imply
an HTTP service or a separately deployed application. Method contracts specialize it:
[Quantile](QUANTILE.md) (STAT-05) and [IntervalCount](INTERVAL_COUNT.md) (STAT-06).
[Backend policy](BACKEND.md) owns library selection, conformance and upgrades (STAT-04);
libraries supply numerical implementations, never public semantic authority.

## Boundaries and dependency direction

Consumers adapt their own data into the Statistics public numerical contract. Statistics does
not consume Research ObservationSets or own their conversion, result association or
interpretation. It does not understand consumer business identities, financial formulas,
or Research Jobs, Batches and Executors.

```text
market_research → market_statistics public API → NumPy / approved numerical backend
```

Statistics must not depend on `market_research`, `data_lake`, `data_snapshot`,
`market_modeling` or inbound `ui_cli` / `ui_http` / `ui_web` modules. It does not
acquire market inputs, access upstream storage, or perform upstream I/O. Generic numerical
results do not automatically become market findings, production states or trading advice.
Consumers retain business meanings and interpretation; Statistics owns statistical legality
and calculation under explicitly defined method contracts.

## Extension boundaries (STAT-07 and STAT-08)

Automatic edge generation is a separate future concern: a consumer chooses an explicit
strategy, Statistics may resolve boundaries, and IntervalCount receives only actual
explicit edges. Conceptually, sample + edge-generation spec → boundary generation →
resolved edges → IntervalCountSpec → compute. No `EdgeGenerationSpec`, `ResolvedEdges`
or `build_edges` public contract/runtime is introduced. Equal-width, fixed-step,
quantile-based or established histogram estimators are possible future strategies;
separately generated data-driven edges do not support direct cross-sample comparison
unless the actual final edges are shared. There is no implicit `auto` binning.

Extend methods before sample shapes. Future Mean, Variance, StandardDeviation, ECDF,
ThresholdFrequency or TailStatistics requires its own semantics/ownership, typed Spec
and Result, explicit backend policy and deterministic acceptance tests. None is added now.
Paired, temporal, grouped or weighted samples require a method with a demonstrated
different mathematical input structure; no such types or scaffold are introduced.
Input ordering alone is not an equally spaced temporal axis. Do not infer independence
or identical distribution; future inference must publish its sampling, dependence and
uncertainty assumptions in its own method contract.

No statistical DSL, arbitrary formula execution, generic registry/plugin architecture,
computational graph, scheduler, Model/Study hierarchy, pipeline framework or automatic
method recommendation is authorized.

## Authority and runtime status

This module currently contains authority only. The intended future Python namespace is
`market_statistics`, but no Python package, callable public API or statistical implementation
is published or installed. NumericSample, both methods, validation, failure semantics
and backend conformance requirements are Implementation Ready; the facade, numerical
adapter and runtime tests remain Expected Implementation Gaps for the separate
STAT-IMP-01 goal. No numerical dependency is added by STAT-01.

The [repository runtime invariant](../ARCHITECTURE.md#3-python-runtime-与-module-boundary)
continues to apply: one root Python project, dependency graph and worktree-local `.venv`.
Authority creation adds no package registration, module-local tooling or independent runtime.
No statistical DSL, universal engine, registry, framework or legacy `shared.distribution`
implementation is introduced or inherited.

Agent reading and verification rules are in [AGENTS.md](AGENTS.md). Method decisions must
be made in the narrow statistical authority before implementation; authority readiness
does not claim runtime readiness.

Future module-boundary acceptance must verify no market-domain imports, upstream I/O,
reverse Research dependency, input mutation, unapproved backend defaults or runtime
registry/framework. These are future runtime obligations, not tests executed by STAT-01.
