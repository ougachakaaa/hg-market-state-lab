# Descriptive scalar sample conversion authority

This contract specializes [Descriptive](ARCHITECTURE.md) and consumes the published
[Observation contract](OBSERVATION.md) and [Statistics public contract](../../market_statistics/CONTRACT.md).
It is the canonical owner of CONV-01: conversion, binding, validation and acceptance.
Result association belongs to [Statistics integration](STATISTICS_INTEGRATION.md);
Job/Batch failure accounting belongs to [Execution](EXECUTION.md).

## Ownership and public operation

Research owns one case-agnostic converter for published single-variable Descriptive
ObservationSets. It understands Research identity and evidence, never market formulas.
Statistics owns NumericSample and numerical legality; it never depends on Research.

```python
from market_research.descriptive.conversion import (
    SampleProjection, SampleBinding, InvalidObservationSet,
    UnmappableSample, NoEligibleObservations, convert,
)
# convert(observation_set: ObservationSet[P]) -> SampleProjection[P]
```

The only newly permitted cross-module edge is from
`market_research.descriptive.conversion` to the **root public** `market_statistics`
facade. Observation, Input Preparation and Construction remain independent of Statistics.
Conversion consumes Observation's public facade, never case internals or Statistics internals.
Explicit alias exports are used; no `__all__` is needed.

## Projection and binding

`SampleProjection[P]` is an immutable Research carrier with `numeric_sample:
market_statistics.NumericSample` and `binding: SampleBinding[P]`.
`SampleBinding[P]` is one concrete immutable carrier composed of:

- `source_observation_reference: ObservationSet[P]`: the actual originating object;
- `ordered_observation_keys: tuple[ObservationKey, ...]`: the Eligible keys in candidate order.

Its read-only properties expose `candidate_count`, `eligible_count`, `unavailable_count`,
`excluded_count`, `unavailable_records` (complete UnavailableObservation tuples),
`exclusion_reasons` (complete ExcludedObservation tuples), `coverage_context`
(the original MarketFactCoverage), `observation_coverage`, `unavailable_ratio`,
`excluded_ratio`, `business_provenance: P` and `sample_dependence_context`.
These derive from/reference the retained source, rather than storing conflicting copies.
The exact `job_identity`, `fixed_job_spec` and `observation_definition` remain reachable
through that typed source. Not Applicable ratios remain `None`.

Preserve all missing fact identities, anchors, reasons, public evidence references and
diagnostics; preserve excluded keys, reason codes/text and offending facts/values.
Keep overall, warm-up and sample fact coverage unchanged. Original public CoverageResults
remain reachable through the source's typed provenance. For Trailing Return this is the
unchanged TrailingReturnProvenance with input_profile, input_fingerprint, retained inputs
and endpoint evidence. Do not rehash, parse private payloads or impose that case's shape
on other provenance types. The source reference is in-memory; no persistent resolution
protocol, metadata dictionary, universal evidence envelope or artifact registry is added.

## Exact mapping and reuse

Every Eligible scalar enters NumericSample once in candidate order; its key occupies
the same position in the binding. Retain equal values with distinct keys and signed zero.
The unit comes unchanged from observation_definition. Binary64 legality is Statistics-owned.

```text
len(numeric_sample.values) = len(binding.ordered_observation_keys) = eligible_count
candidate_count = eligible_count + unavailable_count + excluded_count
```

The producer alone decides eligibility. No sorting values independently, deduplication,
truncation, outlier screen, imputation, winsorization, rounding, unit transformation,
formula recomputation or weights are permitted. Missing values never become zero.
One projection can serve multiple independent Quantile/IntervalCount requests without
changing its source or binding. Only numeric_sample crosses into Statistics; results are
not Research Evidence until later association.

## Validation and failures

At the public conversion boundary verify the public ObservationSet variant and required
typed records/immutable collections, fixed request and identity relationship, valid unique
ordered candidate dates, exactly one correctly keyed outcome per candidate, outcome order,
derived counts, finite binary64 Eligible coordinates, typed coverage and dependence context.
Reuse the published Observation validation capabilities for their existing invariants;
do not define new eligibility or case-specific validity rules. Validate retained record
shapes and required evidence, without reacquiring facts, reconstructing calendar anchors,
recomputing formulas or fingerprints. Provenance is retained as the source's case-owned
typed record; no cross-case provenance schema is published by conversion.

Failure precedence is:

1. Invalid/inconsistent source: `InvalidObservationSet`.
2. Structurally valid source with no Eligible: `NoEligibleObservations`.
3. Otherwise valid source rejected by the public NumericSample constructor:
   `UnmappableSample`.

All three Research errors expose `stage = "conversion"`, their named `category` and a
readable reason; translated exceptions retain the original cause. Reuse Statistics
`InvalidSample`, not a duplicate numerical validator. Observation already rejects illegal
scalar coordinates: such corruption is InvalidObservationSet. A malformed unit rejected
only by Statistics is UnmappableSample; do not weaken either upstream contract for tests.
No empty sample, silent repair, reordering or dropped value is allowed. A failed conversion
leaves all source evidence intact; no JobResult is implemented by this contract.

## Purity and extension boundary

`convert` is synchronous, deterministic and pure. It performs no acquisition, services,
network, persistence, provider calls, statistics execution or source/nested-evidence mutation.
Use immutable/effectively immutable carriers and original typed references, without deep
copying market inputs. Retain horizon, spans and overlapping-lookback meaning; never
assert independence. No metric dispatch, subclasses, BaseConverter, registry, factory,
generic adapter hierarchy, paired/temporal/grouped bindings or Conditional framework is
introduced. Another legal Descriptive scalar case reuses this converter and binding.
Future sample shapes need actual mathematical/association requirements.

## Deterministic acceptance

Converter-owned tests reuse public Observation fixtures, without network or user caches:

| Scenario | Obligation |
| --- | --- |
| Complete [100,110,121,110,121], H=2 | Exact [121/100-1,0,0], three keys, decimal_ratio, unchanged fingerprint |
| Missing D2 in [100,110,missing,90,120,130], H=2 | 4=2+2+0, ordered D3/D5 values, observation coverage 2/4, fact coverage 5/6; all dependency evidence retained |
| Equal values / mixed E,U,X | No deduplication/second eligibility policy; full records and conservation |
| Zero candidates / all U / all X / mixed U,X | NoEligibleObservations, original evidence intact; None ratios for zero candidates |
| Wrong types / corrupted public records | InvalidObservationSet before zero-eligible/mapping checks; no repair |
| Unmappable source | UnmappableSample with cause; illegal Observation coordinates remain InvalidObservationSet |
| Provenance and dependence | Exact source, fixed request, definition, fingerprint/profile, coverage, diagnostics, horizon/spans retained |
| Immutability and purity | Stable positional linkage and original evidence; no I/O or computation invocation |
| Reuse | Same projected sample consumed by public Quantile and IntervalCount; assert numerical outputs and unchanged binding |

Architecture tests enforce the converter's precise public Statistics edge, existing
DataLake public access/preparation-only acquisition and continued absence of Executor.
ASSOC-01 separately authorizes [association](RESULT_ASSOCIATION.md)'s public edges;
Converter remains independent of Association.
