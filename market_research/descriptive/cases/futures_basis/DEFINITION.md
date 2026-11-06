# Futures Basis definition

This is SD01's canonical owner within [futures_basis_v1](ARCHITECTURE.md).
Upstream facts and availability remain under [Inputs](INPUTS.md), observation
outcomes under [Observation](OBSERVATION.md).

## Same-day prices and formula

Use the actual Futures Daily `close` and underlying Index Daily `close` on the
same `trade_date`. Neither settlement, previous close, another date, a continuous
series nor an inferred fair price may substitute. Both prices must be finite
binary64 numbers and strictly positive; bool is not numeric input.

```text
F = futures_close
S = underlying_close
D = (delist_date - trade_date).days

basis_value = F - S
basis_ratio = basis_value / S
annualized_basis_ratio = (365 / D) * ln(F / S)   # only D > 0
```

`ln` is the natural logarithm. D is an integer natural-day distance to the actual
last trading date, not the last delivery date or a delivery-month estimate.
Active lifecycle is inclusive, so D=0 is legal. Never replace D by `max(D, 1)`.
At D=0 the raw difference and ratio remain applicable; only the annualized metric
is Not Applicable with reason `expiry_day`.

Compute the displayed expressions in binary64 without presentation rounding,
including the subtraction before dividing for `basis_ratio`. A valid-input
arithmetic overflow, non-finite intermediate/result, or undefined logarithm from
binary64 underflow fails construction explicitly; do not repair, clip or silently
exclude it. Input and outcome failures are distinguished in the observation contract.

## Sign and units

| Condition on basis_value | State |
| --- | --- |
| > 0 | `Premium` |
| < 0 | `Discount` |
| == 0 | `Parity` |

Use strict zero comparison, including signed zero as Parity. No parity tolerance,
rounding threshold or positive-discount convention exists. State is a financial
price relation, not a statistical regime or recommended position.

`basis_value` uses `index_points`. Both ratios use `decimal_ratio`; the annualized
metric is explicitly identified as a 365-natural-day log rate. It is not an
effective annual return or a forecast. Percentage labels are presentation only;
stored values, numerical samples and chart coordinates remain decimal ratios.
Do not combine raw and annualized ratios into one unnamed metric because their
units share a string. Near-expiry annualization is highly sensitive to D.

## Minimum deterministic examples

- F=110, S=100: value=10, ratio=0.1, Premium; for D=10 use
  `(365 / 10) * ln(1.1)` for the annualized value.
- F=90, S=100: value=-10, ratio=-0.1, Discount.
- F=S=100: zero raw/ratio and Parity; annualized zero when D>0.
- D=0: same raw result, no annualized number. Finite nonpositive prices are
  business exclusions; missing facts are unavailable, not zero prices.

Fixtures must distinguish log annualization from simple linear annualization and
test exact-zero state independently of display precision. Numerical roundoff
tolerance in formula tests never becomes a domain parity tolerance.
