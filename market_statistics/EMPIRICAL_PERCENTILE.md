# Empirical Percentile method authority

Status: planned numerical extension for Calendar Spread L1; no runtime implementation
or public Python export exists yet. Inherits [the public contract](CONTRACT.md).
This file owns generic percentile mathematics, ties, Spec/Result and backend
conformance. Consumers own population selection and interpretation.

## Planned Spec and result

```text
EmpiricalPercentileSpec
  method = empirical_percentile
  queries: nonempty ordered sequence of finite binary64 numbers
  unit: nonempty opaque string

EmpiricalPercentileResult
  method = empirical_percentile
  estimator = midrank_v1
  query_results: ordered (query, less_count, equal_count, greater_count, percentile)
  sample_count
  unit
```

Queries follow NumericSample's public scalar/type/float64 rules, including rejection
of bool, coercible text, NaN, infinities and conversion overflow. Repeated or unordered
queries are legal and retained in supplied order. No sorting/deduplication of public
query parameters. Spec validation is sample-free; compute-time units must match the
sample exactly, otherwise InvalidStatisticalSpec. Sample validation still precedes
spec validation. NumericSample remains nonempty, finite, unweighted and business-free.

## Midrank algorithm and ties

For each query q against sample x with n values, preserving full duplicate multiplicity:

```text
L = count(x < q)
E = count(x == q)
G = count(x > q)
percentile = (L + 0.5 * E) / n
L + E + G = n
```

Counts are exact nonnegative integers. Compare the adapted binary64 numbers without
rounding, tolerance, quantization or snapping. Signed zero compares as zero. Evaluate
the displayed arithmetic in binary64; the finite result is a fraction in [0,1], not
a number in [0,100]. Query units pass through unchanged. Queries need not be observed
sample values or fall within the sample range. No quantile inversion, interpolation,
extrapolation, prediction or significance inference is performed.

The entire tied group receives half its mass. Below minimum is 0; above maximum
is 1; an all-equal sample queried at that value is 0.5. Singleton queried below,
at and above its value produces 0, 0.5 and 1. This is a midrank empirical percentile,
not the right-continuous ECDF `count(x <= q)/n`.

## Backend and failures

Use existing NumPy public `sort` on a private copy and `searchsorted` with explicit
left/right sides to obtain L and L+E; derive E and G and validate conservation.
This adds no dependency or automatic estimator selection. The consumer does not
implement this method. Validate ordered query association, exact counts, n/unit,
estimator and finite fractions before returning. Invalid backend shapes/counts or
results are CalculationFailure; no repaired sample or successful partial result.
The [Backend policy](BACKEND.md) governs scoped errors and backend adaptation.

## Acceptance obligations for implementation

- Sample `[1,1,3,9]`, queries `[0,1,2,3,9,10]` yields percentiles
  `[0,.25,.5,.625,.875,1]` and exact associated counts.
- All equal, singleton, negative values, signed zero, repeated queries and order
  retention; ties use exact values independently of presentation precision.
- Empty sample/queries, illegal numeric types, nonfinite values, unit mismatch,
  sample-first validation precedence and stable failures.
- Input immutability; malformed backend results fail rather than being repaired.

When WP3 is implemented, extend the existing root facade exports, typed Spec/Result
unions, validate_spec and compute dispatch. Existing method semantics stay unchanged.
Until then the live union remains Quantile/IntervalCount/Mean; authority readiness
does not mean the new method is callable.
