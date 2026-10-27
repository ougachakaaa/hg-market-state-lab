# Descriptive Single Job execution contract

This contract specializes [Execution](EXECUTION.md), which owns business identity and
[Plan/Batch control](BATCH_EXECUTION.md). It owns EXEC-01: the direct single Job public boundary,
preflight, immutable execution records and stage accounting. It does not own market
formulas, acquisition, conversion, numerical algorithms or association validation.
Status: EXEC-01 implemented. Actual verification belongs to
[Single Job acceptance](JOB_EXECUTION_ACCEPTANCE.md) and [readiness](ACCEPTANCE.md).

## Public operation and preflight

```python
from market_research.descriptive.execution import (
    InvalidPlan, FailureRecord, AnalysisOutcome, JobResult, execute_job,
)
from market_research.descriptive.association import AnalysisRequest
# execute_job(fixed_job: ObservationJobSpec,
#             analysis_requests: Sequence[AnalysisRequest]) -> JobResult
```

Exports use explicit aliases without `__all__`. The first implementation binds only
the published [Index Trailing Return case](cases/trailing_return/ARCHITECTURE.md).
Before **any** upstream service creation or DataLake operation:

1. Call the case public `validate_job(fixed_job) -> JobIdentity`. It reuses existing
   fixed-request and case validation, including canonical index identity, exact metric
   version, explicit empty parameters, positive non-bool H, date-only inclusive ordered
   window and the existing Asia/Shanghai current-date limit. It returns the existing
   full structural business identity, without I/O or mutation.
2. Require an ordered non-empty `collections.abc.Sequence`, excluding strings, bytes,
   bytearray, maps and sets. Snapshot its order into a tuple, retaining each original
   request. Iterators/generators are not ordered sequence inputs to this API.
3. Require each item to be the public AnalysisRequest with a non-empty string ID retained
   exactly. Validate its exact spec using Statistics public `validate_spec`, even if
   constructor validation was bypassed. Require unique IDs within the Job. Identical
   specs with different IDs are legal distinct occurrences.
4. Require IntervalCount unit to equal the case public immutable `DEFINITION.unit`
   exactly (currently `decimal_ratio`), the same source used by construction. No defaults,
   normalization, implicit parameter generation or method-level deduplication is allowed.

Invalid inputs raise `InvalidPlan` with readable cause and chained originating exception
(including InvalidStatisticalSpec), before preparation and with no JobResult. Direct
preflight does not implement ResearchPlan, Cartesian expansion or Batch preflight.

## Immutable runtime records

All three carriers are Research-owned frozen typed dataclasses. Tuple collections retain
order; original component objects are referenced rather than deep-copied. Direct carrier
construction is not an alternative to validated execution.

`FailureRecord` contains `job_identity`, `failure_stage`, `failure_category`, readable
`reason`, optional attributable `request_id`, and `error: Exception`, the actual original
exception. Its exception chain and typed preparation evidence remain inspectable. Never
flatten UpstreamFailure/InputAttempt or distinct numerical categories into generic text.

`AnalysisOutcome` contains the original `request`, `status: success | failed |
not_attempted`, optional `statistical_result`, `associated_evidence`, `failure` and
`not_attempted_reason`. `request_id` and `spec` are read-only properties of the retained
request, not duplicate fields. Success retains both actual raw result and evidence;
failed compute has a failure and no result/evidence; failed association retains its raw
result and failure, without evidence. Not-attempted has only the blocking readable reason.

`JobResult` contains `fixed_job_spec`, `job_identity`, `status: Success | Failed | Skipped`,
ordered `analysis_outcomes`, optional `prepared_inputs`, `observation_set`, `projection`,
and ordered `failures`. The first implementation uses the case's published typed
PreparedInputs and TrailingReturnProvenance, without a new universal context model.
Read-only `input_attempts` returns the original prepared attempts, or obtained attempts
from the preparation failure when preparation did not return. Provenance, Coverage,
SampleBinding and StatisticalResult remain reachable through original objects.
`skip_reason` and `triggering_failed_job_identity` are reserved optional fields, always
None from execute_job. Only [Batch policy](BATCH_EXECUTION.md) constructs Skipped: no facts/results are
fabricated and every request is not_attempted with its policy reason.

## Stage control and evidence retention

```text
Preflight → prepare_inputs → construct_observations → convert
    → for each original request: compute → associate → AnalysisOutcome
    → JobResult
```

Use only public component facades. One Job prepares once, constructs one ObservationSet
and converts it once into one SampleProjection. All requests share its actual NumericSample.
Pass each exact spec and the actual corresponding returned StatisticalResult to associate.
No hidden reacquisition, reconstruction, recomputation, deduplication, retry, cache,
parallelism or result repair is authorized. Execution identity belongs to this memory run;
no durable execution ID is introduced.

Preparation, Construction or Conversion failure ends those stages: return Failed with
exactly one not_attempted outcome per request, in original order. Retain all obtained
objects: prepared inputs/attempts survive Construction failure; the entire ObservationSet
survives Conversion failure, including every missing/excluded record, original coverage
and typed provenance. Never create an empty NumericSample for zero Eligible.

After legal conversion, attempt every request synchronously in order, even after a prior
compute or association failure. A compute failure records no association attempt for that
request. An association failure retains the raw result. Never fill a missing attempted
outcome during final assembly or discard an already returned result.

Success requires every required analysis and association to succeed. Any stage/required
analysis failure yields Failed while retaining other successes. A legal partial population
with eligible samples may succeed: recoverable Ensure unit failures are diagnostics,
not execution failures; final public inputs must still validate. No extra coverage
threshold is introduced. Zero Eligible fails conversion with NoEligibleObservations.

| Occurring stage | Defined categories retained at that stage |
| --- | --- |
| input_preparation | InputPreparationFailure and its UpstreamFailure, IncompleteInput, InvalidPublicInput, HistoryInsufficient categories; actual requests/attempts and original InvalidRequestError/OperationError cause retained |
| observation_construction | ObservationConstructionFailure; input validation failures raised during pure construction retain their original preparation error category, but failure_stage records the actual construction call |
| conversion | InvalidObservationSet, UnmappableSample, NoEligibleObservations |
| analyze | InvalidSample, InvalidStatisticalSpec, CalculationFailure, without parsing messages |
| result_association | ResultAssociationFailure, raw StatisticalResult retained |

Ordinary unexpected `Exception` at any stage records `ExecutionFailure` at the actual
stage with its original exception and readable type/cause; an unexpected exception is
not falsely labeled as a defined upstream/numerical/association error. Catch no
BaseException: system exit, KeyboardInterrupt and cancellation propagate. FailureRecords
follow occurrence order and request-attributable failures use the original request ID.
The analyze stage name remains Research-owned while computation stays Statistics-owned.

## Authority reconciliation

| Existing owner | EXEC-01 resolution |
| --- | --- |
| Execution identity and all-required-analysis rule | Remain valid; direct Job preflight and complete ordered carriers specialize them here |
| Observation/case preparation and construction | Remain valid; expose minimal pure case validator returning existing identity; Executor never imports private inputs or duplicates case rules |
| Conversion and association | Remain independent, pure, case-agnostic public capabilities; failures/objects retained without changing algorithms |
| Statistics public contract | Root facade only: validate_spec, compute, public spec/result variants and errors; no numerical implementation copied |
| Prior tests forbidding execution | Superseded only for the precise execution-to-public-component edges; components and Statistics cannot depend on execution |
| Plan/Batch | Specialized by [EXEC-02](BATCH_EXECUTION.md); direct Job still returns Success/Failed only |
| Persistence, cache/replay, CLI/HTTP and live-data gate | Deferred; no new runtime/API or live acceptance claim |

Deterministic acceptance must cover complete/partial populations, zero eligible, all
preflight rejection classes with zero upstream I/O, distinct preparation/construction
failures and retained evidence, known versus unexpected errors at every stage, ordered
continuation after compute/association failures, exact object/spec/result passage,
one-time construction/conversion, immutability and complete one-outcome-per-request
accounting. Use public-contract fakes or narrow operation monkeypatches, never real
market services or default caches. No DI framework, case registry or execution engine.
