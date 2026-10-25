# Trailing cumulative return case authority

This is the first concrete Descriptive case, not a generic case framework. It specializes
[Observation](../../OBSERVATION.md), [integration](../../ANALYZE_INTEGRATION.md),
[execution](../../EXECUTION.md) and [public upstream policy](../../../UPSTREAM.md).
Status: Implementation Ready for the explicit semantics below; runtime and real-data
acceptance are Expected Implementation Gaps, not completed capabilities.

## Fixed question and observation identity

Metric identity/version is `trailing_cumulative_return_v1`, with no additional metric
parameters (explicit empty parameter set). Subject is one required full canonical
`index_code` accepted by the Index Daily public contract. CSI1000 is the representative
research target, not a name-to-code default. Neither its bare symbol nor a guessed suffix
is accepted. The current published contract does not establish its exact code; the
real-data acceptance must verify the supplied code against public index metadata.

Horizon H is a strictly positive integer number of trading sessions, excluding bool.
The sample window `[start_date,end_date]` is explicit and inclusive; no 2020–2025 default.
Each H/window is an independent Job with one scalar observation per candidate trading
day T, not a multi-horizon wide table. Anchor T is the return's ending day:

```text
return(T,H) = close(T) / close(T-H) - 1
unit = decimal_ratio
```

`T-H` is H positions earlier in the ordered legal trading sessions, not H calendar days.
Use the actual two close facts, not Source pct_change, pre_close, compounded daily
percentages or a forward return. Binary64 division then subtraction, without presentation
rounding; 0.015 represents +1.5%.

The stable Job identity tuple is `(trailing_cumulative_return_v1, index_code,
empty_metric_parameters, H, trading_sessions, start_date, end_date,
anchor=end_session, bounds=inclusive)`. The definition version fixes formula, unit,
SSE session basis and eligibility policy. Observation key is `(job_identity,T)`;
candidate and outcome ordering is ascending T. Changing inputs' actual facts changes
provenance, not the fixed business question. Changing AnalysisSpec changes no observation
identity. No random ID or execution timestamp enters either key.

## Design-time public capability binding

| Required input | Reviewed and selected public boundary |
| --- | --- |
| Session dates and preceding H sessions | [Calendar domain](../../../../data_lake/datasets/tushare_trade_calendar/ARCHITECTURE.md) → [Calendar SERVICE](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md): `data_lake.datasets.tushare_trade_calendar.create_service()`, `TradeCalendarRange(exchange="SSE",start_date,end_date)`, view `calendar`, schema 1 |
| Index identity, close at anchors/lookbacks | [Index domain](../../../../data_lake/datasets/tushare_index_daily/ARCHITECTURE.md) → [Index SERVICE](../../../../data_lake/datasets/tushare_index_daily/SERVICE.md), [facts](../../../../data_lake/datasets/tushare_index_daily/FACTS.md), [session prerequisite](../../../../data_lake/datasets/tushare_index_daily/TRADING_DAYS.md): `data_lake.datasets.tushare_index_daily.create_service()`, `IndexDailyRange([index_code],start_date,end_date)`, view `index_daily`, schema 1 |

SSE is the Index Dataset's published common session basis, not an exchange inferred
from the index suffix. These services supply the required business facts and verifiable
completeness; no Snapshot Product preparation is needed. DataLake is sufficient, so no
Snapshot service is selected. Failures never authorize runtime Snapshot fallback.
Research calls no providers, private storage, internal planners or Repository IDs.

## Input preparation and warm-up

Use the following minimum public invocation sequence for each required range: export;
if incomplete, ensure that exact range, inspect its outcome (including unit failures),
then export that same range. An ensure failure/incomplete outcome fails the Job; do not
continue with partial facts. A final export must independently prove complete valid
facts. No separate coverage call is required. Do not retry automatically. Fact discovery
of an earlier calendar range is not a retry of a failed operation.

For each export validate Dataset/view/schema, exact canonical scope and inclusive
window, coverage counters/complete and payload together, using that operation's own
coverage. Validate unique identities, required fields/types and expected rows under
the selected public contract. Calendar must contain one row per natural day, including
closures, with integer is_open (not bool). Index must contain one legal public row per
required session for this index. Do not stitch proof from another operation to its rows.

1. Obtain a complete SSE Calendar view for the sample window. Candidate anchors are
   exactly its open dates in ascending order. Nontrading dates are not candidates or
   exclusions. Missing calendar rows are input failure, not nontrading days.
2. If there are no candidates, construct a zero-candidate set; do not acquire unnecessary
   Index history. Conversion reports NoEligibleObservations; there is no successful
   statistical Job for an empty window population.
3. Otherwise let A be the earliest candidate. Discover H open sessions strictly before A
   by requesting complete adjacent Calendar ranges backwards. First request the preceding
   H natural days, bounded by date.min; if insufficient open days, request the immediately
   preceding block of twice that natural-day width, and continue doubling until H earlier
   opens are known. Never estimate weekdays or use Index rows/pretrade_date to fill a
   calendar gap. At date.min, insufficient sessions fail HistoryInsufficient; an incomplete
   or unavailable discovery block fails input_preparation immediately. No arbitrary
   lookback cutoff or silent anchor trimming is allowed.
4. Let L be the Hth open session before A in the complete discovered calendar. Retain the
   complete ordered session sequence from L through the latest anchor B. For each anchor,
   select the session H positions before it. Acquire the single IndexDailyRange from L
   through B, covering warm-up and the observation window. Every open session in that
   range requires its complete daily row under the Index service contract, even if its
   close is not used by a particular anchor. No request extends past the explicit window
   end. Windows ending in the future are rejected before I/O under Index's public limit.
5. Compare Index dates/identity to the retained Calendar session sequence and validate
   both public views. A disagreement or an absent daily row fails input_preparation.
   Separate calls do not guarantee a common snapshot or provider-current freshness.

History before the sample window is a required input dependency. Index list_date is not
the first possible historical quotation date and must not trim warm-up. Missing prices
before the window, including unavailable pre-inception history, fail required input
preparation; they are not legitimate observation exclusions. Public InvalidRequestError,
OperationError and unit failures retain their meaning/context under execution's upstream
failure mapping. Research does not handle tokens or storage paths.

## Eligibility and failures

After complete validated input preparation, account for every candidate exactly once:

| Condition at candidate T | Outcome |
| --- | --- |
| Both required closes strictly positive and computed return finite | Eligible with the scalar return and key |
| Either required close <= 0 in an otherwise valid complete public view | Excluded: `non_positive_close`, retaining which endpoint(s) and actual values; positive index price ratio is undefined for this case's intended interpretation |
| Missing/null/non-finite/illegal required daily fact or duplicate identity | Input failure, never exclusion; the upstream public contract does not admit these as complete legal rows |
| Finite positive closes but division/subtraction yields non-finite result | ObservationConstructionFailure; do not silently exclude or clip |

This is the complete V1 exclusion policy; no outlier trimming, volume filter, winsorizing,
independence sampling or extra converter filter exists. All-excluded populations yield
a valid ObservationSet but fail conversion with NoEligibleObservations. Reasons retain
all offending endpoints in one exclusion outcome rather than counting an anchor twice.
Counts obey the ObservationSet conservation rule. Both gain and loss values and repeated
returns are legal; an H-session loss is a decimal ratio, not percentage points.

Dependence context records H, ordered anchors, their H-session start/end spans, and that
different observations can share daily inputs/overlapping spans (especially H>1), while
distinct windows/Jobs can reuse facts. Research carries this into SampleBinding and
interpretation. The statistics describe this historical population; no IID, causality,
significance, prediction or trading conclusion follows automatically.

## Actual input identity and reproducibility

Retain the exact consumed public Calendar and Index views in the Job's in-memory input
context, plus actual requests, schema versions, coverage outcomes and derivation identity.
ObservationSet and binding reference this context. Failed preparation retains whatever
request/outcome evidence was obtained, without manufacturing a successful input identity.
No mandatory persistence, upstream internal hash or content-addressed artifact is required.

For successful preparation, define `trailing_return_inputs_v1` fingerprint as SHA-256 of
UTF-8 compact JSON (no BOM, no whitespace separators, ensure_ascii=true) for an outer array:

```text
["trailing_return_inputs_v1", calendar_slices, index_slice_or_null]
calendar slice = [dataset, view, export_schema_version,
                  exchange, start_date, end_date, rows]
calendar row = [exchange, cal_date, is_open, pretrade_date_or_null]
index slice = [dataset, view, export_schema_version,
               [index_code], start_date, end_date, rows]
index row = [index_code, symbol, name, market, publisher, category, trade_date,
             open, high, low, close, pre_close, change, pct_change, volume, amount]
```

Use the final complete exports actually consumed for window/discovery blocks and Index
range, not preliminary incomplete exports. Sort calendar slices by (start_date,end_date,
exchange); rows by cal_date; Index rows by (index_code,trade_date). Encode dates as
YYYY-MM-DD, absent fields as JSON null, integers as JSON integers, every public floating
number as its Python binary64 float.hex() string (including signed zero), and text
unchanged with no Unicode normalization. This defines exact bytes without decimal float
format ambiguity. The successful coverage proof and earlier ensure/export outcomes are
retained as execution context but not mixed into the business-fact hash. For no candidates,
index_slice is null and the complete sample-window Calendar slice is still fingerprinted.

The fingerprint covers actual consumed public rows, including calendar discovery padding
and Index metadata, with no private SQLite paths/IDs or provider transport values. This
deliberately fingerprints the acquired public input slices, not just the two price fields.
Reordering semantically identical returned collections before canonical sorting preserves
the hash; changing a consumed fact changes it. Re-fetch does not guarantee the same hash.
Exact rerun requires retaining these facts (or an independently immutable verified copy);
a fingerprint alone cannot reconstruct them. In-memory results retain facts during their
lifetime; exporting/durable retention is outside this task and must not be claimed.

## Direct implementation acceptance

| Scenario | Expected outcome |
| --- | --- |
| Five ordered sessions with closes `[100,110,121,110,121]`; last three anchors, H=2 | Ordered returns `[121/100-1,110/110-1,121/121-1]`, unit decimal_ratio, three eligible distinct keys |
| Holiday/weekend between sessions | H uses session positions, no synthetic observations on closed days |
| One-day window with enough earlier sessions | One candidate; required warm-up acquired outside window |
| Backward discovery needs another block | Complete adjacent block requested; exact Hth prior session selected |
| Missing/incomplete Calendar or Index warm-up, including pre-inception gap | Failed Job at input_preparation; no normal exclusion, no Analyze attempt |
| Complete rows with zero/negative required close | Explicit non_positive_close exclusion; other candidates conserved |
| Positive inputs overflow return | Failed observation_construction, no clipped scalar |
| Empty candidate / all excluded | Valid accounted set; conversion fails NoEligibleObservations |
| Shuffled rows / changed close or public metadata | Same hash after sorting / changed hash after fact change |
| H/spec/window changes | Observation identity changes for H/window, not for spec; dependence retained |

First real-data end-to-end acceptance must supply a code whose returned public metadata
verifies CSI1000 (not just a plausible string), explicit historical dates and H, quantile
points, interval edges in decimal_ratio, unique request IDs and failure policy. Obtain
complete public Calendar/Index views including warm-up, independently check anchor/input
pairs and formula, assert total candidate/exclusion/sample accounting and both result
associations, retain exact facts/fingerprint, and verify Job/Batch success. Use an explicit
small historical window with available warm-up; no hardcoded unverified symbol or implicit
date defaults. This acceptance is a future implementation/live-data gate, not run here.
