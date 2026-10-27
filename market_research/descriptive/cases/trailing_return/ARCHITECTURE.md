# Trailing cumulative return case authority

This first concrete Descriptive case specializes [Observation](../../OBSERVATION.md),
[integration](../../STATISTICS_INTEGRATION.md), [execution](../../EXECUTION.md) and
[public upstream policy](../../../UPSTREAM.md). Status: Implementation Ready for the
index binding below. The independent Observation runtime is implemented; actual checks
and the live-data gate are recorded in [Acceptance](../../ACCEPTANCE.md).

| Concern | Canonical owner |
| --- | --- |
| Fixed question, identity, formula and eligibility | This document |
| Public binding, Calendar discovery, partial Export validation and fact coverage | [INPUTS.md](INPUTS.md) |
| Retained evidence and versioned deterministic fingerprint | [INPUT_IDENTITY.md](INPUT_IDENTITY.md) |
| Cross-contract scenarios, reconciliation and readiness | [Acceptance](../../ACCEPTANCE.md) |

## Fixed question and observation identity

Metric identity/version remains `trailing_cumulative_return_v1`, with explicit empty
metric parameters. This case specializes the asset-agnostic subject to one required full
canonical `index_code` accepted by Index Daily. CSI1000 is a representative target, never
a name-to-code default. No bare symbol or guessed suffix is accepted. Live acceptance must
verify the supplied code against public index metadata; published authority does not
establish that exact code. Stocks and futures need independent case bindings and price
semantics; this formula does not silently authorize them.

H is a strictly positive integer (not bool) number of trading sessions. The historical
window [start_date,end_date] is explicit and inclusive; no date default. Each H/window is
an independent scalar-per-anchor Job. Anchor T is the return ending session:

```text
return(T,H) = close(T) / close(T-H) - 1
unit = decimal_ratio
```

T-H is H positions before T on the complete selected SSE calendar, never on available
price rows or natural days. For open D0..D4, H=2 and T=D3, lookback is D1 even if D1 has
no quotation; D0 cannot replace it. Only the two endpoint closes are required to compute
this metric. Missing intermediate quotations do not invalidate a candidate with both
endpoints available. Input-range fact coverage is still independently reported.
Use actual closes, not pct_change, pre_close, compounded daily percentages or forward
return. Compute binary64 division then subtraction without presentation rounding;
0.015 means +1.5%.

Stable Job identity remains `(trailing_cumulative_return_v1, index_code,
empty_metric_parameters, H, trading_sessions, start_date, end_date,
anchor=end_session, bounds=inclusive)`. This revision retains metric formula/unit and
SSE basis; it supersedes the former strict input consumption and two-outcome policy.
Results under the revision carry input profile `trailing_return_inputs_v2`; retained
historical v1-profile results must not be reused as v2 results on business identity alone.
Observation key is `(job_identity,T)`; candidates/outcomes sort ascending T. Actual input
changes affect provenance, not the question; StatisticalSpec affects neither identity nor
observation keys. No execution time or random identifier enters those identities.

### Public direct-job preflight

`market_research.descriptive.cases.trailing_return.validate_job(job) -> JobIdentity`
is the pure public preflight boundary for this case. It reuses the same existing
fixed-request/case validator as preparation, with the current Asia/Shanghai date limit,
and returns the existing structural identity above. It performs no upstream service
creation, acquisition or mutation and offers no option to disable current-date checks.
Invalid fixed requests raise InvalidObservationRequest. It introduces no new formula,
identity or input policy. The [Single Job contract](../../JOB_EXECUTION.md) owns
InvalidPlan translation and analysis-spec/unit preflight.

## Computability and eligibility

After validating all public inputs, resolve every candidate's exact calendar T-H, then
inspect required endpoints in deterministic order: anchor T, lookback T-H.

| Condition | Outcome |
| --- | --- |
| Either endpoint daily row absent in a validated partial Export | Unavailable; retain every missing endpoint dependency, once per candidate |
| Both endpoints present legally, either close <= 0 | Excluded `non_positive_close`; retain all offending endpoint identities and actual values |
| Both endpoints strictly positive and result finite | Eligible with calculated scalar |
| Any exported row has null/non-finite/illegal fields or duplicate/conflicting identity | InvalidPublicInput at input_preparation, even if that row is not an endpoint |
| Legal positive endpoints produce non-finite division/subtraction | ObservationConstructionFailure, never clipping/exclusion |

Missing takes precedence over business exclusion if one endpoint is absent and the other
non-positive: required facts are not all available, so the candidate is Unavailable;
retain available endpoint facts in context. Required fact identity is
`(tushare_index_daily, index_daily, 1, index_code, trade_date, close)` plus endpoint role.
For an absent daily row use reason `daily_fact_unavailable`, referencing the final Export,
its coverage and expected session key. This public Export does not identify per-key
missing/pending/failed state; do not infer it. Correlate any Ensure UnitFailure by its
public identity and preserve its reason as a diagnostic, not an asserted market event.
Two missing endpoints produce two dependencies but one Unavailable count. A missing fact
shared by several anchors appears in each affected outcome. Intermediate missing rows
appear in fact coverage even where no candidate depends on them.

No outlier trimming, volume screen, winsorizing or converter filter is authorized.
All-excluded/all-unavailable sets are valid; conversion fails NoEligibleObservations.
Dependence context records H, ordered anchors, exact start/end spans and shared/overlapping
inputs, including across Jobs. No IID, causality, prediction or trading claim follows.

## Direct implementation acceptance

The mandatory scenarios A-H and boundary cases are owned by
[ACCEPTANCE.md](../../ACCEPTANCE.md). Also verify exact ordered returns for complete
closes [100,110,121,110,121], H=2, last three anchors:
[121/100-1,110/110-1,121/121-1], with three distinct keys and unchanged decimal_ratio.
Verify discovery doubling, date.min history exhaustion, one-day windows, exclusions,
overflow and canonical fingerprint fixtures. These are covered by the Observation
behavior tests; they do not establish live acceptance or downstream analysis readiness.

First real-data end-to-end acceptance supplies a metadata-verified CSI1000 code,
explicit historical dates/H, quantile points, decimal_ratio interval edges, unique request
IDs and failure policy. Obtain valid Calendar/Index views including warm-up, independently
verify endpoint pairing/formula, total outcomes and sample mapping, both analyses and
associations, retained facts and v2 fingerprint. A controlled partial-data acceptance must
also demonstrate partial Job Success when all required analyses succeed, and zero-eligible
conversion failure with retained coverage. Never modify real user caches to create gaps.
