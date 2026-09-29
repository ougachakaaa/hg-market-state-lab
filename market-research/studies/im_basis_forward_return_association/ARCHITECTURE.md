# IM Basis Forward Return Association retained study authority

本文档是 `IM Basis Forward Return Association` 的稳定 canonical entry。Research 边界见 [market-research architecture](../../ARCHITECTURE.md)；详细 analytical semantics 由 [Method](METHOD.md) 拥有，retained evidence contract 由 [Results](RESULTS.md) 拥有。对应 executable implementation 位于 [im_basis_forward_return_association package](../../src/market_research/studies/im_basis_forward_return_association/__init__.py)。

## Question 与 scope

> T 日 IM 非近月期限结构的整体年化基差水平，与 CSI1000 随后 1 / 3 / 5 / 10 / 15 / 20 个交易 observation 的收益之间存在多大程度的关联？

Public Study ID 为 `im-basis-forward-return-association`。V1 通过简单、可解释的线性与分组证据建立 historical association baseline，不是最终统计方法或 production forecast model。本 Study 与 `IM Annualized Basis Baseline` 是 sibling retained studies；两者均直接消费 Snapshot public result，本 Study 不依赖 Baseline Study 的 persisted result。

## Inputs 与 invocation

Study-local CLI 以显式、含端点的 `start_trade_date` 与 `end_trade_date` 请求 [CSI1000 IM Basis History](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md) 的 public Python application boundary，并把完整 semantic result 交给 Study。两项日期是本 Study 的 request / population bounds，限定两个 Observation 与两个 Analysis；没有 implicit latest/today、默认区间或 query-range fallback。Study computation 不组合 Snapshot dependency。

```bash
lab research run im-basis-forward-return-association --start 2024-01-01 --end 2026-01-01
lab research run im-basis-forward-return-association --help
```

`--start` 与 `--end` 均必填，分别映射为 `start_trade_date` 与 `end_trade_date`。只接受有效日历日期的规范 `YYYY-MM-DD` 表达，且 start 不晚于 end；省略、无效或逆序日期必须失败。规范化后的这两个日期构成整次 Study semantic request 和唯一可变的 run-identity 输入；deterministic run key 为 `<start_trade_date>__<end_trade_date>`。相同规范日期区间得到相同 key，不同日期区间得到不同 key。`--overwrite` 是显式 execution option，不改变研究语义或 run identity。Predictor、horizons、minimum common sample rule 与 quintile probabilities 是固定 [Method](METHOD.md) semantics，不是 invocation inputs。

同一 canonical run directory 已存在时默认在 Snapshot 调用前失败；显式 `--overwrite` 才允许整目录事务性替换。共享 output placement、collision detection 与 replacement mechanics 由 [Research UI authority](../../ui/ARCHITECTURE.md) 拥有。

Research 只消费 Snapshot public result 的 `trade_date`、`contract_slot`、`underlying_close` 与 `annualized_basis_pct`。Snapshot 拥有完整 M0/M1/Q1/Q2 panel、CSI1000 实际交易 observation 顺序及 slot、basis、annualization semantics；Research 不读取 Raw、Capture、Preparation internals 或 persistence path，不经 backend-api / HTTP 获取内部业务数据，也不重算这些上游事实。

## Component → evidence map

两个具名 Observation 均从同一 Snapshot result 构造：[Method](METHOD.md) 中的 `daily_basis_predictor` 形成非近月年化基差 predictor，`forward_return_panel` 形成六个实际交易 observation horizon 的 CSI1000 收益。共同样本的唯一 Method-level eligibility rule 同时约束以下两个 Analysis：

```text
daily_basis_predictor + forward_return_panel
    → linear_association
    → linear direction / magnitude evidence

daily_basis_predictor + forward_return_panel
    → basis_quintile_forward_returns
    → conditional distribution / nonlinear-pattern evidence
```

两个 Analysis 的统计含义与失败条件见 [Method](METHOD.md)；其 sample / provenance summary、association summary、numeric quintile breakpoints、quintile table、human-readable report/table 与 static visualization 见 [Results](RESULTS.md)。

## Dependencies 与 limitations

现有 [IM Basis Research Semantics](../../shared/im_basis/ARCHITECTURE.md) 拥有 `non_front_mean_basis` predictor，[Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md) 拥有 empirical quantile 的 linear-interpolation convention。本既有 Study 合法保留两项 shared dependency；其余 sample、outcome、analysis 与 evidence semantics 由本 Study 拥有。

**Dependency Reconciled：** Snapshot 的 [public read/application contract](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/read-contract.md) 已提供所需字段、完整四槽 panel、按产品规则排序的 observation result 和 production-ready public execution entry；[observation-date authority](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/data.md) 与 [basis authority](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/im-basis-semantics.md) 已拥有交易日、slot 和年化基差事实。本 Study 不需要新增 Snapshot capability，也不得越过该 public boundary。

Forward-return windows 会重叠，Pearson 与 OLS 只是未经重叠校正的 exploratory association；quintile boundaries 与 OLS 均来自同一 historical sample，不证明 out-of-sample predictive power。Association 不等于 causality 或可交易 edge；`positive_return_rate` 是 historical empirical rate，不是 forecast probability。`mean(M1, Q1, Q2)` 是 V1 predictor choice，M0 convergence、其他 predictor、HAC / bootstrap、significance framework、rolling / out-of-sample evaluation、模型、策略和 PnL backtest 均不属于本 Study。Snapshot 的 simple linear annualization 保持其上游含义。本 Study 不产生 forecast、signal、trading action，也不建立 Research 到 Modeling 的自动 promotion 或 runtime dependency。

## Acceptance 与 readiness

- 有效的含端点日期请求只经 Snapshot public boundary 取得完整 result；无效请求和上游 contract violation 明确失败。
- [Method](METHOD.md) 中两个 Observation、两个 Analysis、共享的完整 20D common eligible predictor sample、六个固定 horizons 与 `common_sample_count >= 5` 均可执行；任一必需统计量无定义时整次失败，不保留部分 evidence。
- 成功运行保留 [Results](RESULTS.md) 规定的机器可读与人可读证据、numeric quintile boundaries、可复核的 sample / provenance 关系及静态图；文字和图形遵守上述解释限制，不作显著性、因果、预测或交易结论。

本 Study 的 Question、Inputs、Method、Results、Limitations 与 Acceptance 各有明确 owner；实施所需上游能力已核对。因此 **Study Authority Complete**、**Dependency Reconciled**，本 Study **Implementation Ready**。
