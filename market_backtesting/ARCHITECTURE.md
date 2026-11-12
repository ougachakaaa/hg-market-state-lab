# Market Backtesting module authority

`market_backtesting` is the repository business module for deterministic strategy
backtesting over authorized market facts. It is a sibling analytical module, not a
Research paradigm, a Modeling implementation or an inbound delivery adapter. This
authority owns module identity, ownership boundaries, dependency direction, case
navigation. Strategy, accounting, input, result and online semantics are divided between Core and concrete case through the navigation below.

The module separates strategy-independent Core from the W2 case adapter and analysis.
Current implementation readiness and remaining delivery gates belong to the
[roadmap](cases/futures_roll_long/ROADMAP.md); current authority review and implementation
differences belong to [reconciliation](cases/futures_roll_long/RECONCILIATION.md).

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
| Input preparation, public bindings, completeness, slot reuse, fingerprint and readiness | [Inputs](cases/futures_roll_long/INPUTS.md) |
| BacktestResult, evidence, limitations and Visualization projection | [Result](cases/futures_roll_long/RESULT.md) |
| Portable evidence package, encoding and pure offline reproduction | [Evidence](cases/futures_roll_long/EVIDENCE.md) |
| Online request, run lifecycle, storage, concurrency and delivery ownership | [Online application](cases/futures_roll_long/ONLINE_APPLICATION.md) |
| Delivery status, remaining work packages and acceptance | [Roadmap](cases/futures_roll_long/ROADMAP.md) |
| Concern/consumer inventory, current semantic review and implementation drift | [Reconciliation](cases/futures_roll_long/RECONCILIATION.md) |

Core imports neither W1 nor W2; only the W2 case adapter may consume authorized W1 symbols.
The package root must not eagerly import the case, so Core can load without Research.

## Critical invariants

Core-wide invariants are immutable single-position state, daily transition before
accounting, explicit price assumptions and failure without partial success. The
case constraints belong to W2; Core must not encode them.

W2 owns real-contract selection, expiry-driven rolls and terminal closure through its
[Strategy](cases/futures_roll_long/STRATEGY.md), within Core's generic single-position
boundary. Input failures cannot become successful partial results. HTTP/Web consume
producer-owned results without financial recomputation. Online execution state remains
independent of Research Publication, Job/Batch and Workbench identities.

## Status and verification

The [roadmap](cases/futures_roll_long/ROADMAP.md) is the sole current delivery/status
entry. Synthetic Core checks, full research capability and end-to-end W2 completion
are separate acceptance gates. A passing implementation test does not close an
[implementation drift](cases/futures_roll_long/RECONCILIATION.md#implementation-drift-register).

Agent execution policy is in [AGENTS.md](AGENTS.md).
