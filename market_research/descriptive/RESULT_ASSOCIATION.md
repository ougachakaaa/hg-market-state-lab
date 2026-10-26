# Research statistical result association authority

This contract specializes [Statistics integration](STATISTICS_INTEGRATION.md) under
[Descriptive](ARCHITECTURE.md). It owns ASSOC-01 only: a synchronous, pure, case-agnostic
association of a published scalar observation population, projection, request and result.
Status: Implementation Ready; runtime readiness belongs to [Acceptance](ACCEPTANCE.md).
[Observation](OBSERVATION.md) owns the question/population/market derivation/provenance;
[conversion](SAMPLE_CONVERSION.md) owns NumericSample mapping and SampleBinding;
[Statistics](../../market_statistics/CONTRACT.md) owns numerical types and calculations;
[execution](EXECUTION.md) owns plans, attempts, Job/Batch results and orchestration.

## Public operation and carriers

```python
from market_research.descriptive.association import (
    AnalysisRequest, ResearchAnalysisEvidence, ResultAssociationFailure, associate,
)
# associate(fixed_job: ObservationJobSpec, observation_set: ObservationSet[P],
#           projection: SampleProjection[P], request: AnalysisRequest,
#           statistical_result: StatisticalResult) -> ResearchAnalysisEvidence[P]
```

Research owns these four names, exported with explicit aliases and no `__all__`.
Statistics continues to own NumericSample, StatisticalSpec = QuantileSpec | IntervalCountSpec,
StatisticalResult = QuantileResult | IntervalCountResult, validate_spec and compute.
Association consumes only public Research observation/conversion facades and the root
Statistics facade; no private imports, Execution dependency or new acquisition permission.
Observation stays Statistics-independent; Converter never depends on Association;
Statistics never depends on Research. No metric subclasses, dispatch registry, factory,
method plugins or context framework is introduced.

`AnalysisRequest` is a frozen value object with exactly `request_id: str` and
`spec: StatisticalSpec`. The ID is an explicit non-empty string preserved exactly,
including whitespace; do not trim, normalize or synthesize it. Constructor validation
raises ValueError for illegal IDs and Statistics InvalidStatisticalSpec for illegal specs,
using the public validate_spec exclusively. The exact spec object is retained.
The request contains no sample, Job identity, subject, provenance or acquisition instructions.
Identical specs with distinct IDs denote distinct analysis occurrences. Future ResearchPlan
preflight reuses this one type and owns cross-request ID uniqueness and InvalidPlan.
Malformed requests presented to associate fail as ResultAssociationFailure, even if local
construction was bypassed. No Executor/preflight is implemented by ASSOC-01.

`ResearchAnalysisEvidence[P]` is a frozen composition with exactly:

```text
request: AnalysisRequest
statistical_result: StatisticalResult
projection: SampleProjection[P]
```

Successful evidence from associate retains these three actual original objects, without
copying them. Read-only `source_observation_reference: ObservationSet[P]` follows
projection.binding.source_observation_reference. The source owns the original fixed Job,
full structural identity, definition (formula/version/unit/time meaning), subject,
parameters, horizon and inclusive window. Projection owns the original NumericSample
(ordered binary64 values/unit/derived count) and binding (ordered keys).
Binding/source retain candidate/E/U/X counts, every unavailable dependency and diagnostic,
exclusion reason and offending fact, original observation and market fact coverage,
warm-up/sample coverage, Not Applicable ratios, typed provenance, public inputs/proofs,
and dependence spans/overlapping-lookback interpretation. Where published by a case,
its original input profile/fingerprint remains unchanged. No universal fingerprint field
is required and none is recomputed. No copied ObservationSet, metadata dictionary,
generic ResearchContext or serialized envelope is added. Direct carrier construction is
not a substitute for the validated associate operation.

## Job, source and projection integrity

Validate public carrier types before reading their required fields. Revalidate fixed
ObservationJobSpec through its public construction contract without mutating its parameter
mapping. Reuse ObservationSet's public invariant validation after bounded carrier-shape
checks; do not import Converter validation internals or reproduce its full evidence engine.
Association checks retained coverage/dependence carrier structure and source accounting,
not the truth of case-owned market derivation, fingerprints or upstream public facts.

Structural Job equivalence is the published tuple:

```text
(metric/version identity, subject, metric_parameters sorted by name, horizon,
 definition.horizon_unit, window.start_date, window.end_date,
 definition.anchor_meaning, definition.bounds)
```

It must equal the source's published job_identity; definition.metric must agree.
Use the existing structural equality/parameter semantics, never a new ID or hash.
A separately constructed valid fixed Job with that same identity is accepted; source's
original fixed Job remains reachable, not replaced by the equivalent argument.
The projection binding must reference the **actual supplied ObservationSet** (`is`),
even when another source has equal question fields or equal retained facts.

Required mapping checks, without calling convert or reconstructing observations:

```text
len(numeric_sample.values) = len(binding.ordered_observation_keys) = source.eligible_count
source.candidate_count = eligible_count + unavailable_count + excluded_count
```

Require non-empty immutable NumericSample coordinates and immutable binding keys.
Every key must equal the corresponding Eligible key in source order: no loss, duplication
or reordering. Every value must have the identical binary64 coordinate as the corresponding
Eligible scalar, including the sign of zero. Unit equals definition.unit exactly.
Reuse public NumericSample construction for numerical legality without replacing the
retained sample; do not call private Statistics validators or normalize supplied values.
Original typed source/provenance/coverage/dependence references must remain reachable.

## Exact request/result linkage and bounded result checks

Revalidate the request with public validate_spec. A manually constructed result is not
trusted merely for having a result dataclass type. Require the public V1 concrete variants,
immutable tuples for result sequences, finite built-in binary64 floats for result
coordinates/payloads, an exact positive int sample_count (excluding bool) equal to the
NumericSample count, and a non-empty string unit equal to its unit.
Float parameter matching preserves binary64 coordinates, including signed zero.
No tolerance, rounding, sorting, unit conversion or replacement spec is permitted.

| Request/result | Required linkage and structure |
| --- | --- |
| QuantileSpec / QuantileResult | method=quantile, estimator=type7_linear_v1; points_and_values is an ordered tuple of two-float pairs; point sequence equals the exact request points, once each, with finite values; common count/unit match |
| IntervalCountSpec / IntervalCountResult | method=interval_count; finite edges equal exact spec edges in order; spec/result/sample units equal; exactly len(edges)-1 typed IntervalBins; each left/right equals adjacent requested edges; left_inclusive is True and right_inclusive is True only for the final bin; common count/unit match |

Interval bin/outside counts must be exact nonnegative ints (not bool), individually at
most sample_count, and sum to sample_count. Frequencies must be finite floats in [0,1]
and equal each retained count / sample_count in binary64, including under/overflow.
This checks the public accounting structure, without scanning sample membership.
It implies the published frequency conservation within binary64 roundoff.
These bounded checks validate safe association payloads; they do **not** certify quantile
interpolation, histogram membership or mathematical correctness. No Type 7, histogram,
backend or second general Statistics validation engine is implemented in Research.

## Failures, scope and non-guarantees

`ResultAssociationFailure` exposes `stage = "result_association"`,
`category = "ResultAssociationFailure"`, readable `reason`, and optional `request_id`
and `job_identity`. Retain the ID only when an identifiable public request contains a
legal ID. Retain Job identity only after the supplied fixed Job and source's published
definition safely establish it; malformed inputs do not receive invented identities.
Translated validation failures retain readable causes via exception chaining.
Wrong variants, missing/malformed fields, Job/source mismatches, key/value/unit/count
mismatches and invalid method/estimator/parameter/geometry/accounting all fail here,
never as Statistics CalculationFailure. No partial successful evidence is returned.
No input is mutated, replaced or discarded; the caller still holds the raw result.
Future Executor owns attempts/AnalysisOutcome and must retain returned raw results on
association failure; ASSOC-01 adds no separate outcome/Job/Batch carrier.

A bare StatisticalResult has no source-sample identity. Metadata-identical externally
supplied results may have unrelated hidden computation histories; associate **cannot
prove** that a result was computed from this sample. It verifies the observable relations
above, not cryptographic or execution-origin attestation. Future Executor must pass the
actual result from its corresponding compute call directly to associate. Do not add
hashes, attestations or cache keys to hide this limitation.

Association never acquires facts, calls services, convert or compute, reconstructs
observations, recalculates statistics, changes payloads/units or repairs mismatches.
No network/storage/file I/O, mutation, randomness, clock dependency, background execution,
orchestration, retry, cache, replay, serialization, persistence, evidence search or durable
execution identifier is introduced. In-memory retention permits caller-managed sample
reuse while references live; it is not a caching or storage system.

## Acceptance obligations

Use public complete and partial Trailing Return fixtures and actual public compute
results for both methods. Verify exact retained objects, full question/definition,
sample/keys, original typed fingerprint/profile/inputs, missing/excluded facts, all
coverage/dependence context and one shared projection serving distinct requests.
Test separately constructed equivalent Jobs; reject changed horizon/window/metric/subject
and equal-question but different source objects. Corrupt public carriers deliberately:
wrong variants, missing fields, empty/reordered/duplicate keys, wrong values/count/unit,
signed-zero mismatch, malformed requests, quantile parameters/estimator, interval
edges/bin geometry/closures/counts/frequencies. Assert attributable failures, causes,
unchanged raw results/inputs, immutable evidence and negative no-I/O/no-convert/no-compute
guards. A distinct legal scalar case with another typed provenance must pass without
Trailing Return assumptions. Explicitly accept metadata-identical payloads whose hidden
computation origin cannot be inferred. Executors, persistence and live acceptance remain
separate gates.
