# Futures Basis reader presentation

Specializes the [feature authority](ARCHITECTURE.md) for its shared Online, Static
Demo and Offline reader. Research owns [definitions](../../../../market_research/descriptive/cases/futures_basis/DEFINITION.md),
[validity](../../../../market_research/descriptive/cases/futures_basis/OBSERVATION.md)
and [formal statistics](../../../../market_research/descriptive/cases/futures_basis/STATISTICS.md).
This document owns presentation only; it creates no wire or Bundle contract.

## Reader labels and source disclosure

History chart titles and the distribution metric selector use Chinese presentation
aliases for the four V2 metrics; financial definitions and units remain Research-owned.
V2 four-metric reading and Bin Width presentation are implemented in WP3.
Tail selection remains pending WP4. Compact Demo shows the exact supplied source disclosure in a default-closed
数据来源 disclosure. It is separate from the always-visible static/investment warning;
never infer provider authenticity or replace the supplied statement with a new claim.

## Expiry explanation and full-sample summary

Show this directly beside each annualized history chart, outside any disclosure:

> 合约到期日的剩余期限 D=0，年化基差按研究定义主动留空，并非行情数据错误；原始基差仍然保留。

Do not repeat it on other metrics. Keep nulls, expiry_day and all producer evidence;
do not connect gaps, modify transitions or reinterpret other unavailable outcomes.
The adjacent explanation distinguishes deliberate inapplicability from the generic
无有效指标值日期 disclosure without changing null or outcome semantics.

Near the distribution controls show `Slot | N | Min | P25 | Median | P75 | Max | Mean`
for M0/M1/Q1/Q2 in that order, using the selected Metric, independently of Bin Width
and Tail Exclusion. Label this table “全样本统计”; N and its formal statistics always
describe the original complete Eligible population. Read mean and quantile by explicit method identity and
P0/P25/P50/P75/P100 by point value, never array order or browser computation.
N is the Eligible binding count; absent distributions show unavailable, empty
samples show N=0 and unavailable statistics. Missing/failed methods or points show
unavailable (with failure category when supplied), never a fabricated zero. Failure
takes precedence over a result; successful sibling methods remain readable in Partial.
Use result units with the shared [presentation formatter](../../../PRESENTATION_FORMATTING.md).

All modes share the summary and support narrow-screen horizontal scrolling.
Compact omits a redundant per-Metric mean table. Offline replaces that overview
table with the summary near distributions, keeping every Metric accessible through
the selector and retaining Methods, comparisons, evidence and all six sections.

## Distribution navigation

[Distribution presentation](DISTRIBUTION.md) is the sole owner of Metric/Bin Width
selection, presentation population, rank-based Tail Exclusion, Count/Frequency,
input association validation, exclusion audit and capacity/failure behavior. It
specializes this reader across Online, Static Demo and Offline. The V2 changes
include implemented WP3 Metric/width presentation and implemented WP4 tail selection; no formal statistic or
original Report is modified by those controls.

## UI-05 no-value dates

All four V2 history charts explicitly configure the shared presentation-only
`missingValuesDisclosure`: default-closed 无有效指标值日期, description
“包含合约到期、无有效合约或数据不可用等情况，具体原因见日期详情。”,
then independent default-closed Slot — date records retaining all original details.
No expiry identity is inferred from null, dates or contract codes. Other consumers
without this option keep existing Missing values behavior. Online/Demo/Offline use
one reader; Offline keeps six sections and evidence. Expansion is local state only;
producer Views, nulls, segments, transitions, coordinates and reasons are unchanged.
