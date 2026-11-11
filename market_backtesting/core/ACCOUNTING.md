# Core cumulative accounting

This is the canonical cumulative accounting contract of [Core](ARCHITECTURE.md).
Initial capital is explicitly supplied, numeric (not bool), finite and strictly positive.
Core does not derive capital from an instrument, benchmark or margin requirement.

`AccountingState` starts with zero cumulative PnL and return, equity equal to capital.
`account(previous_accounting, transition)` consumes the already-computed Daily PnL:

```text
CumPnL_t = CumPnL_(t-1) + DailyPnL_t
Equity_t = InitialCapital + CumPnL_t
Return_t = CumPnL_t / InitialCapital
```

All arithmetic must remain finite. No rounding occurs between sessions; fractional
fixtures use declared test tolerance. Accounting never fetches prices, decides targets,
re-executes transitions or independently recomputes Daily PnL. Daily results must be
consumed in increasing session order, once per session.

Core reports finite equity even when non-positive; a case may constrain this further.
W2's positive-equity restriction belongs to its [performance contract](../cases/futures_roll_long/PERFORMANCE.md).
Benchmark comparison, drawdown, excess return and performance interpretation are case
analysis, not Core accounting. There is no broker cash, margin or funding ledger.
