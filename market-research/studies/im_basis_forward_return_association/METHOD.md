# IM Basis Forward Return Association method authority

本文档是本 Study analytical semantics 的唯一 canonical owner；Study identity、请求与 run identity 见 [Study entry](ARCHITECTURE.md)，retained evidence 的结构与呈现见 [Results](RESULTS.md)。

## Method Context 与共同样本

`daily_basis_predictor` 的 predictor 固定为 `non_front_mean_basis`；`forward_return_panel` 的 canonical horizons 为 `H = {1, 3, 5, 10, 15, 20}`，maximum horizon 是 20 条实际 CSI1000 trading observations。`basis_quintile_forward_returns` 的 quintile probabilities 固定为 `{0.2, 0.4, 0.6, 0.8}`。两个 Analysis 的 minimum common sample rule 为 `common_sample_count >= 5`。这些都是 Method-level fixed semantics，不是 invocation inputs；请求日期及 run identity 由 [Study entry](ARCHITECTURE.md) 拥有。

两个 Analysis 共用下列唯一的 **Method-level common eligible predictor sample**，而非各自选择样本：

```text
T 是输入 Snapshot result 内的实际 CSI1000 observation date
+ T 的 M0/M1/Q1/Q2 panel 完整且唯一，finite predictor 可定义
+ 同一 result 内 T 之后存在 20 条实际 CSI1000 observations
= T 进入两个 Analysis 对所有 horizons 共用的 predictor sample
```

输入尾部缺少完整 20D outcome 的合法日期不进入共同样本，仍可作为两个 Observation 的日期并为较早日期提供 future support。该 rule 消费两个 Observation 的语义输出，约束两个 Analysis；不会改变两个 Observation 各自的定义。

## Observation: `daily_basis_predictor`

本 Observation 对输入区间内每个实际 CSI1000 trade date 形成 basis predictor observation。它消费 [CSI1000 IM Basis History public result](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/read-contract.md) 中该日期完整且唯一的 M0/M1/Q1/Q2 panel，以及同一 result 的 `underlying_close`；使用 [IM Basis Research Semantics](../../shared/im_basis/ARCHITECTURE.md) 定义的：

```text
non_front_mean_basis_T
= mean(M1, Q1, Q2 annualized_basis_pct)
```

`M0` 严格排除于 V1 predictor。Semantic output 至少为 `trade_date`、`underlying_close` 与 finite `non_front_mean_basis`；基差单位沿用 Snapshot 的 annualized percentage points。每个日期四槽必须完整且唯一，basis 与 close 必须可定义，同一日期四槽的 `underlying_close` 必须唯一且一致。缺槽、重复、冲突或不可计算值是 upstream contract violation，整次 run 失败；Research 不删行、填补或重新选择合约。M0 convergence 或 near-delivery behavior 不属于本 Study。

本 Observation 不因未来收益缺失而删除合法日期，也不根据某个 Analysis 的输出重新定义 predictor。两个 Analysis 均显式消费其 `trade_date` 与 `non_front_mean_basis`；共同资格由上面的 Method-level rule 判定。

## Observation: `forward_return_panel`

本 Observation 从同一 Snapshot result 的 CSI1000 实际交易 observation path 构造 future-return outcomes。对每个 `h ∈ H` 与存在相应后续 observation 的日期 `T`：

```text
forward_return_h_pct
= (underlying_close[T+h] / underlying_close[T] - 1) * 100
```

`T+h` 是同一输入 result 中 `T` 之后第 `h` 条实际 CSI1000 trading observation，不是 calendar day。结果单位为 percentage points；不使用 log return，也不访问 requested end 之外的数据。Forward return 是本 Study 的 outcome definition，不是 Snapshot field。

Semantic output 以 `trade_date` 关联可定义的 `forward_return_1_pct`、`forward_return_3_pct`、`forward_return_5_pct`、`forward_return_10_pct`、`forward_return_15_pct` 与 `forward_return_20_pct`。尾部日期缺少某些 horizon outcome 时不制造收益值；这些日期仍可支持更早日期的 forward return。只有拥有完整 20D outcome 的 `T` 才能通过 Method-level rule 进入共同样本。输入 observation path 或 underlying close 违反 Snapshot public contract 时整次失败，不在 Research 内删行或填补。两个 Analysis 均显式消费该 Observation 的可定义 horizon outcomes。

## Analysis: `linear_association`

本 Analysis 显式消费 `daily_basis_predictor` 与 `forward_return_panel`，在 Method-level common eligible predictor sample 上回答 predictor 与各 horizon subsequent return 的 descriptive linear association。所有 horizon 使用完全相同的 `T` sample，且 `common_sample_count >= 5`。对每个 `h ∈ H` 计算：

```text
PearsonCorr(non_front_mean_basis_T, forward_return_h_pct)

forward_return_h_pct
= alpha_h + beta_h * non_front_mean_basis_T + error
```

OLS 是带截距的 simple OLS。每个 horizon 的 required evidence 至少表达 `horizon`、`sample_count`、`pearson_correlation`、`ols_alpha`、`ols_beta` 与 `ols_r_squared`；retained table 结构由 [Results](RESULTS.md) 拥有。Pearson 与 OLS 只描述 direction、linear magnitude 与 simple explanatory power，不表达 causality、statistical significance、trading edge 或 forecast model。V1 不报告 p-value、t-statistic、confidence interval 或未校正的 significance claim。

## Analysis: `basis_quintile_forward_returns`

本 Analysis 显式消费 `daily_basis_predictor` 与 `forward_return_panel`，在与 `linear_association` 完全相同的 Method-level common eligible predictor sample 上观察不同 basis state 的 subsequent-return distribution、monotonic pattern 与可能的非线性。按 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md) 的 linear-interpolation convention，在完整共同样本上计算 `non_front_mean_basis` 的 P20、P40、P60、P80。同一组 numeric breakpoints 用于所有 horizon，按数值阈值分组：

```text
Q1: x <= P20                         deepest discount / lowest basis
Q2: P20 < x <= P40
Q3: P40 < x <= P60
Q4: P60 < x <= P80
Q5: P80 < x                          highest basis
```

边界值归入较低组；相同 predictor 值不被人为拆分到不同 state。阈值 ties 若导致任一 quintile empty，整次 run 失败。对每个 `basis_quintile × horizon` 至少计算：

```text
sample_count
mean_forward_return_pct
median_forward_return_pct
positive_return_rate

positive_return_rate
= count(forward_return_h_pct > 0) / sample_count
```

零收益进入 denominator，但不计为 positive。`positive_return_rate` 是本 sample 的 historical empirical conditional rate，不是 forward-looking forecast probability。Quintile 不命名为 buy/sell zone、bullish/bearish 或 cheap/expensive。Numeric breakpoint 与条件统计的 retained representation 见 [Results](RESULTS.md)。

## Run validity

必须有足够 observation dates 形成完整 20D target，且共同样本至少有 5 个日期。若 predictor 或任一 horizon outcome 无方差、阈值 ties 导致任一 quintile 为空、任何必需统计量不可定义，或存在 upstream Snapshot contract violation，整次 retained run 必须显式报告相应失败。不输出部分 evidence、空统计值、推测值或缩短后的 horizon set；失败时的 retained-result boundary 见 [Results](RESULTS.md)。
