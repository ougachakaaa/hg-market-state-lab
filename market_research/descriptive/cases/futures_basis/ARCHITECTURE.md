# Futures Basis Research V1 — R01-A

This independent Descriptive case specializes [Research](../../../ARCHITECTURE.md)
and [Descriptive](../../ARCHITECTURE.md). Its identity is `futures_basis_v1`:
Historical Basis Distribution and Term Structure of Chinese Equity Index Futures.
The minimum real-market delivery is IM / CSI1000; IF, IH and IC may use the same
published product/underlying bindings without an instrument registry.

## Purpose and boundaries

The case observes same-day futures/underlying Close differences, relative tenor
structure, historical variation and Slot-level persistence. These are descriptive
findings, not fair-value models, forecasts, trading signals, recommendations,
holding-period returns or backtests. There is no Horizon or warm-up period.

Research owns these market derivations, daily role resolution, population,
validity, business association and interpretation. DataLake owns source facts,
metadata, lifecycle and complete product-day acquisition. Statistics owns generic
numerical methods. Visualization owns domain-neutral rendering; Research projects
business results into its contract without importing frontend code.

```text
explicit product + window
  → public input preparation → pure Slot resolution / Contract-day construction
  → Slot-day references / transitions
  → case-owned numerical adaptation → Statistics → business-associated findings
  → Research ChartView projection → ui_web offline rendering (WP5)
```

These are responsibility boundaries, not a generic engine, inheritance hierarchy
or mandatory sequence of separately persisted artifacts. The independent Python
boundary is `market_research.descriptive.cases.futures_basis`; its pure Slot
resolver and transition detection are implemented under [Slot resolution](SLOT_RESOLUTION.md).
Preparation alone performs upstream I/O; WP3 implements public preparation and pure
Contract-day/Slot-day observations under [Inputs](INPUTS.md) and [Observation](OBSERVATION.md).

## Authority navigation

| Concern | Canonical owner |
| --- | --- |
| Formula, sign, state, price legality, DTE and units (SD01) | [Definition](DEFINITION.md) |
| Contract identity, relative tenor and daily resolution (SD02–SD04) | [Slot resolution](SLOT_RESOLUTION.md) |
| Exact public bindings, dual calendars, completeness and reproducibility (SD06) | [Inputs](INPUTS.md) |
| Observation grain, validity, accounting and continuity (SD05, SD07–SD08) | [Observation](OBSERVATION.md) |
| Populations, distributions, paired comparisons, runs and numerical ownership (SD09) | [Statistics scope](STATISTICS.md) |
| Business projection and offline report evidence | [Delivery](DELIVERY.md) |
| WP3 runtime/real-market evidence and reproduction | [WP3 acceptance](WP3_ACCEPTANCE.md) |
| Work packages, readiness, reconciliation and known gaps | [Roadmap](ROADMAP.md) |

## Request and compatibility

An observation request fixes this case/version, one explicit canonical
`product_code`, and an inclusive date-only `start_date..end_date`. No subject,
date, Horizon or source defaults exist. Resolve the underlying from the selected
DataLake public facts and its [market mapping](../../../../data_lake/datasets/tushare_equity_index_futures/FACTS.md).
Validate the request before any service I/O; future market end dates are illegal
under the producer's Asia/Shanghai rule. Multiple products are separate explicit
case requests, not an implicitly pooled population.

Structural request identity is `(futures_basis_v1, product_code, start_date,
end_date)`; actual input fingerprint is separate. Statistical parameters belong
to explicit analysis requests and changing them does not require new observations.

The [scalar Observation](../../OBSERVATION.md) requires a positive integer Horizon;
its converter, execution, association and capability dispatch retain their current
scope. This case does not fabricate `horizon=1`, repurpose a scalar carrier, or
claim admission to those APIs. Case-owned adaptation consumes only the root
[Statistics public API](../../../../market_statistics/CONTRACT.md).
Existing Snapshot/Workbench semantics stay frozen; see [reconciliation](ROADMAP.md#reconciliation).

Status: WP0 is authority-only; WP1–WP3 have independent runtime acceptance.
WP3 also passed bounded real IM acceptance; evidence and reproduction instructions
are in [WP3 acceptance](WP3_ACCEPTANCE.md). WP4 statistics and WP5 report
acceptance remain separate work under the roadmap. No new CLI, HTTP route, Research
database, publication lifecycle or Modeling import permission is introduced.
