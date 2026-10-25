# Analyze public numerical contract

This contract specializes the [module authority](ARCHITECTURE.md). It owns the public
numerical model and operation semantics. These are conceptual interfaces, not prescribed
Python classes, field layouts, function names or synchronous/asynchronous mechanisms.

## Public models and operation

| Model | Responsibility |
| --- | --- |
| NumericSample | A numerical sample and the generic statistical context necessary to interpret it, including accountable sample quantity and applicable units/dependence context. It does not carry a requirement to understand market business fields. |
| AnalysisSpec | The requested numerical method and explicit method parameters; it neither acquires inputs nor defines financial variables or business populations. |
| AnalysisResult | The computed numerical result with method/parameter context, sample quantity and diagnostics sufficient to explain the calculation. It remains separate from the input sample. |
| AnalysisFailure | An explicit failure when statistical input, method parameters or calculation cannot legally complete under the applicable contract. |

```text
analyze(NumericSample, AnalysisSpec) -> AnalysisResult
```

This successful-operation notation does not hide `AnalysisFailure`. Whether failures are
represented as exceptions, result variants or another Python mechanism is not decided.
No consumer-specific request/result types or market identifiers are required by this API.
Consumers keep their own linkage between sample/result context and business observations.

Analyze validates its own public sample and method parameters even if a consumer already
validated them. It performs numerical calculation over the supplied sample, without
market-data acquisition, financial derivation or business population selection. It does
not mutate the consumer's observations or silently repair inputs by dropping values,
imputing facts, changing units or substituting a method.

## First statistical methods

| Method | Conceptual input and output responsibility |
| --- | --- |
| Quantile | Numerical sample plus an explicit collection of quantile points; report the calculated quantiles, sample quantity and relevant diagnostics under a declared estimator convention. |
| IntervalCount | Numerical sample plus explicit interval definitions; report counts and relevant sample accounting/diagnostics under declared interval rules. |

These are the initial capability directions, not a complete executable specification.
No quantile points, bucket defaults, estimator conventions, numeric representation or
mathematical library behavior are implicitly selected. No historical `shared.distribution`
formula, output shape or default is inherited.

## Failure ownership

Analyze owns the distinction between invalid numerical input, invalid/unsupported method
parameters, and a calculation that cannot legally produce a defined statistical result.
The applicable method contract must state which conditions fail and which have explicitly
defined valid results or diagnostics. Concrete classifications, thresholds, codes and
Python mechanisms remain pending; this authority creates no executable error taxonomy.

Empty or insufficient samples and undefined statistics must not be guessed into numerical
success. Invalid values must not be silently filtered to manufacture a successful result.
Legal exclusions, if any, require an explicit numerical contract and accountable counts;
Analyze cannot reinterpret a missing market fact or upstream failure as sample eligibility.
Consumers own how a statistical failure affects their execution, without rewriting its
statistical meaning.

## Pending statistical decisions and readiness

The statistical owner must settle the following before implementing each applicable method:

| Concern | Pending decision |
| --- | --- |
| Quantiles | Point domain/validation, interpolation and estimator convention, duplicate points and ordering where applicable. |
| Intervals | Endpoint validity/order, open/closed boundaries, overlap, repeated intervals and values outside all intervals. |
| Sample validity | Numeric representation, non-finite/illegal values, empty and insufficient samples, and failure versus explicitly valid outcomes. |
| Repeated values | How repeated sample values contribute to quantiles and counts; no implicit deduplication. |
| Accounting | Count denominators and any reported proportions, including overlap/outside-value accounting; no normalization default. |
| Statistical context | Representation and treatment of units, sample identity/reference and relevant dependence context, without consumer business semantics. |

These decisions belong to Analyze and any future narrow method authority reached from
this contract. A separate method document is warranted when a stable method-specific
contract is defined; this encoding does not create empty method scaffolds. Consumer
variable selection and business validity remain consumer-owned.

The statistical API and both methods are Expected Implementation Gaps. This contract
neither claims runtime readiness nor authorizes calculation using unresolved defaults.
