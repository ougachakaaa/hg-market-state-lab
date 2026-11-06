# Statistical numerical backend authority (STAT-04)

This contract specializes the [module authority](ARCHITECTURE.md) and inherits the
[public contract](CONTRACT.md). It owns numerical library selection, conformance,
failure adaptation and upgrade policy. Method meaning belongs only to
[Quantile](QUANTILE.md) and [IntervalCount](INTERVAL_COUNT.md) and [Mean](MEAN.md).

## Selection and runtime boundary

Statistics owns public statistical meaning; external libraries supply numerical
implementations. Prefer mature libraries over reimplementing established algorithms.
For V1, the preferred backend is NumPy through supported public APIs only:

| Method | Preferred implementation path | Required adaptation |
| --- | --- | --- |
| Quantile | `numpy.quantile(values, points, method="linear")` | Preserve the method's frozen binary64 branches, operation order and failure boundary wherever library behavior differs. |
| IntervalCount | `numpy.histogram(values, bins=explicit_edges, density=False)` | Retain separately counted underflow and overflow; use the full sample denominator for frequencies. |

Use no private NumPy internals. NumPy is an explicit root-project dependency with a
tested range compatible with repository Python 3.13; a transitive installation is not
the dependency declaration. STAT-01 changed neither pyproject.toml nor poetry.lock and
created no adapter or module-local environment; STAT-IMP-01 implements the runtime.
SciPy and statsmodels are potential future backends, not V1 dependencies.

## Conformance and error boundary

For every method, the facade must:

1. Validate public sample, spec and compatibility under the public validation precedence.
2. Call the approved backend where its behavior conforms to the method authority.
3. Apply only the minimal adaptation needed to preserve that contract.
4. Validate returned type, shape, finiteness, parameters and sample accounting.
5. Return the typed StatisticalResult or raise the declared StatisticalFailure category.

Check method-specific result cardinality/order, unchanged sample_count/unit and finite
payloads. Quantile must retain all requested points and its estimator; IntervalCount
must retain actual boundaries/closures, exact nonnegative integer counts, conservation
and count/sample_count frequencies, including outside categories.

Reject invalid public inputs as InvalidSample or InvalidStatisticalSpec before backend
execution; legal public inputs do not become invalid merely because a backend fails.
Map backend numerical exceptions, non-finite executed arithmetic, and malformed or
contract-inconsistent outputs for valid inputs to CalculationFailure, retaining method
and a readable reason. Backend warnings indicating invalid/non-finite numerical execution
cannot be ignored to produce success, even if an eventual output appears finite.
Do not silently filter, fill, clip, change estimator, substitute a method or repair a sample.
NumPy-specific result objects, warning/error categories and implementation choices are
not the public semantic API. Endpoint handling must avoid unnecessary overflowing
backend operations rather than reinterpret their failure as a successful computation.

## Conformance acceptance and upgrades

The following obligations are implemented by STAT-IMP-01. STAT-01 established only
authority; current runtime evidence is linked from [README](README.md):

| Concern | Required acceptance evidence |
| --- | --- |
| Public boundary | Invalid samples/specs rejected before backend calls; correct precedence, pure operation, unchanged inputs and typed public outputs. |
| Quantile | All method fixtures, p=0/1, singleton, g=0, duplicates, ordinary interpolation, extreme opposite signs, intermediate overflow, and non-finite backend outputs. Compare library interpolation branches with the frozen operation order; isolate each required adaptation. |
| IntervalCount | Explicit-edge count mode, interior/rightmost endpoints, single bin, outside-only samples, repeated values, exact conservation and common frequency denominator. No backend-selected edges or density normalization. |
| Invalid backend output | Wrong type/shape, non-finite output, bad accounting, and numerical-failure exceptions/warnings fail with CalculationFailure; never expose backend-specific failures as the contract. |

Backend version changes must run numerical fixtures and edge-case conformance tests
that detect semantic drift. If published behavior cannot be preserved, reconcile the
authority explicitly and change method version when necessary before accepting the
upgrade. No bitwise identity is promised across untested libraries, versions or
architectures; this does not relax the frozen method operation order and failure rules.

## V1 implementation conformance

The root project declares `numpy>=2.5.3,<2.6.0`, tested on NumPy 2.5.3 and Python 3.13.
Quantile bypasses NumPy interpolation for endpoints, singleton and exact-index requests.
For remaining points it checks the required difference for finiteness, invokes the public
linear quantile API and validates its float64 result shape/finiteness. For `g >= 0.5`,
NumPy's right-endpoint subtraction branch is adapted to the published left-endpoint
addition order. In particular, `[1,1e16]` at `.75` returns `7500000000000001.0` rather
than NumPy's `7500000000000000.0`. Required overflowing differences fail before backend
execution; direct branches never perform that difference. This is method-local handling,
not an alternate estimator or backend engine.

IntervalCount uses the public histogram API with explicit binary64 edges and
`density=False`. Returned integer counts and unchanged edges are checked for shape,
type, nonnegativity and conservation with separately counted outside values. All
frequencies use the actual full sample count. Backend RuntimeWarnings and floating-point
invalid/overflow/division errors become CalculationFailure within a scoped context;
no process-global warning policy is modified. Failure-injection tests cover malformed
outputs, exceptions and finite-looking results after invalid numerical execution.

Mean uses `numpy.mean(array, dtype=numpy.float64)` with finite scalar/type/range validation under the same scoped warning/error boundary. See [Mean](MEAN.md) for intermediate overflow semantics.
