# Futures Basis public inputs and reproduction

This specializes the [case](ARCHITECTURE.md) and [Research upstream policy](../../../UPSTREAM.md).
Only Input Preparation acquires facts. Construction, resolution, conversion,
Statistics and report projection perform no hidden market I/O.

## Selected public boundaries

DataLake-first review finds sufficient source facts and completeness for this
case's strict Futures policy. No Snapshot product is selected or used as fallback.

| Required facts | Exact selected boundary |
| --- | --- |
| Candidate sessions | `data_lake.datasets.tushare_trade_calendar`: `TradeCalendarRange(exchange="CFFEX", start_date, end_date)`, calendar schema 1 |
| Index availability calendar | Same public service, `exchange="SSE"`, same window, calendar schema 1 |
| Futures Close, real identity, underlying, delivery month and lifecycle | `data_lake.datasets.tushare_equity_index_futures`: `FuturesDailyRange(product_codes=[product_code], start_date, end_date)`, futures_daily schema 2 |
| Underlying Close | `data_lake.datasets.tushare_index_daily`: `IndexDailyRange(index_codes=[underlying_index_code], start_date, end_date)`, index_daily schema 1 |

Use each module's public `create_service()` and semantic `export` / `ensure`
operations under [Calendar](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md),
[Futures](../../../../data_lake/datasets/tushare_equity_index_futures/SERVICE.md) and
[Index](../../../../data_lake/datasets/tushare_index_daily/SERVICE.md) contracts.
The underlying relationship is owned by [Futures facts](../../../../data_lake/datasets/tushare_equity_index_futures/FACTS.md);
all exported rows must agree with that mapping. An empty Futures population does
not permit inventing a contract or copying Snapshot's product listing date.

SSE is Index Daily's published common calendar basis; CFFEX remains this case's
observation calendar. Validate both independently. A CFFEX open date without an
SSE session has unavailable same-day underlying Close with reason
`underlying_session_closed`. An SSE-only session is retained upstream evidence
but not a Basis candidate. No prior-date alignment or silent calendar intersection.

## Acquisition and final proof

Validate the explicit request first. Prepare both exact-window calendars before
market exports, then Futures, then the mapped Index. For each dependency export
and validate its envelope and legal partial shape first. If incomplete, ensure
the same request once, retain/validate its outcome, then export the same request
again. No redundant coverage call is required; no ensure is allowed to repair a
malformed export. Fact acquisition belongs to later WP3, not WP0.

Final calendars must be complete, ordered, unique and cover every requested
natural date, including closures. Final Futures must have complete coverage for
every selected product × CFFEX open date. Validate dataset/view/schema, exact
scope/window, non-bool integer counters and their mutual accounting, complete
formula, all public row fields and metadata/lifecycle associations. Successful
Futures rows represent complete product-day sets, not one row per successful
unit. A successful zero-record date is proven empty only through complete
coverage and that date's absence from the complete ordered records.

Futures partial Export cannot prove failed dates' active metadata: fail preparation
with retained diagnostics. Do not retain a successful subset as a completed case,
borrow adjacent-day metadata, or use private catalog/storage access to fill this gap.
Complete Calendar/Futures with zero candidates or proven empty sets remains legal.

This case explicitly authorizes a legal partial final Index Export. Its target
count must match SSE sessions and its row count must equal successful_units;
successful rows are unique and ordered with all public fields legal. Missing
target identities are `underlying_fact_unavailable`, retaining public evidence
without claiming suspension or a Source-confirmed absence. Do not infer per-day
failed/pending status from aggregate counters. If ensure supplied attributable
UnitFailure diagnostics, retain them separately.

Proof and payload must come from the same final Export. Retain each dependency's
separate snapshot; no common acquisition instant or provider-current freshness is
promised. Validate records against the retained calendars; a discrepancy with a
producer's target accounting fails, rather than rebuilding its target population.
OperationError, illegal public facts, duplicate/conflicting identities, invalid
proof or unknown calendar fail input_preparation, never normal Missing. Legal
finite nonpositive closes survive public validation and are business-excluded
under [Observation](OBSERVATION.md). No filling, date shifts or source substitution.

## Retained evidence and actual input identity

Retain the fixed request, actual public requests, final typed Exports and coverage,
available preliminary/ensure diagnostics, metadata/row associations and definition
versions, or lossless immutable equivalents. A mutable cache, date range or digest
alone cannot reproduce inputs. Failure preserves obtained evidence without a
successful input fingerprint. No upstream private path, credentials, provider
response or SDK object is part of this evidence.

The case-owned input profile is `futures_basis_inputs_v1`. Its canonical payload is
the exact object `{profile, calendar_cffex, calendar_sse, futures, index}` containing
the four final public envelopes, including their scope/window, coverage and all
public record fields. Use only published semantic field names, not runtime class
names or private attributes. Encode recursively as follows:

- Dates become ISO `YYYY-MM-DD`; finite float fields become `["float64", value.hex()]`
  after binary64 adaptation. This retains signed zero and avoids display rounding.
- Public integer, boolean, string and None values remain JSON integer, boolean,
  string and null. Ordered sequences become arrays in validated producer order;
  public semantic carriers become objects of their published fields.
- Serialize UTF-8 JSON, without BOM or trailing newline, `sort_keys=true`,
  `ensure_ascii=true`, compact separators `(',', ':')`, and no NaN/Infinity.
  The lowercase hexadecimal SHA-256 of these bytes is the input fingerprint.

Keep the canonical bytes with the retained semantic evidence. Preliminary attempts,
acquisition times, runtime IDs, analysis parameters and local paths are excluded
from this payload. Request identity and actual input identity remain separate;
changed final facts/proofs change the payload even under the same request.
This is a case encoding, not a generic serialization or artifact framework.

WP3 must verify malformed proof rejection, incomplete Calendar/Futures failure,
legal partial Index accounting, same-date alignment, empty populations, calendar
mismatch, metadata consistency, retained failures and an independent canonical
bytes/digest fixture. Real IM acceptance records exact window, facts and evidence;
it must not be replaced by synthetic fixture evidence.
