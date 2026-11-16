# Calendar spread Pair-day Observation

Specializes [the case](ARCHITECTURE.md); financial values follow only
[Definition](DEFINITION.md), public proof follows [Inputs](INPUTS.md).

## Population and identity

One observation candidate is
`(futures_calendar_spread_v1, product_code, trade_date, near_slot, far_slot)`.
The fixed population is complete CFFEX open dates × the six ordered pairs, in
date then public pair order. Each pair/day appears exactly once. Request identity
is separate from retained actual inputs. A changed real mapping does not change
the Slot-pair identity or imply a return across the change.

Each candidate retains both real contract codes and metadata, same-date Close
values, delta_days, near_dte_days, expiry_stage, three metric values/units when
valid, outcome/reason and links to its prepared input and Slot evidence. A real
contract change is exposed through those identities; do not splice adjusted
continuous prices or interpret a level change as PnL.

## Outcomes and legality

| Outcome | Meaning |
| --- | --- |
| `valid` | Both contracts resolve, required prices are strictly positive, and all three finite financial values are computed |
| `not_applicable` / `no_active_contract` | Producer proves an empty active universe; both Slots have the resolver's explicit absence |
| `excluded` / `nonpositive_close` | Resolved pair has one or both finite Close values <=0; retain the offending facts and identities |

No metric value is fabricated for non-valid candidates; absent values are null,
never zero. All three metrics use the same valid candidate population. Input
integrity, missing required rows, invalid Slot structure, same-contract pair,
nonpositive delta_days or negative near_dte_days fail explicitly, not as a normal
business exclusion. Valid-input numerical failures fail construction with pair/date
context and obtained evidence; no partial collection is advertised as success.

For each successful collection:

```text
candidate_count = 6 * number_of_CFFEX_open_dates
candidate_count = valid_count + not_applicable_count + excluded_count
```

An entirely closed window has zero candidates and an empty successful collection.
Daily query on a closed date returns `not_applicable/non_trading_day` and no pair
rows; it never rolls the request to an earlier date. On an open date with a proven
empty universe it returns all six not-applicable candidates. These are distinct
from incomplete or unavailable inputs.

## Expiry stage

Using the actual near contract's last trading date:

| near_dte_days | expiry_stage |
| --- | --- |
| 0–7 inclusive | `0_7` |
| 8–21 inclusive | `8_21` |
| 22 or more | `22_plus` |

Classify each observation on its own date and actual near contract, including
after Slot transitions. Natural days include weekends and holidays. Do not use
remaining trading sessions, pair spacing, delivery date or evaluation-day stage
to relabel historical candidates. An absent contract has no stage.

## WP2 public construction

The case facade exposes a pure `construct_observations(prepared_inputs)`
operation and immutable observation/result carriers. Construction validates input
association and evidence, computes metrics through the WP1 public capability and
retains complete accounting; no upstream acquisition or Statistics call occurs.
Both product queries consume this same collection, never their own formulas.

`construct_observations(prepared_inputs)` returns frozen
`CalendarSpreadObservationSet`, retaining the complete prepared inputs, ordered
`CalendarSpreadDay` results and `OutcomeAccounting`. Its `observations` property
flattens day outcomes in date then fixed pair order. Each natural date appears in
`days`: closed dates have status `closed`, reason `non_trading_day`, no resolution
and zero pairs; open dates have status `open`, a retained `DailySlotResolution`
and six outcomes. Thus a closed date differs from a proven empty open date.

Each `PairDayObservation` retains product/date, near/far Slots, full near/far public
Futures rows (or None for a proven empty universe), delta_days, near_dte_days,
expiry_stage, WP1 `CalendarSpreadResult` (or None), outcome/reason, case and
definition identity and its `DailyUniverseEvidence`. The source_export_ref is
`prepared_inputs.futures_export`, a local reference to the complete retained
Export, not a digest or persistence identity. There is no partial pair absence.
Excluded nonpositive-price pairs retain rows, spacing and stage but no metrics.
Spacing/lifecycle is checked before exclusion, so illegal metadata cannot hide
behind a nonpositive Close. Empty pairs have null spacing/stage/metrics.

`ObservationConstructionError` retains category, stage, dependency, reason,
prepared inputs and applicable date/Slots. Invalid retained input association is
`input_contract_error`; public resolver rejection is `slot_resolution_error`;
illegal pair identities/expiry spacing are `input_contract_error`; WP1 numerical
failure is `calculation_failure`. The whole call fails with no successful partial
collection. Unexpected programming exceptions propagate. No transition/PnL series,
Statistics, storage or acquisition behavior is introduced.
