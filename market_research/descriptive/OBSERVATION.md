# Descriptive observation authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). It owns fixed
observation requests, population accounting, validity and derivation. Public inputs
follow [UPSTREAM.md](../UPSTREAM.md); numerical models/methods remain
[Analyze-owned](../../market_analyze/CONTRACT.md). Status: Implementation Ready for
the [first case](cases/trailing_return/ARCHITECTURE.md); no producer exists yet.

## Fixed observation request

```text
ObservationJobSpec
  subject
  metric: versioned metric definition identity
  metric_parameters
  horizon
  historical_sample_window: inclusive (start_date, end_date)
```

One Job fixes one subject, one scalar metric definition and all its business parameters,
one positive integer horizon (bool rejected), and one inclusive historical date window.
Dates are date values, not timestamps or raw strings, with start <= end. The case defines
the horizon's unit and anchor meaning. `JobSpec` is only contextual shorthand.
Metric parameters are explicit, including an empty parameter set when the definition has
no parameters; statistical method parameters are not observation parameters.

The conceptual operation is `observe(ObservationJobSpec, prepared_inputs) -> ObservationSet`.
Only Input Preparation performs public upstream I/O. Construction consumes prepared
complete inputs; it does not secretly reacquire facts or shift dates. Changing observation
parameters changes the empirical request; changing only AnalysisSpec does not require
new observations. [Execution](EXECUTION.md) owns stable Job identity and expansion.

## ObservationSet

```text
ObservationSet
  job_identity / fixed_job_spec
  observation_definition: grain, key definition, formula/version, unit, temporal meaning
  candidate_anchors: deterministic ordered unique anchor sequence
  eligible_observations: ordered (observation_key, anchor, scalar_value)
  excluded_observations: ordered (observation_key, anchor, reason_code, reason)
  candidate_count / eligible_count / excluded_count
  provenance: actual input references and derivation definition
  sample_dependence_context
```

Counts are derived from their collections, not caller-supplied conflicting claims.
For the first scalar-per-anchor version, every candidate anchor owns exactly one unique
observation key and exactly one outcome: eligible or excluded. The two outcome collections
are disjoint and ordered by the candidate sequence. Duplicate keys, unaccounted anchors,
extra outcomes or inconsistent counts are invalid construction, never silently repaired.

```text
candidate_count = eligible_count + excluded_count
```

The case owns candidate population, exact key/order, scalar formula/unit, required facts,
legitimate null/absence and exclusion codes. Every exclusion keeps its key and reason.
No undeclared population filtering, imputation, truncation, rounding or hidden deduplication
is permitted. Values retain their calculated binary64 numerical coordinate.

Required upstream incompleteness, missing required records and invalid public views fail
the Job at input_preparation. They are not exclusions. Failures in applying a valid
formula/constructing an internally consistent set fail at observation_construction.
A complete population can be empty, or all candidates excluded, yielding a valid
ObservationSet with zero eligible values; conversion then fails explicitly under
[Analyze integration](ANALYZE_INTEGRATION.md). It is never a successful empty analysis.

## Provenance and reuse

Preserve actual requests, validated public input identity, retained consumed facts or
adequate immutable references, and formula/version back to the fixed request. A window
or mutable cache does not establish identical inputs; the case chooses a sufficient
fingerprint/retention strategy. No mandatory database, registry or artifact lifecycle
is imposed. Identity of the observation request differs from identity of the facts used.

One set supports multiple analyses through the Research converter. Research retains
sample dependence, including overlapping lookbacks; neither construction nor conversion
asserts independent samples. Generic statistical calculation belongs only to Analyze.

## Minimum acceptance obligations

Test total/disjoint candidate accounting, unique keys and deterministic ordering,
explicit exclusion reasons, missing required facts as failure, zero-candidate and
all-excluded sets, and unchanged identity when only statistical requests change.
Formula, boundary-history, unit and concrete provenance fixtures are owned by the
[first case](cases/trailing_return/ARCHITECTURE.md), not inferred from retired Research.
