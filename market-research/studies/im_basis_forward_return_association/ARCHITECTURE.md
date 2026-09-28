# IM Basis Forward Return Association retained study authority

本文档是 `IM Basis Forward Return Association` 的 retained-study authority。Research 边界与 retained-study identity 见 [market-research architecture](../../ARCHITECTURE.md)；predictor 见 [IM Basis Research Semantics](../../shared/im_basis/ARCHITECTURE.md)；quantile convention 见 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md)；输入产品见 [CSI1000 IM Basis History](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md)。

对应 executable implementation 位于 [im_basis_forward_return_association package](../../src/market_research/studies/im_basis_forward_return_association/__init__.py)；其 public Study ID 为 `im-basis-forward-return-association`。本文件保有 Study 语义与 retained evidence 的 canonical ownership。

## Question

> T 日 IM 非近月期限结构的整体年化基差水平，与 CSI1000 随后 1 / 3 / 5 / 10 / 15 / 20 个交易 observation 的收益之间存在多大程度的关联？

本 Study 是 `IM Annualized Basis Baseline` 的 sibling retained study。Baseline Study 建立 predictor distribution understanding；本 Study 研究 predictor 与 subsequent return 的 association。两者都直接消费 Snapshot public result，本 Study 不依赖 Baseline Study 的 persisted result。

V1 目标是打通完整研究链路并获得简单、可解释的 association baseline。方法 intentionally minimal and replaceable / extensible，不是最终统计方法或 production forecast model。

## Inputs

Study-local CLI 必须以显式、含端点的 `start_trade_date` 与 `end_trade_date` 调用 `CSI1000 IM Basis History` public Python application boundary，再把完整 semantic result 交给 Study。Study computation 不组合 Snapshot dependency；请求不使用 implicit latest/today 或 query-range fallback。

Research 仅使用 Snapshot result 提供的：

```text
trade_date
contract_slot
underlying_close
annualized_basis_pct
```

Study 不读取 Snapshot Raw，不调用 Capture 或 Preparation internals，不依赖 persistence path，不通过 backend-api / HTTP 获取内部业务数据，也不重算 Snapshot 拥有的 slot、basis 或 annualization semantics。当前 public result 已足够支撑 V1，不需要新 Snapshot product、field 或 Source requirement。

### Study-local invocation

Stable Study ID 为 `im-basis-forward-return-association`。从 repository root 通过统一 CLI 运行：

```bash
lab research run im-basis-forward-return-association --start 2024-01-01 --end 2026-01-01
```

`--start` 与 `--end` 为 required inclusive `YYYY-MM-DD` dates，不使用 today/latest/default。同一日期区间的 canonical run directory 已存在时默认失败；显式 `--overwrite` 才允许事务性替换。`--start` 映射为 `start_trade_date`，`--end` 映射为 `end_trade_date`；两者须为有效日历日期且 start 不晚于 end。省略、无效或逆序日期必须失败，不能由 implementation 选择默认区间。完整参数帮助由以下命令生成：

```bash
lab research run im-basis-forward-return-association --help
```

`start_trade_date` 与 `end_trade_date` 是本 Study 的 request / population bounds，由 Study-local CLI 传给 Snapshot public request；两项日期限定 `daily_basis_predictor`、`forward_return_panel` 及两个 Analysis，并参与整次 run identity。`--overwrite` 仅是 execution option，不改变研究语义或 run identity。Predictor identity、horizons、minimum common sample rule 与 quintile probabilities 是固定 Method semantics，不是 CLI configurable inputs。

## Method

### Method Context

Canonical horizons `H = {1, 3, 5, 10, 15, 20}`；maximum horizon 是 20 条实际 CSI1000 trading observations。两个 Analysis 使用同一组具有完整 20D future support 的 common eligible predictor dates，成功 retained run 必须满足 `common_sample_count >= 5`。`daily_basis_predictor` 的 predictor 固定为 `non_front_mean_basis`；`forward_return_panel` 使用固定 horizons；共同样本规则约束两个 Analysis。`basis_quintile_forward_returns` 的 quintile probabilities 固定为 `{0.2, 0.4, 0.6, 0.8}`。

```text
CSI1000 IM Basis History public result
        ↓
daily_basis_predictor + forward_return_panel
        ↓
linear_association + basis_quintile_forward_returns
        ↓
retained Research Evidence
```

### Observation: `daily_basis_predictor`

本 Observation 为输入区间内每个实际 CSI1000 trade date 形成 basis predictor observation。它消费 Snapshot public result 中该日期完整且唯一的 M0/M1/Q1/Q2 panel，以及同一 result 的 `underlying_close`；使用 [shared Research authority](../../shared/im_basis/ARCHITECTURE.md) 定义的：

```text
non_front_mean_basis_T
= mean(M1, Q1, Q2 annualized_basis_pct)
```

其 semantic output 至少是 `trade_date`、`underlying_close` 与 finite `non_front_mean_basis`。`M0` 严格排除于 V1 predictor。每个日期的四槽 panel 必须完整且唯一，basis 与 close 必须可定义；同一日期四槽的 `underlying_close` 必须唯一且一致。发现缺槽、重复、冲突或不可计算值是 upstream contract violation，整次 run 失败；Research 不删行、填补或重新选择合约。输入尾部不进入共同 predictor sample 的合法日期仍可作为 Observation 存在并提供 future support。M0 convergence 或 near-delivery behavior 是未来独立 Research，不属于本 Study。

### Observation: `forward_return_panel`

本 Observation 从同一 Snapshot result 的 CSI1000 实际交易 observation path 构造 future-return outcomes。对每个 `h ∈ H` 与存在相应后续 observation 的日期 `T`：

```text
forward_return_h_pct
= (underlying_close[T+h] / underlying_close[T] - 1) * 100
```

`T+h` 是同一输入 result 中 `T` 之后第 `h` 条实际 CSI1000 trading observation，不是 calendar day。结果单位是 percentage points，不使用 log return，不访问 requested end 之外的数据。Forward return 是本 Study 的 outcome definition，不上提为 Snapshot field。

Semantic output 至少以 `trade_date` 关联可定义的 `forward_return_1_pct`、`forward_return_3_pct`、`forward_return_5_pct`、`forward_return_10_pct`、`forward_return_15_pct` 与 `forward_return_20_pct`。尾部日期缺少某些 horizon outcome 时，不制造收益值；这些日期仍可支持更早日期的 forward return。只有拥有完整 20D outcome 的 `T` 才能进入两个 Analysis 的共同 predictor sample。输入 observation path 或 underlying close 违反 Snapshot public contract 时整次失败，不在 Research 内删行或填补。

### Analysis: `linear_association`

本 Analysis 显式消费 `daily_basis_predictor` 和 `forward_return_panel`，回答 predictor 与各 horizon subsequent return 的 descriptive linear association。其 population 是输入区间内具有完整 20D future support 的 common eligible predictor dates：

```text
T exists in the input result
+ complete M0/M1/Q1/Q2 upstream panel and finite predictor exist
+ 20 subsequent CSI1000 observation dates exist in the same result
```

所有 horizon 使用完全相同的 `T` sample，`common_sample_count >= 5`。对每个 `h ∈ H` 计算：

```text
PearsonCorr(non_front_mean_basis_T, forward_return_h_pct)

forward_return_h_pct
= alpha_h + beta_h * non_front_mean_basis_T + error
```

每个 horizon 的 evidence row 至少表达 `horizon`、`sample_count`、`pearson_correlation`、`ols_alpha`、`ols_beta` 与 `ols_r_squared`。Pearson 与带截距 simple OLS 仅描述 direction、linear magnitude 与 simple explanatory power，不表达 causality、statistical significance、trading edge 或 forecast model。V1 不报告 p-value、t-statistic、confidence interval 或未校正的 significance claim。

### Analysis: `basis_quintile_forward_returns`

本 Analysis 显式消费 `daily_basis_predictor` 和 `forward_return_panel`，使用与 `linear_association` 完全相同的 common predictor sample，观察不同 basis state 的 subsequent-return distribution、monotonic pattern 与可能的非线性。在该完整 sample 上，按 [shared linear-interpolation convention](../../shared/distribution/ARCHITECTURE.md) 计算 `non_front_mean_basis` 的 P20、P40、P60、P80。同一组 numeric breakpoints 应用于所有 horizon，并按数值阈值分组：

```text
Q1: x <= P20                         deepest discount / lowest basis
Q2: P20 < x <= P40
Q3: P40 < x <= P60
Q4: P60 < x <= P80
Q5: P80 < x                          highest basis
```

边界值归入较低组；相同 predictor 值不被人为拆分到不同 state。对每个 `basis_quintile × horizon` 至少计算：

```text
sample_count
mean_forward_return_pct
median_forward_return_pct
positive_return_rate
```

```text
positive_return_rate
= count(forward_return_h_pct > 0) / sample_count
```

零收益进入 denominator，但不计为 positive。`positive_return_rate` 是本 sample 的 historical empirical conditional rate，不是 forward-looking forecast probability。阈值 ties 若导致任一 quintile empty，整次 run 失败。Quintile 不命名为 buy/sell zone、bullish/bearish 或 cheap/expensive。

### Run validity

必须有足够 observation dates 形成完整 20D target，且 `common_sample_count >= 5`。若 predictor 或任一 horizon outcome 无方差、阈值 ties 导致任一 quintile 为空、任何必需统计量不可定义，或存在 upstream Snapshot contract violation，整次 retained run 必须显式报告相应失败。不输出部分 evidence、空统计值、推测值或缩短后的 horizon set。

### Retained run identity

本 Study 的 semantic request 由显式 start/end dates 决定；predictor、horizons、quintiles 与 Analyses 均为固定 canonical Method，不是 invocation parameters。相同规范日期区间使用 [Research UI authority](../../ui/ARCHITECTURE.md) 已记录的 `<start_trade_date>__<end_trade_date>` deterministic run key。`--overwrite` 不改变 semantic request 或 run identity；collision 与 output placement 遵循 Research UI authority。

## Results

尚未运行真实研究，当前无统计结果、plot 或 finding，本节不使用 placeholder 数值。

两个 named Observations 与两个 named Analyses 是 Study-local semantic components，V1 不要求独立 materialized 或 retained component Artifacts。整次成功 run 至少保留 machine-readable result、human-readable report/table 与 static visualization，并包含以下可复核 evidence；具体 filename 与 serialization 不构成稳定语义契约：

```text
Sample summary
    requested_start_trade_date
    requested_end_trade_date
    effective_predictor_start_trade_date
    effective_predictor_end_trade_date
    source_observation_count
    common_sample_count
    future_support_only_count = 20
    horizons = 1, 3, 5, 10, 15, 20 trading observations
    predictor identity = non_front_mean_basis

Quintile breakpoint evidence
    P20
    P40
    P60
    P80

Association summary table
    horizon
    pearson_correlation
    ols_alpha
    ols_beta
    ols_r_squared
    sample_count

Quintile table
    basis_quintile
    horizon
    sample_count
    mean_forward_return_pct
    median_forward_return_pct
    positive_return_rate
```

`source_observation_count` 是完整 Snapshot result 中的实际 CSI1000 observation dates 数；`future_support_only_count` 是输入尾部只提供 future support、未进入 common predictor sample 的日期数。在 Snapshot result 的完整连续实际 observation sequence 与成功 run 的固定 20D maximum horizon 下，`source_observation_count = common_sample_count + future_support_only_count = common_sample_count + 20`。Retained evidence 必须能复核这一路径及当次 Q1–Q5 的实际 numeric boundaries，不能仅有 quintile label。

Static visualization 可展示 predictor-vs-forward-return scatter 与 simple OLS line、correlation-by-horizon 或 quintile forward-return comparison。Plot 是 Research evidence presentation，不是 production UI。

Retained result 仍是 exploratory Research Evidence。`positive_return_rate` 必须作为 historical empirical rate 保留，不得呈现为 forecast probability；结果不得直接输出 forecast、expected-return signal、forward-looking probability、confidence、model score 或 trading action。

## Limitations

- 3 / 5 / 10 / 15 / 20D 的每日 forward-return windows 会重叠，observations 并非严格独立。V1 不做校正，Pearson 与 OLS 只是 exploratory association baseline。
- Quintile boundaries 与 OLS 都基于同一 historical sample；V1 是 in-sample evidence，不证明 out-of-sample predictive power。
- Association 不等于 causality，也不自动意味存在可交易 edge。
- `mean(M1, Q1, Q2)` 是 V1 Research choice。Individual slots、median、weighted mean、term-structure slope/curvature 与 `M0` 都是未来独立扩展。
- Snapshot `annualized_basis_pct` 使用 simple linear annualization；本 Study 沿用该事实，不重新解释或改写。

Future statistical improvements 可以包括 HAC / Newey-West inference、bootstrap、robustness tests、out-of-sample evaluation、rolling regression、alternative predictors 与 nonlinear methods，但全部不属于 V1。

### Research / Modeling boundary

```text
CSI1000 IM Basis History
        ↓
daily non-front basis predictor
        +
CSI1000 simple forward returns
        ↓
Pearson + simple OLS + quintile statistics
        ↓
retained Research Evidence
```

本 Study 定位为 association / predictive-association research，不是 production forecast model。如果未来 evidence 显示 basis 具有稳定预测价值，仍必须经过 `Evidence → Semantic Decision → Modeling Authority`；本 Study 不建立 Research 到 Modeling 的 runtime dependency 或自动 promotion。

### Strict non-goals

```text
HAC / Newey-West or bootstrap
p-value / significance framework
out-of-sample testing or rolling regression
machine learning or nonlinear model
production forecast model
trading strategy or PnL backtest
M0 arbitrage research
HTTP endpoint or frontend
generic statistics or feature framework
database or cache
```

## Acceptance

- 显式且有效的含端点日期区间通过 Snapshot public boundary 产生完整四槽 panel；`non_front_mean_basis` 由 shared IM-basis authority 定义，不消费 Baseline Study 的 retained result。
- `daily_basis_predictor` 与 `forward_return_panel` 供两个 named Analyses 消费；六个 horizon 共用满足 20 条后续实际 observations 且 `common_sample_count >= 5` 的 predictor sample。每个 horizon 的 forward return、Pearson、带截距 OLS 与 quintile 条件统计符合 Method。样本、方差、quintile、必需统计量或 Snapshot contract 不满足时整次 run 失败，不保留部分 evidence。
- 成功结果至少保留 Results 已列的 sample / provenance summary、numeric quintile breakpoints、association summary table、quintile table、human-readable evidence 与 static visualization；输入 observation 数、共同样本及尾部 support 数可相互复核。`positive_return_rate` 只作为 historical empirical rate 呈现；图形和文字不作显著性、因果、预测或交易结论。
