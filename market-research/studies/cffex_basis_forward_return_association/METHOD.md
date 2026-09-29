# CFFEX Study Method authority

本文档从属于 [Study entry](ARCHITECTURE.md)，拥有本 Study 的统计 convention、Method Context、三个 Observation、各自 Artifact identity 与四个 Analysis。上游确定性事实见 [Snapshot Product](../../../market-snapshot/src/market_snapshot/products/cffex_equity_index_basis_history/ARCHITECTURE.md)。

## Method

### Study-local statistical conventions

对非空 numeric sample 排序为 `x[0] <= ... <= x[n-1]`，对 `0 <= p <= 1` 定义 `h = (n - 1) * p`。`h` 为整数时取该 observation；否则在相邻两条 observation 之间线性插值。此 convention 适用于本 Study 使用的 P10/P20/P25/P40/P50/P60/P75/P80/P90，full-history 与 common-period 均相同。`median = empirical_quantile(p = 0.5)`。空 sample 的分位数与 median 为 `null`。

Sample standard deviation 使用 `ddof = 1`，即 `sqrt(sum((x_i - mean(x))²) / (n - 1))`；`sample_count < 2` 时为 `null`，不是 0、NaN 或 failure。所需输入与可定义的派生统计必须 finite；数学上未定义的 Pearson/OLS statistic 为 `null`，并记录原因。对带截距 OLS，若 predictor 方差为零，`beta`、`alpha`、`R²` 为 `null`；若 predictor 方差非零而 outcome 方差为零，可定义的 `alpha`、`beta` 如实计算，`R²` 为 `null`。Pearson 在样本少于两条或任一变量方差为零时为 `null`。

### Method Context 与 ownership

共同上下文是固定的四个 family、各自上市界限、同一含端点请求区间、四个 slot、非前月年化 basis predictor、实际交易观测 horizons `{1, 3, 5, 10, 20}` 及完整 20D predictor sample。日期与 family 定义 Study population；family 对应的上市界限、slot、同日 close、合约级 basis 的事实语义属于 Snapshot Product。`daily_non_front_basis` 的聚合和 20D 样本规则属于本 Study Method，分别由下述 Observation 与 Analysis 使用。任何 Observation 均不从另一个 Observation 的研究结果定义自身；实现可以复用相同 public result 或中间数据。

### Observation: `basis_term_structure`

本 Observation 从所需 Snapshot public result 独立观察每个 family × 实际交易日 × active contract 的合约级事实。每个有效 family-date 必须有唯一的 M0、M1、Q1、Q2；四槽的合约身份、期限位置与有效性由 Snapshot 共享 CFFEX basis authority 定义。至少保留 `trade_date`、`family`、`underlying_code`、`contract_code`、`contract_slot`、`delist_date`、`days_to_delist`、`annualization_days`、`underlying_close`、`futures_close`、`basis_points`、`basis_pct`、`annualized_basis_pct`。同日 close 与上游 completeness 必须成立；缺失 slot、重复或不可用的必需事实不能以删行、换日或填零修复。本 Observation 覆盖有效区间内的全部 basis dates，不因未来收益不足裁剪尾部。

### Observation: `daily_basis_environment`

本 Observation 独立消费同一上游完整期限结构事实，对每个有效 family-date 计算：

```text
daily_non_front_basis
  = (M1 annualized_basis_pct
     + Q1 annualized_basis_pct
     + Q2 annualized_basis_pct) / 3
```

它保留 `trade_date`、`family`、`daily_non_front_basis` 和 M1/Q1/Q2 的各自年化 basis；单位均为 annualized percentage points。三项必须全部有效且 finite，不能按可得项数求平均。M0 仍在 `basis_term_structure`，但其临近交割的收敛与年化敏感性不进入 V1 predictor。本 Observation 包含有效区间内全部日期，不由任何 Analysis 的分组或未来收益反向筛选。

### Observation: `underlying_forward_returns`

本 Observation 从 public market result 的标的指数同日 close 独立构造每个 family × 实际交易日的有序价格路径。对 `h ∈ {1, 3, 5, 10, 20}`：

```text
forward_return_h_pct
  = (underlying_close[T+h] / underlying_close[T] - 1) × 100
```

`T+h` 是同一 family 在请求区间内第 `h` 条后续实际指数交易 observation，不是日历日；不用 log return，也不读取 `end_trade_date` 之后的数据。逐日输出至少保留 `trade_date`、`family`、`underlying_close` 及五个 horizon 的收益。请求尾部未获某个 horizon 完整未来路径的日期仍可作为其他日期的 future support，并在自身对应收益字段标为 `null`；这不是零收益或需要补取的缺失。无法形成完整 20D outcome 的日期不进入任何 Analysis 的 predictor sample。

### Observation Artifact identity

三个 Observation 的上述 stable local name 各自构成组件身份。它们须独立保留可供复核的 machine-readable Artifact；各自的 semantic identity 由组件身份、适用的有效日期区间、family/source public input identity，以及影响该组件的固定计算参数共同确定。`underlying_forward_returns` 的 identity 还包含请求终点所限定的 future-support 范围；`daily_basis_environment` 的 identity 包含非前月聚合规则。Artifact identity 不取决于 Analysis、文件名、表示格式、执行时间、随机 UUID 或偶然路径。语义身份匹配的已物化 Observation 可供后续 Analysis 消费，但本 authority 不要求分段执行、通用 DAG、cache 或 Artifact Registry。

### Analysis: `historical_basis_context`

消费三个具名 Observation，回答每个 family 的指数价格和期限结构基差在历史中怎样演化。覆盖有效区间内所有完整 basis dates，不以 20D predictor eligibility 裁剪历史图或基差摘要。逐 family 保留基差环境、M0/M1/Q1/Q2 年化 basis 与对应标的 close 的有序时间序列；价格图将该 family 首条有效 close 规范为 100，仅供比较展示。图形展示历史背景，不从时间序列外观直接宣称预测关系。

### Analysis: `basis_regime_forward_returns`

消费 `daily_basis_environment` 与 `underlying_forward_returns`，按 family 独立使用同时具备完整 20D outcome 的 predictor dates。对各 family 的这一完整 numeric sample，按本 Study 的 empirical quantile convention 求 daily predictor 的 P20/P40/P60/P80，再以 `Q1: x <= P20`、`Q2: P20 < x <= P40`、`Q3: P40 < x <= P60`、`Q4: P60 < x <= P80`、`Q5: P80 < x` 分组。相同 basis 值不拆组；重合阈值可形成空组。Q1/Q5 仅表示该 family 自身样本中较低/较高的 basis environment。

对每个 family × quintile × horizon 计算样本数、算术平均收益、median、P25、P75 和 `positive_return_rate = count(forward_return_h_pct > 0) / sample_count`。零收益进入分母但不算 positive。各 horizon 使用完全相同的 predictor dates；不能按较短 horizon 扩张样本。全历史阈值只用于事后历史分组。

### Analysis: `linear_association`

消费 `daily_basis_environment` 与 `underlying_forward_returns`，在与上一 Analysis 相同的各 family 完整 20D predictor dates 上，对每个 horizon 计算 `Corr(daily_non_front_basis_T, forward_return_h_pct)` 的 Pearson 系数，以及带截距的简单 OLS：`forward_return_h_pct = alpha + beta × daily_non_front_basis + error`。保留 family、horizon、sample count、相关系数、alpha、beta、R²。可定义的统计照实计算；因样本数或零方差在数学上未定义的值标 `null`，不伪装为 0。OLS 只提供方向、线性幅度和简单解释程度，不作显著性推断。

### Analysis: `common_period_cross_family_comparison`

消费 `daily_basis_environment` 与 `underlying_forward_returns`。先取四个 family 均具完整 basis predictor 和 20D outcome 的**实际交易日期交集**，而不是只设相同日历起止区间。四者在这一相同日期集合上分别重新计算自己的 P20/P40/P60/P80，依照 `basis_regime_forward_returns` 的分组边界与条件收益统计重做 quintile × horizon 表。不得复用 full-history 阈值；此表明确标记 `population = common_period`，并记录交集首末实际日期及日期数。它用于减少不同上市年份和交易日期组成造成的跨 family 比较偏差，不把四个指数当作独立实验。
