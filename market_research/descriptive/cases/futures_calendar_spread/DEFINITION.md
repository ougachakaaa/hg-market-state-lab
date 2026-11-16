# Calendar spread financial definition

This is the unique financial definition for [futures_calendar_spread_v1](ARCHITECTURE.md),
shared by both products through [the application boundary](APPLICATION.md).
DataLake owns the input facts; Statistics owns numerical statistics, not these metrics.

## Products and ordered pairs

Products are the canonical IF, IH, IC and IM. Resolve each day's real M0/M1/Q1/Q2
identities through the existing [Slot Resolution contract](../futures_basis/SLOT_RESOLUTION.md).
Public pair order is:

```text
M0/M1, M0/Q1, M0/Q2, M1/Q1, M1/Q2, Q1/Q2
```

Each pair has exactly one near and one far Slot in that order, never a reversed
duplicate. Real contract identity, delivery month and last trading date come from
validated public metadata. Do not infer expiry from contract codes, a month label,
a third-Friday formula or last delivery date.

## Same-day prices and formulas

```text
N = near contract Close on trade_date
F = far contract Close on the same trade_date
delta_days = (far.delist_date - near.delist_date).days
near_dte_days = (near.delist_date - trade_date).days

signed_spread = N - F
annualized_point_spread = signed_spread * 365 / delta_days
annualized_spread_ratio = 365 * ln(N / F) / delta_days
```

`delist_date` is the producer's real last trading date. `delta_days` must be a
strictly positive integer natural-day difference; `near_dte_days` must be
nonnegative. Dates use `datetime.date`, rejecting datetime timestamps. On the near
contract's last trading date, near_dte_days=0 remains
legal and all three metrics remain applicable if delta_days>0. Do not borrow the
Basis annualization denominator or clamp a day count to one.

Both Close values must be finite binary64 and strictly positive; bool is not a
price. No settle/pre_close substitution, interpolation, prior-date alignment,
continuous contract, multiplier conversion or presentation rounding is allowed.
Use the displayed binary64 operation order and natural logarithm. Non-finite
executed intermediates/results, overflow or undefined logarithm caused by
underflow are explicit calculation failures, never repaired successful values.

| Metric | Stored/sample unit | Meaning |
| --- | --- | --- |
| signed_spread | `index_points` | Near Close minus far Close |
| annualized_point_spread | `index_points_per_365_natural_days` | Point difference normalized to 365 natural days |
| annualized_spread_ratio | `decimal_ratio` | 365-natural-day normalized log price ratio |

Metric identity is retained separately from unit. Percent formatting of a decimal
ratio is presentation only; financial values and statistical coordinates remain
unrounded. Signed zero is numerical zero; no parity tolerance is defined.

## Interpretation and examples

For a long holder selling near and buying far, a higher signed spread means a
relatively more favorable contemporaneous Close relationship. Within a fixed
product/pair/metric population, a higher historical percentile means the selected
price relationship ranks higher. This is not an executable roll quote or an
annual return; it excludes fees, slippage, margin, financing, dividends, future
changes and waiting value. Neither annualization nor historical rank proves
profitability, predicts returns or gives a trade instruction. Different metrics
may rank observations differently.

With N=110, F=100 and delta_days=30, results are 10 points,
`10 * 365 / 30` normalized points and `365 * ln(1.1) / 30` decimal ratio.
N=90, F=100 produces negative values; equal positive prices produce zero for
all metrics. Tests must distinguish log from linear annualization and the
between-contract denominator from near DTE. Price legality and failure outcomes
follow [Observation](OBSERVATION.md).
