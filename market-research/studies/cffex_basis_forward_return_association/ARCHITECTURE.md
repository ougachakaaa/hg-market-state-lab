# CFFEX Equity Index Basis Environment × Forward Return Association retained Study authority

本文档是本 retained Study 的独立 canonical authority。Stable public Study ID 为 `cffex-basis-forward-return-association`，对应未来的 runnable package `cffex_basis_forward_return_association`。Authoring 遵循 [Study Authority Authoring](../AUTHORING.md)；Research 边界见 [market-research architecture](../../ARCHITECTURE.md)，CLI 转发、输出位置及覆盖规则见 [Research UI authority](../../ui/ARCHITECTURE.md)。Empirical quantile、median 与 sample standard deviation 引用 [Empirical Distribution Research Semantics](../../shared/distribution/ARCHITECTURE.md)。所需市场事实必须来自 [market-snapshot](../../../market-snapshot/ARCHITECTURE.md) 支持的 public product boundary；当前 capability gap 见 Inputs。

## Question

研究 CFFEX IF、IH、IC、IM 四类股指期货自各自上市以来的历史基差环境，以及该环境与对应标的指数随后 1、3、5、10、20 条实际交易观测收益之间是否存在可观察、跨 family 相似的历史关联。具体回答：各 family 的基差与标的指数经历过怎样的历史变化；该 family 自身较低到较高的基差环境之后，指数收益分布有何差异；相同市场时期内四个 family 的关系是否具有相似方向。

预期产物是可复核的历史 evidence，不预设关联一定存在，也不把 observed basis 当作估值偏离、预测值、交易信号或策略收益。完整有效基差历史是各 family 的主要历史描述 population；需要未来收益的分析另使用具备完整 20D 后续观测的共同 predictor sample。跨 family 对照另外使用四者同日有效的 common-period sample。

## Inputs

V1 固定全部四个 family，不提供 family、underlying 或 contract 选择参数。上市日期之前不属于该 family 的 population，不计为缺失观测。

| Family | Underlying | Source identity | Listing date |
| --- | --- | --- | --- |
| IF | 沪深300 | `000300.SH` | `2010-04-16` |
| IH | 上证50 | `000016.SH` | `2015-04-16` |
| IC | 中证500 | `000905.SH` | `2015-04-16` |
| IM | 中证1000 | `000852.SH` | `2022-07-22` |

| Input / option | 用户可见表达 | 必填与默认 | Semantic owner 与消费位置 |
| --- | --- | --- | --- |
| `start_trade_date` | `--start YYYY-MM-DD` | 必填，无默认 | Study population bound；三个 Observation 与全部 Analysis 使用。 |
| `end_trade_date` | `--end YYYY-MM-DD` | 必填，无默认 | Study population 与 forward-support bound；三个 Observation 与全部 Analysis 使用。 |
| `overwrite` | `--overwrite` | 可选，默认 false | Study-owned execution option；仅按 Research UI authority 替换已有完整 run directory，不参与研究语义或 identity。 |

两端均为有效、含端点的 calendar dates，要求 `start_trade_date <= end_trade_date`；不使用 `today`、`latest`、隐式窗口或自动最近 N 年。每个 family 的请求有效起点为 `max(start_trade_date, listing_date)`，终点不超过 `end_trade_date`。请求可以早于某些 family 上市，但成功 run 必须满足 Acceptance 的四 family 样本要求。CLI 示例：

```bash
lab research run cffex-basis-forward-return-association \
  --start 2010-04-16 --end 2026-09-28
```

### Upstream public capability requirement

Study 需要一个窄的 Snapshot public product，以 `futures_family ∈ {IF, IH, IC, IM}` 和显式起止日期返回每个实际标的指数交易日的完整 active futures term structure、同日标的收盘价、合约身份、期限位置、距到期日数和合约级基差事实。产品应固定上述 family ↔ underlying 映射，并拥有 active universe、M0/M1/Q1/Q2 slot、完整性、same-day close、单位、基差公式与 classified failure 的 canonical contract。所需基差事实至少包括 `basis_points = futures_close - underlying_close`、`basis_pct = (futures_close / underlying_close - 1) × 100` 和 `annualized_basis_pct = basis_pct × 365 / max(days_to_delist, 1)`；这些是对上游产品的语义要求，不由 Research 复制实现或作为跨 family Snapshot 公式 owner。

当前 [CSI1000 IM Basis History](../../../market-snapshot/src/market_snapshot/products/csi1000_im_basis_history/ARCHITECTURE.md) 仅覆盖 IM，尚无支持四 family 的统一历史 basis public product。本 authority 可以完成；runnable implementation 在该 Snapshot capability 的 canonical authority 与 public boundary 建立前仍被阻塞。Research 不得因此自行调用 Tushare、Capture、Raw Artifact、私有 Preparation 或 HTTP DTO。新产品的具体 Source scope 和 public result 由 Snapshot 单独设计，本 Study 不预先建立 generic futures query API。

### Retained request identity

V1 的 family、predictor、horizons 和方法均固定。两个日期先校验并规范为 `YYYY-MM-DD`；同一有效日期区间具有同一 semantic request 和 run key：`<start_trade_date>__<end_trade_date>`。改变任一日期必须改变 run key。`--overwrite`、output root、执行时间、随机值和原始命令拼写不参与。共享 Research UI 使用该 key 安排 `<output-root>/<study-id>/<run-key>/`，并在调用 Snapshot 前处理已有目录冲突。

## Method

### Method Context 与 ownership

共同上下文是固定的四个 family、各自上市界限、同一含端点请求区间、四个 slot、非前月年化 basis predictor、实际交易观测 horizons `{1, 3, 5, 10, 20}` 及完整 20D predictor sample。日期与 family 定义 Study population；slot、同日 close、合约级 basis 的事实语义属于待建 Snapshot 产品。`daily_non_front_basis` 的聚合和 20D 样本规则属于本 Study Method，分别由下述 Observation 与 Analysis 使用。任何 Observation 均不从另一个 Observation 的研究结果定义自身；实现可以复用相同 public result 或中间数据。

### Observation: `basis_term_structure`

本 Observation 从所需 Snapshot public result 独立观察每个 family × 实际交易日 × active contract 的合约级事实。每个有效 family-date 必须有唯一的 M0、M1、Q1、Q2；M0 是当月、M1 是下月、Q1/Q2 是随后两个季月，期限位置不是按成交量、持仓量或主力标记动态选出的合约。至少保留 `trade_date`、`family`、`underlying_code`、`contract_code`、`contract_slot`、`days_to_delist`、`underlying_close`、`futures_close`、`basis_points`、`basis_pct`、`annualized_basis_pct`。同日 close 与上游 completeness 必须成立；缺失 slot、重复或不可用的必需事实不能以删行、换日或填零修复。本 Observation 覆盖有效区间内的全部 basis dates，不因未来收益不足裁剪尾部。

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

消费 `daily_basis_environment` 与 `underlying_forward_returns`，按 family 独立使用同时具备完整 20D outcome 的 predictor dates。对各 family 的这一完整 numeric sample，按 shared empirical quantile semantics 求 daily predictor 的 P20/P40/P60/P80，再以 `Q1: x <= P20`、`Q2: P20 < x <= P40`、`Q3: P40 < x <= P60`、`Q4: P60 < x <= P80`、`Q5: P80 < x` 分组。相同 basis 值不拆组；重合阈值可形成空组。Q1/Q5 仅表示该 family 自身样本中较低/较高的 basis environment。

对每个 family × quintile × horizon 计算样本数、算术平均收益、median、P25、P75 和 `positive_return_rate = count(forward_return_h_pct > 0) / sample_count`。零收益进入分母但不算 positive。各 horizon 使用完全相同的 predictor dates；不能按较短 horizon 扩张样本。全历史阈值只用于事后历史分组。

### Analysis: `linear_association`

消费 `daily_basis_environment` 与 `underlying_forward_returns`，在与上一 Analysis 相同的各 family 完整 20D predictor dates 上，对每个 horizon 计算 `Corr(daily_non_front_basis_T, forward_return_h_pct)` 的 Pearson 系数，以及带截距的简单 OLS：`forward_return_h_pct = alpha + beta × daily_non_front_basis + error`。保留 family、horizon、sample count、相关系数、alpha、beta、R²。可定义的统计照实计算；因样本数或零方差在数学上未定义的值标 `null`，不伪装为 0。OLS 只提供方向、线性幅度和简单解释程度，不作显著性推断。

### Analysis: `common_period_cross_family_comparison`

消费 `daily_basis_environment` 与 `underlying_forward_returns`。先取四个 family 均具完整 basis predictor 和 20D outcome 的**实际交易日期交集**，而不是只设相同日历起止区间。四者在这一相同日期集合上分别重新计算自己的 P20/P40/P60/P80，依照 `basis_regime_forward_returns` 的分组边界与条件收益统计重做 quintile × horizon 表。不得复用 full-history 阈值；此表明确标记 `population = common_period`，并记录交集首末实际日期及日期数。它用于减少不同上市年份和交易日期组成造成的跨 family 比较偏差，不把四个指数当作独立实验。

## Results

成功 retained run 同时保留 machine-readable evidence、human-readable report/table 和 Python 生成的静态图片。三个 Observation Artifact 分别独立物化；四个 Analysis 的 evidence 随整次 run 保留，无需另建 Analysis Artifact identity。具体文件名和编码格式不是稳定语义契约，但所有数值、单位、分组边界、日期与来源须可机器读取并相互对账。当前尚无已执行的 evidence、统计数值或 finding。

| Evidence | 最低语义内容 |
| --- | --- |
| Request / provenance | public Study ID、规范起止日期、run key、四个 family ↔ underlying 映射、上游 public product 与 request/source identity、三个 Observation Artifact identities、固定 predictor 与 horizons。 |
| Sample summary | requested bounds；逐 family 的上市界限、有效历史首末实际日期、basis-date count、20D predictor 首末日期与 count、因 future 不足排除的 basis-date count；common-period 首末实际日期与交集 count。 |
| Historical basis summary | 每 family 的完整有效基差历史 count、mean、median、sample standard deviation、min、max、P10/P20/P40/P50/P60/P80/P90；`daily_non_front_basis > 0` 的 premium count/rate、`< 0` 的 discount count/rate、`= 0` 的单独 count/rate。 |
| Full-history breakpoints / regime table | 每 family 的 P20/P40/P60/P80 阈值及其 20D predictor population count；每 family × Q1–Q5 × horizon 的 count、mean/median/P25/P75 forward return（percentage points）、positive return rate（`[0, 1]` ratio）。 |
| Linear association table | 每 family × horizon 的 count、Pearson correlation、OLS alpha/beta/R²，记录 `null` 所对应的未定义原因。 |
| Common-period breakpoints / regime table | 标记 `population = common_period`；各 family 在同日交集上重新计算的阈值，及与 full-history 表同结构的条件收益统计。 |

历史基差 summary 的 population 是**完整有效 basis history**；full-history regime 和 linear 表的 population 是各 family 的完整 20D predictor sample；common-period 表的 population 是四者的同日交集。这三种分母必须在 metadata、表和报告中分别标明。每个 family × quintile × horizon 均保留一行；空组 `sample_count = 0`，全部条件收益与 positive rate 为 `null`。标准差在少于两条历史 basis observation 时按 shared distribution authority 为 `null`。以逐日 Observation、样本界限、排除数、阈值和上游 provenance 可以复核每张表；不能把 `null` 表示成零或静默省略。

人类可读 evidence 至少包括样本与限制说明、历史基差摘要、两张分别标识 population 的 regime 表、线性关联表和以下静态图：

1. 各 family 的历史背景图：归一化指数水平与 `daily_non_front_basis` 上下排列、共享时间轴，不使用误导性双 Y 轴。
2. 各 family 的 M0/M1/Q1/Q2 年化 basis 期限结构历史图，用于核对聚合 predictor 是否代表整体期限环境。
3. 各 family 的 quintile × 1D/3D/5D/10D/20D heatmap，median forward return 与 positive return rate 分开展示；空组留空。
4. 使用 common-period 证据的跨 family Q1→Q5 对照图，明确所展示的 horizon 与统计量，用于比较关系方向。

报告引用表与图，不在无实际 evidence 时预写研究结论；可视化舍入不改变 machine-readable 数值。

## Limitations

- Association 不证明因果：下跌与套保需求变化也可能共同驱动贴水，basis 可具有内生性。
- 利率、预期分红、剩余期限、资金与流动性等均影响 observed futures basis；它不直接等于指数估值或相对理论 fair basis 的偏离。
- 不同时期的交易制度、参与者、规模和宏观环境会变化；全历史关系未必平稳。common-period 视图只控制比较日期，并不能消除这些变化。
- 全样本分位点含事后信息，不能直接作为实时状态定义或交易阈值。未来 Modeling 若使用此发现，需先另作语义决定与 authority update。
- 5D/10D/20D forward windows 大量重叠，简单 correlation/OLS 不支持 p-value、置信区间或显著性结论；四个相关指数也不是四组独立实验。
- 本 Study 不产生 forecast、expected-return signal、买卖或持仓建议、策略 PnL、理论 fair basis、机器学习模型、盘中数据、HTTP API 或 frontend UI。

## Acceptance

- 六节 authority 明确四 family、映射、上市界限、必填日期、CLI ID、run identity、upstream capability gap 与 Research/Snapshot ownership；不能通过访问 Source 或现有 IM 产品私有实现绕开缺口。
- 三个具名 Observation 的事实、派生值、有效性、尾部 future-support 和独立 Artifact identity 均可从上游 public input 追踪；完整 M0/M1/Q1/Q2 保留，M0 不进入每日 predictor。
- `historical_basis_context` 使用完整 basis history；其他三个 Analysis 使用各自明确的 20D 或同日交集 population，不跨越请求终点。每个 Question aspect 均有 Observation → Analysis → retained evidence 链路。
- 四 family 均须至少有一条完整 20D predictor observation，且 common-period 同日交集非空；否则整次 run 失败，不发布成功 evidence。上游缺失或不完整的必需 basis facts 亦不能被静默丢弃。
- Full-history 与 common-period 分位点各按自身 population 计算；同值不拆桶，空组、零收益、未定义统计与 premium/discount/zero 的分母表达正确。各 family 的 full-history 20D predictor count 等于五个 quintile 在每个 horizon 的 count 之和；common-period 的相应总数等于交集日期数。
- 成功 evidence 含所列逐日 Artifact、provenance、样本和排除计数、阈值、统计表、报告与静态图；表图能从 machine-readable 数值复核，且不会把历史关联陈述为因果、显著性、forecast 或交易建议。
