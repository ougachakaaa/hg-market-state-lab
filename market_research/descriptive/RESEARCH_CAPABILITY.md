# Research capability publication authority

This narrow contract specializes [Descriptive](ARCHITECTURE.md). It owns the read-only
publication of admitted Research capabilities and pure plan preview. Case, observation,
execution and numerical semantics retain their existing owners. HTTP transport belongs
to the [HTTP contract](../../ui_http/products/research/http-contract.md).

## One admitted capability

`market_research.descriptive.capabilities` publishes `list_capabilities()` and
`get_capability(id)` as immutable descriptions, with exactly one explicit declaration:
`trailing_cumulative_return_v1`, descriptive Index Trailing Cumulative Return Research.
Unknown IDs raise `CapabilityNotFound`; never synthesize a supported capability. No
registry, plugin/provider framework or runtime registration is authorized. Another entry
requires Research-owned semantic admission and its case/public input contract first. The
[Price Segmentation](cases/price_segmentation/ARCHITECTURE.md) case implements an
independent `price_segmentation_v1` Python Observation API. Its specified isolated
real-market scopes are recorded as passed in [Acceptance](ACCEPTANCE.md). It is not
published by this facade, ResearchPlan, preview or HTTP; these remain Trailing Return only.
The R01-A [Futures Basis case](cases/futures_basis/ARCHITECTURE.md) is likewise not a
published capability. Its separate [online application](cases/futures_basis/ONLINE_APPLICATION.md)
is a case-specific HTTP/Web workflow that does not extend capability discovery,
ResearchPlan, preview, Batch or Publication.
Offline human review does not extend Capability Publication.

Read metric, formula, units, calendar and time meaning from the existing public case
`DEFINITION` where possible. Supported means implemented, not currently live-ready.
Descriptors perform no service creation, export, ensure, provider probing or market I/O.

The descriptor publishes these explicit constraints, without defaults:

- Full canonical index_code, pattern `[0-9]{6}\.(SH|SZ|CSI)`; `000852.SH` is the
  metadata-verified CSI1000 example from
  [bounded real-market validation](ACCEPTANCE.md#real-market-validation-evidence),
  never a subject default. Syntax validation does not prove provider membership.
- Exact versioned metric and explicit `metric_parameters={}`. Ordered non-empty unique
  subjects, horizons and windows; ordered non-empty analyses with unique unchanged IDs.
- Positive non-bool integer horizons in trading_sessions; date-only inclusive windows,
  start <= end, end no later than today in Asia/Shanghai. No inferred inputs or provider.
- Quantile: method `quantile`, required points, non-empty strictly increasing unique
  finite probabilities in [0,1], estimator `type7_linear_v1`.
- IntervalCount: method `interval_count`, required edges (at least two strictly increasing
  finite coordinates) and exact unit `decimal_ratio`; final bin includes its right edge,
  other bins are left-closed/right-open, with underflow/overflow and full-sample frequencies.
- Statistics public Specs / `validate_spec` remain the only numerical legality authority:
  [contract](../../market_statistics/CONTRACT.md), [Quantile](../../market_statistics/QUANTILE.md),
  [IntervalCount](../../market_statistics/INTERVAL_COUNT.md). Descriptions are publication,
  not another validator or method dispatch engine.
- Required on_job_failure `continue` or `stop`; Batch `success|partial_success|failed`,
  Job `Success|Failed|Skipped`, analysis `success|failed|not_attempted` retain
  [Batch](BATCH_EXECUTION.md) and [Job](JOB_EXECUTION.md) meanings.
- Live upstream can be unavailable; partial Index facts may succeed with honest coverage,
  no eligible samples or incomplete Calendar may fail. No persistent Research Run,
  replay, result cache, stock case, Conditional Research, predictions or trading signals.

## Pure preview facade

`market_research.descriptive.execution.preview_plan(plan) -> PlanPreview` reuses the
same complete `preflight_plan` expansion as execute_batch, including every late Job.
It returns frozen `PlanPreview(plan, jobs)` and frozen `PlannedJob(fixed_job_spec,
job_identity)` records in subjects → horizons → windows order. Derived planned_count and
analysis_attempt_count describe required attempts if all Jobs execute; stop can reduce
actual attempts. It revalidates a potentially corrupted Plan; InvalidPlan precedes any I/O.
No service is created, no availability probe occurs, and no preview/result is persisted.

This adds no Plan legality rule, calculation or second expansion implementation. Python
ResearchPlan remains free of HTTP limits, acknowledgment and transport dependencies.
The stable [usage guide](../USAGE.md) explains human and agent operation; it is not authority.
