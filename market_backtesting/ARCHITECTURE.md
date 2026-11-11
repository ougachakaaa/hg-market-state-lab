# Market Backtesting module authority

`market_backtesting` is the repository business module for deterministic strategy
backtesting over authorized market facts. It is a sibling analytical module, not a
Research paradigm, a Modeling implementation or an inbound delivery adapter. This
authority owns module identity, ownership boundaries, dependency direction, case
navigation and implementation status. Strategy, accounting, input, result and online
semantics are divided between Core and concrete case through the navigation below.

WP0/WP1 established the original authority and pure holding simulator. The approved
Position-Driven Core reconciliation directly replaces that simulator with a generic
single-position Core plus W2 Policy. No DataLake integration, HTTP/Web, online run or
full Performance Analyzer is included. Historical completion and current gates are in
the [roadmap](cases/futures_roll_long/ROADMAP.md).

## Purpose

The module turns a fixed, human-approved strategy definition plus complete public
market exports into:

- a real-contract position and execution timeline;
- gross PnL, benchmark comparison and drawdown;
- an immutable backtest result, evidence and visualization projection;
- case-specific read-only readiness assessment and online execution.

The current scope is exactly one case: `futures_roll_long_v1`
([case authority](cases/futures_roll_long/ARCHITECTURE.md)). The [Position-Driven Core V1](core/ARCHITECTURE.md) owns replay/state/transition/PnL/accounting/recording.
No order-driven engine, plugin system, broker, matching engine, strategy registry,
optimizer, multi-asset portfolio framework or future case scaffold is authorized. A second case requires its own explicit
semantic decision and authority.

## Ownership

`market_backtesting` owns:

```text
strategy definition and case request identity
real-contract selection and position simulation
roll, entry and exit decisions
gross PnL accounting
benchmark comparison
maximum drawdown and return normalization
backtest result, evidence and limitations
producer-owned Visualization projection
case-specific readiness/online run lifecycle and result publication
```

It does not own:

```text
market facts, calendars, source acquisition, Dataset caches or completeness proofs
W1 Slot resolution formulas or Research observations/reports/statistics/publications
generic numerical statistics
Visualization Layer/View semantics or frontend rendering
HTTP DTOs, OpenAPI, authentication or HTTP runtime
Web interaction, application shell or presentation state
market_modeling state models, signals or strategy abstractions
```

## Stable dependency direction

```text
market_backtesting.cases.futures_roll_long
    ├──→ data_lake public Application Services
    │      (Calendar, Futures, Index)
    └──→ market_research public pure Slot resolution boundary
           (exactly the symbols authorized by the case Inputs authority)

ui_http → market_backtesting public application boundary
ui_web  → ui_http HTTP/OpenAPI
```

The dependency on `data_lake` is a consumer dependency on published semantic
request/result/view contracts. It does not grant access to SQLite, repositories,
source adapters, provider clients, raw artifacts or private composition.

The dependency on `market_research` is deliberately narrower than a module-wide
dependency. It authorizes only the existing public pure Slot resolution boundary
named in the case [Inputs](cases/futures_roll_long/INPUTS.md). It does not authorize
Research observations, Sample Conversion, Statistics adaptation, Job/Batch execution,
reports, evidence, Publication, Preflight or online runs. The W1 module remains the
owner of that boundary; its code, formulas and behavior are unchanged by W2.

`data_lake`, `data_snapshot`, `market_research`, `market_statistics` and
`market_modeling` must not import `market_backtesting`. Inbound adapters (`ui_cli`,
`ui_http`, `ui_web`) may consume only the published boundaries; business modules never
depend on them. No shared virtual environment, package graph or filesystem location
grants an additional import permission.

`market_modeling` remains reserved and independent. W2 neither implements modeling
inside this module nor derives a Modeling design, signal framework or backtest
framework from it.

## Case navigation

| Concern | Canonical owner |
| --- | --- |
| Replay, Portfolio, Transition, Daily PnL, cumulative accounting and Recorder | [Core](core/ARCHITECTURE.md) |
| Case identity, request, strategy profiles, scope and status | [Futures Roll Long case](cases/futures_roll_long/ARCHITECTURE.md) |
| Real-contract position state machine, session decisions and contract/slot identity | [Strategy](cases/futures_roll_long/STRATEGY.md) |
| Initial notional, benchmark, drawdown and case performance | [Performance](cases/futures_roll_long/PERFORMANCE.md) |
| Public upstream bindings, completeness, slot reuse, fingerprint and readiness | [Inputs](cases/futures_roll_long/INPUTS.md) |
| BacktestResult, evidence, limitations and Visualization projection | [Result](cases/futures_roll_long/RESULT.md) |
| Online request, run lifecycle, storage, concurrency and delivery ownership | [Online application](cases/futures_roll_long/ONLINE_APPLICATION.md) |
| WP0–WP8, acceptance and reconciliation | [Roadmap](cases/futures_roll_long/ROADMAP.md) |

Core imports neither W1 nor W2; only the W2 case adapter may consume authorized W1 symbols.
The package root must not eagerly import the case, so Core can load without Research.

## Critical invariants

- The unit of strategy exposure is one lot of an immutable real `contract_code`, not
  a daily re-selected M1 Slot. Slot identity is only a decision-day role.
- Entry and roll decisions happen at the close of a CFFEX session. The roll day's PnL
  belongs to the old contract; the new contract begins at that same close. No
  cross-contract price difference creates PnL.
- The last study session closes all exposure and never opens a position without a
  holding period.
- Missing calendar, contract, metadata, price or lifecycle evidence fails the
  operation. No silent skipping, filling, expiry guessing, contract substitution or
  second market cache is permitted.
- The Web layer displays producer-owned values. It never recalculates PnL, returns,
  benchmark, drawdown or trade decisions in React.
- Backtesting is not Research evidence and not Publication. The case-specific online
  run is disposable application execution state, not a Workbench Run, ResearchPlan,
  Job/BatchResult or durable research identity.

## Status and verification

WP0 is a documentation/authority gate. It runs link, anchor, reachability and topology
checks only; no full Python/HTTP/Web test matrix or real-market acquisition is claimed.
WP1 historically added pure holding simulation. Reconciliation introduces the executable
Core subset under a separate acceptance gate; remaining WP2 owns Performance Analyzer
and benchmark. WP4 PASS means W2 research capability, while WP8 PASS remains required
for full W2 completion. See the [roadmap](cases/futures_roll_long/ROADMAP.md).

Agent execution policy is in [AGENTS.md](AGENTS.md).
