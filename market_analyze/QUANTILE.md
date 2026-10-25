# Quantile method authority

Inherit the [public contract](CONTRACT.md) for samples, validation, errors and results.
This file owns Quantile only. Status: Implementation Ready, no implementation.

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

## Minimum deterministic acceptance

| Input / condition | Expected behavior |
| --- | --- |
| values `[3,1,1,9]`, points `[0,.25,.5,.75,1]` | values `[1,1,2,4.5,9]`, count 4; original input unchanged |
| values `[7]`, points `[0,.5,1]` | `[7,7,7]` |
| values `[1,3]`, point `.25` | `1.5` |
| Empty/duplicate/descending points; outside `[0,1]`; NaN/infinity/bool/text | `InvalidAnalysisSpec`, no repaired request |
| values `[-1e308,1e308]`, point `.5` | `CalculationFailure`: the executed difference overflows |
| Same extreme values, points `[0,1]` | Both finite endpoints directly, without overflowing subtraction |

Exact binary fixtures above use exact equality. Other interpolation tests allow binary64
roundoff against Type 7, not presentation precision.
