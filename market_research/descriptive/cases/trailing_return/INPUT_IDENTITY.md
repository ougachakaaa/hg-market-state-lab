# Trailing Return input identity

This contract specializes [the case](ARCHITECTURE.md) and its
[public input policy](INPUTS.md). It owns retained input evidence and canonical bytes;
request identity and formula remain case-owned.

## Evidence and versioning

Retain exact final consumed Calendar and Index public views in the Job's in-memory input
context, actual requests, schema versions and unchanged public CoverageResults. Also retain
preliminary Export and Ensure outcomes, every UnitFailure identity/reason, expected /
available / absent daily keys and per-candidate endpoint dependencies. ObservationSet and
SampleBinding reference this context. Evidence remains available when conversion fails.
Failed preparation retains obtained diagnostics without a successful input fingerprint.
No mandatory persistence or artifact registry is added; a hash alone cannot reconstruct
facts and mutable caches do not guarantee exact reruns.

`trailing_return_inputs_v1` is retired for new construction. Its historical complete-export
fact hash semantics are unchanged in Git history; do not reinterpret it to accept partial
inputs. This revision uses `trailing_return_inputs_v2` for complete and partial inputs.
The metric identifier/formula is unchanged. Input version explicitly distinguishes the
revised availability policy and evidence; historical v1 outputs are not v2 cache hits.

## V2 canonical payload

Fingerprint is SHA-256 of UTF-8 compact JSON, without BOM/whitespace separators, with
ensure_ascii=true, of this ordered outer array:

```text
["trailing_return_inputs_v2", "descriptive_missing_tolerant_v1",
 fixed_question, calendar_slices, index_slice_or_null,
 expected_daily_keys, absent_daily_keys, endpoint_requirements]
fixed_question = ["trailing_cumulative_return_v1", index_code, [], H,
                  "trading_sessions", start_date, end_date,
                  "end_session", "inclusive"]
coverage = [requested_units, successful_units, missing_units,
            pending_units, failed_units, complete]
calendar_slice = [dataset, view, export_schema_version,
                  exchange, start_date, end_date, coverage, rows]
calendar_row = [exchange, cal_date, is_open, pretrade_date_or_null]
index_slice = [dataset, view, export_schema_version,
               [index_code], start_date, end_date, coverage, rows]
index_row = [index_code, symbol, name, market, publisher, category, trade_date,
             open, high, low, close, pre_close, change, pct_change, volume, amount]
daily_key = [index_code, trade_date]
endpoint_requirement = [anchor, anchor_daily_key, lookback_daily_key,
                        missing_required_facts]
missing_required_fact = [endpoint_role, daily_key, "close", "daily_fact_unavailable"]
```

Dataset/view/schema in each slice supplies the public namespace for daily keys and required
facts. Use final validated exports actually consumed, including discovery padding, never
preliminary incomplete exports. Calendar slices sort by (start_date,end_date,exchange),
Calendar rows by cal_date and Index rows/daily-key sets by (index_code,trade_date).
endpoint_requirements follow ascending candidate anchor; missing_required_facts order is
anchor then lookback, and contains exactly absent endpoints. Endpoint roles are literal
`anchor` and `lookback`. Expected keys span every open session L..B; absent keys are the
expected-minus-final-available set. Available keys derive exactly from final Index rows.
Do not independently serialize conflicting coverage counts or outcome claims.

Encode dates as YYYY-MM-DD strings, absent optional fields as JSON null, integers as JSON
integers, boolean complete as JSON boolean, and every public float as its Python binary64
float.hex() string (including signed zero). Text is unchanged, without Unicode normalization.
Do not round or hash private IDs/paths, provider responses, credentials or execution times.
For zero candidates, index_slice is null, expected/absent/endpoint arrays are empty; the
complete sample-window Calendar is still included. For all-unavailable positive population,
index_slice is a real empty-record partial view, never null.

The hash includes all final public rows/metadata, exact requests, calendar resolution,
expected/absent keys, endpoint absence and final CoverageResults. Changes in any of these
change the canonical payload, including missing/pending/failed distribution even where
available rows are unchanged. Same facts/proof and explicit missing state normalize to
same bytes, independent of collection arrival order. Validate producer ordering before
canonicalization; hashing does not silently repair an illegal Export.

Earlier preparation attempts and Ensure diagnostics are retained execution evidence but
excluded from the hash: retry history, reason wording and acquisition order must not
change final input identity. Their public identities link to absent endpoints where
applicable, but do not override final Export proof. Derived ratios/outcome totals are not
separate hash fields; they must derive from the fingerprinted facts and fixed question.

## Acceptance obligations

Verify deterministic bytes/hash after canonical sorting of equivalent legal collections,
changed close/metadata/calendar/key/proof-state sensitivity, signed-zero preservation,
missing endpoint ordering, all-unavailable versus no-candidate distinction, and unchanged
hash for different preliminary diagnostics with identical final inputs. Verify v1/v2
separation and no acquisition of private provenance. Retention/export beyond in-memory
result lifetime remains outside this design.
