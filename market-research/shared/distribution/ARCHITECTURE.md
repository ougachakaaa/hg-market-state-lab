# Empirical Distribution Research Semantics authority

本文档是 `market-research` 中一维 empirical numeric distribution 的 canonical semantic owner。Research 模块边界与 retained Study 导航见 [market-research architecture](../../ARCHITECTURE.md)。本 authority 只定义完整 numeric sample 上的 empirical quantile、fixed-width bins 与最小 descriptive summary；它不是 generic statistics framework、Research Math Library、feature framework、Experiment Engine 或 Modeling semantic。

## Input 与 ownership

输入是由调用 Study 构造的、非空且每个 observation 都是 finite numeric value 的完整 eligible sample。shared distribution 不解释数值代表 basis、price deviation、return、volatility、instrument 或 strategy，也不决定 eligibility、缺失值处理或单位转换。`NaN`、infinity、malformed value 与空 sample 必须显式失败，不自动丢弃 observation。

调用 Study 拥有 Snapshot public result 的获取、交易日与 instrument 选择、eligible sample，以及后续证据的解释、保留和可视化。两个 price-to-lagged-MA Study 共用的 warm-up 计算要求、moving reference 与 deviation 语义由 [Price-to-Lagged-Reference Research Semantics](../price_to_lagged_reference/ARCHITECTURE.md) 拥有。shared distribution 只消费 Study 交付的 numeric observations；它不拥有 Snapshot access、CLI、run identity、artifact 命名或展示格式。

## Empirical quantile

对排序后的完整 eligible sample `x[0] <= ... <= x[n-1]` 和 finite numeric probability `0 <= p <= 1`，位置为：

```text
h = (n - 1) * p
```

若 `h` 落在两个 observation 之间，对相邻值做 linear interpolation；落在整数位置时取该位置的值。非 finite、非 numeric 或超出 `[0, 1]` 的 probability 必须失败。`median = empirical quantile(p = 0.5)`；同一 sample 上报告的 median 与 P50 必须一致。

本 authority 只决定 quantile 的计算 convention。P05/P10/P20 等具体 percentile probabilities 由调用 Study 显式选择；本 authority 不规定固定 percentile set、ranking、rolling quantile 或 out-of-sample threshold policy。

## Fixed-width empirical distribution

输入除完整 eligible sample 外，还包括与 observations 同 numeric unit、finite 且大于零的 `granularity = g`。以 `0` 为 canonical anchor，向正负方向延伸的 bin grid 为：

```text
..., [-2g, -g), [-g, 0), [0, g), [g, 2g), ...
bin(k) = [k*g, (k+1)*g), k 为整数
```

所有 bin 左闭右开；`0` 属于 `[0, g)`，恰好位于边界的 observation 只落入从该边界开始的 bin。正负值使用同一 grid。

V1 从 sample minimum 所在 bin 到 sample maximum 所在 bin 连续 materialize canonical bins，包括中间的 zero-count bins；不设 configured min/max range、隐藏的百分比范围、underflow bucket 或 overflow bucket。每个 materialized bin 至少包含 numeric `lower_bound`、`upper_bound`、`count` 和 `frequency`：

```text
frequency = count / sample_count
sum(count) = sample_count
sum(frequency) = 1  # 允许正常 floating-point tolerance
```

zero-count bin 的 `frequency` 为 `0`。display label、percentage formatting 与 plot label 属于调用 Study 的 representation，不属于 shared numeric result。

## Narrow descriptive summary

与 empirical distribution 直接相关的最小 summary 为 `sample_count`、`mean`、`median`、`sample_standard_deviation`、`min` 和 `max`。非空 finite numeric sample 即可产生完整 summary；`sample_count` 是 eligible sample 的 observation 数量，`mean` 是其算术平均值，`median` 使用本文的 quantile convention。当 `sample_count >= 2` 时，`sample_standard_deviation` 使用 `ddof = 1`；当 `sample_count < 2` 时，其值为 `null`，表示该 sample statistic 在数学上未定义，不是 failure，也不得用 `0`、NaN 或 infinity 代替。空 sample、NaN、infinity 或 malformed numeric value 仍按 Input 与 ownership 的约定失败；granularity 与 probability 的既有校验同样不变。调用 Study 可因自身研究含义规定更严格的最小样本量。

本 authority 不定义 skewness、kurtosis、regression、correlation、rolling statistics、normality test、confidence interval、parametric distribution fitting 或 kernel density estimation。Study-specific method、output 与 failure condition 仍由对应 retained Study authority 拥有。
