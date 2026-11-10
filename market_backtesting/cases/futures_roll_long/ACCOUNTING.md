# Futures Roll Long PnL and benchmark accounting

This contract owns the numerical accounting of the [case](ARCHITECTURE.md). Position
decisions are owned by [Strategy](STRATEGY.md). This document freezes units, the
initial notional denominator, close-to-close PnL, roll treatment, benchmark comparison,
return curves, drawdown and the manual oracle.

## Units and value semantics

| Concept | Unit |
| --- | --- |
| Futures/Index price | index point |
| Multiplier | CNY per index point per lot |
| PnL, equity, initial notional | CNY |
| Return, excess return, drawdown | decimal ratio (`0.01` means 1%) |

Return and drawdown values are never stored as preformatted percentage strings. The
producer reports finite JSON-compatible numbers; the Web layer owns display formatting.
No intermediate rounding is permitted. The same semantic inputs and definition version
must produce deterministic values. The worked oracle below uses integers, so an
independent WP2 implementation can compare exactly. For non-integer fixtures, tests
use a declared tolerance rather than changing the semantic formulas.

## Fixed initial index-equivalent notional

```text
N0 = Index(first_session).close × M_entry
```

`M_entry` is the real multiplier of the entry contract. It is fixed for the whole
backtest and must not be replaced by a later contract's multiplier. Every contract used
for PnL must carry the same positive multiplier as the entry contract; otherwise the
backtest fails `multiplier_mismatch`.

`N0` is an index-equivalent exposure denominator, not the futures entry price times the
multiplier. It gives strategy return and index benchmark return the same initial base.
If the entry futures price differs from the index level, that difference is not PnL; it
is part of the basis and is not decomposed in W2.

## Daily PnL

For a session `t` with PnL-attribution contract `c_t`:

```text
entry session:          pnl_t = 0
normal/roll/final:      pnl_t = (Close(c_t, t) - Close(c_t, t-1)) × M
```

`Close(c_t, t-1)` is the same real contract's immediately preceding CFFEX session
close. Weekends and holidays create no rows and no interpolation. `t-1` means the
previous supplied session, not `t` minus one calendar day.

Attribution rules:

- entry session: `c_t` is the newly opened M1, but PnL is zero because the position was
  opened at that session's close;
- ordinary holding session: `c_t` is the held contract;
- roll session: `c_t` is the old contract; the new contract's PnL starts next session;
- final session: `c_t` is the old/held contract; its close-to-close move is included and
  the position is then closed.

The result's `pnl_contract_code` records `c_t`. The result's
`position_contract_code` records the contract held at the end of the session: the new
contract after entry or roll, null after the final close.

## Roll accounting invariant

On a roll session:

```text
old contract PnL = (old Close_t - old Close_{t-1}) × M
new contract PnL = 0
```

The old contract is sold at `old Close_t`; the new contract is bought at
`new Close_t`. The price difference between the two contracts is never a PnL term. If
the implementation adds `(new Close_t - old Close_t) × M`, it double-counts a contract
switch as profit or loss and violates this contract.

This is the accounting reason W2 uses real contract close-to-close variation instead of
daily Slot returns or a synthetic continuous series.

## Benchmark

The benchmark is the underlying index's price return, buy-and-hold from the first CFFEX
session close to each observed session close. The index code is derived from the
Futures public rows; W2 does not maintain a second product-to-index table. No dividend
yield, total-return adjustment, ETF fee or cash return is applied.

```text
benchmark_cumulative_return_t = Index_t / Index_first - 1
benchmark_daily_return_t      = Index_t / Index_{t-1} - 1     (t > first)
benchmark_equity_t            = N0 × (1 + benchmark_cumulative_return_t)
```

On the first session, benchmark daily return and cumulative return are zero. Every
CFFEX session must have an Index Close; missing values fail input preparation. The
benchmark is a normalized comparison series, not a claim that the index is directly
tradable as one lot or that an ETF would reproduce it.

## Strategy returns and equity

```text
cum_pnl_t      = Σ pnl_i
equity_t       = N0 + cum_pnl_t
gross_return_t = cum_pnl_t / N0
daily_return_t = pnl_t / N0
```

`gross_return_t` is a simple cumulative gross return on the fixed initial notional. It
is not compounded, annualized or reinvested. The equity curve is linear in cumulative
PnL because the position is always exactly one lot.

Final `gross_return` is `cum_pnl_final / N0`. Final `benchmark_return` is
`benchmark_cumulative_return_final`. Final `excess_return` is:

```text
excess_return = gross_return - benchmark_return
```

Daily excess, when projected, is `daily_return_t - benchmark_daily_return_t`. It is
diagnostic only and is not summed into the final excess return; compounding of the
benchmark and simple summation of futures PnL make the two notions different.

## Drawdown

Drawdown is computed on equity, not on a price series:

```text
peak_t     = max(N0, equity_1, ..., equity_t)
drawdown_t = equity_t / peak_t - 1
max_drawdown = min_t drawdown_t          # <= 0
```

The denominator is the running peak equity, which is at least `N0`. If equity never
falls below its running peak, drawdown is zero. Benchmark drawdown uses
`benchmark_equity_t` and its own running peak with the same formula. The final
`max_drawdown` is the minimum (most negative) daily drawdown, not only the final
drawdown.

A strategy equity value `<= 0` at any session, or a benchmark equity `<= 0`, is an
accounting failure (`non_positive_equity`). W2 does not publish a result with an
undefined/negative drawdown denominator or silently clamp the value.

## Manual independent oracle

This is a complete artificial example. It does not claim any real calendar, price or
contract. Five CFFEX sessions are assumed: D1 entry, D2 hold, D3 roll, D4 hold, D5 final.
`M = 200 CNY/point`, D1 Index Close = 6000, initial `M1` contract `C1` entry = 5900,
and `C1.delist_date = D3`.

Initial notional:

```text
N0 = 6000 × 200 = 1,200,000 CNY
```

### `expiry_to_M1_v1`

At D3, the old `C1` closes at 6000 and the new `M1` `C2` is opened at 6010. The roll
price difference is not PnL.

| Session | PnL contract | Contract Close | Index Close | Daily PnL | Cumulative PnL | Equity | Strategy cumulative | Benchmark cumulative | Strategy drawdown | Benchmark drawdown |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| D1 | C1 (entry) | 5900 | 6000 | 0 | 0 | 1,200,000 | 0 | 0 | 0 | 0 |
| D2 | C1 | 5950 | 6060 | 10,000 | 10,000 | 1,210,000 | 0.0083333333 | 0.01 | 0 | 0 |
| D3 | C1 (roll) | 6000 | 6030 | 10,000 | 20,000 | 1,220,000 | 0.0166666667 | 0.005 | 0 | -0.0049504950 |
| D4 | C2 | 6030 | 6090 | 4,000 | 24,000 | 1,224,000 | 0.02 | 0.015 | 0 | 0 |
| D5 | C2 (exit) | 6020 | 6075 | -2,000 | 22,000 | 1,222,000 | 0.0183333333 | 0.0125 | -0.0016339869 | -0.0024630542 |

M1 summary:

- total PnL = 22,000 CNY;
- gross return = 22,000 / 1,200,000 = 0.0183333333 (1.8333333333%);
- benchmark return = 6075 / 6000 - 1 = 0.0125 (1.25%);
- excess return = 0.0058333333 (0.5833333333%);
- strategy maximum drawdown = -0.0016339869 (-0.16339869%);
- benchmark maximum drawdown = -0.0049504950 (-0.49504950%, at D3);
- entry/exit/roll executions = 4 legs; roll count = 1.

### `expiry_to_Q1_v1`

At D3, the new `Q1` `C2'` opens at 6025. D4 `C2'` Close = 6030; D5 = 6020.

- D4 PnL = (6030 - 6025) × 200 = 1,000;
- D5 PnL = (6020 - 6030) × 200 = -2,000;
- total PnL = 10,000 + 10,000 + 1,000 - 2,000 = 19,000;
- gross return = 19,000 / 1,200,000 = 0.0158333333 (1.5833333333%);
- benchmark return = 0.0125; excess = 0.0033333333 (0.3333333333%);
- strategy maximum drawdown = 1,219,000 / 1,221,000 - 1 = -0.0016380016
  (-0.16380016%);
- benchmark maximum drawdown remains -0.0049504950.

### Oracle checks and invalid shortcuts

- Summing the five daily strategy returns equals the final simple gross return.
- The final excess is the arithmetic difference of final holding-period returns; it is
  not the sum of daily benchmark differences. In the M1 example the daily benchmark
  returns sum to about 0.0125367, while the compounded holding-period benchmark return
  is 0.0125.
- Adding the roll-day contract price gap would overstate the M1 total by
  `(6010 - 6000) × 200 = 2,000` and the Q1 total by
  `(6025 - 6000) × 200 = 5,000`. Both are prohibited.
- Using the futures entry price 5900 instead of the index close 6000 would produce
  `N0 = 1,180,000`, which is not this contract's normalization.

## Exclusions and forbidden interpretations

W2 does not include and does not approximate:

- commissions, exchange fees, taxes, slippage, bid/ask, market impact or fill risk;
- margin calls, initial/maintenance margin, margin account return or leverage;
- daily settlement cash flows or variation-margin financing;
- funding cost, risk-free rate, collateral return or cash drag;
- dividends, total-return index adjustment, ETF fees/tracking difference or ETF
  comparison;
- roll-yield decomposition, basis carry attribution, annualized basis or any direct
  use of W1 basis values as strategy return;
- CAGR, annualized volatility, Sharpe, Sortino, alpha, beta or risk-adjusted metrics;
- strategy optimization, parameter search, multi-product aggregation or portfolio
  construction.

The Close is an idealized execution and valuation price. The result is a gross,
one-lot, long-only research measurement, not a tradable PnL promise. W3 features require
a new authority/version and must not be inferred from this contract.
