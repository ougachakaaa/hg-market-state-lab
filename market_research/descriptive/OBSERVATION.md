# Descriptive observation authority

This contract specializes the scalar observation path in the [Descriptive entry](ARCHITECTURE.md).
It does not govern the independent structured [Price Segmentation observation](cases/price_segmentation/ARCHITECTURE.md). It owns fixed
requests, population, outcomes, coverage and derivation. Public inputs follow
[UPSTREAM.md](../UPSTREAM.md); numerical contracts remain
[Statistics-owned](../../market_statistics/CONTRACT.md). Status: Implementation Ready for
the [index first case](cases/trailing_return/ARCHITECTURE.md). Its independent Python
producer is published under `market_research.descriptive.observation`.

## Fixed observation request

```text
ObservationJobSpec
  subject
  metric: versioned metric definition identity
  metric_parameters
  horizon
  historical_sample_window: inclusive (start_date, end_date)
```

One Job fixes one subject, scalar metric and explicit business parameters (including an
empty set where appropriate), one positive integer horizon (not bool) and one inclusive
date window with start <= end. Dates are date values, not timestamps or raw strings.
The case defines horizon unit, calendar and anchor meaning. Statistical parameters are
not observation parameters. JobSpec is contextual shorthand.

A subject is a market observation object with explicit stable identity, time basis and
authorized public fact source. It is not universally index_code. Indexes, individual
stocks, index futures, commodity futures and other formally published market series can
share this abstraction without an Instrument Master, market-series framework or metric
DSL. Each concrete case must bind identity, public source, applicable calendar, time and
measurement units, record identity/availability validation and metric price convention.
For stocks, raw-price change and adjusted/economic return must be distinguished; splits
and dividends cannot be ignored while claiming economic return. Abstract permission does
not publish a data capability. Current bindings/gaps are in [ACCEPTANCE.md](ACCEPTANCE.md).

The public operation is `observe(ObservationJobSpec) -> ObservationSet`; the independent
pure operation is `construct_observations(ObservationJobSpec, prepared_inputs)`.
Only Input Preparation performs upstream I/O. Construction consumes validated facts and
availability proof; it cannot reacquire facts or shift dates. Changing only StatisticalSpec
does not require new observations. [Execution](EXECUTION.md) owns Job identity/expansion.

## Population and temporal invariants

The case's formal calendar determines candidate anchors in the inclusive sample window
and horizon offsets. All legal open dates are candidates, even when quotations are absent.
Closed dates are neither candidates nor missing observations. Warm-up sessions can precede
the window but never enter its candidate denominator. Price-row positions do not determine
the calendar, and code suffixes do not select it. Missing prices never compress horizon.
If the necessary calendar/history cannot prove candidates and offsets, preparation fails;
weekdays, natural-day approximations, unknown-range skipping or shorter horizons cannot
substitute. The first case owns its exact backward discovery in
[INPUTS.md](cases/trailing_return/INPUTS.md).

## ObservationSet and outcome accounting

```text
ObservationSet
  job_identity / fixed_job_spec
  observation_definition: grain, key definition, formula/version, unit, temporal meaning
  candidate_anchors: deterministic ordered unique sequence
  eligible_observations: ordered (observation_key, anchor, scalar_value)
  unavailable_observations: ordered (observation_key, anchor, missing_dependencies)
  excluded_observations: ordered (observation_key, anchor, reason_code, reason, offending_facts)
  candidate_count / eligible_count / unavailable_count / excluded_count
  market_fact_coverage / observation_coverage / unavailable_ratio / excluded_ratio
  provenance: actual inputs, public availability evidence, derivation definition
  sample_dependence_context
```

Every candidate owns one unique observation key and exactly one outcome. Collections
are disjoint and follow candidate order. Counts derive from collections, never independent
conflicting claims.

```text
candidate_count = eligible_count + unavailable_count + excluded_count
```

| Outcome | Meaning and retained evidence |
| --- | --- |
| Eligible | All required legal facts satisfy declared business eligibility; finite scalar with key and anchor. |
| Unavailable | Candidate is legal but at least one necessary fact is unavailable under authorized partial-input policy. Each missing dependency retains required fact identity, missing reason and reference to applicable public availability evidence, in deterministic case order. |
| Excluded | All required facts exist legally but fail a declared business qualification. Retain key, anchor, reason code/text and all offending facts. |

An unavailable candidate is counted once even with several missing dependencies. One
missing fact may affect many candidates, each with its own outcome and dependency links.
No row alone proves suspension, pre-listing or delisting. Invalid public facts and unknown
calendar are failures, never Unavailable or Excluded. The case defines precedence for
mixed missing/business-invalid endpoints and exact reason codes.

No undeclared filtering, imputation, truncation, rounding, deduplication or outlier screen.
Eligible numbers retain calculated binary64 coordinates. Duplicate keys, extra outcomes,
unaccounted anchors and inconsistent counts fail construction, never silent repair.
Legal zero-candidate, all-unavailable and all-excluded populations yield valid zero-eligible
sets; [conversion](SAMPLE_CONVERSION.md) then fails explicitly, preserving diagnostics.

## Coverage

Market Fact Coverage is `available_fact_units / expected_fact_units` in the declared
necessary request range, including warm-up. Cases define keys and unit basis consistent
with the public contract and full legal calendar; count distinct fact units, not repeated
uses by anchors. Retain expected and available identities, numerator/denominator and the
original public CoverageResult separately. A legal non-positive price is available even
if business-excluded. Multiple sources retain separate coverage; incompatible unit bases
cannot be summed into an undefined overall rate. Report warm-up coverage independently
when applicable. Empty expected-unit populations have Not Applicable fact ratios.

For candidate_count > 0:

```text
observation_coverage = eligible_count / candidate_count
unavailable_ratio   = unavailable_count / candidate_count
excluded_ratio      = excluded_count / candidate_count
```

All three ratios are Not Applicable when candidate_count = 0, never invented 0% or 100%.
Positive candidates with zero eligible have 0% observation coverage. Eligible count is
never the population denominator. Fact availability, computable observation proportion
and business exclusion proportion are distinct quantities, all preserved for interpretation.

## Failures, provenance and reuse

Under a case's missing-tolerant policy, legal partial facts can construct a set; malformed
scope/schema/identity/counters/records and calendar insufficiency fail input_preparation.
Operation-wide errors remain UpstreamFailure. Illegal numerical results from valid inputs
or inconsistent sets fail observation_construction. Other cases remain fail-closed under
UPSTREAM. ObservationSet validity alone never establishes final Job Success.

Retain actual requests, validated public inputs/proofs or adequate immutable references,
formula/version and fixed request linkage. Mutable cache/window labels cannot establish
identical inputs. The case chooses sufficient fingerprint/retention rules; request identity
differs from actual input identity. No database or durable lifecycle is mandated.
One set can support several analyses; dependence/overlapping lookbacks remain Research
context, never an independence assertion.

## Python boundary

`market_research.descriptive.observation` publishes `ObservationJobSpec`, `DateWindow`,
`ObservationSet`, outcome / coverage records, explicit failure types and `observe`.
`subject` is a stable identity string, with its interpretation and validation selected
by the metric case, rather than an index-specific field on the general request.
The first case requires a full canonical index code and an explicit empty mapping of
metric parameters. Requests copy parameters into an immutable mapping; dates and H have
no defaults. `None` represents a Not Applicable ratio. Counts derive from immutable
outcome tuples. Observation keys use the full structural Job identity and anchor.

The case boundary `market_research.descriptive.cases.trailing_return` publishes
`prepare_inputs` and `construct_observations` for independent consumption/testing,
plus the pure `validate_job(job) -> JobIdentity` for [direct Job preflight](JOB_EXECUTION.md).
The validator reuses case rules without service creation and preserves caller inputs.
Preparation defaults to the selected public factories; keyword-only Calendar / Index
service arguments support public-contract fakes without changing source selection.
Construction consumes retained, validated prepared views and performs no I/O.
Its provenance retains typed case inputs, exact canonical bytes / SHA-256 and endpoint
requirements. Preparation failures expose their stage, category, request and all obtained
attempt evidence; upstream errors retain their original exception as the cause.
No observation API implements Research Job/Batch execution or conversion.

## Minimum acceptance obligations

Verify total/disjoint accounting, unique ordered keys, all missing dependencies, explicit
exclusions, coverage denominators and zero-denominator semantics. Verify malformed inputs
fail while legal partial exports preserve candidates. Cover empty, all-unavailable,
all-excluded and mixed sets, unchanged identity for statistical-only changes, formula,
history and provenance fixtures through [ACCEPTANCE.md](ACCEPTANCE.md).
