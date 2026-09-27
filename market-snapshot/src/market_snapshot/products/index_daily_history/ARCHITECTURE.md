# Index Daily History 产品 authority

本文档是 `Index Daily History` 的 bounded-context 入口，只拥有产品身份、query identity、稳定 invariant 与 authority 路由。模块边界见 [market-snapshot architecture](../../../../ARCHITECTURE.md)。

## Product identity

`Index Daily History` 为调用方显式指定的一个指数提供指定 sample calendar interval 内实际存在的日线观测，以及该区间之前指定条数的历史观测，供外部 analyzer 做确定性 warm-up。V1 只覆盖共享 `index_daily` Source capability 支持的指数，不定义股票、ETF、期货或 generic instrument routing。

```text
shared index_daily Source Capture
    → product-owned query-scoped Source facts
    → Index Daily History Analysis Preparation
    → public Python application result
    → market-research
```

本产品是独立的 request-scoped analysis-ready product，不读取 sibling product 的 Raw 或 final artifact。`csi1000-5d-analysis` 使用的 `index_daily_history.json` 是其私有 Raw artifact 名称，不是本产品的结果或可复用边界。

本产品拥有自己的 Application Service 与 public Python request/result/failure/execution contract。Capture 可以在内存中把 query-scoped Source Facts 交给 Preparation；persisted Raw Artifact 不是本产品的成功前提。

## Query identity and stable invariants

Caller 显式指定 `ts_code + start_trade_date + end_trade_date + pre_start_observation_count`；不使用隐式日期、默认指数或 Research method。具体格式、校验及结果字段见 [read/application contract](read-contract.md)。

1. sample 只包含请求区间内实际存在的该指数日线观测，成功时至少一条；不额外引入交易日历或制造缺失日期。
2. `pre_start_observation_count = N` 是 actual observation count，不是 calendar-day duration。成功时 warm-up 恰好为 sample 区间之前紧邻的 N 条真实观测；不足或无法确认完整性则整个请求失败。
3. result 明确分开 warm-up 与 sample，两组都按 `trade_date` 升序排列；任何观测不得同时属于两组。
4. 相同 Source facts、query 与 Preparation Definition 得到语义一致的 result；失败不通过 fallback、填补、删行或 partial success 隐藏。
5. Snapshot 只准备 Source facts，不计算 MA、reference、deviation、percentile、distribution 或 Research finding。

## Authority routing

| Owner | Canonical knowledge |
| --- | --- |
| [Shared Source Capture authority](../../capture/ARCHITECTURE.md) | `index_daily` endpoint、range query、Source 字段与 minimal normalization |
| [Data authority](data.md) | 产品 Source scope、观测集合、warm-up 与 completeness |
| [Read/application contract](read-contract.md) | semantic request、Preparation projection、result、public Python boundary 与 failure |

V1 的 result 可完全 request-scoped、in-memory；不要求 persisted final artifact、`dms` CLI binding、HTTP endpoint、database 或 cache。
