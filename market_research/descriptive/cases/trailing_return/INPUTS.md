# Trailing Return public inputs and availability

This contract specializes the [case authority](ARCHITECTURE.md) within
[UPSTREAM](../../../UPSTREAM.md). It owns the index case's fixed
`descriptive_missing_tolerant_v1` consumption policy. This is case semantics, not a new
runtime mode option, universal gateway or change to DataLake completeness.

## Design-time binding

| Required input | Selected public contract |
| --- | --- |
| Calendar and H preceding sessions | [Calendar SERVICE](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md), via [domain](../../../../data_lake/datasets/tushare_trade_calendar/ARCHITECTURE.md): `data_lake.datasets.tushare_trade_calendar.create_service()`, `TradeCalendarRange(exchange="SSE",start_date,end_date)`, view calendar, schema 1 |
| Index identity and daily facts | [Index SERVICE](../../../../data_lake/datasets/tushare_index_daily/SERVICE.md), via [domain](../../../../data_lake/datasets/tushare_index_daily/ARCHITECTURE.md), [FACTS](../../../../data_lake/datasets/tushare_index_daily/FACTS.md) and [TRADING_DAYS](../../../../data_lake/datasets/tushare_index_daily/TRADING_DAYS.md): `data_lake.datasets.tushare_index_daily.create_service()`, `IndexDailyRange([index_code],start_date,end_date)`, view index_daily, schema 1 |

SSE is Index Daily's published common calendar basis, never inferred from code suffix.
DataLake public facts and coverage suffice; no Snapshot Product is selected. No provider,
SDK, SQLite, Repository, internal planner or CLI/JSON interface is authorized. Runtime
failure never switches sources. Stock daily facts are absent from the published
[Dataset catalog](../../../../data_lake/DATASETS.md); see [readiness](../../ACCEPTANCE.md).

## Invocation and proof validation

For each required range, export first and validate even an incomplete view before any
ensure. If valid but incomplete, ensure that exact semantic range once, inspect and
retain its result/UnitFailures, then export the same range for final proof. No separate
coverage call, automatic retry or runtime Snapshot substitution. Discovery of an earlier
calendar block is a new range, not a failed-operation retry.

Calendar final Export must be complete. Calendar Ensure complete=false still leads to a
final Export check; if it remains incomplete, fail preparation. Any operation-level
InvalidRequestError/OperationError fails with public context; do not catch and recast as
missing. For Index, a normal partial EnsureResult is diagnostic, not immediate Job failure;
a final legal partial Export is admissible. Ensure complete retains DataLake's meaning.
Earlier Ensure success or failure is not proof of final Export availability.
Validate EnsureResult types, public counter equalities and UnitFailure identities/reasons
against the requested target under the producer contract. A malformed normal result is
InvalidPublicInput, not an admissible partial outcome; do not stitch its counts to a later
Export's snapshot.

Validate Dataset/view/schema, exact scope/window and all records under producer contracts.
Coverage counters must be nonnegative integers excluding bool; four categories sum to
requested_units, and complete exactly matches the public formula. Schema 1 is an integer,
not bool. Records are unique, legally typed, in the declared producer ordering, within
scope/window, and exactly match successful_units in count. Reject duplicate/conflicting
or illegal records rather than dropping them. Validate every numeric and metadata field,
not only close. Do not replace a malformed Export by an ensure attempt.

Calendar successful units require one legal row each, including closures, with matching
exchange, integer is_open 0/1 (not bool), legal dates/pretrade_date. requested_units
equals inclusive natural-day count on every Export; the final view also has that many
successful_units and zero other counters, with every natural date represented.
Index requested_units on every Export equals the retained full open-session count for this single
index; each available row has the selected canonical index identity and an expected open
date. len(records) equals successful_units; missing/pending/failed account for all absent
expected keys in aggregate. Coverage does not expose their per-key state. Any disagreement
with Research's complete calendar is InvalidPublicInput, not ordinary missing or closure.
Proof and payload belong to the same Export operation. No cross-call or cross-Dataset
common snapshot/freshness is promised.

## Calendar resolution and warm-up

1. Obtain complete SSE Calendar for the inclusive sample window. All open dates in
   ascending order are candidates; closures are neither candidates nor missing facts.
2. With no candidates, construct the zero-candidate set and do not request Index history.
   Retain calendar identity; ratios with zero denominators are Not Applicable and
   conversion fails NoEligibleObservations.
3. Otherwise let A be earliest anchor. Discover H opens strictly before A using adjacent
   complete Calendar ranges backwards. First request H preceding natural days, bounded
   by date.min. If insufficient opens, request the immediately preceding block of twice
   that width, doubling until H opens are known. At date.min insufficient sessions fail
   HistoryInsufficient; an unavailable/incomplete final block fails input_preparation.
   If A is date.min, fail HistoryInsufficient without constructing an invalid prior range.
   No arbitrary cutoff, weekday estimate, pretrade_date shortcut, price-row calendar,
   unknown-gap skipping or trimming candidates is authorized.
4. Let L be the Hth open before A, B the latest anchor. Retain the complete ordered
   sessions from L through B. Each candidate's lookback is H positions earlier. Acquire
   one IndexDailyRange L..B, including all open sessions, even intermediate sessions not
   used as endpoints. Never extend past explicit window end; future windows are rejected
   before I/O under Index's Asia/Shanghai current-date limit.
5. Compare final Index proof/records to this exact full session set. Absent daily rows
   under valid partial proof are unavailable facts, never closed days. Missing warm-up
   prices are allowed; missing calendar/history resolution is not. Index list_date is
   not the first possible quotation date and cannot trim warm-up or prove absence.

## Fact coverage

Expected fact units are distinct `(index_code, session_date)` daily-row keys for every
open session in L..B. Available units are the final Export's successful row keys. Keep
both ordered key sets and their set difference. Overall fact coverage is
`len(available_keys) / len(expected_keys)`, consistent with the final Index CoverageResult.
Warm-up coverage uses keys with date < A; sample coverage uses keys in the historical
window. Retain each numerator/denominator; zero denominators are Not Applicable. Do not
sum Calendar natural-day units with Index daily units or multiply facts by candidate uses.
Retain original Calendar and Index CoverageResults unchanged. An available non-positive
close counts as an available fact; endpoint business exclusion belongs to construction.

A final legal empty Index payload with positive expected units proves zero currently
available exported facts: retain all candidates, all Unavailable outcomes and 0% fact /
observation coverage. It does not prove why the source lacks rows, nor verify a human
index name without metadata. Require canonical request identity; a missing stock service,
invalid code representation and an absent cached row are different conditions.

Retain actual requests, final exports, preliminary export / Ensure diagnostics and exact
endpoint dependencies under [INPUT_IDENTITY.md](INPUT_IDENTITY.md). Failures preserve
obtained evidence without manufacturing successful preparation.
