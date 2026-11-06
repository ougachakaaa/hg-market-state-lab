# Futures Basis observation and continuity

This owns SD05, SD07 and SD08 for the [case](ARCHITECTURE.md). Formulas belong
only to [Definition](DEFINITION.md), roles to [Slot resolution](SLOT_RESOLUTION.md),
and upstream proof/failures to [Inputs](INPUTS.md).

## Two grains

| Logical carrier | Natural identity | Required retained meaning |
| --- | --- | --- |
| Contract-day | `(contract_code, trade_date)` | Product/underlying, actual real contract, same-day prices or missing dependencies, delivery month, list/delist dates, DTE, three metric outcomes, state when eligible, input/definition provenance |
| Slot-day | `(product_code, trade_date, slot)` | Resolved contract and reference to its Contract-day outcome, or proven no-active-contract outcome; resolution evidence |

These keys are scoped by the result's fixed request and actual input fingerprint
when comparing executions. A Slot does not own duplicate prices, another formula
or a synthetic contract. Keep source association through to each numerical sample
and chart point. Order Contract-days by date then code, and Slot-days by date then
M0/M1/Q1/Q2. Every resolved active contract-day appears once; there is no Contract-day
placeholder for a proven empty active set.

This is an instantaneous cross-sectional observation, not the existing scalar
ObservationSet. No Horizon, return horizon, generic SampleBinding mutation,
fabricated Job identity or dispatch registration is authorized.

## Outcomes and precedence

Each candidate Slot-day has exactly one base outcome; each metric additionally
has exactly one outcome with explicit value/unit or a reason and evidence.

| Outcome | Meaning |
| --- | --- |
| Eligible | Required facts exist, prices are positive/finite and applicable derivation is finite |
| Unavailable | A resolved candidate lacks an authorized same-day underlying fact |
| Excluded | Legal public facts fail business price eligibility; retain offending value(s) |
| Not Applicable | Proven no active contract, or annualized metric at expiry day |

Malformed upstream facts, non-finite source values, invalid resolution or arithmetic
failure are explicit stage failures, not Excluded rows. For legal inputs, a proven
empty active set takes Not Applicable precedence. Otherwise a present nonpositive
price is Excluded (`nonpositive_futures_close` / `nonpositive_underlying_close`);
retain any simultaneously missing dependency. If no present price is disqualifying,
missing underlying is Unavailable. Otherwise the base outcome and raw metrics are
Eligible. Only then does D=0 make the annualized metric Not Applicable (`expiry_day`).
D=0 does not override an already unavailable/excluded base observation.

Record all missing/offending facts once with exact identities and source references.
Absence, nonpositive price, not-yet-existing contract and annualized inapplicability
are distinct. Do not delete candidates, round, deduplicate, screen outliers or
silently replace unavailable/Not Applicable metrics by zero.

## Population and coverage

For one product, candidates are all CFFEX open dates in the inclusive requested
window × four Slots, including proven no-contract dates. Closed dates never enter
the denominator. For each Slot and metric retain ordered outcome collections:

```text
candidate_count = eligible_count + unavailable_count + excluded_count
                  + not_applicable_count
```

The base and each metric have independent accounting; annualized eligibility may
be smaller than raw eligibility. Collections are disjoint, complete and uniquely
keyed, and counts derive from them. Each candidate-denominator outcome ratio is
its count / candidate_count, or Not Applicable for zero candidates. Zero eligible
values remain an honest outcome; numerical analysis then reports no eligible
sample rather than passing an empty NumericSample to Statistics.

Report Calendar coverage in natural-date units, Futures coverage in product-day
units and Index coverage in index-session units separately, with original public
proofs. Do not sum unlike unit counts or confuse source availability with business
eligibility. Contract-day counts use the proven active sets and have no artificial
four-Slot denominator. [Statistics](STATISTICS.md) owns analysis-specific populations.

## Time series and transitions

Slot-day is the primary historical statistical/time-series input. Each point retains
trade_date, Slot, real contract reference, selected metric outcome/value and source
association. Changing the selected metric does not remap contracts or reacquire facts.

For adjacent CFFEX candidates whose resolved contracts differ, emit
`(product_code, slot, previous_date, trade_date, previous_contract_code,
contract_code)` plus resolution/source association. This records observed role
change, not a claim about an intraday execution or roll return. Proven absence
before/after active periods is a separate boundary, not an invented contract pair.

Research assigns new line segments at each contract change, unavailable/excluded/
Not Applicable gap and absence boundary. The next eligible point starts a new
segment. Keep missing candidate marks and reasons in the projection; do not bridge
them. A weekend or closed session alone does not split an otherwise contiguous
trading-calendar segment. A contract transition splits the chart even when it
does not split the [Slot-level Discount Run](STATISTICS.md#slot-level-discount-runs).

Visualization receives only generic segments, events and point details under
[V2](../../../../ui_web/VISUALIZATION_V2.md); it never discovers a roll from codes,
prices or date gaps. WP3 acceptance verifies references, per-metric total accounting,
expiry-only inapplicability, mixed invalid/missing precedence, strict zero state,
contract transitions with unavailable prices and non-interpolated gaps.
