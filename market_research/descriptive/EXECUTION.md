# Descriptive execution authority

This entry specializes the existing scalar analysis path in [Descriptive](ARCHITECTURE.md);
it does not govern the independent [Price Segmentation observation](cases/price_segmentation/ARCHITECTURE.md). It owns shared business identity,
execution boundaries and navigation. Observation, conversion, association and numerics
remain owned by [Observation](OBSERVATION.md), [Conversion](SAMPLE_CONVERSION.md),
[Association](RESULT_ASSOCIATION.md) and [Statistics](../../market_statistics/CONTRACT.md).
Acquisition follows [UPSTREAM.md](../UPSTREAM.md).

## Execution boundaries

| Concern | Narrow canonical owner |
| --- | --- |
| Direct fixed Job, pure preflight, stage failures and original evidence | [Single Job](JOB_EXECUTION.md) |
| ResearchPlan, whole-plan preflight, expansion, continue/stop, Skipped and BatchResult | [Batch](BATCH_EXECUTION.md) |
| Actual runtime readiness and verification | [Acceptance](ACCEPTANCE.md) |

Both operations use `market_research.descriptive.execution`. Batch composes public Single
Job execution, with no second execution engine. Reuse the existing Research-owned
[AnalysisRequest](RESULT_ASSOCIATION.md#public-operation-and-carriers); every listed analysis
is required, and analyses do not add an observation dimension. No hidden parameters,
dates, horizon, failure policy, normalization or deduplication are authorized. InvalidPlan
precedes all service creation and DataLake I/O.

Status: EXEC-01 and EXEC-02 are implemented for Index Trailing Return. Deterministic
verification belongs to the affected contract tests; current readiness and bounded
real-market validation are recorded in [Acceptance](ACCEPTANCE.md).

## Business identity and execution scope

A Job's stable business identity is the structural tuple of case/metric definition
identity and version, canonical subject identity, all metric parameters, horizon with
its unit, and window bounds with their anchor/inclusion semantics. Parameter names are
compared in canonical name order; collection-valued parameters follow the case's defined
order/equality. For the first case this tuple is specified in its authority. An
implementation may use this tuple directly or a collision-safe deterministic encoding;
a hash alone must never silently merge unequal tuples.

Identity never depends on random values, execution time, list position or process ID.
StatisticalSpec is not part of observation identity. Each analysis occurrence is associated
using (job_identity, request_id, exact spec). Results retain the exact request/spec and
execution context, so changing a spec under the same request_id cannot silently overwrite
or reuse a previous result. JobResult instances belong to a particular execution, not a
global cache keyed solely by observation identity. No durable execution ID scheme is
required; execution time, if retained, is context and not business identity.

Each attempted Job independently delegates preparation, construction, conversion,
Statistics and association through Single Job's public boundaries. No implicit sharing
of inputs, ObservationSet or projection across Jobs/runs is authorized. No retry,
concurrency, scheduler, persistence, replay, CLI, HTTP or report rendering is introduced.
Cancellation and process termination do not promise a complete BatchResult.
