# V2 Decision Topics

本文件是 [V2 Semantic Authority](ARCHITECTURE.md) 的后续决策清单，不是已确定的 contract，不授予实现权限。已确定的不变量唯一归 V2 入口及其上层 authority；本清单不为缺失规则提供默认值。专题形成稳定独立 concern 后再建立窄 authority，并更新入口链接，不预建空目录或 framework。

## 待决专题与验收问题

| Topic / 未来 owner | 必须回答的问题 |
| --- | --- |
| Condition 与 Sample Selection | 代码式条件的输入 / 输出与参数如何表达和识别？判定时点、时区、信息实际可用性如何验证？候选日期 / 对象范围如何声明？连续触发、去重、重叠窗口与多对象样本如何处理和追溯？ |
| Forward Outcome Evaluation | Horizon 使用什么日历与计数约定？观察起止价格、复权 / 合约连续性等口径如何选定？跨对象与跨市场日期如何对齐？公式、无效价格、停牌 / 缺失、历史尾部不足如何处理，并如何保留未评价样本的原因？ |
| Outcome Dataset | 观察粒度、身份 / 唯一性、字段 / 类型与合法性是什么？Sample、目标资产、定义、执行、数据来源及计算口径如何关联？空样本 / 不可评价观察如何表达？如何交接稳定、可重复分析的事实，而不混入统计结果？存储与发布方式在这些语义确定后再设计。 |
| Distribution Analysis | 第一组必需统计量是什么，Bucket、胜率、赔率、分位数如何定义？分母、零收益、空样本、无效值如何处理？重叠样本下允许何种描述或推断、如何披露依赖？基准比较需要什么公开输入？分析口径与 Report 的关联如何识别？ |
| Research Lifecycle / Report | 定义身份与变更、代码 / 参数版本、一次执行绑定、历史范围及数据版本如何表达？如何保留 / 标识实际输入以验证重放？重复执行与重复分析如何区分？Report 最小证据、方法与局限如何引用并核验？ |
| Upstream acquisition / complete input handoff | V2 哪个角色允许直接消费 Dataset / Product public service，谁准备 Condition / Evaluation 的完整输入？在 [UPSTREAM](../UPSTREAM.md) 明确权限后，具体研究需要哪些 facts、选定哪份 public contract、缺什么 capability / readiness？不得先假定 V1 producer 模型或新增 generic gateway。 |

## 已识别的上游约束与设计 gap

- DataLake public export 的 coverage + payload 保证单次 committed snapshot 的完整性语义，不保证不同调用 / Dataset 的共同 snapshot 或历史信息可见性。Condition contract 须证明其使用的信息在判定时点已知；不能仅凭 trade_date 推断。
- 现有 [Index Daily public contract](../../data_lake/datasets/tushare_index_daily/SERVICE.md) 发布历史日线和 cached metadata，明确 metadata 不宣称为 trade_date 当时的历史 metadata。它可以作为后续 capability review 的一个候选，不是本轮绑定的默认资产或数据源，不能据此宣称满足任意 point-in-time 条件。
- DataLake schema version、cache completeness 和事实版本 / 可重放输入不是同一概念。V2 必须在 Lifecycle / Outcome 专题解决公开边界内的输入标识与复现证据；本轮不要求上游新增 version API 或迁移 cache。
- V2 的概念职责已确立，具体 upstream caller permission、schema、公式、持久化及运行入口未定。因此本轮 authority 完成不代表任何具体研究 implementation-ready。

## 建议推进顺序

1. 优先联合完善 **Condition / Sample Selection** 与 **Evaluation**：先决定信息时点、样本单位、Horizon 和收益口径，避免 Outcome schema 固化未经决定的含义。
2. 基于明确输入需求完成 **Upstream acquisition 权限与具体 capability review**，并与 **Lifecycle 的定义 / 执行 / 输入版本追溯** 协同确定，发现 gap 就记录正确 owner，不绕过 public boundary。
3. 发布 **Outcome Contract**，稳定原始观察与追溯交接，再独立推进 **Analysis Contract** 与最小 Report 证据要求。统计口径变化应能复用同一 Outcome。

上述顺序是设计建议，不授权自动启动 implementation、V1 migration 或上游扩展。
