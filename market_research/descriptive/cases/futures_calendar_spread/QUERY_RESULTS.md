# Calendar Spread query results and association

Specializes [Application](APPLICATION.md). Owns the immutable Python query result
schema and statistical association; population policy remains in
[Relative Value](RELATIVE_VALUE.md). These are business carriers, not HTTP DTOs.

## Issue #13 compatibility and preparation evidence

The execution entrypoints in [Application](APPLICATION.md#explicit-execution-entrypoints-issue-13-target)
reuse these Result types and existing request.operation literals. Operation identifies
the analysis, not read-only permissions. Do not add an execution identity, require a
new Result version or change existing Demo Bundle bodies to support preparation.
The additive prepared-input attempts and failure diagnostics belong to
[Inputs](INPUTS.md#execution-preparation-and-diagnostics-boundary); they are retained
through the same observation_set/prepared_inputs association, not another collection.

`source_context` keeps its existing shape. Read-only query results retain the
read-only/separately-prepared-cache disclosure. Execution results instead disclose:
"Explicit execution may prepare incomplete caches through DataLake public services;
analysis uses validated complete final exports." This describes permission, not a
claim that Ensure ran on a hot cache. Other provider, independent-snapshot,
point-in-time metadata and financial limitations remain unchanged. Do not publish
raw Exports, attempts, UnitFailure reasons or exception text in source_context.
Existing captured source_context strings remain valid historical disclosures;
validators must not require a new text value for old Demo results.

## Requests and shared evidence

The case facade publishes `DailySpreadsRequest`, `HistoricalRelativeValueRequest`,
`DailySpreadsResult`, `HistoricalRelativeValueResult` and their nested typed carriers.
Requests retain exact product/date inputs, operation identity, and for Historical,
metric and owned binary64 `histogram_edges` (None when omitted). Operation, case,
definition and echoed request identify a result; no Run ID is created.

Each result retains one complete WP2 `observation_set`. `prepared_inputs` delegates
to this collection, so the WP2 `source_export_ref` literal
`prepared_inputs.futures_export` resolves directly against the result as well as
the collection. It is a local typed reference, never an external URI, digest or
expression to evaluate. Each Pair-day's rows and Slot evidence refer to this same
retained final Export and its exact request/coverage. No duplicate raw collection
is acquired or stored. `source_context` provides safe provider/exchange/Close
labels, immutable source/financial limitations and no credentials or storage paths.

Daily exposes `day` and `accounting` from its single-day collection. A closed date
has no pairs; an open empty universe has six not-applicable pairs. Valid zero
metrics remain zero; non-valid metrics remain absent.

Historical exposes `current_day`, `historical_days`, `historical_accounting`,
selected `metric`/`unit` and six ordered `PairRelativeValueResult` values. Every
natural date, closed status, candidate, excluded row and real contract transition
remains in the retained collection. `historical_days` excludes evaluation_date.
No continuous-contract price adjustment or PnL is inferred.

## Historical projections

Each pair has four ordered `HistoricalDistribution` objects: `0_7`, `8_21`,
`22_plus`, `all_stages`. A `HistoricalSamplePoint` references its original valid
Pair-day and its selected immutable WP1 metric; trade_date, actual rows, stage
and source evidence remain accessible through `observation`. Points are reused
between their stage and all-stage groups. `sample_dates` and `sample_count` are
read-only projections; duplicate numeric values retain separate points/dates.

Each distribution carries stage, metric/unit, candidate dates, OutcomeAccounting,
samples, sufficiency status, reason/warnings, optional NumericSample and typed
Quantile/Histogram analyses. Stage candidates include only observations with that
observed stage, including excluded nonpositive-price observations. Unstaged empty
universes occur only in all_stages accounting; never invent a stage for absence.
The all-stage group accounts for every open historical Pair-day. Its valid count
is the numerical sample count; closed dates are retained outside candidate counts.

N=0 gives `empty_sample` / `no_valid_historical_observations`, no NumericSample
or Statistics call. N=1..29 gives `small_sample` with a descriptive-only warning;
N>=30 gives `available`, without a reliability assertion. Histogram status is
`not_requested` if edges were omitted, `empty_sample` if requested with N=0, or
`available` with the full typed IntervalCount result including outside counts.

## Current assessments and numerical association

Each pair has `matching_stage` and `all_stages` CurrentAssessment carriers.
They retain kind, current Pair-day (None on closure), historical distribution,
status/reason/warnings and optional typed PercentileAnalysis. Matching-stage
selects the current Observation-owned stage even if that group's sample is empty.
It never substitutes all_stages. Closed/absent/excluded current values yield
`not_applicable` with their original reason and no percentile. All historical
summaries remain available. When the current stage is unknown, matching distribution
is None; the all-stage distribution still exists. Valid current observations use
the referenced distribution's sufficiency status and sample without alteration.

QuantileAnalysis, HistogramAnalysis and PercentileAnalysis retain the exact public
NumericSample, concrete Spec and typed Result. Association requires exact method,
estimator (where applicable), sample_count/unit, requested parameters, ordered
finite payloads and count accounting. Percentile must retain the one requested
current query, exact nonnegative integer L/E/G summing to N and a finite [0,1]
fraction. Research checks structure and association, never recalculates generic
quantiles, histogram counts or L/E/G/rank. Statistics is trusted for mathematics.
A wrong result type, method, unit/count, estimator or parameters is a classified
`statistical_failure`, never empty availability or a repaired successful result.

## Failure evidence

`CalendarSpreadQueryError` retains category, stage, dependency, safe reason,
method/date/Slots where applicable, validated InputEvidence, prepared inputs and
obtained ObservationSet where available. Preparation adaptation also preserves
optional reason_code, operation and immutable attempts with backward-compatible
None/empty defaults, under Inputs. A failure never carries a successful partial
business result. It adapts only the known WP2 classified
exceptions, public StatisticalFailure and local association violations. Causes
remain attached. Raw upstream exception text is not copied to its public reason;
programming exceptions propagate. Invalid query/statistical parameters use
`invalid_request` before service construction or calls.

## Daily underlying index result (DD-02 target)

Implemented in DD-02 WP-01. DailySpreadsResult adds required
`underlying_index: DailyUnderlyingIndexReference` and `underlying_index_evidence: DailyUnderlyingIndexEvidence`. Both are frozen,
slotted public carriers exported by the case facade, with tuple-owned sequence
fields. Existing observation_set, prepared_inputs, day and accounting retain their
meaning. HistoricalRelativeValueResult/current_day add neither field. WP-01 updated
Daily constructors/fixtures; no fabricated Python default reference is introduced.

DailyUnderlyingIndexReference contains `index_code: str`, `trade_date: date`,
`close: float | None`, `availability`, `reason_code: str | None` and
`failure_category: str | None`. Exact state combinations and legality belong solely
to [Daily Index Reference](DAILY_INDEX_REFERENCE.md). Identity/date bind to the
request and authority-governed selection; this is separate from PairObservation.

DailyUnderlyingIndexEvidence retains immutable per-dependency attempts with exact
SSE/Index requests, validated preliminary/final typed Exports and normal EnsureResults,
plus safe dependency/operation/reason and original exception association on failure.
Reuse existing acquisition evidence conventions where their types fit; do not insert
Index evidence into shared Calendar/Futures prepared inputs. An unreached dependency
has no attempt; a reached failure keeps its request and preceding validated evidence.
Malformed objects are never retained as validated proof. Evidence is caller-retained
in memory, with no new store, HTTP representation or persistence identity.

Classified reference failure is a successful Daily result with an explicit reference
state, a specialization of the whole-core failure rule above. Unknown defects still
propagate. Daily source_context keeps its shape and CFFEX core identity, adding accurate
independent SSE/Index snapshot and acquisition-permission disclosures; the reference supplies independent Daily futures–spot comparisons only.
Do not mutate shared SourceContext defaults used by Historical. Old captured disclosures
remain valid; validation never requires updated prose.

## Daily futures–spot results

DailySpreadsResult additionally requires `futures_spot_comparisons`, an immutable tuple
of frozen/slotted DailyFuturesSpotComparison carriers under the independent
[financial authority](DAILY_FUTURES_SPOT_COMPARISON.md). Each item contains product_code,
trade_date, slot, futures (the validated original row or None), underlying_index (the
same Daily reference), remaining_days, expiry_stage, signed_spread,
annualized_point_spread, annualized_spread_ratio (nullable floats), outcome, reason,
failure_category and its own definition_version. Source universe and reference evidence,
and safe calculation failure association, remain caller-retained internal evidence.
Open/closed item counts are four/zero, independent of existing six-pair accounting.
HistoricalRelativeValueResult and all shared observation/sample carriers are unchanged.
Daily source disclosure now distinguishes reference consumption by these independent
comparisons from its exclusion from calendar-spread and historical calculations.
