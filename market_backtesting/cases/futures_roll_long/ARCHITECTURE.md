# Futures Roll Long V1 — W2 case authority

This independent case specializes [Market Backtesting](../../ARCHITECTURE.md) and the
[repository architecture](../../../ARCHITECTURE.md). Its identity is
`futures_roll_long_v1`.

## Research question and scope

> Does a long-only strategy that holds one real Chinese equity index futures contract
> and rolls to a farther contract under a fixed rule produce a better historical gross
> return than passively holding the underlying index over the same window?

V1 answers this only under the fixed semantics below. It is not a general strategy
laboratory, execution system, trading signal, recommendation, fair-value model or
Research observation.

Supported products: `IF`, `IH`, `IC`, `IM`. The same contract applies to all four.
Real-market end-to-end acceptance (WP8) is required for `IM`; the other products must
be semantically and synthetically verified and may receive bounded real evidence in a
later accepted scope.

The first real research compares both profiles against CSI 1000 index Buy & Hold for
`IM`, requested window `2024-01-01` through `2026-10-30` inclusive, under the one-lot,
ideal Close and gross assumptions below. This acceptance window is not a request default.

The strategy is long only, holds exactly one real futures contract, and is normalized
by a fixed initial index-equivalent notional. It is intentionally idealized:

- entry, roll and exit execute at the session Close;
- no fees, slippage, taxes, bid/ask, market impact or fill uncertainty;
- no margin account, settlement cash flow, funding cost, dividend adjustment or ETF;
- no shorting, leverage, position sizing, compounding or optimization;
- no generic strategy or portfolio framework.

These exclusions are W2 boundaries. W3 features require a new authority/version.

## Request and identity

The semantic request is:

```text
case              = futures_roll_long_v1
product_code      = IM | IC | IF | IH
start_date        = date (inclusive)
end_date          = date (inclusive)
strategy_profile  = expiry_to_M1_v1 | expiry_to_Q1_v1
```

There is no product, date, profile, benchmark or parameter default. The structural
request identity is `(case, product_code, start_date, end_date, strategy_profile)`;
the actual input fingerprint is separate and defined by [Inputs](INPUTS.md).

Dates are validated as date-only, `start_date <= end_date`, `end_date` not after the
current date in `Asia/Shanghai`, and inclusive span
`(end_date - start_date).days + 1 <= 1,096`. The window must contain at least two
CFFEX open sessions; session discovery and completeness are input-preparation
responsibilities.

The two profiles differ only in the target of a roll triggered by a held contract's
actual last trading day:

- `expiry_to_M1_v1` rolls to that decision session's `M1`;
- `expiry_to_Q1_v1` rolls to that decision session's `Q1`.

Both enter initially at the first session's `M1`. The profile name is immutable: a
changed roll rule requires a new profile version and a new request identity.

## Responsibility flow and validation ownership

```text
W2 input preparation → price-free Decision Context + Close Snapshot
W2 Mechanical Roll Policy → Target Portfolio
Core Replay → Transition/Daily PnL → Accounting → immutable Daily Records
W2 Performance Analyzer → BacktestResult/evidence/projections
```

Input preparation owns public-fact completeness, metadata consistency and input identity.
W2 Policy owns product/profile, M1/Q1 selection, expiry decisions, one-lot constraints
and final flat target. Core owns actual state, daily valuation/execution, PnL,
daily/cumulative accounting and recording. W2 derives initial index-equivalent capital and
requires consistent contract multipliers and positive equity. Benchmark/drawdown and
BacktestResult remain case concerns. Only input preparation may perform market I/O.

## Authority navigation

| Concern | Canonical owner |
| --- | --- |
| Replay, actual Portfolio, Transition/PnL, cumulative accounting and Recorder | [Core](../../core/ARCHITECTURE.md) |
| Real-contract target policy, session order, entry/hold/roll/exit, contract vs Slot, failure rules | [Strategy](STRATEGY.md) |
| Initial notional, benchmark, drawdown, case performance and five-day oracle | [Performance](PERFORMANCE.md) |
| Exact DataLake public bindings, completeness, W1 Slot reuse, underlying derivation, fingerprint, readiness | [Inputs](INPUTS.md) |
| BacktestResult, evidence, limitations, result-version and V2 projection | [Result](RESULT.md) |
| Portable evidence package contents, encoding and pure offline reproduction | [Evidence](EVIDENCE.md) |
| Online request, run lifecycle, ownership, store, concurrency, HTTP/Web ownership | [Online application](ONLINE_APPLICATION.md) |
| Delivery, WP2–WP8 acceptance and deferred scope | [Roadmap](ROADMAP.md) |
| Concern/consumer inventory, current semantic review and implementation drift | [Reconciliation](RECONCILIATION.md) |
| Actual real-market, HTTP and Windows Chrome execution evidence | [WP8 acceptance](WP8_ACCEPTANCE.md) |

W1's descriptive futures-basis work remains owned by
[`market_research`](../../../market_research/descriptive/cases/futures_basis/ARCHITECTURE.md).
W2 does not consume W1 Observations, Basis values, annualized basis, Statistics,
Reports, Publications or Online runs. It reuses only the published pure Slot
resolution boundary named by [Inputs](INPUTS.md); W1 Slot Transitions are descriptive
role changes, not W2 roll trades.

## Status

Current completion, remaining work and acceptance boundaries belong to the
[roadmap](ROADMAP.md). Contract-to-code differences are tracked separately in the
[current reconciliation](RECONCILIATION.md); declared authority is not implementation
or real-market acceptance evidence.
