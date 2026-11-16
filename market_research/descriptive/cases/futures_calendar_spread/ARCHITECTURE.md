# Futures Calendar Spread L1

Status: WP1 pure financial Python API is implemented. WP2–WP7 Input Preparation,
Observation, Statistics, product queries, HTTP, Web and Demo remain unimplemented.
This independent Descriptive case specializes [Research](../../../ARCHITECTURE.md)
and [Descriptive](../../ARCHITECTURE.md). Case identity is
`futures_calendar_spread_v1`; financial definition version is
`futures_calendar_spread_definition_v1`.

## Purpose and ownership

L1 observes daily equity-index futures calendar spreads and their historical
relative value to help a holder of a long position understand whether the current
roll price relationship is relatively favorable. It produces descriptive evidence,
not expected returns, execution prices, timing advice or trading instructions.
L2 waiting value and L3 strategy validation are excluded; no framework or empty
implementation is authorized for either.

Two independent products share one Research-owned financial calculation and
Observation capability:

- **Daily Data — Futures Calendar Spread**: one product/date, six ordered Slot pairs.
- **Research — Calendar Spread Historical Relative Value**: one product/evaluation
  date, explicit historical start, comparable distributions and current assessment.

DataLake owns market facts, real contract metadata and completeness. Research owns
financial metrics, pair Observations, historical population and interpretation.
Statistics owns generic numerical methods. HTTP owns transport/DTOs, Web owns
Presentation, and Demo captures only formal HTTP Results.

## Authority navigation

| Concern | Canonical owner |
| --- | --- |
| Formula, sign, units and financial interpretation | [Definition](DEFINITION.md) |
| Public inputs, completeness and reproduction | [Inputs](INPUTS.md) |
| Pair-day population, legality and accounting | [Observation](OBSERVATION.md) |
| Comparable historical samples and relative assessment | [Relative value](RELATIVE_VALUE.md) |
| Shared Python business boundary and the two queries | [Application](APPLICATION.md) |
| WP1–WP7, acceptance, reconciliation and readiness | [Roadmap](ROADMAP.md) |

## Independence and reuse

The public Python facade for WP1 is
`market_research.descriptive.cases.futures_calendar_spread`. It consumes only
the standard library for WP1. Later work may consume only
Calendar/Futures public services, the existing [public pure Slot resolver](../futures_basis/SLOT_RESOLUTION.md)
and the root Statistics facade. No sibling case private module is authorized.
The resolver remains owned by its current contract; this case does not copy or
move it, change `futures_basis_v1`, or consume Basis financial calculations,
Observations, statistics adapters, online application or storage.

This case is not admitted to scalar Observation/Converter, ResearchPlan, Job/Batch,
capability dispatch, Publication or Research Explorer. It creates no generic engine,
Run identity, mandatory persistence or CLI. W2 Position-Driven Backtesting and its
existing Slot consumption remain unchanged. Neither upstream modules nor Statistics
depend on this case, HTTP or Web.
