# Price Segmentation V1 public inputs

This contract specializes the [case](ARCHITECTURE.md) and [Research upstream policy](../../../UPSTREAM.md).
Input Preparation alone performs market I/O. DataLake-first review selects the published
[Index Daily service](../../../../data_lake/datasets/tushare_index_daily/SERVICE.md) and
[Calendar service](../../../../data_lake/datasets/tushare_trade_calendar/SERVICE.md):

| Fact | Public boundary |
| --- | --- |
| Calendar | `data_lake.datasets.tushare_trade_calendar.create_service()`, `TradeCalendarRange("SSE", start_date, end_date)`, calendar view schema 1 |
| Index Close | `data_lake.datasets.tushare_index_daily.create_service()`, `IndexDailyRange([index_code], start_date, end_date)`, index_daily view schema 1 |

SSE is the Index Dataset's published common calendar basis, not inferred from code suffix.
Public facts suffice; no Snapshot fallback, private provider, storage, CLI or JSON is used.
No warm-up, horizon, data beyond the explicit inclusive range, or cross-source snapshot
freshness guarantee is implied. Index Daily disallows a future end date according to its
Asia/Shanghai operation-time rule; reject illegal requests before market I/O.

## Acquisition, validation and failure

Export the exact calendar range first. Validate the public envelope, exact scope/window,
view/schema, types, ordering, identities, coverage counters and record accounting even
if incomplete. If a valid export is incomplete, ensure the same range once, retain and
validate its result, and re-export that same range for final proof. Require complete final
Calendar, one valid record for every natural date including closures. Derive the ascending
open-session dates solely from that proof; fail if fewer than two. Do not infer weekdays,
use price rows as a calendar or skip unknown dates.

Export the exact requested index range, validate it under the public service and compare
its requested units and rows with the complete SSE open-session set for the selected index.
If a valid export is incomplete, ensure that same range once, retain and validate its
result and re-export for final proof. Final Index Export must be complete: each expected
session has exactly one legal ordered row for the requested index, with no extra, duplicate,
conflicting, missing, illegal or non-finite row/field. Validate the entire public record,
not just Close; each close must be finite and strictly positive before `ln(close)` (natural logarithm).
Require each transformed value finite. A legal partial export is not acceptable for this
case, unlike Trailing Return. Do not skip, fill, interpolate or bridge missing facts.

Each final export carries its own proof and payload; never stitch proof and rows from
separate calls. Validate nonnegative integer counters excluding bool, the producer's
accounting and completeness formula, schema and successful-row count; reject malformed
exports instead of repairing or ensuring them. An ensure success is not final proof and
operation-level failure is not ordinary missing. If final completeness fails, or any
input, calendar, transformation or public operation is invalid, fail explicitly with stage,
request, reason and all available export/ensure diagnostics. Do not manufacture a result,
change date range or source, or infer a market explanation for absence.

Preserve exact public requests, final exports and proofs, preliminary/ensure evidence
when present, selected ordered dates and closes and their actual identity under the
[case provenance contract](ARCHITECTURE.md#input-fingerprint-and-retained-evidence). This evidence distinguishes
calendar natural-date units from index session units. Do not promise provider freshness or
an atomic snapshot across calls.
