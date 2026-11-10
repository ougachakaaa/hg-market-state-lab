# Futures Roll Long result, evidence and visualization contract

This contract owns the immutable `BacktestResult` semantic payload and its
producer-owned evidence/visualization projection for the [case](ARCHITECTURE.md).
Position decisions are owned by [Strategy](STRATEGY.md); accounting values and their
canonical formulas are owned by [Accounting](ACCOUNTING.md). This document defines the
result fields and required cross-field consistency; it does not create a second
accounting formula. Web transport and rendering are separate contracts.

## One result, three contracts

These are distinct and must not be collapsed:

| Contract | Owner | Purpose |
| --- | --- | --- |
| `BacktestResult` | `market_backtesting` | Immutable semantic result, evidence summary and views |
| Run state | `market_backtesting` online application | Mutable execution lifecycle; only a completed run has a result |
| HTTP DTO | `ui_http` (WP6) | Transport projection of the run state and result; no financial recomputation |

The HTTP layer may wrap the result with transport identity, status and timestamps. It
must not derive, repair or reinterpret PnL, returns, benchmark values, trades,
drawdown, coverage, fingerprint or limitations. The Web layer may format values and
lay out charts, but must not calculate them.

## Result profile

```text
profile             = futures_roll_long_result_v1
case                = futures_roll_long_v1
definition_version  = futures_roll_long_definition_v1
status              = complete
```

W2 v1 has no partial scientific result. Input preparation, holding simulation or
accounting failure produces a run failure and no `BacktestResult`; it never publishes a
successful result with missing dates, filled prices or partial exposure.

A result is published only after all of the following are true:

- the final Calendar/Futures/Index exports are complete and validated;
- the strategy state machine ends flat on the final session;
- accounting is finite, equity is positive and the benchmark is valid;
- every cross-field invariant in this document holds;
- the views validate against the generic Visualization V2 contract;
- the versioned profile and request association are exact.

## Request and observed window

```text
request = {
  case,
  product_code,
  start_date,
  end_date,
  strategy_profile
}
window = {
  first_session,
  last_session,
  cffex_session_count
}
```

`request.start_date`/`end_date` are the user-requested inclusive dates.
`window.first_session`/`last_session` are the observed CFFEX sessions after Calendar
resolution. The two must remain distinct; the browser, HTTP DTO and evidence must
never relabel requested dates as observed dates or vice versa. The daily series starts
at `first_session` and ends at `last_session`.

## Benchmark and initial notional

```text
benchmark = {
  index_code,
  index_name,
  first_close,
  last_close
}
initial_notional = {
  index_first_close,
  multiplier,
  currency: "CNY",
  value
}
```

- `index_code` is derived from the validated Futures public rows and must agree with
  the Index export.
- `index_name` is the public name from the retained Index rows; it is display metadata,
  not a second identity.
- `first_close` is the Index Close on the first CFFEX session; `last_close` is the
  Index Close on the final CFFEX session.
- `value = index_first_close × multiplier`; `multiplier` is the entry contract's real
  multiplier, fixed for the backtest.

## Daily series

`daily` is ordered by strictly increasing `trade_date`, contains exactly one row for
each CFFEX session in `[first_session, last_session]`, and no rows for request dates
outside those sessions.

Each row contains:

```text
trade_date
position_contract_code       # end-of-session real holding; null after final close
pnl_contract_code           # contract whose close-to-close move is attributed
previous_close              # null on entry day; otherwise previous close of pnl contract
close                       # session close of pnl contract
daily_pnl
cumulative_pnl
equity
daily_return
cumulative_return
benchmark_close
benchmark_daily_return
benchmark_cumulative_return
benchmark_equity
excess_cumulative_return
drawdown
benchmark_drawdown
```

Semantics:

- On the entry row: `pnl_contract_code` is the new M1, `position_contract_code` is the
  same contract, `previous_close` is null and all PnL/return values are zero.
- On a normal holding row: both contract fields are the held contract; `previous_close`
  is that contract's previous session close.
- On a roll row: `pnl_contract_code` is the old contract, `position_contract_code` is
  the new contract, `close`/`previous_close` belong to the old contract; the new
  contract's first close is the roll Close and its first PnL appears on the next row.
- On the final row: `pnl_contract_code` is the held contract; `position_contract_code`
  is null after the close.
- `daily_pnl`, `cumulative_pnl`, `equity`, returns and drawdowns follow
  [Accounting](ACCOUNTING.md) exactly; no value is recomputed by a consumer.
- `benchmark_equity = initial_notional.value × (1 + benchmark_cumulative_return)`.
- `excess_cumulative_return = cumulative_return - benchmark_cumulative_return`.
- `drawdown`/`benchmark_drawdown` use each series' running peak; they are `<= 0`.

Every numeric value is finite. A missing price or a non-finite/negative-equity value is
a failure, not a null daily cell. W2 v1 does not use null to represent an unavailable
price; it fails the backtest.

## Executions and roll events

`trades` is the ordered list of individual execution legs:

```text
trade_date
side                  # BUY | SELL
contract_code
price                 # ideal session Close
multiplier
reason                # entry | expiry_close | expiry_open | study_end_close
selection_slot        # M1 or Q1 on entry/expiry_open; null on close legs
```

`rolls` groups the two legs of each expiry roll:

```text
trade_date
old_contract_code
old_slot              # actual resolved Slot of the old contract; validated M0 on a roll
old_close
new_contract_code
new_slot              # profile target M1 or Q1
new_close
reason                # expiry
```

Rules:

- The first execution is a BUY of the entry M1 on `first_session`.
- Every roll has a SELL of the old contract at its expiry Close followed by a BUY of
  the target at the same session's Close; the order is close then open.
- The final execution is a SELL of the held contract on `last_session`, reason
  `study_end_close`; there is no subsequent BUY.
- A final session that is also the old contract's expiry produces a SELL only, not an
  `expiry_open` and not a roll.
- No execution is created by a W1 Slot mapping change, a daily Slot re-resolution or a
  contract metadata refresh.
- `selection_slot` is present only for opens; close legs use null. The roll event carries
  the old session slot and the profile target slot.
- `old_slot` is the Slot mapping whose `contract_code` is `old_contract_code` in the
  same decision-session resolution used to select the new target. It is not inferred
  from the delivery month, contract code or a recalled role.
- A valid roll requires the expiring held contract to be present in the complete active
  set and to map to `M0`; this follows from the expiring contract being the front
  contract. If it is absent or maps elsewhere, the simulation fails
  `invalid_contract_lifecycle` and publishes no result. Thus `old_slot = M0` is a
  validated invariant, not an unconditional assumption.

## Summary

```text
summary = {
  initial_notional,
  total_pnl,
  gross_return,
  benchmark_return,
  excess_return,
  strategy_max_drawdown,
  benchmark_max_drawdown,
  execution_count,
  roll_count
}
```

`execution_count = len(trades)`, `roll_count = len(rolls)`, and a v1 successful result
has at least one entry and exactly one final exit. Summary values are projections of the
daily series and must not be independently recomputed with different arithmetic.

## Evidence and limitations

`evidence` contains at least:

```text
input_profile
input_fingerprint
public_requests
coverage                  # Calendar/Futures/Index coverage contexts
sources                   # Dataset/view/schema identities and Slot authority reference
slot_resolution_authority
definition_version
result_profile
limitations
```

- `input_fingerprint` is the canonical `futures_roll_long_inputs_v1` fingerprint from
  [Inputs](INPUTS.md); it is not a request hash or a provider freshness claim.
- `public_requests` records the exact Calendar/Futures/Index semantic requests used.
- `coverage` records final target counts and completeness; it is evidence, not a
  substitute for retained inputs.
- `sources` identifies the DataLake public dataset/view/schema and the W1 pure Slot
  authority; it contains no paths, credentials, SQL or provider responses.
- `limitations` is an ordered, fixed list owned by the producer. It must state the
  gross idealized close execution, absence of fees/slippage/margin/funding/dividends,
  one-lot/no-compounding normalization, index-price benchmark nature, and the fact
  that cache completeness is not provider freshness.
- The full canonical input package/replay is a case-owned WP4 evidence artifact. The
  online result carries this evidence summary; an online evidence/replay endpoint is
  not part of W2 v1 unless a later authority adds it.

## Visualization projection

The result carries producer-owned generic V2 Views under `views`. They conform to the
[Visualization V2 contract](../../../ui_web/VISUALIZATION_V2.md); W2 does not add
financial fields to the generic schema.

Required views:

| View | Content |
| --- | --- |
| `returns` | two `LineV2` bindings: strategy cumulative return and benchmark cumulative return, date x-axis, y-axis unit `decimal_ratio` |
| `drawdown` | two `LineV2` bindings: strategy drawdown and benchmark drawdown, same coordinate conventions |

Requirements:

- x dates are exactly the daily session dates; no invented weekend/holiday points;
- y values are finite; no null interpolation is needed in v1;
- each line uses one contiguous segment for the whole series; v1 does not introduce
  gap-null segmentation or connect across missing dates;
- events mark entry, each roll and exit on the date axis; event Details are literal
  text such as contract code, profile and ideal Close; no business-specific fields
  enter the generic schema;
- Binding labels identify strategy/benchmark unambiguously; the unit is the exact
  `decimal_ratio`/`date` value, not a display string;
- the producer validates the V2 structures before publication; the frontend validates
  again before rendering and never recalculates the series.

The `returns` view is the primary return chart. The `drawdown` view is the risk view.
The trades/rolls and evidence sections are separate tables/read-only projections; they
are not encoded as an alternative chart DSL.

## Cross-field invariants

A result is invalid unless all of the following hold:

1. `daily` dates equal the observed CFFEX sessions exactly, strictly increasing.
2. `summary.total_pnl == Σ daily.daily_pnl == last daily.cumulative_pnl`.
3. `daily.equity == initial_notional.value + daily.cumulative_pnl`.
4. `summary.gross_return == summary.total_pnl / initial_notional.value`.
5. `summary.benchmark_return == last daily.benchmark_cumulative_return`.
6. `summary.excess_return == summary.gross_return - summary.benchmark_return`.
7. `summary.strategy_max_drawdown == min(daily.drawdown)`;
   `summary.benchmark_max_drawdown == min(daily.benchmark_drawdown)`.
8. `daily.cumulative_return == daily.cumulative_pnl / initial_notional.value`.
9. `daily.benchmark_cumulative_return == daily.benchmark_close / first_close - 1`.
10. On entry, both contract fields are the entry contract and PnL is zero; on a roll,
    `pnl_contract_code` is the old contract and `position_contract_code` is the new
    contract; on the final row, position is null.
11. `trades`/`rolls` match the daily position changes: one entry, two legs per roll,
    one final exit; no execution after the final exit; no trade on a non-roll day.
12. `views` numeric values match the corresponding daily series; no view contains a
    value absent from the daily/result evidence.

## Versioning and non-goals

- `futures_roll_long_result_v1` is tied to `futures_roll_long_definition_v1`.
- A changed strategy rule, roll profile formula, accounting formula or result field
  meaning requires a new profile/definition version and a new request identity; it may
  not be silently served as the same result.
- V1/V2 Visualization coexistence follows the generic Visualization authority; W2 does
  not alter V1 consumers.
- This contract does not define the HTTP wire schema. WP6 owns the HTTP DTO projection
  under the W2 [online application](ONLINE_APPLICATION.md) boundary; WP7 owns the Web
  feature and generated contract. Until those WPs exist, no HTTP endpoint or Web result
  surface is claimed.
