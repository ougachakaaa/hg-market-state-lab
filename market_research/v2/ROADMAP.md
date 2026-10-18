# Market Research V2 Development Roadmap

本文件是 V2 开发阶段、依赖、TODO、验收标准与完成状态的唯一 authority。稳定领域语义归 [V2 Architecture](ARCHITECTURE.md) 及其上层 authority，未决语义归 [Decision Topics](DECISIONS.md)；本文件通过链接引用它们，不覆盖领域规则。五个 Goal 是开发阶段，不要求对应五个代码模块。

## 状态与完成证据

| 状态 | 含义与记录要求 |
| --- | --- |
| TODO | 尚未启动或尚无阶段交付证据。 |
| In Progress | 正在推进，记录已完成事项、剩余事项及相关证据。 |
| Completed | 已满足本 Goal 全部验收门槛，链接可追溯的 Commit、Authority 或实际验收证据；文档完成不自动证明实际能力就绪。 |
| Blocked | 明确记录阻塞原因、正确 owner、受影响门槛和解除条件；未解决的实质能力缺口不得视为完成。 |

Goal 1–4 主要验收稳定语义与 implementation readiness；Goal 5 验收完整实际研究交付。测试验证 Implementation Correctness，真实研究验收验证 Research Usability，两者均为 V2 最终完成的必要条件。

## 阶段总览与依赖

| Goal | 状态 | 完成所需依赖 | 完成证据 |
| --- | --- | --- | --- |
| [Goal 1](#goal-1--v2-semantic-bootstrap) | Completed | 无 | Baseline commit `3de2c1e345744648ccf88dc58f9d4b97aa40a77e`；见本 Goal 的 Authority 证据。 |
| [Goal 2](#goal-2--condition--sample-selection-contract) | TODO | Goal 1 | 尚无。 |
| [Goal 3](#goal-3--forward-evaluation--outcome-contract) | TODO | Goal 2 | 尚无。 |
| [Goal 4](#goal-4--distribution-analysis--report-contract) | TODO | Goal 3 | 尚无。 |
| [Goal 5](#goal-5--mvp-implementation--real-research-acceptance) | TODO | Goal 2–4 完成，所需上游实际能力就绪 | 尚无。 |

下一步启动 Goal 2。Condition、Evaluation 与输入需求可以协同澄清，但不跳过依赖验收，也不在 Outcome 含义未定前固化 schema。Goal 2 锁定真实案例的目标研究口径，Goal 3 将其编码为完整计算契约；发现冲突回到正确 owner 显式 reconciliation，不静默改变案例。

## Goal 1 — V2 Semantic Bootstrap

**状态：Completed。** 以 baseline commit 为完成证据，仅表示 semantic bootstrap 完成，不表示具体研究 implementation-ready 或 runtime-ready。

范围与验收：

- 独立 V2 Authority 与 Conditional Forward Return Research 范式已建立；核心概念及 Condition、Sample Selection、Evaluation、Outcome、Analysis 的职责见 [V2 核心主线](ARCHITECTURE.md#核心执行主线与领域职责)。
- 顶层语义、关键 invariants 和后续专题的稳定入口已建立，见 [V2 Authority navigation](ARCHITECTURE.md#authority-navigation-与后续设计)。
- V1 不被替换、迁移或改变行为；范式隔离与依赖边界见 [Research module authority](../ARCHITECTURE.md#research-paradigms-与-authority-scope) 和 [Research UPSTREAM](../UPSTREAM.md#research-paradigm-scope)。

保留审查事项：收益观察锚点与交易执行价格的区分已在 [Evaluation invariants](ARCHITECTURE.md#forward-outcome-evaluation-invariants) 澄清，具体时点与口径由 Goal 2–3 落实；V2 不套用 V1 专有 authoring / handoff gate，见 [Research execution policy](../AGENTS.md#authority-first-execution-与-gap-handling)。后续 caller permission 与输入交接仍由 Goal 3 决定，不能从本阶段完成推导。

## Goal 2 — Condition & Sample Selection Contract

**状态：TODO。依赖：Goal 1。** 待决问题见 [Decision Topics](DECISIONS.md#待决专题与验收问题)。

范围：

- 确定代码式 Condition 的输入数据、参数、输出、判定时点、时区与信息实际可用性；AI 可根据研究问题生成 Condition，但执行行为必须确定、可验证、可复现。
- 明确候选研究范围、Condition 判定与样本选择的关系，及连续触发、重复样本、多对象样本、重叠观察窗口的处理与追溯。
- 选择首个真实研究案例，明确标的、可检验的 Condition、历史范围、Horizon 与目标收益口径，作为 Goal 5 的验收目标。历史范围的选择不改变 Architecture 中 Definition / Execution 分离的职责。

验收门槛：Condition / Sample Selection 专题 Authority 足以指导实现，核心业务语义无未决项；真实案例及 Condition 已确定且可检验。不得根据最终统计结果事后调整条件或样本规则。

优先评估的候选是中证1000历史日线条件收益研究，例如“单日跌幅超过某阈值后，未来 1、5、20 个交易日累计涨跌幅分布”。这不是已选案例、默认 Horizon 或数据源；本轮不确定阈值、日期范围和来源。若后续更改研究定义，须显式记录，不能伪装为原定义的重复执行。

## Goal 3 — Forward Evaluation & Outcome Contract

**状态：TODO。依赖：Goal 2。** 语义边界见 [Evaluation invariants](ARCHITECTURE.md#forward-outcome-evaluation-invariants)、[Outcome boundary](ARCHITECTURE.md#outcome-与-analysis-boundary) 及 [Lifecycle invariants](ARCHITECTURE.md#research-lifecycle-与可复现性)。

范围：

- 明确累计未来收益公式、Horizon、交易日历与计数、目标资产、观察起止价格、价格口径、跨对象 / 跨市场日期对齐；落实合法 close-to-close 观察与可执行交易收益的区别，避免未来信息泄漏和可交易性误读。
- 明确缺失 / 无效数据、历史尾部不足、停牌及不可评价样本的处理与原因记录。
- 确定 Outcome 的身份、粒度、结构、合法性及样本 / 定义 / 执行 / 收益输入的追溯交接，保持原始观察与 Analysis 解耦。
- 完成 Research Definition / Execution 分离、实际输入标识或保留及重放验证机制，不把 cache completeness 或 schema version 当事实版本证据。
- 在 [UPSTREAM](../UPSTREAM.md) 明确 V2 acquisition owner / caller permission，并在实际专题明确 Condition / Evaluation 的 complete input 与 failure handoff。
- 根据首个真实案例审查正式 DataLake public capabilities；仅在证明语义不足后按 UPSTREAM 审查 Snapshot。核对语义能力与实际 readiness，记录发现的 Upstream Capability Gap、已检查契约、正确 owner、影响与解除条件。

验收门槛：Evaluation / Outcome 及所需 Lifecycle / handoff Authority 完整；相同研究定义、执行上下文与输入事实能够产生确定、可追溯且独立于 Analysis 的 Outcome。实际研究所需数据能力已确认；未解决的实质能力缺口使相应 readiness 门槛阻塞，不得绕过既有公共契约或把缺口记录本身当作能力就绪。

## Goal 4 — Distribution Analysis & Report Contract

**状态：TODO。依赖：Goal 3。** 领域边界见 [Outcome / Analysis](ARCHITECTURE.md#outcome-与-analysis-boundary)，未决口径见 [Decision Topics](DECISIONS.md#待决专题与验收问题)。

范围：

- 建立统一的 Outcome 分析契约，确定第一阶段必需统计量，包括 Bucket、胜率、赔率、均值、分位数和收益分布的具体需要与定义；本轮不选择公式或阈值。
- 明确统计样本、有效分母、零收益、空样本和无效值的处理；明确样本依赖、重叠窗口、描述性统计 / 推断、统计显著性与研究局限的表达要求。
- 确定最小 Research Report Contract，关联研究定义、执行、样本、Outcome、分析方法及结果，允许核验统计口径与发现。
- 明确同一 Outcome 可按不同统计配置重新分析，无须重复 Evaluation；Visualization 保持可选诊断能力，不成为核心框架依赖。

验收门槛：Analysis 无须理解 Condition 内部实现即可消费 Outcome；Report 具备完整证据追溯；统计口径明确、真实结果可核验，Outcome 可重复分析。

## Goal 5 — MVP Implementation & Real Research Acceptance

**状态：TODO。依赖：Goal 2–4 完成，所需上游实际能力就绪。**

基于已稳定 Authority，实现最小完整执行链：

```text
Research Definition → Condition → Sample Selection
    → Forward Outcome Evaluation → Outcome Dataset
    → Distribution Analysis → Research Report
```

必须实际完成 Goal 2 确定的真实案例，并满足实现相关验证及下列全部真实研究验收。不能仅凭单元测试、Mock 数据、示例脚本成功或组件连通宣布完成。

### Mandatory End-to-End Acceptance

1. 经 Data Lake / Snapshot 正式 Public Contract 使用真实历史市场数据，不以 Mock、Synthetic 或手工伪造数据代替。
2. 实际执行完整 Condition → Sample → Outcome → Analysis → Report 流程。
3. 产生非空且有效的真实样本与未来收益观察，并明确记录不可评价样本及原因。
4. 生成可核验的真实统计结果，至少包含样本量、收益分布、胜率、赔率及必要描述性统计，核验依据 Goal 4 确定的口径。
5. 产出真实 Research Report，解释研究问题、数据范围、Condition、统计口径、实际发现和局限。
6. Outcome 能追溯到具体历史样本与收益计算输入。
7. 使用同一份 Outcome，以另一统计配置重新 Analysis，无须重新 Evaluation。
8. 提供可重复执行的研究入口与明确验证方式，并实际执行复现检查，保留核验结果。
9. 真实数据获取、样本有效性、统计计算或报告产出失败时，Goal 5 不得标记 Completed。

完成证据必须链接实际执行与复现记录、所用定义 / 输入 / Outcome、两种分析配置及结果、真实报告和相关实现验证；不得以文档编写完成替代实际执行证据。

## 维护与边界

- 后续发现缺失语义，更新 narrowest canonical authority，并在 [Decisions](DECISIONS.md) 跟踪未决项；不在本 Roadmap 发明公式、schema 或 caller rules。
- 专题按真实、独立 semantic ownership 落位并从 V2 入口导航；不提前建立空 Contract、通用 Engine、Registry、数据库或执行框架。
- 保持 V1 与冻结的 DataLake 边界；公共能力缺口按 [UPSTREAM escalation](../UPSTREAM.md#upstream-capability-gap-与-escalation) 交正确 owner，不通过 private access、provider 调用或 runtime 换源规避。
- 本轮仅落位 Roadmap、导航和必要 Authority reconciliation；不开展 Goal 2–5 详细设计、业务实现或真实研究，不修改 Data Lake / Snapshot。
