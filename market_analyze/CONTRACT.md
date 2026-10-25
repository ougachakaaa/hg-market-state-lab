# Analyze public numerical contract

This contract specializes the [module authority](ARCHITECTURE.md). It owns the public
sample, operation, method/result unions and failures. Independently readable method
contracts are [Quantile](QUANTILE.md) and [IntervalCount](INTERVAL_COUNT.md).
These contracts are Implementation Ready; runtime remains an Expected Implementation Gap.

## Public API and validation

```text
analyze(sample: NumericSample, spec: AnalysisSpec) -> AnalysisResult
validate_spec(spec: AnalysisSpec) -> valid or InvalidAnalysisSpec
AnalysisSpec   = QuantileSpec | IntervalCountSpec
AnalysisResult = QuantileResult | IntervalCountResult
```

The public Python semantic operation is synchronous, pure computation: no I/O,
randomness, input mutation or persistent state. Failures raise Analyze-owned errors,
never fabricated successful results. Python class layout and internal file organization
are implementation choices; named fields and typed variants below are public obligations,
not an unconstrained dictionary protocol. The `method` tag discriminates specs/results:
`quantile` or `interval_count`. Unknown tags are invalid specs.

The intended public facade is `market_analyze`: consumers must be able to import
NumericSample, both Spec variants, both Result variants, the AnalysisSpec/AnalysisResult
unions, analyze, validate_spec and the three public error categories from it. This fixes
the future consumer boundary without creating or registering that package in this task.

Public `validate_spec` validates without a sample or I/O and raises
`InvalidAnalysisSpec` on independently illegal specs. Construction may also validate;
consumers need not import internals. `analyze` revalidates sample, independent spec, then
sample/spec compatibility, even after preflight. If both arguments are invalid,
`InvalidSample` takes precedence.

## NumericSample

```text
NumericSample
  values: ordered, non-empty sequence of finite float64 numbers
  unit: non-empty opaque string identifier
sample_count = len(values)
```

The coordinate is IEEE-754 binary64. Public Python scalar inputs are built-in int or
float, excluding bool; integers undergo ordinary correctly rounded binary64 conversion.
Other numeric representations must be adapted to these scalars before public submission;
do not implicitly parse text, Decimal, fractions, complex or null values. Reject
conversion overflow, NaN and either infinity.
Values must form a one-dimensional ordered sequence, not a set, mapping, scalar string
or nested data. Container class is not prescribed. No independent input count is accepted.
Weights, grouped samples and multivariate inputs are unsupported.

Duplicates retain full multiplicity. Preserve input order and values; methods may sort
private copies. No deletion, filling, clipping, deduplication, presentation rounding or
unit conversion. Binary64 representation/arithmetic rounding is inherent and is not
presentation rounding. Pass `unit` through exactly, case sensitively, without trimming
or alias resolution. Empty/non-string units are invalid; Analyze assigns no business
meaning to an otherwise non-empty identifier. Singleton samples are valid, empty ones
are always invalid.

Sample keys, source references, dependence and business context belong to consumers,
not NumericSample. Analyze does not require or interpret them.

## Results and diagnostics

Each typed result retains method identity, full parameters/estimator, actual derived
`sample_count`, unchanged `unit` and method-specific calculated payload. Counts are exact
nonnegative integers; calculated scalars must be finite binary64 values. No non-finite
successful result or implicit percentage conversion is permitted.

Method contracts define applicable diagnostics; no free-form metadata envelope is needed.
The initial methods are descriptive only: no independence assertion/test, confidence
interval or statistical significance inference.

## Stable failure categories

`AnalysisFailure` names the public failure family below, not an additional result variant
or a required fourth error category.

| Category | Meaning |
| --- | --- |
| `InvalidSample` | Illegal shape, empty sample, illegal/non-finite scalar or invalid unit. Never silently discard values. |
| `InvalidAnalysisSpec` | Unknown method, illegal parameters/order/types, or sample/spec unit mismatch. Compatibility is checked at analyze time. |
| `CalculationFailure` | Valid inputs cannot produce a finite defined result, including arithmetic overflow or numerical execution failure. Retain method and readable reason. Never substitute another method or repaired sample. |

Wrong public object variants fail in the respective validation category. Consumers can
identify the three categories without parsing messages; exact exception hierarchy is an
implementation detail. Process termination is not a successful numerical result.

## Minimum acceptance obligations

Test invalid types/shapes, bool, empty sample/unit, NaN and both infinities; finite
representation conversion and overflow; duplicates; input immutability; unchanged opaque
units; unknown-tag preflight; analyze-time revalidation and validation precedence.
Method fixtures belong to the linked method contracts. Verify public facade attributes
directly; this authority does not require `__all__`.
