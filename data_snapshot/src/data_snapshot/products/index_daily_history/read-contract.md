# Index Daily History read/application contract

本文档从属于 [product authority](ARCHITECTURE.md)，拥有 semantic request、Analysis Preparation projection、result、public Python application boundary 与 product failure。Source scope、warm-up selection 和 completeness 见 [data authority](data.md)。

## Application request

Public application boundary 接收 `IndexDailyHistoryRequest`，语义字段为：

```text
ts_code                         required index identity supported by index_daily
start_trade_date                required YYYY-MM-DD, inclusive
end_trade_date                  required YYYY-MM-DD, inclusive
pre_start_observation_count     required integer >= 0
```

日期必须是真实有效的日历日期，且 `start_trade_date <= end_trade_date`。在调用 Capture 前校验请求；不接受空白或无效指数 identity，不使用默认指数、`today`、`latest`、隐式历史窗口或最近交易日 fallback。请求的四项组成 query identity。

## Preparation and observation

对 [data authority](data.md) 定义的 sample 与 warm-up 各行，Preparation 只投影：

```text
trade_date
close
volume
```

`close` 来自 Source `close`，必须是存在、非 null、有限且大于零的数值；否则整次请求失败。`volume` 是 Source `vol` 的 analysis-friendly rename，保留 Source 单位（手）。Source 合法缺失 / null 的 `vol` 映射为 `volume = null`；存在时必须是有限且非负的数值，真实数值零保留为零；malformed、负值或非有限值导致失败。不从其他字段推算、不填零、不删去该观测。某个 Research reference method 是否要求非 null volume，由该 consumer 的 Study authority 决定。

Preparation 验证每条观测的指数 identity、日期归属、唯一性与必需数值，按 `trade_date` 升序排列两组，并在完整验证后一次性产生 result。它不访问网络、当前时间、Research code、HTTP DTO 或 sibling product artifact。

## Semantic result

Public result 为：

```text
IndexDailyHistoryResult
    ts_code
    requested_start_trade_date
    requested_end_trade_date
    requested_pre_start_observation_count
    warmup_observations[]
    sample_observations[]
```

两组使用相同的 `IndexDailyObservation` shape；`warmup_observations` 恰好 N 条且均严格早于请求起点，`sample_observations` 至少一条且均位于请求区间内。各组日期唯一、升序，互不重叠。结果本身足以区分 warm-up 与统计 sample，无需 caller local state、Raw path 或隐式日期逻辑。

## Public Python boundary

产品自有 public module 暴露 semantic request/result/observation types、classified application failure、可注入 Source client 的 application service，以及 production-ready execution entry：

```python
run_index_daily_history(
    request: IndexDailyHistoryRequest,
) -> IndexDailyHistoryResult
```

调用方只提供 semantic request。该 entry 在 Snapshot 边界内完成 credential loading、Source client 创建、Capture orchestration 与 Preparation，并返回完整结果或 `IndexDailyHistoryError`。Research study-local CLI 不创建 Tushare client、Capture adapter，不读取 credential、Raw、product-private Preparation 或 persistence internals，也不经过 `ui_http` / HTTP DTO。V1 结果可完全 request-scoped、in-memory，不要求 persisted final artifact 或 HTTP endpoint。

## Success and failure

成功要求有效 query、至少一条 sample、恰好 N 条紧邻的 warm-up、所有返回行归属与唯一性正确、每行 `close` 可用、`volume` 满足上述 nullable fact 契约，并完成确定性排序与分组。

以下情况均转换为 classified product application failure，不返回 partial result：

```text
invalid or unsupported index identity
invalid date, start_trade_date > end_trade_date
invalid or negative pre_start_observation_count
credential / Source-client creation or Source request failure
no sample observation in requested interval
insufficient or unverifiable exact pre-start observations
duplicate observation for the same index + trade_date
observation for another index or outside its requested scope
required close missing, malformed, non-finite or unusable
present volume malformed, non-finite or unusable
other contract violation preventing a deterministic complete result
```

不通过 fallback date、previous available sample boundary、partial warm-up、silent row dropping、zero fill、fabricated observation 或 partial success 隐藏失败。具体 exception 实现可以再细化，但必须由本产品 public boundary 分类并传递。
