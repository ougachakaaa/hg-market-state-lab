# Price-to-Lagged-Reference Research Semantics authority

本文档是 `market_research` 中共用的 lagged moving reference 和 price-to-reference deviation 的 narrow canonical owner。Research 边界与 retained Study 入口见 [market_research architecture](../../ARCHITECTURE.md)；输入 observation 与精确 warm-up 的产品契约见 [Index Daily History](../../../data_snapshot/src/data_snapshot/products/index_daily_history/ARCHITECTURE.md) 的 [public read/application contract](../../../data_snapshot/src/data_snapshot/products/index_daily_history/read-contract.md)。

## Observation window 与时间方向

对一个指数的 sample observation `T`，`reference_window = N` 是 `T` 之前紧邻的 `N` 条**实际日线 observations**，其中 `N` 为正整数；它不是 `N` 个日历日。按 `trade_date` 升序连接 Snapshot 返回的 `warmup_observations[]` 与 `sample_observations[]`，计算：

```text
Reference_{T-1} = reference_method(observations T-N ... T-1)
D_T             = Close_T / Reference_{T-1} - 1
```

`Close_T` 不进入自己的 `Reference_{T-1}`。第一条 sample observation 使用恰好 `N` 条 pre-start warm-up observations；后续 sample observations 可以成为更晚日期 reference 的输入。Warm-up rows 只支持计算，不成为调用 Study 的统计 sample。Snapshot 产品负责返回恰好 `N` 条完整、紧邻且有序的 warm-up observations；无法提供时整个请求失败。Consumer 不缩短窗口、不丢弃 sample 起点，也不制造不存在的交易日。

## 正式 reference methods

V1 的 `reference_method` 只接受 `sma` 与 `volume_weighted`，两者的 `reference_method_parameters` 均固定为 `{}`，没有 method-specific parameters。

- `sma` 是 prior `N` 条 `close` 的算术平均。
- `volume_weighted` 对相同的 prior `N` 条 observations 计算：

```text
Reference = sum(close_i * volume_i) / sum(volume_i)
```

`decay_weighted` 尚未定义；其权重函数、参数、归一化与 age direction 都未决定。新增 method 前须先在本 authority 明确 token、参数、确定性公式及校验和失败语义，不能以含糊的 `weighted`、`decay` 或 `custom` 代替。

## 输入有效性与失败

Snapshot public contract 保证每条所需 `close` 存在、finite 且严格大于零；Consumer 遇到违反该 contract 的结果仍须显式失败。`volume_weighted` 还要求每条所需 `volume` 非 null、finite 且 `>= 0`，并要求 `sum(volume_i) > 0`。任一 method 的最终 reference 必须 finite 且严格大于零，所得 `D_T` 也必须 finite。任一所需 observation 不能计算时，整个 run 失败；不填值、不回退 SMA、不删除日期，也不发布 NaN、infinity 或除零结果。

`D_T` 使用 decimal ratio：`0.05` 表示 `+5%`。上述规则只定义 lagged reference 与 deviation 的共同计算语义，不决定调用 Study 的日期范围、instrument 选择、eligible population、percentile、统计或结果解释。

## Ownership boundary

本 authority 不拥有 empirical distribution bins、percentile sets、distribution granularity、forward return、MR、MFE、bucket design、run identity、CLI flags/defaults、result artifacts、hypothesis、visualization 或 findings。Empirical quantile 与 fixed-width distribution 由 [shared distribution authority](../distribution/ARCHITECTURE.md) 拥有；调用 Study 各自拥有其 research question、sample interpretation、execution identity、retained results 与 acceptance。本 authority 不是 generic MA、reference 或 feature framework，也不改变 Snapshot 产品对 Source facts 和 public result 的 ownership。
