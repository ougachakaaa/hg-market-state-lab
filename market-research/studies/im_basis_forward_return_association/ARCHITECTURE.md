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

## Method

### Daily predictor

每个 candidate trade date `T` 使用 [shared Research authority](../../shared/im_basis/ARCHITECTURE.md) 定义的：

```text
non_front_mean_basis_T
= mean(M1, Q1, Q2 annualized_basis_pct)
```

`M0` 严格排除于 V1 predictor。M0 convergence 或 near-delivery behavior 是未来独立 Research，不属于本 Study。

### CSI1000 forward-return targets

Canonical horizons：

```text
H = {1, 3, 5, 10, 15, 20}
```

全部 horizon 表示输入 result 中的 CSI1000 subsequent trading observations，不是 calendar days。对 observation date `T`，`T+h` 是 result 中 `T` 之后第 `h` 个 CSI1000 observation trade date。

V1 target 是 simple forward return：

```text
forward_return_h_pct
= (underlying_close[T+h] / underlying_close[T] - 1) * 100
```

单位是 percentage points，不使用 log return。每个 trade date 在四槽 observation 中的 `underlying_close` 必须唯一且一致；否则作为 upstream contract violation 失败。Forward return 是本 Study 的 outcome definition，不上提为 Snapshot field。

### Common eligible sample

一个 trade date `T` 当且仅当满足以下条件时进入 predictor sample：

```text
T exists in the input result
+ M0/M1/Q1/Q2 complete upstream panel exists
+ non_front_mean_basis_T can be computed
+ at least 20 subsequent CSI1000 observation dates exist
   inside the same input result
```

因此六个 horizon 使用完全相同的 `T` sample。输入尾部最多 20 个 observation dates 可以仅作为 future-return support dates，不是 predictor observations。Study 不把 calendar day 当作 trading observation，不自动到 requested bounds 之外获取 future data，也不缩短 horizon。

### Pearson correlation

对每个 `h ∈ H` 计算：

```text
PearsonCorr(non_front_mean_basis_T, forward_return_h_pct)
```

每行至少表达 `horizon`、common `sample_count` 和 `pearson_correlation`。Pearson 只表达 linear association，不表达 causality 或可交易预测能力。

### Simple OLS

对每个 horizon 独立拟合带截距的：

```text
forward_return_h_pct
= alpha_h
+ beta_h * non_front_mean_basis_T
+ error
```

每行至少表达 `horizon`、common `sample_count`、`alpha`、`beta` 和 `r_squared`。V1 不报告 p-value、t-statistic、confidence interval 或未校正的 significance claim；OLS 只用于描述 direction、linear magnitude 与 simple explanatory power。

### Basis-quintile conditional statistics

在完整 common eligible predictor sample 上，按 [shared linear-interpolation convention](../../shared/distribution/ARCHITECTURE.md) 计算 `non_front_mean_basis` 的 P20、P40、P60、P80。同一组 breakpoints 应用于所有 horizon，并按数值阈值分组：

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

零收益不计为 positive。Quintile analysis 只用于观察 monotonic pattern、可能的非线性，以及不同 basis state 的 subsequent-return distribution；不将 quintile 命名为 buy/sell zone、bullish/bearish 或 cheap/expensive。

### Run validity

必须有足够 observation dates 形成包含 20D target 的 common sample。如果 common sample 太小、predictor 或任一 horizon outcome 无方差、阈值 ties 导致任一 quintile 为空，或任何必需统计量不可定义，整次 retained run 必须显式报告样本或变异不足并失败。不输出部分 evidence、空统计值、推测值或缩短后的 horizon set。

## Execution

Stable Study ID 为 `im-basis-forward-return-association`。从 repository root 通过统一 CLI 运行：

```bash
poetry run python dev.py research run im-basis-forward-return-association --start 2024-01-01 --end 2026-01-01
```

`--start` 与 `--end` 为 required inclusive `YYYY-MM-DD` dates，不使用 today/latest/default。同一日期区间的 canonical run directory 已存在时默认失败；显式 `--overwrite` 才允许事务性替换。完整参数帮助由以下命令生成：

```bash
poetry run python dev.py research run im-basis-forward-return-association --help
```

## Results

尚未运行真实研究，当前无统计结果、plot 或 finding，本节不使用 placeholder 数值。

未来每次成功 retained run 至少保留：

```text
Sample summary
    requested start_trade_date
    requested end_trade_date
    effective predictor start_trade_date
    effective predictor end_trade_date
    common sample_count
    horizons = 1, 3, 5, 10, 15, 20 trading observations
    predictor identity = non_front_mean_basis

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

允许保留 predictor-vs-forward-return scatter 与 simple OLS line、correlation-by-horizon 及 quintile forward-return comparison。Plot 是 Research evidence presentation，不是 production UI。

Retained result 仍是 exploratory Research Evidence，不得直接输出 forecast、expected-return signal、probability、confidence、model score 或 trading action。

## Limitations

- 3 / 5 / 10 / 15 / 20D 的每日 forward-return windows 会重叠，observations 并非严格独立。V1 不做校正，Pearson 与 OLS 只是 exploratory association baseline。
- Quintile boundaries 与 OLS 都基于同一 historical sample；V1 是 in-sample evidence，不证明 out-of-sample predictive power。
- Association 不等于 causality，也不自动意味存在可交易 edge。
- `mean(M1, Q1, Q2)` 是 V1 Research choice。Individual slots、median、weighted mean、term-structure slope/curvature 与 `M0` 都是未来独立扩展。
- Snapshot `annualized_basis_pct` 使用 simple linear annualization；本 Study 沿用该事实，不重新解释或改写。

Future statistical improvements 可以包括 HAC / Newey-West inference、bootstrap、robustness tests、out-of-sample evaluation、rolling regression、alternative predictors 与 nonlinear methods，但全部不属于 V1。

## Research / Modeling boundary

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

## Strict non-goals

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
