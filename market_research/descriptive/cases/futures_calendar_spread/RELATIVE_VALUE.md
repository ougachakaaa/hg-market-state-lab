# Historical Distribution and Relative Assessment

This contract owns the historical population and business association for
[the case](ARCHITECTURE.md). It consumes [Observations](OBSERVATION.md) and only
the root [Statistics public numerical API](../../../../market_statistics/CONTRACT.md).
Neither the frontend nor the case implements competing numerical algorithms.

## Fixed evaluation and comparable populations

A request fixes one product, `history_start`, `evaluation_date` and one metric.
Default metric is `annualized_spread_ratio`; `signed_spread` and
`annualized_point_spread` are explicit alternatives. All six pairs are returned;
pair selection for viewing is local presentation state. Historical observations
must satisfy:

```text
history_start <= trade_date < evaluation_date
outcome == valid
same product_code, ordered Slot pair and metric
```

There is no implicit lookback or pooled multi-product sample. Evaluation-day
observations are never part of their own reference sample, even if already cached.
For later evaluation dates reconstruct the cutoff-specific sample; never reuse a
full-window distribution as an earlier date's empirical percentile.

For each pair produce independent distributions for stages `0_7`, `8_21`,
`22_plus`, and `all_stages`. Each valid Pair-day contributes one equally weighted
value; repeated numeric values retain multiplicity. Preserve sample keys/dates and
observed counts separately from unavailable/excluded candidate accounting.
The all-stages distribution pools only that same product/pair/metric's stages.
It is contextual comparison, not a substitute for an empty matching-stage sample.

## Numerical consumption

Nonempty groups are adapted to `NumericSample` with the selected metric's exact
unit; Research retains sample keys and source linkage outside Statistics.

- Historical quantiles use `QuantileSpec` with fixed probabilities
  `[0, .05, .25, .5, .75, .95, 1]`, consuming the existing Type 7 result unchanged.
- Histogram is optional. An explicit `histogram_edges` request supplies actual
  boundaries in the selected metric's unit, shared across all groups in that
  request. Validate them through `IntervalCountSpec`; no automatic edge generation,
  density, quantile-derived binning or dropped overflow is authorized. When omitted,
  the histogram is `not_requested`, not an empty observed distribution.
- Current rank consumes the planned [Empirical Percentile method](../../../../market_statistics/EMPIRICAL_PERCENTILE.md)
  with the current valid metric as query. This capability is not yet implemented.

No direct NumPy import, local quantile interpolation, histogram or percentile
counting is authorized in Research. Statistics failures remain explicit analysis
failures with method/sample association; they are not normal empty samples.

## Relative Assessment and sample sufficiency

For a valid current observation, return two separately identified assessments:
its own expiry-stage historical group and the `all_stages` group. Each retains
current real contracts/value/stage, metric/unit, history bounds, actual sample
dates/count, estimator, ties counts and the fractional empirical percentile returned
by Statistics under its unique midrank method contract. Research does not derive
or recompute the returned rank. Frontend may
format the fraction as a percentage without changing its value or identity.

| Valid historical N | Distribution / assessment |
| --- | --- |
| 0 | `empty_sample`; quantile/histogram/percentile payloads absent, no Statistics call |
| 1–29 | `small_sample`; retain valid statistics/percentile with explicit descriptive-only warning |
| >=30 | `available`; still descriptive, with no assertion of independence or predictive reliability |

Threshold 30 is an interpretation cue, not a numerical legality rule or proof of
adequacy. Count is valid Pair-days, not distinct values or independent observations.
Report actual historical coverage, exclusions and each group's N. Never conceal a
small matching-stage N using a larger all-stages N.

If the evaluation date is closed or the current pair is absent/excluded, its current
assessment is not applicable with the explicit observation reason. Historical
distributions may still be returned. This differs from a valid current value with
an empty reference sample. No synthetic percentile, neutral score or date fallback.

Higher percentile describes a higher selected price relationship relative to the
stated historical population. For the long roll it may be described as relatively
more favorable under [the financial limits](DEFINITION.md); no high/low trading
threshold, forecast, waiting value, confidence interval or trade recommendation is
defined. Historical quantile values and a current value's empirical percentile
are different statistics and must have distinct labels and result fields.
