# IntervalCount method authority

Inherit the [public contract](CONTRACT.md) for representation, validation and errors.
This file owns interval boundaries, accounting and diagnostics (STAT-06).
Status: Implementation Ready, no implementation.

## Spec and partition

```text
IntervalCountSpec
  method = interval_count
  edges: at least two strictly increasing finite numeric boundaries
  unit: explicit non-empty opaque string
```

Boundary scalars follow sample binary64/type rules, including rejection of bool.
Test strict ordering after conversion. Do not sort, deduplicate or infer edges.
Standalone validation checks shape, values, ordering and unit. At `compute` time,
spec.unit must equal sample.unit exactly; mismatch is `InvalidStatisticalSpec`.
No unit conversion or automatic binning occurs.

For `[e0,e1,...,ek]`, create exactly k mutually exclusive bins in edge order:

```text
[e0,e1), [e1,e2), ..., [e{k-1},ek]
underflow: value < e0
overflow:  value > ek
```

Only the final bin includes its right endpoint, including the single-bin case. Every
value, with full duplicate multiplicity, belongs to exactly one bin or outside category.
Signed zero compares as numerical zero. No tolerance band is used.

## Backend conformance

Under [BACKEND.md](BACKEND.md), prefer NumPy histogram with explicit edges and count
mode (`density=False`). Histogram in-range counts exclude outside values; explicitly
count x < e0 and x > ek and retain their diagnostics. Validate returned bin/edge shape,
closures and exact nonnegative integer counts before computing full-sample frequencies.
No tolerance snapping, implicit edge extension, density normalization or automatic
bin generation is allowed. Explicit parameter generation is a separate future concern
under the [module extension boundary](ARCHITECTURE.md#extension-boundaries-stat-07-and-stat-08).

## Result and accounting

```text
IntervalCountResult
  method = interval_count
  edges: unchanged boundaries in input order
  bins: ordered sequence of
    boundary: (left, right, left_inclusive=true, right_inclusive=<last bin only>)
    count
    frequency
  underflow_count
  overflow_count
  underflow_frequency
  overflow_frequency
  sample_count
  unit
```

Every frequency is `count / sample_count`, including outside categories, never divided
only by in-range count. Frequencies are finite binary64 values without display rounding.
Outside counts/frequencies are applicable diagnostics, including zero values.

```text
sum(bin_counts) + underflow_count + overflow_count = sample_count
```

The frequency total including outside categories is one within binary64 roundoff.
Do not force a displayed 100% by changing counts or discarding outside values.

## Minimum deterministic acceptance (future implementation)

| Input / condition | Expected behavior |
| --- | --- |
| values `[-1,0,1,1,2,3]`, edges `[0,1,2]` | bin counts `[1,3]`, underflow 1, overflow 1; denominator 6 throughout |
| values `[0,1,2]`, edges `[0,2]` | single closed bin count 3, frequency 1 |
| All values outside edges | zero ordinary counts, retained outside counts; conservation |
| Duplicate/descending/non-finite edges; fewer than two; bool/text; invalid unit | `InvalidStatisticalSpec` |
| Valid spec but mismatched sample unit | Preflight valid; compute raises `InvalidStatisticalSpec` |
| Singleton sample; repeated values at each edge | Exactly one assignment per value; interior edges go right, last edge to final bin |
| Backend count/edge shape, type or conservation failure for valid inputs | `CalculationFailure`, never repaired counts or a partial successful result |

Verify the NumPy path against all partition fixtures, outside frequencies (including
zero), unchanged sample/edges/unit, typed results and exact count conservation. These
are future implementation obligations; STAT-01 executes no numerical runtime tests.
