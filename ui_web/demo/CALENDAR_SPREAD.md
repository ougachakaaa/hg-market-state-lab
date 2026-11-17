# Calendar Spread L1 Demo integration

Status: locally implemented. No publication is authorized. Specializes [Demo](ARCHITECTURE.md),
[Bundle](BUNDLES.md), [Build](build/ARCHITECTURE.md) and
[Release Requirements](release/ARCHITECTURE.md).

## Formal sources and identities

| Bundle ID | Formal source | Shared Presentation owner |
| --- | --- | --- |
| `calendar_spread_daily` | [Daily HTTP 200](../../ui_http/products/futures_calendar_spread/http-contract.md) | `futures_calendar_spread` |
| `calendar_spread_relative_value` | [Research HTTP 200](../../ui_http/products/calendar_spread_relative_value/http-contract.md) | `calendar_spread_relative_value` |

The active dataset contains nine required Bundles and one Manifest. The two new
captures were acquired through authenticated FastAPI HTTP on 2026-11-16, using
existing retained Tushare/CFFEX facts without Ensure or cache modification.
All seven prior Bundle files retain their baseline SHA-256. There is no second
Demo dataset, synthetic success result, financial algorithm or production hook.

Static routes `#/data/futures-calendar-spread` and
`#/research/calendar-spread-relative-value` join the prior eight routes.
Results pass the same feature-owned validators and public Presentations as
Production. Query controls are absent; local Pair, axis, viewport, sample-detail
and disclosure interactions remain available.

The integration is implemented. Local integration never means Pages publication;
completed execution evidence remains in Git history.

## WP7 delivery contract

The two contract identities are `futures_calendar_spread:DailyResponse` and
`calendar_spread_relative_value:HistoricalResponse`, anchored to the delivered
feature-owned OpenAPI schemas (no invented DTO version). Both Results are complete
synchronous HTTP 200 bodies. The original WP7 capture used Daily GET and Research
POST with the configured same-origin header, without Runs, polling, retries or
acquisition. This describes that completed capture before Issue #13.

Authenticated selections are IM / 2026-09-30 and IM / 2026-03-01 through
2026-09-30 / annualized_spread_ratio, omitting histogram_edges. Both were verified as complete, usable HTTP 200
Results before the coordinated cutover.

Repeated Collector `--only` selects both new members in one transaction. During
membership extension, unchanged active files must match their existing Manifest
hashes before copying; the entire nine-member candidate independently passes
Preflight before the existing journal/replacement protocol commits it. A failed
capture preserves all active bytes. Never recollect the unrelated seven.

The static controller passes validated Results to the two WP6 public Presentations.
It supplies fixed captured identity and source disclosure without production hooks.
Pair, date-axis, viewport, sample-table and disclosure interactions remain local.
Histogram appears only when present in the captured Result; absence is never filled.

Release content admission additionally requires all six Daily pairs to have valid
actual contracts/metrics; each Research pair must have at least 30 dated all-stage
samples with Quantile and a current all-stage Percentile, and a nonempty matching
stage comparison. The 30-observation minimum is a Demo content requirement, not a
change to the business definitions of empty_sample, small_sample or available.
Actual historical dates must precede evaluation. No values are recomputed to pass.

## Future collection after Issue #13

The retained WP7 captures and their original read-only disclosures remain historical
facts. Static display and offline Build Preflight consume those Bundle bytes only;
neither submits Research POST nor calls Ensure.

A future explicit Collector invocation still uses Daily GET (read-only) and the
formal Historical POST. Issue #13 changed that POST to execution: Research may
conditionally Ensure missing Calendar/Futures facts through DataLake before returning
the complete Result. Collection can therefore acquire data and take longer on cold
caches, even though the resulting static application remains offline and read-only.
The Collector's existing default per-request timeout is 60 seconds; timeout does not
promise worker cancellation or cache rollback and must not cause automatic resubmission.

The Demo/build authority permits explicit formal HTTP generation; it does not impose
a permanent no-Ensure restriction on the Collector. No new read-only Historical
endpoint, collection permission, Bundle or Manifest change is introduced here.
