# Market Research V2 Semantic Authority

本文件是 **Market Research V2** 的独立顶层 authority，拥有研究范式、核心概念、职责边界、执行主线与关键不变量。V2 属于 `market_research`，继承 [module authority](../ARCHITECTURE.md) 及 [repository authority](../../ARCHITECTURE.md)；它不是新的 repository-level module、Python project 或已发布运行能力。

V2 是对研究范式的重新设计，与既有 V1 并存，不对 V1 原地重构、迁移或改变行为。V1 的 Component / Observation / Study、配置、CLI 与 retained outputs 继续由原 authority 拥有；V2 不把自己的 Outcome Dataset 等同于 V1 Observation Artifact，也不默认复用其生命周期。

## Purpose 与第一阶段范围

第一阶段聚焦 **Conditional Forward Return Research（条件未来收益分布研究）**：将人提出的市场研究问题，通过 AI 转换为明确、确定、可复现的 Condition，在历史数据上识别样本、计算指定未来区间的累计收益，并以标准统计框架分析条件收益的概率分布，形成可追溯的研究报告。

AI 负责辅助表达研究意图、编写研究定义与解释结果；执行所依据的 Condition 必须落为明确的确定性定义，不能在逐日判定中依赖 AI 临场解释。Research Intent 不能替代可执行研究定义，统计结果也不能反向修改本次执行所用的条件或样本规则。

职责终点是 research evidence / findings。V2 不包含 production market-state output、交易信号、买入、卖出、持仓、交易成本、策略 PnL 或交易回测语义；未来累计收益观察不等于策略绩效。

## 核心执行主线与领域职责

```text
Research Intent
    → Condition Definition
    → Sample Selection
    → Forward Outcome Evaluation
    → Outcome Dataset
    → Distribution Analysis
    → Research Report
```

这是语义主线，不规定 engine、package layout、调度机制或持久化实现。

| 概念 / 职责 | 负责什么 | 交付与边界 |
| --- | --- | --- |
| Research Intent | 人提出的问题、研究目标与背景 | 指导 Research Definition；自然语言本身不构成确定性执行契约。 |
| Research Definition | 明确条件、候选研究范围的语义、样本规则、目标资产、Horizon 与收益口径 | 与执行分离；具体历史范围和数据版本由每次 Execution 明确绑定，不靠隐式默认改变定义含义。 |
| Condition Definition | 定义候选 T 日是否满足条件 | 确定性判定；只使用约定判定时点之前已知的信息。 |
| Sample Selection | 将条件触发按明确规则转为历史样本 | 可追溯的 Sample Dates 与研究上下文；不计算未来收益来筛选样本。 |
| Forward Outcome Evaluation | 对样本计算指定目标资产与 Horizon 的未来累计收益率 | 交付收益观察事实，不负责分桶、胜率或策略模拟。 |
| Outcome Dataset | 承载 Evaluation 的原始收益观察事实及追溯上下文 | 可被重复分析；不保存衍生统计结论。 |
| Distribution Analysis | 消费 Outcome，按明确统计口径分析条件收益分布 | 不依赖 Condition 内部实现，不重新执行 Evaluation。 |
| Research Report | 表达研究定义、执行上下文、统计方法、结果与局限 | 引用所用 Outcome / Analysis，形成可核验 findings，不改变底层观察事实。 |
| Research Execution | 将同一研究定义绑定到一次明确的数据版本、历史范围及计算上下文 | 记录执行与结果的关联；不把一次运行状态混入定义身份。 |

## Condition 与 Sample invariants

Condition 定义 **T 日**是否满足研究条件，必须明确判定时点与信息可用边界。只能使用该时点之前已知的信息；日期早于或等于 T 不自动证明字段当时已知，未来发布、修订后的信息或未来收益不能倒灌条件。相同定义、合法输入与上下文必须给出相同判定，能够复现。优先允许代码式 Condition，本阶段不设计通用 DSL。

Condition 决定哪些历史日期满足条件；Sample Selection 再按研究定义中明确的规则确定样本。每个 Sample 必须保留可追溯的 Sample Date 和研究上下文。连续触发如何保留或去重、重叠观察窗口如何处理，必须具有明确且可复现的规则；本入口不选择默认规则，也不默认样本独立。

研究必须区分候选范围、条件判定、最终样本和收益可评价性。不得因未来收益值选择或删除样本；历史尾部不足、目标资产缺失等无法评价的情形必须由后续 contract 明确处理并可追溯，不能静默变为条件不成立、零收益或普通有效观察。

## Forward Outcome Evaluation invariants

第一阶段 Outcome **仅限未来累计收益率**。研究必须明确目标资产、Horizon 的含义、收益观察起点和终点、日历 / 日期对齐以及价格口径；不得从 Sample Date 或 Horizon 名称推定 close-to-close、自然日或交易日等具体约定。观察锚点与 Condition 判定时点的关系必须明确，Condition 不得使用其约定信息边界之后的信息。

允许在信息边界明确的情况下，以 T 日收盘信息判定条件，观察 T 日收盘至未来收盘的累计收益。这里的收盘价是市场统计观察锚点，不宣称条件确认后能够以该价格成交；不得将观察收益解释为可执行交易收益，也不得将判定前已经发生的收益冒充条件成立后的未来收益。具体判定时点、公式和日历由后续专题 contract 明确，本入口不设默认口径。

Condition 的数据对象可以与 Outcome 目标资产不同，例如用一个市场对象的条件观察另一个资产；两者的身份与对应关系须明确且可追溯。Evaluation 不拥有买卖执行、仓位、交易成本、信号、策略收益或回测框架。具体公式、异常 / 缺失与边界日期处理留给专题 contract，不在此选定默认值。

## Outcome 与 Analysis boundary

Outcome 是原始收益观察事实，最小观察信息包括 **Sample Date、Horizon、Return**。这些是语义最小项，不是已经定稿的表结构或唯一键。观察还必须能够追溯目标资产、研究定义、执行、数据来源和收益计算口径；上下文可通过明确关联表达，不要求每行重复存储。

Outcome Dataset 是 Research-owned 观察结果，不是 DataLake 自治 Dataset，不取得 source-fact ownership，不进入 DataLake cache 或改变其 Dataset Contract。Outcome 不保存 Bucket、胜率、赔率、分位数等衍生统计结果；Analysis 的产出及报告另行表达。

Distribution Analysis 只依赖 Outcome 的公开语义与解释它所需的研究 / 执行上下文，不依赖 Condition 内部代码或上游取数过程。同一份 Outcome 可以在不同统计口径下重复分析，无须重新选择样本或执行 Evaluation。改变条件、样本规则或收益口径不属于仅重跑 Analysis。

后续可逐步扩展 Bucket、胜率、赔率、分位数、收益分布、基准比较等通用分析能力；本入口不定义其公式、默认阈值、检验方法或通用统计 DSL。Analysis 必须区分描述性统计与统计推断，不因观察行数多就声称独立样本或显著性；连续触发及重叠观察窗口带来的依赖必须明确处理或披露。基准比较若需要额外收益观察，应先明确其输入 contract，不借 Analysis 直接执行未声明的上游取数或 Evaluation。

## Research lifecycle 与可复现性

Research Definition 与 Research Execution 分离；同一研究定义允许在不同数据版本或历史范围上重复执行，并明确区分执行绑定与定义变更。结果必须可追溯、可验证、可复现：能够识别实际使用的定义、条件代码与参数、样本规则、输入事实及其数据上下文、目标资产、Horizon、计算口径和 Analysis 口径。

数据版本是研究执行必须交代的输入上下文，不表示 DataLake 已提供任意历史版本查询、跨 Dataset 一致 snapshot 或 point-in-time replay。Export schema version 不是事实内容版本；完整 cache 也不证明 T 日可见性。具体输入保留 / 标识和重放验证方式须后续决定，不能以当前 cache 可读取替代复现证据，不能为此穿透上游私有存储。

Visualization 是可选诊断能力，不属于核心执行链，也不是 Outcome 或 Report 有效性的必备条件。未来可以按 Sample Dates 按需绘制带条件标记的 K 线；ownership 仍归 Research，继承模块 visualization 边界，不在本轮建立 Chart API、Web UI 或通用展示框架。

## Upstream 与模块依赖边界

V2 继续消费现有 DataLake 的正式 public capabilities，遵循 [Research UPSTREAM](../UPSTREAM.md) 的 DataLake-first design-time selection、完整性 / 失败、public provenance 和禁止换源规则。需要实际 facts 时经 [DataLake entry](../../data_lake/ARCHITECTURE.md) → [Dataset catalog](../../data_lake/DATASETS.md) → 具体 Dataset public contract 选择；不修改冻结的 Kernel、Dataset、Provider 或 Public Application Contract。

DataLake 继续拥有 source facts，Snapshot 继续拥有其 canonical deterministic Product preparation；V2 不复制这些 ownership，不直接访问 provider、credentials、SQLite、Repository、Source / Capture / Raw / private Preparation，也不经 CLI / JSON round-trip 取代 public semantic result。只有按 UPSTREAM 证明 DataLake semantic capability insufficient 后，才可审查 Snapshot 的正式 public Product；runtime failure 不授权替换来源。能力不足记录 gap，交正确 owner，不在本轮扩展上游。

本轮不决定 V2 中哪个实现角色取得 upstream acquisition 权限，也不从 Condition / Evaluation 名称推导调用权限；后续须在 UPSTREAM 与实际专题 contract 明确 caller 和完整输入交接后才能实现。Analysis 与条件内部实现、上游 acquisition 解耦。依赖方向保持 Research → 已授权的 DataLake / Snapshot public boundary；上游与 Modeling 不反向依赖 Research，Research 不依赖 HTTP / frontend。

## Authority navigation 与后续设计

稳定路径为 repository entry → module entry → 本文件 → 已发布的窄专题 contract。本文件拥有稳定设计语义与 invariants；[Decision Topics](DECISIONS.md) 拥有待决语义问题；[Development Roadmap](ROADMAP.md) 唯一拥有开发阶段、依赖、TODO、验收标准与完成状态。Roadmap 不覆盖领域 authority，Decision Topics 不构成默认规则或 implementation readiness。

当前尚未发布 Condition、Sample Selection、Evaluation、Outcome、Analysis 或 Lifecycle 的具体 contract；后续设计问题进入 Decision Topics，推进顺序与验收进入 Roadmap。

后续按独立 semantic ownership 发布专题并从本入口导航：Condition / Sample Selection 拥有判定与样本契约，Evaluation 拥有收益观察计算，Outcome 拥有观察及追溯交接，Analysis 拥有统计解释，Lifecycle 拥有定义与执行的具体关联。专题只能在本文件与上层 invariant 内 specialize / constrain；不预建空 contract、通用研究引擎、插件系统、调度器、通用 DSL 或数据库设计。
