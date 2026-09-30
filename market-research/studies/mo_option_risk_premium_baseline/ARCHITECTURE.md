# MO Option Risk Premium Baseline retained Study authority

## Identity

本文件是 `mo_option_risk_premium_baseline` 的 canonical Study entry；stable public Study ID 为 `mo-option-risk-premium-baseline`。本 Study 预期成为 runnable retained Study，未来 executable package 位于 `market-research/src/market_research/studies/mo_option_risk_premium_baseline/`。当前仅有研究设计，尚无 executable implementation 或真实 retained evidence。

创建与审查遵循 [Study Authority Authoring](../AUTHORING.md)、[Study Schema](../SCHEMA.md) 与 [Study Review](../REVIEW.md)；Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI、配置及 output placement 见 [Research UI authority](../../ui/ARCHITECTURE.md)。

## Question

> 卖出 MO 期权并持有至到期时，entry 日的期权价格 proxy 相对于事后到期赔付 proxy，历史上留下多少卖方 realized compensation？它随 entry DTE、underlying-relative moneyness 和 CALL／PUT 如何变化？

本 Study 是 descriptive empirical baseline，不预设 compensation 的方向。它比较各 expiry 的 compensation 分布、正负频率和尾部损失，不声称测得严格的 risk-neutral probability premium、策略收益或可执行交易价格。

## Method 与预期证据概览

具名 Observation ExpiryDteOptionOutcome 为每个 expiry × target DTE × CALL／PUT × moneyness target 建立至多一个代表性合约的到期 outcome。DteCompensationProfile 与 MoneynessCompensationProfile 两个 Analysis 均消费它，分别以 DTE 和 moneyness 为主要呈现轴。选择、proxy、排除和统计的唯一契约见 [Method](METHOD.md)。

预期保留 option_outcome_panel、compensation_summary 和 risk_premium_report，供逐行复核、机器读取与人工观察。三个 Evidence Product 的 defined_by、必需内容和空结果处理见 [Results](RESULTS.md)。

## Dependency status

现有 MO Option Chain 提供单日 high／low chain facts，Index Daily History 提供 CSI1000 历史 close；但 Snapshot 尚无公共能力发现指定到期日范围内的全部真实 MO expiry 及各 expiry 可用的历史 entry 交易日。这是 implementation 的阻塞性 dependency gap，须由 Snapshot owner 后续 reconciliation；Study 不越过其 public boundary 自行发现。Option volume 只是非阻塞的可选质量 metadata。详细事实、能力与 owner 见 [Inputs](INPUTS.md)。

## Limitations

- `(high + low) / 2` 是 standardized daily estimator，不是 VWAP、mid quote 或 executable price；option 与 underlying 的 high／low 也不保证发生在同一盘中时刻。
- CSI1000 expiry-day close 不是 CFFEX 精确期权结算价，故 `expiry_payoff_proxy` 及 compensation 均是 proxy。相同 expiry 的不同日期、strike、CALL／PUT 共享同一终值事件，contract count 不是独立市场事件数。
- 年化 ratio 仅作期限归一化比较，不是 portfolio CAGR、保证金回报、资本回报或可实现的年化策略收益。
- 本 Study 不观察盘中路径、mark-to-market 压力、强平、止损、止盈、展期、动态／Delta 对冲、交易成本、滑点、保证金、融资或资本占用。正的 terminal compensation 不表示持有路径无风险。
- 不按市场、IV、basis、趋势或波动 regime 条件化；不估计 risk-neutral／physical density 或两者的概率差。`premium - realized payoff` 不能直接解释为 risk-neutral probability premium，也不足以推导连续重复策略的完整期望收益。

## Acceptance

- 六个 semantic areas、Study identity、参数 owner／consumer、CLI 契约、run identity、Observation → Analysis → Evidence Product 路径均在当前 Study authority graph 中有唯一 canonical owner；不依赖 sibling Study 的研究语义。
- 每个 expiry × target DTE × type × target moneyness 至多一个有效 observation；最近日期及合约 tie-break 确定，target 与 actual 及误差均保留。未设偏差上限不会被实现暗中加入筛选阈值。
- 可从 panel 逐行复核 high／low entry proxy、expiry close payoff proxy 和三种 compensation；缺失、无效或不一致的事实有可计数原因，不改选次近候选、不插值、不伪造。
- 两个 Analysis 均只消费具名 Observation，跨 expiry 等权；每个 cell 报 sample 与 unique expiry counts、coverage、空值、分位数和尾部最小值；CALL／PUT 不混合，重复合约及同 expiry 的多个 cell 不宣称独立。
- 三个 Evidence Products 保留请求与上游 provenance、可追踪的统计／图示及解释限制。整次零有效样本失败；尚无真实 evidence 时不预写结果。
- 在 Snapshot owner 提供历史发现 public capability 前，本 Study 不进入 implementation；option volume 缺失不使 authority 或 baseline 计算语义不完整。完成 CREATE 后须按 [Study Review](../REVIEW.md) 逐项通过 Study Authority Completeness Gate，再单独进行 dependency reconciliation。

## Authority Navigation

- [Inputs](INPUTS.md)：population、上游事实、参数与 CLI、规范化、run identity 和 dependency gaps。
- [Method](METHOD.md)：Observation、Analyses、选择与有效性、统计及组件 Artifact identity。
- [Results](RESULTS.md)：retained Evidence Products、provenance、空结果及呈现。

本入口遵循 [Study Authoring](../AUTHORING.md)、[Schema](../SCHEMA.md)、[Skeleton](../SKELETON.md) 与 [Review](../REVIEW.md)；既有 Study 的触发式 reconciliation 遵循 [Compatibility](../COMPATIBILITY.md)。Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI 与 output placement 见 [Research UI authority](../../ui/ARCHITECTURE.md)。
