# IM Annualized Basis Baseline retained study authority

本文档是 `IM Annualized Basis Baseline` 的 retained-study authority。Research 边界与 retained-study identity 见 [market-research architecture](../../ARCHITECTURE.md)；共用 predictor 见 [IM Basis Research Semantics](../../shared/im_basis/ARCHITECTURE.md)；quantile convention 见 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md)；输入产品见 [CSI1000 IM Basis History](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md)。

对应 executable implementation 位于 [im_basis_baseline package](../../src/market_research/studies/im_basis_baseline/__init__.py)；其 public Study ID 为 `im-basis-baseline`。本文件保有 Study 语义与 retained evidence 的 canonical ownership。

## Question

> 历史上，不同 IM term-structure slot 的 annualized basis 通常处于什么水平，其分布、稳定性和期限结构有何特征？

该问题为 sibling `IM Basis Forward Return Association` Study 建立 predictor distribution understanding，但本 Study 不研究未来收益或预测能力，也不向后者提供 persisted result dependency。

## Inputs

Study-local CLI 必须以显式 `start_trade_date` 与 `end_trade_date` 调用 `CSI1000 IM Basis History` 的 public Python application boundary，再把完整 semantic result 交给 Study。Study computation 不组合 Snapshot dependency；Study run 必须记录 result 携带的实际 query bounds。

Research 直接使用 Snapshot 提供的：

```text
trade_date
contract_slot
annualized_basis_pct
```

并可在 diagnostic 输出中保留其他 result facts。Research 不重新定义 slot、days-to-delist 或 basis formula，不读取 Snapshot Capture、Raw、Preparation internals、persistence layout 或 HTTP DTO。

## Method

### Daily series

按 `trade_date` 组织输入，为 `M0`、`M1`、`Q1`、`Q2` 四个 slot 分别形成每日 `annualized_basis_pct` 序列。

输入 product 已保证每个 observation date 四槽完整且唯一。Study 不定义缺槽填补、partial-date retention 或基于 liquidity 的二次筛选；若 consumer 看到缺槽或重复 slot，应作为 upstream contract violation 失败。

### Shared Research aggregate

对每个交易日计算 [shared Research authority](../../shared/im_basis/ARCHITECTURE.md) 定义的 `non_front_mean_basis`。本 Study 不重新定义公式、slot 选择或单位。

### Baseline statistics

对 `M0`、`M1`、`Q1`、`Q2` 和 `non_front_mean_basis` 五个 daily series 分别计算：

```text
count
mean
median
standard_deviation

P05
P10
P25
P50
P75
P90
P95

min
max
```

Canonical statistical conventions：

- `standard_deviation` 使用 sample standard deviation（`ddof = 1`）；当 `count < 2` 时该 run 不足以产生完整 baseline，应显式失败，不输出猜测值。
- `Pxx` 使用 [shared distribution authority](../../shared/distribution/ARCHITECTURE.md) 定义的 linear-interpolation empirical quantile convention。
- `median` 与 `P50` 都保留；两者使用该共享 convention，其数值必须一致。
- 所有值保持 Snapshot `annualized_basis_pct` 的 percentage points annualized 单位。

### Allowed retained outputs

除统计表外，Study 可以保留 per-series time-series plot、histogram / empirical distribution 和 term-structure comparison plots。图形仅呈现 descriptive evidence，不增加交易阈值、signal zone 或 directional label。

## Execution

Stable Study ID 为 `im-basis-baseline`。从 repository root 通过统一 CLI 运行：

```bash
poetry run python dev.py research run im-basis-baseline --start 2024-01-01 --end 2026-01-01
```

`--start` 与 `--end` 为 required inclusive `YYYY-MM-DD` dates，不使用 today/latest/default。同一日期区间的 canonical run directory 已存在时默认失败；显式 `--overwrite` 才允许事务性替换。完整参数帮助由以下命令生成：

```bash
poetry run python dev.py research run im-basis-baseline --help
```

## Results

尚未运行真实研究，当前无统计结果、plot 或 finding。本节不使用 placeholder 数值。未来首次 retained run 必须与 query bounds、方法版本和输出共置，并在结果变成项目语义之前继续作为 Research evidence。

## Limitations

- `annualized_basis_pct` 使用 simple linear annualization；不是 log 或 continuously compounded yield。
- `annualization_days` 在交割日为 1，且近到期的线性年化会放大小幅非年化基差；这是展示和解释限制，不得在 Study 中改写 Snapshot 公式。
- 样本区间由每次 run 的显式 query bounds 决定，不代表所有市场环境。
- Baseline 是 descriptive / exploratory evidence，不证明 causal relation、tradability 或 predictive power。

## Strict non-goals

```text
future return
predictive correlation
regression
trading signal
arbitrage rule
PnL backtest
market regime
bullish / bearish classification
recommendation
```

即使 `M0` 呈现 convergence anomaly，本 Study 也只能把它保留为 finding 或 future research question，不得自动提升为套利规则、Modeling semantic 或 production decision。
