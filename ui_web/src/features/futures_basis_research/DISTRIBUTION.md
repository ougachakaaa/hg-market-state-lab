# Futures Basis distribution presentation

Specializes [Reader presentation](PRESENTATION.md) for the shared Online, Static
Demo and Offline reader. This is the sole owner of local distribution controls,
presentation populations, projection and audit. Financial formulas/units belong to
[Research Definition](../../../../market_research/descriptive/cases/futures_basis/DEFINITION.md);
formal populations and methods belong to
[Research Statistics](../../../../market_research/descriptive/cases/futures_basis/STATISTICS.md).
WP3 implements V2 structural admission, Metric/width/format changes and complete
original-population validation. WP4 implements rank-based trimming and complete exclusion audit.

## Controls and interpretation

Reader order is `basis_value`, `basis_ratio`, `annualized_basis_ratio`, then
`annualized_basis_value`. Default Metric remains `annualized_basis_ratio`.

| Metric | Axis label | Default width | Allowed widths |
| --- | --- | --- | --- |
| basis_value | 基差（点） | 10 points | 2 / 5 / 10 / 15 / 20 points |
| basis_ratio | 基差率（%） | 0.1 percentage points | 0.05 / 0.1 / 0.2 / 0.5 percentage points |
| annualized_basis_ratio | 年化基差率（%） | 1 percentage point | 0.5 / 1 / 2 / 5 / 10 / 20 percentage points |
| annualized_basis_value | 年化基差点（点/年） | 10 points/year | 2 / 5 / 10 / 15 / 20 points/year |

Percentage-point widths convert to decimal_ratio for raw-value comparisons.
`tail_exclusion_pct` offers `0 / 1 / 2 / 5 / 10`, interpreted as the planned
percentage **per side**, default 0. Metric changes reset Bin Width to its default,
preserve Tail Exclusion and recompute local selection from the new Metric's original
samples. Width changes do not change the selected/retained population.

For annualized ratios retain the explanation:

> 年化基差率用于比较不同到期期限下的基差强度，不等于实际持有收益；临近到期时数值可能较敏感。

Annualized points likewise identify points/year and explain that they do not
represent actually obtainable annualized returns. The reader consumes producer
values; it never derives a fourth metric from prices or another metric.

## Validate the complete original population first

For the selected Metric, match exactly one history binding, Distribution and
Accounting entry per Slot. Match finite non-null original history coordinates to
Eligible identities `[product, date, slot]` in Distribution and Accounting, preserving
numerical duplicates. Candidate and outcome identities must match the published date
population. Successful method sample counts and units must agree with the original
Eligible population, before trimming. Filtering must never hide inconsistent inputs.

Missing, duplicate or inconsistent associations stop the entire selected Metric's
filtering and plotting with an explicit display-data error; formal summaries and
evidence remain readable. No tooltip parsing, contract-code inference, null filling,
sample repair or recovery of a formally rejected result is allowed.

## Rank-based tail selection

For each Slot independently, sort its current Metric's original Eligible values
ascending, retaining every original sample identity. Do not pool Slots or use
formal Type-7 Quantile results as rank cutoffs.

Let N be original Eligible N, p = tail_exclusion_pct / 100, and k = floor(N × p).
If N=0 or k=0, exclude nothing and report no truncation boundaries. Otherwise use
one-based ranks: lower retained cutoff is value k+1; upper retained cutoff is
value N−k. Exclude only values strictly below/above those cutoffs, labeled
`lower` / `upper`. Keep the cutoff values and **all** ties at either cutoff.

Without ties each tail excludes k rows; ties can reduce the actual count below k.
Never split equal values by date, Contract Code or array order. Use unrounded raw
values, including zero and signed zero as equal. Negative/positive mixtures and
repeated values use the same ordering rule. Small samples with k=0 remain intact;
all-equal nonempty samples remain intact even when k>0 (equal cutoffs then exist).
Do not winsorize, fill, delete from, or mutate the original Report.

The original population is a disjoint union of retained and tail-excluded identities:

```text
original_eligible_n = retained_n + tail_excluded_n
tail_excluded_n = lower_excluded_n + upper_excluded_n
```

This is a Presentation Population, never a new Statistics method or a Research
`excluded` Outcome. The original full-sample summary stays unchanged and labeled
“全样本统计”. Controls perform no HTTP, acquisition, research execution or polling
change. Original History, Mean, Quantile, IntervalCount, term comparisons, Accounting
and Evidence are unchanged. Changing selection always starts from the full original
population, never an already trimmed sample.

## Histogram projection and chart

After each Slot is independently filtered, all retained values across M0/M1/Q1/Q2
determine one shared set of ordered X-axis edges. Hidden Slots retain their samples
and contribute to edges. Bins are left-inclusive/right-exclusive, except the final
right-inclusive bin. No retained value falls outside bins or is counted twice.

Use zero-anchored integer edge indices and preset integer numerator/denominator
widths. Generate each binary64 edge directly from its index; never accumulate float
steps. Correct range estimates by exact edge comparisons, and assign via ordered-edge
binary search without epsilon or sample rounding. Equal-valued samples receive at
least one full bin. Do not clip, automatically merge bins, fabricate frequencies or
silently change the selected width. At most 2,000 shared bins are permitted.

For each successfully plotted nonempty Slot, Count sums exactly to retained_n and
Frequency uses that Slot's retained_n denominator, summing to 1 mathematically
(normal binary64 roundoff does not authorize frequency repair). Formal method sample
counts still refer to original_eligible_n, not retained_n.

Controls precede one stepped Frequency comparison, the full-sample summary and an
expandable “尾部排除明细”. M0/M1/Q1/Q2 start visible, with their history-series colors
and independent legend toggles. Prefer stepped/overlay comparison, never mutually
occluding opaque groups or duplicate Count/Frequency curves. Y-axis is Frequency（%）.
Tooltip includes Slot, interval closure, Count, Frequency and explicitly labeled
retained N; original N remains identifiable in summary/audit. Frequency uses one
decimal percent. Boundaries follow the narrow exception owned by
[Formatting](../../../PRESENTATION_FORMATTING.md#5-例外); point units use two decimals.
Generic Visualization rendering performs no aggregation.

## Complete exclusion audit

For each Slot show original Eligible N, lower/upper excluded N, total excluded N,
retained N, actual total excluded fraction (tail_excluded_n / original_eligible_n),
lower/upper retained cutoffs, and actual retained minimum/maximum. Distinguish
cutoffs from the actual retained range, even when numerically equal. N=0 has no
applicable actual fraction, cutoff or range. With k=0 there are no cutoffs; a
nonempty retained population still has an actual min/max and zero excluded fraction.
Use standard percentage formatting for the actual fraction; counts remain integers.

Every excluded row retains Product, Trade Date, Slot, Metric, original raw value
and explicit unit, plus `lower` / `upper`. Raw/evidence labels follow the existing
formatting exception. Reuse validated History/binding identities, never parse
tooltips. Actual Contract Code may be shown only when explicitly provided and
associated by the producer, never inferred from Slot or naming conventions.

Retain the complete list and true count. Pagination is allowed; arbitrary first-N
truncation must not masquerade as a complete list. Existing CSV export may be reused
but is optional; no generic export framework is required. Width/capacity failures
must not discard already computed selection summaries or excluded rows.

## Empty, partial and capacity behavior

- Original N=0: no eligible sample, no curve, cutoff or fabricated frequency.
  All-empty inputs show no eligible samples.
- Empty retained population: show empty result and actual exclusion counts, with
  no frequencies or retained min/max. Do not fabricate samples to create a curve.
- Formal IntervalCount failure wins over any supplied result: retain its category
  and omit that Slot's curve. Valid sibling curves remain readable. All validated
  retained samples, including failed-method Slots, still determine shared edges.
  Filtering must never mask Partial/Failure or recompute failed formal statistics.
- `no_eligible_sample` is legal only for original N=0. Original N>0 with that
  category is inconsistent and rejects the selected Metric's display aggregation.
- Unsafe indices, non-increasing edges or more than 2,000 bins: do not plot invalid
  bins; ask the user to adjust Bin Width. Keep selection summaries and the complete
  audit. Never automatically clip, merge, change width or silently omit outliers.

WP3/WP4 verification covers each preset and reset, no-network interactions, full
association rejection before filtering, N=0/k=0, all equal, tied cutoffs, negative/
positive/zero/duplicate values, exact identities and conservation, Slot independence,
retained denominators, hidden-Slot edges, formal failures and capacity-preserved audit.
Online, Static Demo and Offline share this implementation and all these rules.
