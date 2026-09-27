# Index Daily History data authority

本文档从属于 [product authority](ARCHITECTURE.md)，拥有本产品的 Source scope、实际观测集合、warm-up selection 与 completeness。`index_daily` endpoint、`ts_code + start_date + end_date` 历史查询、Source 字段及 Raw normalization 由 [shared Capture authority](../../capture/index-stock-contract.md) 与 [common contract](../../capture/common-contract.md) 拥有。

## Source scope and sample

V1 只请求调用方指定的一个 `ts_code` 对应的 Tushare `index_daily` facts。`start_trade_date` 与 `end_trade_date` 是显式、含端点的 calendar bounds；sample 集合定义为成功取得的、满足 `start_trade_date <= trade_date <= end_trade_date` 的实际观测。边界日没有观测时不自动调整日期；sample 集合为空则请求失败。

不依据周末、休市推断缺失观测，不引入独立交易日历，也不使用其他产品的 Raw、final artifact 或固定指数 universe。相同指数与 `trade_date` 只能有一条观测，所有返回行必须属于所请求指数及实际查询范围。

## Exact pre-start observations

设 `pre_start_observation_count = N`。warm-up 是严格早于 `start_trade_date`、在该指数实际历史观测序列中紧邻 sample 区间的最后 N 条观测，而不是 `start_trade_date - N` 个日历日。`N = 0` 时 warm-up 为空；`N > 0` 时成功结果必须恰好包含 N 条。

Source 查询范围如何扩展以获取足够历史属于实现选择，不在 authority 中锁定估算天数、分页或重试 heuristic。不能因预估范围过短就声称历史不足；只有能确认实际历史不足 N 条时才报告不足。若 Source 请求失败或无法确认所选 N 条确为紧邻区间的完整序列，则整个请求失败。

## Completeness and Raw boundary

产品可以拥有 query-scoped Source facts / Raw Artifact，但不得复用 sibling product 的 Raw 或 final artifact。Raw 保留 Source `close`、`vol` 等事实及 legitimate null，仅作共享 Capture 允许的 minimal normalization。sample/warm-up selection、字段投影、数值校验、排序与两组分离属于 Analysis Preparation。

重复 `ts_code + trade_date`、错属指数、超出对应查询范围、无法形成完整 sample/warm-up，或必需 Source request 失败，均不得通过 silent row dropping、fallback date、zero fill、fabricated observation 或 partial result 隐藏。具体 public result 与 failure 分类见 [read/application contract](read-contract.md)。
