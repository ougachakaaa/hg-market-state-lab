# Futures Calendar Spread Daily export

DD-02 WP-02 implemented; inherits [feature authority](ARCHITECTURE.md) and
[Daily Data Copy / Export](../../../data-copy-export.md). This document owns only
feature-local source, Context metadata, CSV mapping and filenames. It creates no
HTTP schema or financial calculation.

## Source, actions and Context

Use the entire current validated DailyResponse as received, or the entire validated
Bundle.result in Demo. Preserve fields, arrays, null/zero and omitted reference fields;
do not use Table projections or reconstruct from draft inputs. Known reference error
states still belong to a successful Result and remain exportable. Invalid/failed
whole results, loading and stale results are not export sources.

At the top of the successful result, in this order, expose 复制原始 JSON、复制上下文 JSON、
导出 CSV、导出上下文 JSON. Clipboard feedback is 复制成功/复制失败; downloads report
已开始下载/导出失败, never that a file was saved. Reuse the existing shared CSV and
download utilities; keep feature builders pure and local, and feedback/lifecycle in
feature components/hooks. No sibling DTO imports or new Export Framework.

Raw is the complete response without an envelope. Context uses the canonical
`daily-data-context-v1` envelope, with `metadata.product="Futures Calendar Spread"`.
`metadata.response_identity` has case, definition_version, operation (from
request.operation), product_code and trade_date (from request), all from that response.
Copy and download call the same serializer and produce identical pretty JSON text.
`data` is exactly the Raw business object, including absence of underlying_index.

Reading notes organize these confirmed meanings in Chinese: real same-day contract
Close; near minus far spread; annualized price relationship is not return or trading
instruction; delta/DTE use natural days and actual last trading dates; zero and null
differ; index Close is a same-date reference reused by independent futures–spot comparisons with no fallback. If the
reference field is absent, additionally state 历史数据包未提供指数参考信息. Do not
infer Source absence from cache/preparation failure or add an investment conclusion.
Static origin stays in adjacent UI, outside Raw/Context metadata.

## CSV mapping

Rows are the six actual day.observations in producer order (calendar_spread), then
actual futures_spot_comparisons in M0/M1/Q1/Q2 order (futures_spot). Closed days are
header-only. Omitted collections never produce synthetic rows. All values retain
raw precision, original decimal ratios, null/zero distinction and formal row outcomes.

The fixed 35-column order is:

```text
case,definition_version,product_code,trade_date,day_status,day_reason,comparison_type,comparison_definition_version,slot_a,slot_b,instrument_a_type,instrument_a_code,instrument_a_close,instrument_a_delist_date,instrument_b_type,instrument_b_code,instrument_b_close,instrument_b_delist_date,delta_days,remaining_days,expiry_stage,signed_spread,annualized_point_spread,annualized_spread_ratio,outcome,reason,failure_category,underlying_index_present,underlying_index_code,underlying_index_trade_date,underlying_index_close,underlying_index_availability,underlying_index_reason_code,underlying_index_failure_category,futures_spot_comparisons_present
```

Common identity/day fields come from response/request/day. Calendar rows use the
calendar definition version, near/far slots, futures instrument types and their actual
contract fields. delta_days is the between-contract interval; remaining_days is near DTE.
Its metrics select the existing named metric.value fields; failure_category is null.
Spot rows use their independent definition_version, slot_a=slot, slot_b=null,
instrument_a_type=futures and instrument_b_type=index. A is the actual futures
contract or null; B is the returned underlying index identity/Close, never a futures
code. Index delist_date and delta_days are null; remaining_days is contract DTE.
Spot metrics/outcome/reason/failure_category map directly from the formal item.
Missing objects yield null fields, never fake identities or zero prices.

Repeat response-level underlying reference fields and presence on each row. Repeat
futures_spot_comparisons_present using Object.hasOwn; omission is distinct from an
empty provided collection. Keep BOM, CRLF, escaping, formula protection and literal
null/numeric zero under the shared CSV contract. No financial recomputation.

Filenames remain futures-calendar-spread_{product_code}_{trade_date}.csv and
futures-calendar-spread_{product_code}_{trade_date}_context.json. Context is UTF-8
without BOM and retains complete response dates, states, omission and new results.
Reading notes distinguish near-minus-far/between-contract annualization from
futures-minus-index/remaining-life annualization; missing collections add the exact
historical-omission explanation. The existing four export actions are unchanged.
