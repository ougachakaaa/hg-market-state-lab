# PIP vertical-error-bounded algorithm V1

This is the canonical numerical contract for the future public Python boundary
`market_research.algorithm.pip`, owned by [Research](../../ARCHITECTURE.md). It is a
PIP greedy important-point selection variant with maximum-error stopping, not the
original fixed-K formulation. It accepts ordered numerical values only: it knows no
financial subject, dates, upstream service, observation or Statistics; it performs no
I/O, persistence or financial segmentation. [Price Segmentation](../../descriptive/cases/price_segmentation/ARCHITECTURE.md)
may consume it; the dependency never reverses. No registry or plugin framework is implied.

## Contract and mathematics

Algorithm identity is `pip_vertical_error_bounded_v1`. Input is a finite IEEE-754 binary64
sequence `y[0..N-1]`, N >= 2, and an explicit finite positive binary64 epsilon in the
same units as y.
Time x is the equally spaced original integer index, not elapsed calendar time. Reject
invalid length, non-finite values or epsilon, and non-positive epsilon explicitly.

Start with retained indices 0 and N-1. For each pair of adjacent retained indices a < b,
reconstruct each original position i between them by linear interpolation:

```text
r(i) = y[a] + (y[b] - y[a]) * (i - a) / (b - a)
e(i) = abs(y[i] - r(i))
```

Evaluate the displayed expression in binary64 in its written order: subtract `y[b] - y[a]`,
multiply by binary64 `(i - a)`, divide by binary64 `(b - a)`, then add `y[a]`; calculate
error by binary64 subtraction `y[i] - r(i)` followed by absolute value. Each arithmetic
operation rounds to nearest, ties to even; do not fuse operations or introduce intermediate
rounding beyond binary64. Index differences are exact integers converted to binary64; fail
if a conversion or intermediate result is non-finite. Compare the actual computed binary64
errors directly, with no implicit tolerance or decimal rounding.

Among all unretained indices select the global maximum e(i), breaking exact equal-error
ties by lowest original index. If its error is <= epsilon, stop; otherwise retain that
index and repeat. If no unretained indices remain, stop with maximum error 0. Return
strictly increasing original indices including both endpoints and the actual maximum
vertical reconstruction error over all original positions, including retained points
(which have zero error). The result must satisfy max error <= epsilon; no interpolated
point is passed off as an original observation. The operation must fail explicitly if
numerical computation cannot yield finite valid diagnostics, rather than report success
with NaN, infinity or a violated bound.

## Version and verification

An optimization may retain this ID only if it preserves the selected indices, tie and
stopping behavior and diagnostics for the same valid input and parameters; demonstrate
output equivalence against a reference implementation. Changing distance, selection or
stopping semantics requires a new algorithm ID. Previously recorded results retain their
original version and are never silently reinterpreted or replaced.

Tests must cover N=2 and invalid lengths/values/epsilon, constant and linear sequences,
sharp peaks, repeated values, equal maximum errors and earliest-index tie selection,
threshold equality, and deterministic repeated calls. Check every retained point is an
original index, endpoint/order and reconstruction bound, and actual error independently.
For positive scaling of both y and epsilon, mathematically equivalent results have the
same indices and scaled error; translation leaves errors and indices invariant, subject
to representable numerical precision. Test representative cases and numerical failure
rather than assume arbitrary floating-point operations are exact.

The same valid binary64 input and epsilon in the same execution environment and these
operation conventions produce deterministic indices and diagnostics. This does not promise
bitwise identity across arbitrary platforms or floating-point backends. Implementation
optimizations must preserve the specified computed output, including ties and threshold
comparisons, under the same environment; performance changes do not change mathematical
semantics or authorize a silent algorithm version change.
