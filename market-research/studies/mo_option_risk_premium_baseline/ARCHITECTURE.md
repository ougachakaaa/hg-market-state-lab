# MO Option Risk Premium Baseline retained Study authority

## Identity

本文件是 `mo_option_risk_premium_baseline` 的 canonical Study entry；stable public Study ID 为 `mo-option-risk-premium-baseline`。本 Study 预期成为 runnable retained Study，未来 executable package 位于 `market-research/src/market_research/studies/mo_option_risk_premium_baseline/`。当前仅有研究设计，尚无 executable implementation 或真实 retained evidence。

创建与审查遵循 [Study Authority Authoring](../AUTHORING.md)、[Study Schema](../SCHEMA.md) 与 [Study Review](../REVIEW.md)；Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI、配置及 output placement 见 [Research UI authority](../../ui/ARCHITECTURE.md)。

## Question

> 卖出 MO 期权并持有至到期时，entry 日的期权价格 proxy 相对于事后到期赔付 proxy，历史上留下多少卖方 realized compensation？它随 entry DTE、underlying-relative moneyness 和 CALL／PUT 如何变化？

本 Study 是 descriptive empirical baseline，不预设 compensation 的方向。它比较各 expiry 的 compensation 分布、正负频率和尾部损失，不声称测得严格的 risk-neutral probability premium、策略收益或可执行交易价格。

## Method 与预期证据概览

具名 Observation ExpiryDteOptionOutcome 为每个 expiry × target DTE × CALL／PUT × moneyness target 建立至多一个代表性合约的到期 outcome。DteCompensationProfile 与 MoneynessCompensationProfile 两个 Analysis 均消费它，分别以 DTE 和 moneyness 为主要呈现轴。选择、proxy、排除和统计的唯一契约见 [Method](METHOD.md)。

预期保留由 Observation 定义的 `option_outcome_panel`，以及由两个 Analyses 定义的 `compensation_summary` 和 `risk_premium_report`，供逐行复核、机器读取与人工观察。1 个 retained Observation Artifact 与 2 个 retained Evidence Products 的 ownership、必需内容和空结果处理见 [Results](RESULTS.md)。

```text
Inputs → ExpiryDteOptionOutcome ──→ retained Observation Artifact: option_outcome_panel
                ├──→ DteCompensationProfile ───────┐
                └──→ MoneynessCompensationProfile ──┴──→ Evidence Products:
                                                         compensation_summary
                                                         risk_premium_report
```

## Dependency status

Dependency Reconciled：现有 Index Daily History 公开结果提供历史窗口内真实交易日与 CSI1000 close；Study-local CLI 对这些日期调用 MO Option Chain 公开单日结果，从 active expiry groups 确定真实出现的 MO expiry 与各 expiry 可观察 entry dates。多个 public Snapshot calls 可能较慢，但不是 semantic capability gap；option volume 仍只是非阻塞的可选质量 metadata。discovery window、事实、failure 边界及 owner 见 [Inputs](INPUTS.md)。

## Limitations

- `(high + low) / 2` 是 standardized daily estimator，不是 VWAP、mid quote 或 executable price；option 与 underlying 的 high／low 也不保证发生在同一盘中时刻。
- CSI1000 expiry-day close 不是 CFFEX 精确期权结算价，故 `expiry_payoff_proxy` 及 compensation 均是 proxy。相同 expiry 的不同日期、strike、CALL／PUT 共享同一终值事件，contract count 不是独立市场事件数。
- 年化 ratio 仅作期限归一化比较，不是 portfolio CAGR、保证金回报、资本回报或可实现的年化策略收益。
- 本 Study 不观察盘中路径、mark-to-market 压力、强平、止损、止盈、展期、动态／Delta 对冲、交易成本、滑点、保证金、融资或资本占用。正的 terminal compensation 不表示持有路径无风险。
- 不按市场、IV、basis、趋势或波动 regime 条件化；不估计 risk-neutral／physical density 或两者的概率差。`premium - realized payoff` 不能直接解释为 risk-neutral probability premium，也不足以推导连续重复策略的完整期望收益。

## Acceptance

- 六个 semantic areas、Study identity、参数 owner／consumer、CLI 契约、run identity、Observation → Analysis → Evidence Product 路径均在当前 Study authority graph 中有唯一 canonical owner；不依赖 sibling Study 的研究语义。
- `moneyness_targets >= 0`，负值为 CLI／Study input failure；每个 expiry × target DTE × type × target moneyness 至多一个有效 observation。最近日期及合约的 tie-break 确定，target、actual 与误差均保留；有效 observation 必须满足 `abs(dte_error) <= 5` calendar days 和 `abs(moneyness_error) <= 0.025`，超限以具名 reason 排除。
- 可从 panel 逐行复核 high／low entry proxy、expiry close payoff proxy 和三种 compensation；缺失、无效或不一致的事实有可计数原因，不改选次近候选、不插值、不伪造。
- 两个 Analysis 均只消费具名 Observation，跨 expiry 等权；每个 cell 报 sample 与 unique expiry counts、coverage、空值、分位数和尾部最小值；CALL／PUT 不混合，重复合约及同 expiry 的多个 cell 不宣称独立。
- 1 个 retained Observation Artifact 与 2 个 retained Evidence Products 保留请求与上游 provenance、逐 cell 审计、可追踪的统计／图示及解释限制。整次零有效样本失败；尚无真实 evidence 时不预写结果。
- 历史发现只组合现有 Snapshot public application results；公开请求失败为整次 Study 失败，缺少容差内 entry date 为 cell exclusion，不把前者当作后者。Option volume 缺失不阻塞 implementation；Study Authority Completeness Gate 按 [Study Review](../REVIEW.md) 逐项复核。

## Authority Navigation

- [Inputs](INPUTS.md)：population、上游事实、参数与 CLI、规范化、run identity 和 dependency reconciliation。
- [Method](METHOD.md)：Observation、Analyses、选择与有效性、统计及组件 Artifact identity。
- [Results](RESULTS.md)：retained Observation Artifact 与 Evidence Products、provenance、空结果及呈现。

本入口遵循 [Study Authoring](../AUTHORING.md)、[Schema](../SCHEMA.md)、[Skeleton](../SKELETON.md) 与 [Review](../REVIEW.md)；既有 Study 的触发式 reconciliation 遵循 [Compatibility](../COMPATIBILITY.md)。Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI 与 output placement 见 [Research UI authority](../../ui/ARCHITECTURE.md)。
