# Futures Basis descriptive statistics scope

This is SD09's canonical owner for [futures_basis_v1](ARCHITECTURE.md), consuming
[Slot-day observations](OBSERVATION.md). Numerical sample legality, Quantile and
IntervalCount remain owned by [Statistics](../../../../market_statistics/CONTRACT.md).
These are descriptive historical populations, with no iid, predictive, causal,
confidence-interval or significance claim.

## Minimum Week 1 outputs

| Output | Population and required interpretation |
| --- | --- |
| Basis distributions | Separately for `basis_value` and `basis_ratio`, one product/Slot/window; all and only that metric's Eligible days |
| Annualized distribution | Same, for `annualized_basis_ratio`; report expiry-day Not Applicable separately and sensitivity near expiry |
| Term structure comparison | All six unordered Slot pairs in M0/M1/Q1/Q2 order, separately for each metric, using common Eligible dates |
| Slot-level persistence | Observed consecutive Discount spans on the complete CFFEX calendar; complete runs and censored fragments separated |
| Data quality / coverage | Per-source units/proofs, per-Slot/base/metric candidate accounting, missing/exclusion/Not Applicable reasons and common-date sample loss |

For each of the three metrics deliver Quantile and explicit-edge IntervalCount
distributions and an arithmetic mean. Mean is a required WP4 addition to Statistics,
not an algorithm to copy into Research. The Statistics owner must define its
method contract, typed spec/result, backend and numerical failure/conformance
tests before runtime extension, under its [extension policy](../../../../market_statistics/ARCHITECTURE.md#extension-boundaries-stat-07-and-stat-08).
WP4 implements Mean under its independent Statistics authority and public API.

No distribution pools Slots, products or metrics. Histogram frequencies retain
Statistics' full eligible-sample denominator, underflow and overflow; the chart
does not recalculate them or infer automatic edges. Sample window means the
explicit inclusive research dates, not first/last available quote dates.

## Explicit requests, adaptation and association

Each analysis fixes a unique caller-supplied analysis ID, case request and actual
input identity, metric, Slot (or ordered pair), inclusive window, requested
numerical methods and parameters. Quantile points and IntervalCount edges are
explicit; there are no automatic bins, method recommendations or hidden default
parameters. Means have no consumer-selected market estimator; their legal
spec is Statistics-owned. Comparative distributions use identical points and
actual edges for both members of a metric/pair.

The case-owned adapter emits the public NumericSample of finite Eligible values
in ascending trade_date order, preserving duplicate values and unchanged units.
Keep an equally ordered binding of Slot-day keys and Contract-day/input references
outside Statistics. For each result retain the original spec/result, analyzed
keys, metric/window/subject, candidate and outcome counts, reason records and
source identity. Verify exact positional linkage and sample_count on association;
do not recompute statistical values to validate or display them.

Only NumericSample and legal StatisticalSpec cross the Statistics boundary.
No Horizon, observation ID, market calendar, source metadata or grouped/temporal
sample shape is added to Statistics. Empty eligible samples produce an explicit
`no_eligible_sample` analysis outcome with diagnostics, never a zero mean or empty
successful Statistic. Statistics failures remain analysis failures with their
public category; one failed method is not another successful method.

## Common-date term comparison

For every metric and Slot pair, candidates are the same CFFEX session dates in
the requested window. The paired Eligible set is the intersection of the two
metric-specific Eligible date sets. Submit the two values on exactly these dates
as two scalar samples, in identical date order, and associate both results to
the same common-date binding. This is paired population selection, not a new
paired numerical method. Compare their distributions and means; no undeclared
spread formula or statistical significance test is introduced.

Retain the candidate dates, each side's original outcome accounting, common
eligible count and dates dropped from common eligibility with both sides' reasons.
An empty intersection is no eligible comparison, not two independent historical
means. Report that other per-Slot distribution panels may use larger populations.

## Slot-level Discount runs

Use the sign of `basis_value`, equivalent to `basis_ratio` for legal positive
underlying prices. D=0 does not interrupt a run when the raw Basis remains valid.
On ascending CFFEX candidate dates, each Eligible Discount extends the current
observed span. Eligible Parity/Premium terminates it and proves a non-Discount
boundary. A real-contract switch does not interrupt a Slot-level run.

Unavailable, Excluded or Not Applicable base outcomes break the observed span;
never bridge a gap or assume its sign. Window endpoints also bound observation
support. Retain for each nonempty span: product/Slot, start/end dates, ordered
Slot-day keys, observed length in trading sessions, traversed contract transitions,
left/right boundary kind, and `left_censored` / `right_censored` flags. A flag is
true when that side reaches the window edge or an ineligible gap rather than an
observed Eligible nonnegative day. A span is complete only if both flags are false.
Do not fetch outside-window prices solely to remove censoring.

Summarize complete runs separately from censored observed fragments. If applying
Quantile/IntervalCount to lengths, use separate samples with unit `trading_sessions`
and explicit parameters; no empty sample reaches Statistics. A censored length is
an observed lower bound, not an estimate of total uninterrupted duration. Do not
combine complete and censored values into an unlabeled run-length distribution,
infer survival probabilities or annualize run lengths. Weekends and holidays add
no sessions and do not split a run.

## Acceptance and interpretation

Every reported analysis identifies subject/Slot, window, metric/unit, candidate
and Eligible population, missing/exclusion/Not Applicable accounting, exact method
and parameters, source association and limitations. Report Dependence: Slot values
share underlyings and market dates; run lengths and daily levels are not independent
draws. Annualized and raw comparisons may use different date populations.

WP4 fixtures must verify order/multiplicity and exact keys, all three metrics,
expiry-day sample differences, pairwise common-date equality and empty intersection,
full histogram accounting, mean delegation, no empty numerical calls and failure
association. Run fixtures cover negative→zero/positive, contract switches within a
run, holidays, missing/excluded days, both window boundaries, all-negative windows,
no negative days and complete versus censored samples. Numerical algorithm tests
belong to Statistics; Research tests verify population, invocation and association.

WP4 typed runtime contract: [Python analysis API](STATISTICS_API.md). Mean is now owned by [Mean authority](../../../../market_statistics/MEAN.md).
