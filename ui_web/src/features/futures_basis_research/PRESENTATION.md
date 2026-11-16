# Futures Basis reader presentation

Specializes the [feature authority](ARCHITECTURE.md) for its shared Online, Static
Demo and Offline reader. Research owns [definitions](../../../../market_research/descriptive/cases/futures_basis/DEFINITION.md),
[validity](../../../../market_research/descriptive/cases/futures_basis/OBSERVATION.md)
and [formal statistics](../../../../market_research/descriptive/cases/futures_basis/STATISTICS.md).
This document owns presentation only; it creates no wire or Bundle contract.

## Implemented: expiry explanation and summary (SD-01, SD-04)

Show this directly beside the annualized history chart, outside any disclosure:

> 合约到期日的剩余期限 D=0，年化基差按研究定义主动留空，并非行情数据错误；原始基差仍然保留。

Do not repeat it on other metrics. Keep nulls, expiry_day and all producer evidence;
do not connect gaps, modify transitions or reinterpret other unavailable outcomes.
The adjacent explanation distinguishes deliberate inapplicability from the generic
Missing values list without changing that renderer's semantics.

Near the distribution controls show `Slot | N | Min | P25 | Median | P75 | Max | Mean`
for M0/M1/Q1/Q2 in that order, using the selected Metric, independently of the
Bin Width selection. Read mean and quantile by explicit method identity and
P0/P25/P50/P75/P100 by point value, never array order or browser computation.
N is the Eligible binding count; absent distributions show unavailable, empty
samples show N=0 and unavailable statistics. Missing/failed methods or points show
unavailable (with failure category when supplied), never a fabricated zero. Failure
takes precedence over a result; successful sibling methods remain readable in Partial.
Use result units with the shared [presentation formatter](../../../PRESENTATION_FORMATTING.md).

All modes share the summary and support narrow-screen horizontal scrolling.
Compact removes the redundant 12-row mean table. Offline replaces that overview
table with the summary near distributions, keeping every Metric accessible through
the selector and retaining Methods, comparisons, evidence and all six sections.

## Implemented: dynamic presentation bins (SD-02)

The shared reader aggregates already published, validated Eligible historical raw
values into temporary presentation bins. It must use original values, never display
rounding; preserve duplicate observations, the true per-Slot population and full
count conservation; and perform no fill, clipping or financial recalculation.

| Metric | Default width | Selectable widths |
| --- | --- | --- |
| basis_value | 10 index points | 5 / 10 / 20 / 50 index points |
| basis_ratio | 0.1 percentage points | 0.05 / 0.1 / 0.2 / 0.5 percentage points |
| annualized_basis_ratio | 5 percentage points | 2.5 / 5 / 10 / 20 percentage points |

Percentage-point widths convert to decimal_ratio for comparison with raw values.
Bins share explicit ordered edges, are left-inclusive/right-exclusive except for
the final right-inclusive bin, and span the full selected Metric population across
all four Slots. No value may fall outside the displayed bins or be counted twice.
Hidden Slots retain their population and do not change shared edges.
Frontend owns only this temporary display aggregation. Formal IntervalCount remains
Research / Statistics-owned and retained unchanged; Mean/Quantile are never recomputed.
The generic Visualization renderer performs no aggregation.

## Implemented: one four-Slot distribution (SD-03, SD-05)

Replace the duplicate Count/Frequency charts with one distribution, defaulting to
Frequency. Tooltip shows Count and Frequency from the same sample and bin; Frequency
uses percent with one decimal place. Do not draw duplicate curves for both measures.

M0/M1/Q1/Q2 are initially visible with shared X-axis bin boundaries, independent
Eligible samples and per-Slot denominators. Default comparison uses Frequency.
Legend toggles each Slot independently, using its history-series color. Prefer
overlay or stepped distributions suitable for comparison, never four mutually
occluding opaque bar groups. Online, Demo and Offline share this projection and chart.

## Consumption integrity and numerical display limits

For the selected Metric, match exactly one history binding, Distribution and
Accounting entry per Slot. Match finite non-null original history coordinates to
Eligible identities `[product, date, slot]` in Distribution and Accounting, preserving
numerical duplicates. Candidate and outcome identities must match the published date
population. Successful method sample counts and units must agree. Missing, duplicate
or inconsistent associations stop the entire selected Metric comparison with an
explicit display-data error; formal summaries and evidence remain readable.
No tooltip parsing, contract-code inference, null filling or sample repair is allowed.

Formal IntervalCount failure takes precedence over any result: show its supplied
failure category and omit that Slot's successful curve. Valid sibling curves remain
visible. All validated samples still determine shared edges. Empty Slots have N=0
and no curve or fabricated frequencies; all-empty inputs show no eligible samples.

`no_eligible_sample` is legal only for an empty Eligible population. With N=0 it is an
empty finding, not a numerical failure, so it needs no failure curve or alert. With N>0
it contradicts the formal Method contract, so the entire selected Metric's display
aggregation is rejected as inconsistent instead of silently hiding the curve. A
nonempty Slot's other formal failure keeps that Slot's curve omitted while the sibling
Slots stay readable. No reader path may repair, recover or rerun a result the formal
validator already rejected.

Use zero-anchored integer edge indices and preset integer numerator/denominator
widths. Generate each binary64 edge directly from its index, correct range estimates
by exact edge comparisons, and assign using ordered-edge binary search without an
epsilon or rounding sample values. Equal-value samples get at least one full bin.
At most 2,000 shared bins may be displayed; unsafe indices, non-increasing edges or
excess capacity explicitly request a larger width, with no clipping or automatic change.
Every nonempty Slot conserves Count exactly and uses its own Eligible N denominator.

Controls precede one stepped Frequency comparison and the formal summary table.
Metric changes reset the width to that Metric's default; width changes do not change
Mean/Quantile, history, HTTP or report data. Tooltip includes Slot, interval closure,
Count, Frequency (one decimal percent) and Eligible N. Boundary labels follow the
[presentation formatting authority](../../../PRESENTATION_FORMATTING.md): one decimal for
percentage boundaries and two decimals for index-point boundaries. The 0.1 percentage-point
minimum width keeps one-decimal percentage boundaries distinguishable. Offline retains
formal method details for every Slot and all six report sections.

Execution evidence: [Task 2 distribution acceptance](DISTRIBUTION_ACCEPTANCE.md).
