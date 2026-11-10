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
current date in `Asia/Shanghai`, and inclusive span at most 20 calendar years
(operationally 7,305 days). The window must contain at least two CFFEX open sessions;
session discovery and completeness are input-preparation responsibilities.

The two profiles differ only in the target of a roll triggered by a held contract's
actual last trading day:

- `expiry_to_M1_v1` rolls to that decision session's `M1`;
- `expiry_to_Q1_v1` rolls to that decision session's `Q1`.

Both enter initially at the first session's `M1`. The profile name is immutable: a
changed roll rule requires a new profile version and a new request identity.

## Responsibility flow

```text
explicit request
  → public input preparation (Calendar / Futures / Index)
  → ordered CFFEX sessions + complete real contract facts
  → decision-day Slot resolution (authorized W1 pure boundary)
  → real-contract entry / hold / roll / exit simulation
  → gross PnL + benchmark + drawdown
  → immutable BacktestResult / evidence / V2 projection
  → case-specific online application / HTTP / Web (later WPs)
```

These are responsibility boundaries, not a generic engine, inheritance hierarchy or
mandatory sequence of separately persisted artifacts. Input preparation alone performs
public service I/O. Holding simulation performs no I/O. Accounting consumes a validated
position/price timeline. Result projection consumes accounting output without
recomputing it.

## Authority navigation

| Concern | Canonical owner |
| --- | --- |
| Real-contract position state machine, session order, entry/hold/roll/exit, contract vs Slot, failure rules | [Strategy](STRATEGY.md) |
| Initial notional, daily PnL, roll accounting, benchmark, returns, equity, drawdown, manual oracle | [Accounting](ACCOUNTING.md) |
| Exact DataLake public bindings, completeness, W1 Slot reuse, underlying derivation, fingerprint, readiness | [Inputs](INPUTS.md) |
| BacktestResult, evidence, limitations, result-version and V2 projection | [Result](RESULT.md) |
| Online request, run lifecycle, ownership, store, concurrency, HTTP/Web ownership | [Online application](ONLINE_APPLICATION.md) |
| WP0–WP8, acceptance, reconciliation, deferred scope | [Roadmap](ROADMAP.md) |

W1's descriptive futures-basis work remains owned by
[`market_research`](../../../market_research/descriptive/cases/futures_basis/ARCHITECTURE.md).
W2 does not consume W1 Observations, Basis values, annualized basis, Statistics,
Reports, Publications or Online runs. It reuses only the published pure Slot
resolution boundary named by [Inputs](INPUTS.md); W1 Slot Transitions are descriptive
role changes, not W2 roll trades.

## Status

WP0 is a documentation/authority gate. This case has no Python package, runtime,
market-data acquisition, HTTP product or Web feature yet. WP1 starts with the pure
holding simulation; WP4 PASS completes the core research capability; WP8 PASS is
required before W2 is declared complete. See the [roadmap](ROADMAP.md).
