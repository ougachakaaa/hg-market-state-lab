# Position-Driven Backtest Core V1

This authority specializes the [module](../ARCHITECTURE.md). Core owns daily
clock-driven replay, actual Portfolio State, Target Portfolio consumption, position
transition, Gross Daily PnL, daily/cumulative accounting and immutable in-memory recording.
W2 is its first consumer, not its definition.

## Boundaries and navigation

| Concern | Canonical owner |
| --- | --- |
| Replay, policy handoff, time causality, recorder, failures | [Replay](REPLAY.md) |
| Portfolio, target, snapshot, state events and Daily PnL | [Portfolio transition](PORTFOLIO_TRANSITION.md) |
| Explicit capital, cumulative PnL, equity, daily and cumulative return | [Accounting](ACCOUNTING.md) |

Public Python entry is `market_backtesting.core`. Core and the package root import
no case or business module. Core has no W1 Slot, W2 profile/product, Research,
DataLake, HTTP/Web, persistence or benchmark dependency. Case adapters consume Core;
Core never imports adapters. Standard-library pure deterministic computation is enough.

V1 supports flat or one active real instrument with fixed positive long quantity.
No dynamic scaling, shorts, multi-asset portfolio, order/broker/matching framework,
registry, event bus or scheduling framework is authorized. Immutable carriers and a
callable policy suffice. Fees, slippage and margin ledgers remain outside this core.

Core acceptance is synthetic and independent of full W2 acceptance. See the case
[roadmap](../cases/futures_roll_long/ROADMAP.md).
