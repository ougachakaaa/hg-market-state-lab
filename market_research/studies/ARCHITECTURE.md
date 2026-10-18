# Research Study framework authority

本文件是 Study framework 的稳定入口，说明职责与阅读路径；继承 [Research module boundaries](../ARCHITECTURE.md)。对象、字段与关系唯一由 [SCHEMA.md](SCHEMA.md) 定义，runtime / retained state 唯一由 [WORKFLOW.md](WORKFLOW.md) 定义，不在本入口复制细节。

## Study 与 related owners

Study 是值得保留、复查或继续推进的 bounded research question / preparation objective 的 authority unit。它拥有 request、input bindings、Component invocation / Observation ensure orchestration、execution order、runtime plan / state / outcome 与可选 Analysis orchestration。

Study 不拥有 Observation definition 或 reusable empirical persistence；[Observation](../observations/ARCHITECTURE.md) 独立保留 empirical Artifact，Study 只经 public boundary 确保并消费 complete Artifact。[Shared Component](../shared/ARCHITECTURE.md) 复用窄机制，resolver / reader 可由 orchestration 准备 complete inputs；Analysis 只计算已经准备好的 complete inputs，可调用 pure component，不自行获取 facts、ensure Observation 或读取 persistence。Study / Analysis 不直接消费 DataLake / Snapshot；legacy 适用范围仅沿 Compatibility 进入。

Analysis 仍为 Study-local，拥有研究计算、比较、统计与解释；Evidence 若实际存在，是 Study-owned interpretation / finding，其 defining Analysis 关系归 Schema / concrete RESULTS。Study 不通过相似代码、sibling Study 或 historical shared semantics 继承研究含义，也不建立 reusable Analysis framework。

## Retained authority 与 execution output

Retained Study 表达被保留的研究 / orchestration 知识，不表示每次 execution 必须有 retained output，也不自动成为 production / reusable capability authority。Study-local retained Workflow Artifacts、Analysis、Evidence 均可为零；只有真实需求明确声明时才存在 retained Workflow Artifact / Evidence。

Runtime plan、references、counts 和 failure summaries 可以只存在于本次 invocation，不自动成为 Artifact。Observation persistence 与 Study retained output 是独立边界；Study 不复制 market rows 建 canonical empirical cache。Runtime / retained distinction、materialization 和 complete-input rules 进入 [WORKFLOW](WORKFLOW.md)。

## Task navigation

| 当前任务 | 下一份 authority |
| --- | --- |
| 新 Study、四文件布局、human decision loop、semantic completeness review / handoff | [AUTHORING.md](AUTHORING.md) |
| 对象模型、六个 semantic areas、inputs / identity、实际 dependencies、Analysis / Evidence relationships | [SCHEMA.md](SCHEMA.md) |
| Steps / runtime outcome / retained state / materialization / complete consumption | [WORKFLOW.md](WORKFLOW.md) |
| Runnable package、implementation responsibilities / progressive disclosure / acceptance review | [IMPLEMENTATION.md](IMPLEMENTATION.md) |
| Legacy maintenance、migration、consolidation、historical reconciliation、substantial legacy semantic modification | [COMPATIBILITY.md](COMPATIBILITY.md)，仅触发范围适用，不在新 Study 默认路径。 |

新 Study 最小路径是本 entry → AUTHORING / SCHEMA / WORKFLOW → actual Component / Observation contracts → concrete Study entry → INPUTS / METHOD / RESULTS；不扫描 sibling concrete owners。Implementation 时再进入 package contract 与 concrete handoff；authority completion 不自动启动 implementation / execution。

Concrete entry：[cffex_option_expiry_dte_collection](cffex_option_expiry_dte_collection/ARCHITECTURE.md)。具体 objective、bindings、method、results 与 readiness 留在该 owner。
