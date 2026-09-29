# MO Option Risk Premium Baseline retained Study authority

## Identity

本文件是 `mo_option_risk_premium_baseline` 的单一 canonical Study authority；stable public Study ID 为 `mo-option-risk-premium-baseline`。本 Study 预期成为 runnable retained Study，未来 executable package 位于 `market-research/src/market_research/studies/mo_option_risk_premium_baseline/`。当前仅有研究语义，尚无 executable implementation 或真实 retained evidence。

创建与审查遵循 [Study Authority Authoring](../AUTHORING.md)、[Study Schema](../SCHEMA.md) 与 [Study Review](../REVIEW.md)；Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI、配置及 output placement 见 [Research UI authority](../../ui/ARCHITECTURE.md)。

## Question

> 卖出 MO 期权并持有至到期时，entry 日的期权价格 proxy 相对于事后到期赔付 proxy，历史上留下多少卖方 realized compensation？它随 entry DTE、underlying-relative moneyness 和 CALL／PUT 如何变化？

本 Study 是 descriptive empirical baseline，不预设 compensation 的方向。它比较各 expiry 的 compensation 分布、正负频率和尾部损失，不声称测得严格的 risk-neutral probability premium、策略收益或可执行交易价格。

## Inputs

V1 population 为 MO 中证1000股指期权及其 CSI1000（`000852.SH`）标的指数；MO → CSI1000 映射由 [MO Option Chain](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) 拥有。CALL 与 PUT 均纳入，但分别呈现。`start_expiry_date` 与 `end_expiry_date` 是含端点的到期日范围，不是 entry 日范围；只能纳入该范围内由上游 canonical facts 确认的真实 MO expiry。每个 expiry 是一次 terminal risk event。

| 输入或选项 | CLI 表达与契约 | Semantic owner；consumers；作用 |
| --- | --- | --- |
| `start_expiry_date` | `--start-expiry YYYY-MM-DD`，必填、有效日期 | Study；`ExpiryDteOptionOutcome` 与两个 Analysis；限定 expiry population，改变 evidence identity。 |
| `end_expiry_date` | `--end-expiry YYYY-MM-DD`，必填、有效日期且不早于起点 | Study；同上；限定 expiry population，改变 evidence identity。 |
| `dte_targets` | `--dte-targets`，可选的逗号分隔正整数；默认 `10,20,30,40,50,60`；非空 | `ExpiryDteOptionOutcome`；两个 Analysis 消费其 observation 的 target 轴；改变 entry 选择和 evidence identity。 |
| `moneyness_targets` | `--moneyness-targets`，可选的逗号分隔有限十进制数；默认 `0,0.05,0.10,0.15,0.20`；非空，可含负值 | `ExpiryDteOptionOutcome`；两个 Analysis 消费其 observation 的 target 轴；改变合约选择和 evidence identity。负值表示 ITM target。 |
| `overwrite` | `--overwrite`，可选布尔开关，默认 false | Study-owned execution-only option；CLI／output handling 消费，不进入 semantic request 或 run identity。 |

固定而不可配置的语义是 `option_product=MO`、`underlying=CSI1000`、CALL 与 PUT、entry high／low 均值 proxy、expiry-day index close payoff proxy。输入列表经解析、验证、去重、数值升序排序后成为 resolved target sets；省略参数与显式给出相同默认集合等价，原始空格和顺序不影响研究请求。`-0` 与 `0` 规范为同一 target。无效日期、倒置区间、空集合、非正 DTE、非有限 moneyness 或不可解析值均为输入失败。

从 repository root 的预期调用方式：

```bash
lab research run mo-option-risk-premium-baseline \
  --start-expiry 2024-01-01 --end-expiry 2026-01-01 \
  --dte-targets 10,20,30,40,50,60 \
  --moneyness-targets 0,0.05,0.10,0.15,0.20
```

### Canonical upstream facts and dependency gaps

[MO Option Chain read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 的公开单日结果具有 expiry group、CALL／PUT、instrument identity、strike、所选 `price_type` 的 option price 及 CSI1000 price。对同一 entry 日分别请求 `price_type=high` 和 `low`，按 expiry、type、instrument identity 配对，才能形成所需 high／low facts；不能把不同合约或日期的价格拼接。该产品不公开 option volume。其单日查询不能发现某一历史 expiry 范围内的全部 expiry 与可用 entry 交易日；这一历史发现能力是后续 Snapshot-owner RECONCILE 的阻塞性 dependency gap，不允许 Study 读取 Source、Raw、私有 Preparation 或其他内部路径自行补足。

[Index Daily History public contract](../../../market-snapshot/src/market_snapshot/products/index_daily_history/read-contract.md) 可按 `000852.SH` 与显式日期范围提供实际存在的 index close；本 Study 只用 expiry 当日 close，不以前一日或邻近日期替代。该产品不提供 MO expiry／entry-date 发现能力。现有 MO Chain 无 volume public fact；它只是可选 quality metadata gap，不阻止 compensation 计算。Exact option settlement、Delta、IV、Greeks 不是 V1 所需能力。

### Retained run identity

整次 semantic request identity 由规范化的 `start_expiry_date`、`end_expiry_date`、resolved `dte_targets` 与 resolved `moneyness_targets` 构成。日期用 `YYYY-MM-DD`；DTE 用十进制整数；moneyness 用无多余前后零的规范十进制字符串，不采用浮点显示文本。将这四个具名字段按固定顺序编码为 UTF-8 canonical JSON（数组为前述升序顺序），run key 为 `<start_expiry_date>__<end_expiry_date>__<该 JSON 的 SHA-256 小写十六进制摘要>`。同一规范请求得到同一 key；任一 identity-changing input 的不同规范值产生不同请求摘要。`--overwrite`、output root、运行时间、临时路径和用户原始拼写不参与。Run directory 与冲突／事务性覆盖规则沿用 Research UI authority。

## Method

### Observation: `ExpiryDteOptionOutcome`

**Purpose 与粒度。** 对每个真实 expiry、resolved target DTE、CALL／PUT 和 resolved moneyness target，最多形成一个代表性合约的 realized outcome row。它消费 Inputs 的日期和 target sets、MO Chain 公开 high／low chain facts、Index Daily History 的 expiry-day close；所有选择、proxy、moneyness 与 compensation 均为本 Study 语义。

**Entry 选择。** 在公开历史发现能力给出的、该 expiry 有上市 MO 合约且早于 expiry 的可观察交易日中，以 `abs(actual_dte - target_dte)` 最小选择 entry 日；`actual_dte = expiry_date - entry_trade_date` 的 calendar-day distance，必须大于零。等距离时取 `actual_dte` 更大的日期。没有最大 DTE 偏差；保留 `target_dte`、`actual_dte`、`dte_error = actual_dte - target_dte` 及两个日期。选中日期的价格无效时计数排除，不转选次近日期。

**合约选择。** 同一 entry 日及 expiry 内，CALL 与 PUT 分开处理。`entry_underlying_proxy = (entry_underlying_high + entry_underlying_low) / 2`，CALL 的 `otm_distance = (strike - entry_underlying_proxy) / entry_underlying_proxy`，PUT 的 `otm_distance = (entry_underlying_proxy - strike) / entry_underlying_proxy`。正、零、负分别表示 OTM、ATM、ITM。每个 type × target 选择 `abs(otm_distance - moneyness_target)` 最小的 listed contract；严格等距离时先取更 OTM（较大的 `otm_distance`），再按 `instrument_id` 字典序取最小者。没有最大 moneyness 偏差；保留 target、`actual_moneyness = otm_distance`、`moneyness_error = actual_moneyness - moneyness_target`、strike 和 identity。同一合约可以被多个 target 选中；这些不是独立风险事件。被选合约的 high／low 无效时排除该 cell，不改选次近 strike。

**Price、payoff 与 compensation。** `entry_premium_proxy = (entry_option_high + entry_option_low) / 2`；`expiry_underlying_proxy` 是 CSI1000 在 expiry 当日的 close。CALL 的 `expiry_payoff_proxy = max(expiry_underlying_proxy - strike, 0)`；PUT 为 `max(strike - expiry_underlying_proxy, 0)`。计算：

```text
seller_compensation_points = entry_premium_proxy - expiry_payoff_proxy
seller_compensation_ratio = seller_compensation_points / entry_underlying_proxy
annualized_compensation_ratio = seller_compensation_ratio * 365 / actual_dte
```

一行须保留上述原始和派生量，并保留 entry option high／low、entry underlying high／low、expiry close、option type、所有 selection identity 和 error。若后续 Snapshot public result 提供 canonical option volume，额外保留 `entry_volume` 作为 liquidity／quality metadata；volume 不加权 entry premium、不自动排除样本，也不因缺失阻止计算。

**Validity 与 exclusion。** 必须先有一致的 expiry／entry／contract 关系、同一合约的 high 与 low、有限且 `0 <= low <= high` 的 option prices、有限且 `0 < low <= high` 的 underlying prices、正的 strike、正的 `actual_dte`、以及 expiry 当日有限且正的 underlying close。缺 entry high／low、malformed price、缺 expiry close、无可选日期／type／contract、无有效 strike／underlying、以及所选合约与 expiry 关系无效，均不能制造值或使用 fallback。对每个预期的 expiry × DTE × type × target cell 保留 exclusion reason 与计数；一个 cell 可有多个诊断 reason，但 excluded-cell 总数按唯一 cell 计，不能把 reason 数之和当作排除样本数。上游整个请求失败，或 high／low chain 的日期、universe、合约 identity 等全局结构互相矛盾时，整次 Study 失败，并区分于可计数的 Study cell exclusion。

**Observation Artifact identity。** `option_outcome_panel` 独立保留该 Observation；其语义 identity 包含 `ExpiryDteOptionOutcome`、规范化的四个 Study inputs，以及所消费的 Snapshot product／query identities 与实际返回数据的 provenance。该 identity 不使用文件名、格式、运行时间或临时路径。

### Analyses

两个 Analysis 均明确消费 `ExpiryDteOptionOutcome`，只汇总有效 rows。每个 group cell 中一个 expiry 最多贡献一行；跨 expiry 等权，不按 strike 数、volume 或同 expiry 其他 DTE 加权。`sample_count` 是有效 row 数，`unique_expiry_count` 是不同 expiry 数；二者均须输出。同一 expiry 的不同 DTE、type、target 共享 terminal market event，不能跨 cell 相加解释为独立事件数。

两者共用以下 Study-local 统计定义：对 entry premium、expiry payoff、seller compensation points／ratio／annualized ratio 各报 mean 与 median；对三种 compensation 各报最小值和 P05、P25、P50、P75、P95。经验分位数对排序样本按位置 `(n-1)*p` 作相邻值线性插值，故 P50 等于 median。正／负／零 compensation frequency 分别以 `seller_compensation_points > 0`、`< 0`、`= 0` 的个数除以有效 `sample_count`。各 cell 同时给出预期 expiry 数、有效 unique expiry coverage、excluded-cell 数及 reason counts；零有效样本的统计值明确为空，不填零。无显著性检验。

| Analysis | Purpose、consumes 与 grouping | Produces |
| --- | --- | --- |
| `DteCompensationProfile` | 回答 entry DTE 的 compensation profile；消费 `ExpiryDteOptionOutcome`；按 `target_dte × option_type × moneyness_target` 分组，以 DTE 为主要呈现轴。 | 各 DTE 的等权跨 expiry 统计、分布与覆盖。 |
| `MoneynessCompensationProfile` | 回答同一 DTE 下 moneyness 差异及 CALL／PUT 对照；消费 `ExpiryDteOptionOutcome`；按 `option_type × target_dte × moneyness_target` 分组，以 moneyness 为主要呈现轴。 | DTE × moneyness compensation surface 与分布、覆盖。 |

两个 Analysis 的分组键相同，统计约定相同，但问题视角不同；可以由同一组已计算数值呈现，无须重复计算或把其视为两组独立证据。若独立物化 Analysis Artifact，其 semantic identity 分别由 Analysis stable name、所消费的完整 `ExpiryDteOptionOutcome` Artifact identity 和本节固定统计定义决定；不能仅用 Analysis 名称或文件路径标识。

## Results

以下是预期 retained Evidence Products；目前没有真实运行、数值、图形或 finding。成功 run 应与规范化请求、实际上游查询／结果 provenance、计数及排除原因共置，供人工复核。

| Evidence Product | `defined_by` | 必须保留的内容 |
| --- | --- | --- |
| `option_outcome_panel` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Machine-readable `ExpiryDteOptionOutcome` 逐 cell observation，能复核日期、合约、high／low proxy、terminal close、payoff、compensation 和误差；附 excluded-cell reason record。其行义由 Observation 定义，两个 Analysis 不改变它。 |
| `compensation_summary` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Machine-readable group identity、计数／coverage、上述 central 与 distribution statistics、空 cell、exclusion reason counts；共享统计值可只存一次并标明两个 Analysis view。 |
| `risk_premium_report` | `DteCompensationProfile`、`MoneynessCompensationProfile` | Human-readable retained report，直观显示 DTE profile、DTE × moneyness surface、CALL／PUT 及尾部分布；静态图可采用 line／point、matrix／heatmap 和适当分布图。报告必须标注 proxy、coverage 与解释限制，并可追溯 summary 与 panel。 |

预期 cell 没有有效 observation 时仍在 summary／report 中以零 count 和空统计值表示；不能制造均值、分位数或图上数值。若整次请求没有任何有效 observation，则 Study/sample failure，不发布成功的 panel、summary 或 report。具体文件名、序列化格式、绘图库与颜色不是当前研究语义。

## Limitations

- `(high + low) / 2` 是 standardized daily estimator，不是 VWAP、mid quote 或 executable price；option 与 underlying 的 high／low 也不保证发生在同一盘中时刻。
- CSI1000 expiry-day close 不是 CFFEX 精确期权结算价，故 `expiry_payoff_proxy` 及 compensation 均是 proxy。相同 expiry 的不同日期、strike、CALL／PUT 共享同一终值事件，contract count 不是独立市场事件数。
- 年化 ratio 仅作期限归一化比较，不是 portfolio CAGR、保证金回报、资本回报或可实现的年化策略收益。
- 本 Study 不观察盘中路径、mark-to-market 压力、强平、止损、止盈、展期、动态／Delta 对冲、交易成本、滑点、保证金、融资或资本占用。正的 terminal compensation 不表示持有路径无风险。
- 不按市场、IV、basis、趋势或波动 regime 条件化；不估计 risk-neutral／physical density 或两者的概率差。`premium - realized payoff` 不能直接解释为 risk-neutral probability premium，也不足以推导连续重复策略的完整期望收益。

## Acceptance

- 六个 semantic areas、Study identity、参数 owner／consumer、CLI 契约、run identity、Observation → Analysis → Evidence Product 路径均在本文件有唯一 canonical owner；不依赖 sibling Study 的研究语义。
- 每个 expiry × target DTE × type × target moneyness 至多一个有效 observation；最近日期及合约 tie-break 确定，target 与 actual 及误差均保留。未设偏差上限不会被实现暗中加入筛选阈值。
- 可从 panel 逐行复核 high／low entry proxy、expiry close payoff proxy 和三种 compensation；缺失、无效或不一致的事实有可计数原因，不改选次近候选、不插值、不伪造。
- 两个 Analysis 均只消费具名 Observation，跨 expiry 等权；每个 cell 报 sample 与 unique expiry counts、coverage、空值、分位数和尾部最小值；CALL／PUT 不混合，重复合约及同 expiry 的多个 cell 不宣称独立。
- 三个 Evidence Products 保留请求与上游 provenance、可追踪的统计／图示及解释限制。整次零有效样本失败；尚无真实 evidence 时不预写结果。
- 在 Snapshot owner 提供历史发现 public capability 前，本 Study 不进入 implementation；option volume 缺失不使 authority 或 baseline 计算语义不完整。完成 CREATE 后须按 [Study Review](../REVIEW.md) 逐项通过 Study Authority Completeness Gate，再单独进行 dependency reconciliation。

## Authority Navigation

本文件独占当前 Study 的 Question、Inputs、Method、Results、Limitations 与 Acceptance；没有下层 specialized authority。上游事实与能力沿 [MO Option Chain](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) 的 [read contract](../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 及 [Index Daily History read contract](../../../market-snapshot/src/market_snapshot/products/index_daily_history/read-contract.md) 阅读。历史 expiry／entry-date 发现与 volume 的 public capability gap 已在 Inputs 记录；未来 implementation 只能在相应 Snapshot public boundary reconciliation 后开展。
