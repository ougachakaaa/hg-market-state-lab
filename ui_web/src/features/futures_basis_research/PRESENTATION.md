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
Histogram Slot selection. Read mean and quantile by explicit method identity and
P0/P25/P50/P75/P100 by point value, never array order or browser computation.
N is the Eligible binding count; absent distributions show unavailable, empty
samples show N=0 and unavailable statistics. Missing/failed methods or points show
unavailable (with failure category when supplied), never a fabricated zero. Failure
takes precedence over a result; successful sibling methods remain readable in Partial.
Use result units with the existing index_points / decimal_ratio formatter.

All modes share the summary and support narrow-screen horizontal scrolling.
Compact removes the redundant 12-row mean table. Offline replaces that overview
table with the summary near distributions, keeping every Metric accessible through
the selector and retaining Methods, comparisons, evidence and all six sections.

## Authority only: dynamic presentation bins (SD-02)

Task 1 keeps the existing producer Count and Frequency charts unchanged. A future
implementation may aggregate already published, validated Eligible historical raw
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

## Authority only: one four-Slot distribution (SD-03, SD-05)

Replace the duplicate Count/Frequency charts with one distribution, defaulting to
Frequency. Tooltip shows Count and Frequency from the same sample and bin; Frequency
uses percent with one decimal place. Do not draw duplicate curves for both measures.

M0/M1/Q1/Q2 are initially visible with shared X-axis bin boundaries, independent
Eligible samples and per-Slot denominators. Default comparison uses Frequency.
Legend toggles each Slot independently, using its history-series color. Prefer
overlay or stepped distributions suitable for comparison, never four mutually
occluding opaque bar groups. These changes remain Task 2 work.
