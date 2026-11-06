# WP4 Python analysis contract

Specializes [statistics scope](STATISTICS.md). The public case facade exports
`DistributionRequest`, `ComparisonRequest`, `analyze_distribution`, `compare_terms`,
`discount_runs` and their frozen result carriers. Each analysis request contains
an explicit nonempty analysis_id, metric, subject Slot/ordered canonical pair,
inclusive start/end within the source request, QuantileSpec and IntervalCountSpec.
MeanSpec is fixed and parameterless. Quantile/edges are mandatory; histogram units
must equal metric units. Invalid requests raise AnalysisRequestError retaining request.
Caller orchestration owns uniqueness of IDs across calls; no global registry exists.

DistributionResult retains request, original FuturesBasisResult (and thus full
coverage/proofs/definition/fingerprint), ordered candidates, eligible binding and
three MethodOutcome objects. Each retains original spec and original statistical
result or typed failure category/reason. Empty samples have no_eligible_sample and
never call Statistics. Association rejects result count/unit/method/parameter mismatches as
association_failure, retaining the raw result as failed association evidence.
Candidates retain every metric status/reason and Contract-day source object; counts are derived, never copied from another population.

ComparisonResult retains both candidate populations, ordered common dates, both
MethodOutcome sets and every dropped date with both original Slot-day objects.
Side computations use only the common date population and identical explicit specs.
No spread is computed. Empty intersections yield no_eligible_sample on both sides.

DiscountSummary retains explicit window/Slot, source and separate complete/censored
DiscountRun collections. Each run retains ordered Slot-day objects and traversed
ContractTransition objects, start/end and observed session count. Boundaries are
window, gap or non_discount; only non_discount proves an uncensored boundary.
A transition is traversed only when both endpoint dates lie in that run.
This API computes no run-length estimator and no output persistence or presentation.
