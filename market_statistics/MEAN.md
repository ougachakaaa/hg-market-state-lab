# Arithmetic Mean (STAT-09)

Specializes [public contract](CONTRACT.md); backend policy: [BACKEND.md](BACKEND.md).
`MeanSpec()` has only method `mean`. `MeanResult` retains method `mean`, estimator
`arithmetic_binary64_v1`, `value`, actual `sample_count` and unchanged opaque `unit`.
Every legal nonempty NumericSample is compatible; no weights or extra parameters.

Compute NumPy `mean` on an owned float64 array with explicit float64 accumulation:
sum in the backend reduction order, then divide by sample_count. No scaling,
compensated summation or alternative estimator is substituted. Binary64 rounding
and backend reduction order apply; exact real arithmetic is not promised.
Even when a mathematical average would be finite, overflowing intermediate sums
raise CalculationFailure. Backend warnings, exceptions, malformed/non-float64 or
nonfinite results, or a value outside the sample range also raise CalculationFailure.
Singletons and duplicates are valid. Input order/multiplicity and units are preserved.

Acceptance covers ordinary and singleton means, duplicate multiplicity, cancellation,
extreme same-sign intermediate overflow, invalid sample/spec revalidation, immutability,
unchanged units and injected malformed results/numerical warnings.
