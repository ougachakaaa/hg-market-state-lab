# Quantile method authority

Inherit the [public contract](CONTRACT.md) for samples, validation, errors and results.
This file owns Quantile only (STAT-05). Status: Implementation Ready, no implementation.

## Spec and estimator

```text
QuantileSpec
  method = quantile
  points: non-empty strictly increasing sequence of unique finite probabilities
```

Each point follows the public numeric scalar/type contract and lies in `[0,1]`; bool
and coercible text are invalid. Validate strict increase after binary64
conversion; never sort or deduplicate an illegal request.

Use **Hyndman–Fan Type 7 / Linear Interpolation**, identity `type7_linear_v1`.
Sort a private sample copy numerically, preserving repeated values. With zero-based
indices and `n = sample_count`:

```text
h = (n - 1) * p
j = floor(h)
g = h - j
Q(p) = x[j] + g * (x[j+1] - x[j])
```

Return minimum at `p=0`, maximum at `p=1`, and the sole value for all legal points when
`n=1`. If `g=0`, return `x[j]` directly without reading a following element.
Evaluate the formula in binary64 in the displayed operation order, without fused
arithmetic or presentation rounding. If any executed interpolation intermediate or
output is non-finite, raise `CalculationFailure`, never clip, rearrange arithmetic to
change this failure boundary, or change estimator. Endpoint and g=0 branches bypass
interpolation, so they do not evaluate an unnecessary overflowing difference.

## Backend conformance

Under [BACKEND.md](BACKEND.md), prefer
`numpy.quantile(values, points, method="linear")`; matching the estimator name alone
does not establish conformance. Check endpoint, singleton and exact-index branches,
intermediate finiteness and differences between library interpolation branches and the
displayed operation order. Where necessary, use minimal method-local handling or a
narrow fallback preserving this contract. Do not create a second generic quantile engine,
silently redefine Type 7, or accept a finite library output after an operation that the
published contract requires to fail.

## Result

```text
QuantileResult
  method = quantile
  estimator = type7_linear_v1
  points_and_values: ordered sequence of (point, value), in requested point order
  sample_count
  unit
```

Every requested point appears once and unmodified. This retains all method parameters.
No additional successful warning diagnostics are required; estimator and common sample
accounting suffice. No independence inference is made.

## Minimum deterministic acceptance (future implementation)

| Input / condition | Expected behavior |
| --- | --- |
| values `[3,1,1,9]`, points `[0,.25,.5,.75,1]` | values `[1,1,2,4.5,9]`, count 4; original input unchanged |
| values `[7]`, points `[0,.5,1]` | `[7,7,7]` |
| values `[1,3]`, point `.25` | `1.5` |
| values `[1,1e16]`, point `.75` | `7500000000000001.0` in the frozen operation order; a branch returning `7500000000000000.0` needs adaptation |
| values `[-1e308,1e308,1e308]`, point `.5` | `1e308` directly at g=0, without overflowing interpolation |
| Empty/duplicate/descending points; outside `[0,1]`; NaN/infinity/bool/text | `InvalidStatisticalSpec`, no repaired request |
| values `[-1e308,1e308]`, point `.5` | `CalculationFailure`: the executed difference overflows |
| Same extreme values, points `[0,1]` | Both finite endpoints directly, without overflowing subtraction |
| Backend emits numerical-failure warning, non-finite payload or wrong result shape for valid inputs | `CalculationFailure`, no successful non-finite or malformed result |

Exact binary fixtures above use exact equality. Other interpolation tests allow binary64
roundoff against Type 7, not presentation precision.
Check repeated values, every requested point in order, method/estimator/count/unit and
input immutability across backend and adapted paths. These are deterministic acceptance
requirements, not evidence that a numerical implementation or conformance tests exist.
