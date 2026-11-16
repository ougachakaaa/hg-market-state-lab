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

## Expiry-day inapplicability (SD-01)

Annualization requires a strictly positive remaining time span. On the last trading
day D=0, there is no remaining maturity period to annualize. Futures Close, Index
Close and the final cash-delivery settlement price are different price conventions;
the Close basis cannot simply be interpreted as a delivery return. Using 365/(D+1)
would systematically change every near-expiry observation, rather than losslessly
repair missing data. Therefore retain Not Applicable (`expiry_day`) deliberately:
no D+1, zero, interpolation, forward fill or other substitute. Valid raw basis_value
and basis_ratio remain available. This is neither missing market data nor a
calculation failure. The [outcome precedence](OBSERVATION.md#outcomes-and-precedence)
still applies before expiry-day applicability, including excluded prices and missing
underlying facts; neither is masked by expiry_day. The formula and definition
version are unchanged.

Reusable principle: for a derived metric requiring a strictly positive time span,
a zero span that removes its business definition should be expressed as Not
Applicable. Never change its time denominator or fill a substitute merely to keep
a chart continuous. Apply the specific metric's existing validity precedence first;
this is not a global rule for every metric at D=0.

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
