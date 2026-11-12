# Core daily and cumulative accounting

This is the canonical daily and cumulative accounting contract of [Core](ARCHITECTURE.md).
Initial capital is explicitly supplied, numeric (not bool), finite and strictly positive.
Core does not derive capital from an instrument, benchmark or margin requirement.

`AccountingState.daily_return` exposes daily return as well as cumulative PnL, equity and cumulative
return. It starts with zero daily return, cumulative PnL and cumulative return, and
equity equal to capital.
`account(previous_accounting, transition)` consumes the already-computed Daily PnL:

```text
DailyReturn_t = DailyPnL_t / InitialCapital
CumPnL_t = CumPnL_(t-1) + DailyPnL_t
Equity_t = InitialCapital + CumPnL_t
CumulativeReturn_t = CumPnL_t / InitialCapital
```

Daily return uses fixed initial capital, not prior equity, and is not compounded.
The supplied initial capital never changes during a replay. An Analyzer or result
projection consumes both returns unchanged; it does not supply a second daily-return
calculation.

All arithmetic must remain finite. No rounding occurs between sessions; fractional
fixtures use declared test tolerance. Accounting never fetches prices, decides targets,
re-executes transitions or independently recomputes Daily PnL. Daily results must be
consumed in increasing session order, once per session.

Core reports finite equity even when non-positive; a case may constrain this further.
Benchmark comparison, drawdown, excess return and performance interpretation are case
analysis, not Core accounting. There is no broker cash, margin or funding ledger.
