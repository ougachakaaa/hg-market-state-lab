# Descriptive execution authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). Research owns
`ResearchPlan`, single-job and batch orchestration, `JobResult` and `BatchResult`.
Observation semantics belong to [OBSERVATION.md](OBSERVATION.md), outbound adaptation to
[ANALYZE_INTEGRATION.md](ANALYZE_INTEGRATION.md), and numerical methods/results/failures to
[Analyze](../../market_analyze/CONTRACT.md). Public input invariants remain in [UPSTREAM.md](../UPSTREAM.md).

## Plan and execution boundaries

A `ResearchPlan` expresses batch research parameters and execution policy. It may contain
subjects, horizons, historical windows, metric parameters, requested Analyze-owned
`AnalysisSpec`s and execution policy. Validate the plan before beginning execution; an
invalid plan fails explicitly rather than launching a partial selection of valid Jobs.

The plan expands by a declared rule into fixed-parameter `ObservationJobSpec`s. `JobSpec`
is a shorthand, not an additional model. Each Job fixes one subject, metric definition,
horizon, historical sample window and necessary business parameters. The selected rule
must make the planned Jobs identifiable so all can be accounted for in the BatchResult.
No Cartesian product, pairing, ordering or duplicate-handling default is chosen here.

Conceptual operations, without prescribed Python classes, callable names or concurrency:

```text
execute_job(ObservationJobSpec, AnalysisSpecs) -> JobResult
execute_batch(ResearchPlan) -> BatchResult

Single Job:
    complete input preparation → ObservationSet → NumericSample
        → Analyze public API → Research result association → JobResult
Batch:
    validate ResearchPlan → expand fixed Jobs → Single Job execution → BatchResult
```

Executors control execution and reporting. Market formulas belong to Observation
Construction; statistical formulas belong to Analyze. Executors do not calculate either.
Only Input Preparation acquires upstream facts. Conversion, Analyze and result assembly
must not hide upstream I/O.

The Job is the independent execution and result-reporting unit; it need not be the upstream
acquisition unit. Several Jobs may reuse already prepared complete inputs when each Job's
requirements and the selected public contracts are satisfied. Reuse must preserve actual
input provenance and grants no implicit common-snapshot or freshness guarantee.

## Results, statuses and failure isolation

`JobResult` associates the fixed observation request, requested analyses, actual execution
and input context, observation/sample references, Analyze results or failure context, and
the final Job status. It supplies the context needed for Research interpretation without
redefining Analyze's result or failure types. The exact field layout is not prescribed.

| Status | Meaning |
| --- | --- |
| Success | The attempted Job completed legally under its declared requirements and execution policy. |
| Failed | The Job was attempted but could not legally complete. Preserve its failure stage and reason. |
| Skipped | The Job was not attempted under the declared execution policy. Preserve the policy reason. |

A failure during input preparation, observation construction, conversion, Analyze or
result association remains a failure at that stage. Upstream incompleteness is never a
population exclusion or a successful partial research input. Failed must not be converted
to Skipped merely to continue execution.

Batch policy explicitly controls whether a failed Job stops execution or other independent
Jobs continue. A `BatchResult` must account for every planned Job's final status and
applicable failure stage/reason or skip reason. It includes successful results and failure
context, not only successful Jobs. Partial Success is permitted at batch level; it does
not authorize partial required inputs within a Job. Unattempted Jobs after a policy stop
must remain visible with their declared skip reason.

## Decisions required before implementation

This authority fixes ownership and status distinctions, not undeclared execution defaults.
The following decisions remain pending here and must be made before the corresponding
executor is implemented:

- Plan expansion and validation rules, including ordering and duplicate handling where relevant.
- Execution policy selection and defaults, including stop/continue behavior after failure.
- How multiple requested analyses are accounted for when one fails: continuation within
  the Job, retained results and final Job / batch summary aggregation. Individual failures
  must stay visible and cannot be relabeled Skipped after an actual attempt.

Concrete cases must also settle their observation/input contracts; Analyze must settle
the numerical methods being invoked. No fallback behavior may be inferred from silence.

Single Job and Batch Executors are Expected Implementation Gaps. V1 does not introduce
a generic DAG, queue, scheduler, concurrency framework, retry framework, permanent task
database, mandatory research persistence or compatibility with retired runners.
