# Descriptive Analyze integration authority

This contract specializes the [Descriptive entry](ARCHITECTURE.md). Research owns the
outbound Sample Converter and business association of Analyze results. Numerical public
types and statistical semantics are owned only by [Analyze CONTRACT.md](../../market_analyze/CONTRACT.md).

## Outbound sample conversion

```text
Research ObservationSet
    → Research-owned conversion → Analyze NumericSample
    → Analyze-owned statistics → Analyze AnalysisResult
    → Research-owned association → Research JobResult
```

The conceptual operation is `convert(ObservationSet) -> NumericSample`. `NumericSample`
is Analyze's published input, not a parallel Research type. This notation does not select
a Python function name, class hierarchy or synchronous/asynchronous mechanism.

The converter must explicitly select the requested empirical variable and declared
Research population, validate observation validity and numerical legality, and map values
to the Analyze contract. Preserve the units, counts, sample identities, source linkage
and sample-dependence information required to interpret the statistics. For example,
overlapping horizons may create dependent observations; conversion must not erase relevant
dependence context or assert independence merely because the output is numeric.

Research retains the business association needed to relate numerical inputs and results
to the subject, metric, horizon, historical window and original observations. Analyze
receives only its generic numerical contract; it does not interpret these business fields.
The precise representation of generic statistical context belongs to Analyze's contract,
while business linkage belongs here. No universal metadata envelope is prescribed.

The converter must not implicitly:

- Recalculate market indicators, redefine a return formula or change the meaning/units of values.
- Fill missing market facts, conceal an upstream failure or silently drop unfavorable samples.
- Change the population without an explicit case rule and accountable exclusion reasons.
- Mutate the ObservationSet or acquire upstream inputs, including through hidden helpers.

Reconcile constructed, eligible and submitted sample counts and retain exclusion reasons.
Conversion validation does not replace Analyze's responsibility to validate its own public
input. Unsettled numerical validity rules must be resolved by the statistical owner;
the converter cannot invent filtering defaults to make a calculation succeed.

Each concrete Research case may use small local conversion logic. V1 introduces no
Converter Registry, generic Adapter Framework or cross-paradigm converter.

## Analysis calls and result association

Research calls only Analyze's public Python semantic boundary with `NumericSample` and
Analyze-owned `AnalysisSpec`. This grants no dependency on Analyze internals and implies
no HTTP service. One ObservationSet can be converted for several requested analyses;
changing only statistical parameters does not require reacquiring facts or rebuilding it.

Analyze returns its numerical `AnalysisResult` or exposes `AnalysisFailure` under its own
contract. Research retains the originating analysis request and sample association and
links the result, counts, diagnostics or failure context into the Research-owned
[JobResult](EXECUTION.md). Analyze results do not automatically become Research findings.
Research interpretation supplies subject, horizon, window, observation/input provenance,
method context and limitations; result assembly does not recalculate statistics.

Research execution control owns how an Analyze failure affects Job / Batch reporting;
it must preserve the statistical failure meaning and stage rather than silently changing
it to success, a different population or Skipped. Multi-analysis aggregation policy must
be settled in Execution authority before executor implementation.

The converter and result association remain Expected Implementation Gaps. There is no
reverse business dependency from Analyze to Research, DataLake or Snapshot.
