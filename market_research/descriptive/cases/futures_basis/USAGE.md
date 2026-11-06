# Futures Basis statistics usage

Usage-only; semantics enter through [Case](ARCHITECTURE.md) and
[analysis contract](STATISTICS_API.md). Run from repository root's Poetry environment.
The following is a real-market Python example; public preparation may obtain missing
facts through the configured DataLake services. All dates and numerical parameters
are explicit. Existing WP3 observations can be passed directly instead.

```python
from datetime import date
from market_statistics import QuantileSpec, IntervalCountSpec
from market_research.descriptive.cases.futures_basis import (
    FuturesBasisRequest, DistributionRequest, ComparisonRequest,
    observe_futures_basis, analyze_distribution, compare_terms, discount_runs,
)

start, end = date(2026, 10, 12), date(2026, 10, 23)
observations = observe_futures_basis(FuturesBasisRequest("IM", start, end))
points = QuantileSpec([0, .25, .5, .75, 1])
edges = IntervalCountSpec([-1000, -500, -100, 0, 100, 500, 1000], "index_points")
request = DistributionRequest("im-m0-basis", "M0", "basis_value", start, end, points, edges)
result = analyze_distribution(observations, request)
print([(m.spec, m.result, m.failure_category, m.reason) for m in result.methods])
print({s: result.count(s) for s in ("eligible", "unavailable", "excluded", "not_applicable")})
print([r.identity for r in result.binding])
print(result.source.prepared.input_fingerprint)
comparison = compare_terms(observations, ComparisonRequest(
    "im-m0-m1-basis", ("M0", "M1"), "basis_value", start, end, points, edges,
))
print(comparison.common_dates, comparison.dropped)
runs = discount_runs(observations, "M0", start, end)
print(runs.complete, runs.censored)
```

For `basis_ratio` or `annualized_basis_ratio`, explicitly supply edges in
`decimal_ratio`, e.g. `[-1, -.1, -.01, 0, .01, .1, 1]`. The three methods are
Mean, Quantile and IntervalCount, in that order. There are no default quantile
points or edges. Inspect each method's failure_category before interpreting it.
Empty eligibility gives `no_eligible_sample`; histogram outside counts retain the
full eligible denominator. Annualized expiry days are Not Applicable.

`source.prepared` exposes separate CFFEX/SSE natural-date coverage, Futures
product-day and Index-session coverage and original proofs. `source.accounting`
contains base and all metric populations for the full source window; distribution
`candidates` and `count` cover the requested analysis subwindow. Every candidate
retains status/reason and original Contract-day/source references. Comparisons'
`candidates` and `dropped` retain both sides' original outcomes; both computed
populations use exactly `common_dates`.

Complete runs and censored fragments are separate collections. The fragment's
observed session count is a lower bound, not a complete duration. Slots share
underlyings/dates; neither daily levels nor runs assert independent draws. This
short window is an E2E check and supports no long-term inference.

No production evidence-file reader, formal CLI, HTTP endpoint, persistence or
report renderer is provided. The test-only offline replay of retained WP3 caches
and independently checked real results is documented in [WP4 acceptance](WP4_ACCEPTANCE.md).
