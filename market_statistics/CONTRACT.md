# Statistics public numerical contract

This contract specializes the [module authority](ARCHITECTURE.md). It owns the public
sample (STAT-03), operation, method/result unions and failures (STAT-02). Independently
readable method contracts are [Quantile](QUANTILE.md) and [IntervalCount](INTERVAL_COUNT.md).
STAT-IMP-01 implements these contracts through the public `market_statistics` facade.

## Public API and validation

```text
compute(sample: NumericSample, spec: StatisticalSpec) -> StatisticalResult
validate_spec(spec: StatisticalSpec) -> None
StatisticalSpec = QuantileSpec | IntervalCountSpec
StatisticalResult = QuantileResult | IntervalCountResult
```

The public Python semantic operation is synchronous, pure computation: no I/O,
randomness, input mutation, persistence or reliance on current market state. Failures
raise Statistics-owned errors, never fabricated successful results. Python class layout
and internal file organization are implementation choices; named fields and typed
variants below are public obligations, not an unconstrained dictionary protocol.
The `method` tag discriminates specs/results:
`quantile` or `interval_count`. Unknown tags are invalid specs.

The public facade is `market_statistics`: consumers must be able to import
NumericSample, both Spec variants, both Result variants, the StatisticalSpec/StatisticalResult
unions, compute, validate_spec and the three public error categories from it. The package
is registered in the repository root project; no separate environment is required.

```python
from market_statistics import (
    NumericSample,
    QuantileSpec,
    IntervalCountSpec,
    QuantileResult,
    IntervalCountResult,
    InvalidSample,
    InvalidStatisticalSpec,
    CalculationFailure,
    validate_spec,
    compute,
)
```

Public `validate_spec` validates without a sample or I/O, returns None on success and raises
`InvalidStatisticalSpec` on independently illegal specs. Construction may also validate;
consumers need not import internals. `compute` revalidates sample, independent spec, then
sample/spec compatibility, even after preflight, then validates the computed result
before returning it. If both arguments are invalid, `InvalidSample` takes precedence.
Backend execution and result validation follow [BACKEND.md](BACKEND.md); backend defaults
cannot choose a method, estimator, units or missing-value policy.

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
or alias resolution. Empty/non-string units are invalid; Statistics assigns no business
meaning to an otherwise non-empty identifier. Singleton samples are valid, empty ones
are always invalid.

Sample keys, source references, dependence and business context belong to consumers,
not NumericSample. Statistics does not require or interpret them. Do not add subject,
anchor_dates, horizon, market, coverage, observation_keys, provenance or job_id to this
sample. Research retains them in its SampleBinding; unavailable/excluded market markers
never cross the numerical boundary.

## Results and diagnostics

Each typed result retains method identity, full parameters/estimator, actual derived
`sample_count`, unchanged `unit` and method-specific calculated payload. Counts are exact
nonnegative integers; calculated scalars must be finite binary64 values. No non-finite
successful result or implicit percentage conversion is permitted.

Method contracts define applicable diagnostics; no free-form metadata envelope is needed.
The initial methods are descriptive only: no independence assertion/test, confidence
interval or statistical significance inference.

## Stable failure categories

`StatisticalFailure` names the public failure family below, not an additional result variant
or a required fourth error category.

| Category | Meaning |
| --- | --- |
| `InvalidSample` | Illegal shape, empty sample, illegal/non-finite scalar or invalid unit. Never silently discard values. |
| `InvalidStatisticalSpec` | Unknown method, illegal parameters/order/types, or sample/spec unit mismatch. Compatibility is checked at compute time. |
| `CalculationFailure` | Valid inputs cannot produce a finite defined result, including arithmetic overflow, numerical execution failure or a backend result that violates the result contract. Retain method and readable reason. Never substitute another method or repaired sample. |

Wrong public object variants fail in the respective validation category. Consumers can
identify the three categories without parsing messages; exact exception hierarchy is an
implementation detail. Process termination is not a successful numerical result.

## Minimum acceptance obligations

Test invalid types/shapes, bool, empty sample/unit, NaN and both infinities; finite
representation conversion and overflow; duplicates; input immutability; unchanged opaque
units; unknown-tag preflight; compute-time revalidation and validation precedence.
Verify sample-free validate_spec returning None, compatibility failure only at compute
when a standalone spec is legal, both typed dispatch/result variants, derived count,
unchanged unit and stable failure categories, including invalid public object variants.
Method fixtures belong to the linked method contracts. Facade re-exports use
explicit aliases (`from pkg.module import Name as Name`); verify expected attributes
directly without introducing `__all__`. Executable evidence is in `tests/`; current
verification is recorded in [README](README.md).
