# Daily underlying index reference

DD-02 authority, encoded in WP-00 and implemented in WP-01; current delivery status belongs to
[Roadmap](ROADMAP.md). Specializes [Inputs](INPUTS.md) and [Application](APPLICATION.md).
This document owns Daily reference selection, preparation and availability;
[Query Results](QUERY_RESULTS.md#daily-underlying-index-result-dd-02-target) owns its
immutable business carriers. HTTP projects these semantics without reclassification.

The existing [Definition](DEFINITION.md) and [Observation](OBSERVATION.md), including
signed_spread, annualized_point_spread, annualized_spread_ratio, delta_days,
near_dte_days and all three expiry stages, are unchanged.

## Selection and isolation

The sole price source is the public
[Index Daily Service](../../../../data_lake/datasets/tushare_index_daily/SERVICE.md),
`data_lake.datasets.tushare_index_daily`. Construct
`IndexDailyRange(index_codes=[index_code], start_date=trade_date, end_date=trade_date)`.
Explicit consumer selections follow the existing
[Futures Instrument mapping](../../../../data_lake/datasets/tushare_equity_index_futures/FACTS.md#3-underlying-market-contract-ownership):
IF → 000300.SH, IH → 000016.SH, IC → 000905.SH, IM → 000852.SH.
This is not a second instrument authority or permission to import private constants.
Every retained Futures row must agree with the selected underlying identity.
Closed/empty Futures days still use the authority-governed selection.

First complete the existing Calendar/Futures preparation and Observation construction;
only then prepare the Daily reference. Core failures remain whole-query failures and
do not start reference acquisition. Reference Close never enters financial computation,
Pair-day population, accounting, DTE or expiry stages. CFFEX and SSE are independent:
do not intersect calendars or skip SSE because CFFEX is closed.

Historical Relative Value, including current_day, never acquires this reference.
Shared prepare_inputs, prepare_inputs_for_execution, prepared carriers and pure
construction remain unchanged. No new financial module, Source, cache or generic
preparation framework is introduced.

## Daily-only preparation

Only Daily-specific Input Preparation performs reference I/O. Validate the request
before any factory or call; factories stay lazy. Daily query is export-only; Daily
execution permits conditional Ensure. Consume public Calendar/Index services only.

1. Export `TradeCalendarRange(exchange="SSE", start_date=trade_date,
   end_date=trade_date)`. Validate the full public envelope, scope/window, counters,
   complete formula, types and ordered records, including a partial view.
2. For legal incomplete Calendar, query returns unavailable/cache_incomplete.
   Execution Ensures the exact request at most once, validates the normal
   EnsureResult, then Exports again. Require complete final Calendar proof.
3. A complete closed SSE date proves not_applicable/non_trading_day; do not call
   Index. A complete open date proceeds to the exact IndexDailyRange Export.
4. Validate Index dataset/view/schema 1, canonical scope/window, coverage formula,
   ordering and all public row fields. Expected targets are one on this open SSE
   day; records must match successful_units. A complete Export must contain exactly
   the selected index/date row. Apply the same read-only incomplete outcome or
   execution's at-most-once Ensure/validated final Export sequence.
5. Use only the complete legal final row's close, in index points, unrounded and
   without adding a positivity requirement to the producer's finite-value contract.

Ensure only follows legal incomplete Export. A normal EnsureResult, including
complete=false or UnitFailures, always leads to final Export. Validate all public
Ensure counters, types, target identities and accounting under each Dataset contract.
An exception or malformed result stops this reference sequence immediately; never
Ensure to repair malformed evidence. Hot dependencies use one Export/no Ensure;
cold dependencies use at most two Exports/one Ensure. No coverage, per-pair fetching,
reacquisition of core inputs, retry loop or cross-request reference cache is added.

Index retains its own public SSE prerequisite. Internal Calendar calls do not count
as Case attempts and cannot be bypassed. Snapshots are independent: later prerequisite
failure or mismatch with retained SSE proof is explicit failure, without restarting
or changing targets. No common snapshot, acquisition time or freshness is promised.

## Availability and classified failure isolation

Only available has non-null close. All other states have close=null.

| availability | reason_code | failure_category | Meaning / proof |
| --- | --- | --- | --- |
| available | null | null | Complete legal same-day Index Export |
| not_applicable | non_trading_day | null | Complete SSE Calendar proves closure |
| unavailable | cache_incomplete | null | Query encounters legal incomplete SSE or Index Export |
| error | final_export_incomplete | incomplete_inputs | Execution final Export remains incomplete |
| error | credential_missing | upstream_unavailable | Public CredentialMissingError |
| error | cache_incompatible | upstream_unavailable | Public CacheIncompatibleError |
| error | operation_unavailable | upstream_unavailable | Other public OperationError, including wrapped prerequisite failures |
| error | malformed_export | input_contract_error | Invalid Export or retained identity/calendar association |
| error | malformed_ensure_result | input_contract_error | Invalid normal EnsureResult |
| error | upstream_request_rejected | input_contract_error | Producer rejects validated semantic request |

Catch public subclasses before OperationError. Known factory/operation failures use
this table. Classify by public type and validated evidence, never exception messages,
Provider internals or UnitFailure reason strings. Unexpected programming exceptions
propagate; no broad catch converts them into availability.

These classified failures are independent reference outcomes inside successful Daily
results, preserving all otherwise legal six-pair results. The prohibition on partial
successful core results remains binding. Malformed reference carriers/HTTP projections
are defects, not permission for HTTP to repair or reclassify business results.

Index requires one row per open target; it has no successful empty open-day quote.
Incomplete cache, delayed/unpublished Source data and preparation failure cannot be
called proven legal no-quote availability. Do not invent such a state or infer Source
causes. A complete legal final Export may succeed despite Ensure UnitFailures, retaining
diagnostics internally. Never substitute a prior date, Futures Close, zero or another index.

Retain immutable exact requests, validated preliminary/final Exports and normal
EnsureResults for each reached dependency, plus safe dependency/operation/reason and
exception association on failure. Unreached dependencies have no attempt; invalid
objects are never labeled validated evidence. Final Export is proof, not Ensure.complete.
HTTP exposes only its declared safe result fields, never raw evidence or exceptions.
