# Futures Calendar Spread Daily export

DD-02 target; inherits [feature authority](ARCHITECTURE.md) and
[Daily Data Copy / Export](../../../data-copy-export.md). This document owns only
feature-local source, Context metadata, CSV mapping and filenames. It creates no
HTTP schema or financial calculation. WP-02 implements it.

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
differ; index Close is an independent same-date reference with no fallback. If the
reference field is absent, additionally state 历史数据包未提供指数参考信息. Do not
infer Source absence from cache/preparation failure or add an investment conclusion.
Static origin stays in adjacent UI, outside Raw/Context metadata.

## CSV mapping

Each actual `day.observations` item produces one row in producer order, including
excluded/not_applicable observations. A closed day has header-only CSV; do not create
a reference-only placeholder row. Context JSON retains that day's full reference.
All numbers use original values; ratios stay decimal ratios. No business recomputation.

The fixed header order is:

```text
case,definition_version,product_code,trade_date,day_status,day_reason,near_slot,far_slot,near_contract_code,near_close,near_delist_date,far_contract_code,far_close,far_delist_date,delta_days,near_dte_days,expiry_stage,signed_spread,annualized_point_spread,annualized_spread_ratio,outcome,reason,underlying_index_present,underlying_index_code,underlying_index_trade_date,underlying_index_close,underlying_index_availability,underlying_index_reason_code,underlying_index_failure_category
```

case/definition_version come from the response; product_code/trade_date from request;
day_status/day_reason from day. Slots, contracts, delta/DTE/stage and outcome/reason
come directly from each observation. Contract columns select near/far object's
contract_code, close and delist_date; absent objects yield null. Metric columns take
corresponding metrics.<metric>.value; absent metrics yield null. Units remain those
of the named metrics under the unchanged financial definition.

Repeat response-level reference fields on each row. underlying_index_present is
Object.hasOwn(response, 'underlying_index'); false means all six reference columns
are null, distinguishing historical omission from provided unavailable/error Close.
When present, map index_code/trade_date/close/availability/reason_code/failure_category
verbatim. Do not synthesize identity or state for an old payload.

Use common UTF-8 BOM/CRLF/quoting/formula protection, literal null and numeric zero
rules. Filenames are `futures-calendar-spread_{product_code}_{trade_date}.csv` and
`futures-calendar-spread_{product_code}_{trade_date}_context.json`, using validated
response identity and shared safe filename handling. Context is UTF-8 without BOM.
