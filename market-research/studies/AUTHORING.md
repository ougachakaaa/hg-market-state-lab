# Research Study Authority Authoring

本文件是新 retained Study 的稳定创建入口，拥有 Study Intention 到 Canonical Study Authority 的 workflow。Research 边界见 [module architecture](../ARCHITECTURE.md)，必需语义见 [Schema](SCHEMA.md)，四文件布局见 [Skeleton](SKELETON.md)，实现拓扑见 [Implementation Package Contract](IMPLEMENTATION.md)，完整性验证见 [Review](REVIEW.md)，历史适用规则见 [Compatibility](COMPATIBILITY.md)。Observation 独立设计流程见 [Observation Authoring](../observations/AUTHORING.md)。Agent 不得自行发明未给出的研究语义。

## Study identity 与完成范围

Study 必须回答 Question、Inputs、Method、Results、Limitations、Acceptance 六个 areas，并实例化 `ARCHITECTURE.md`、`INPUTS.md`、`METHOD.md`、`RESULTS.md` 四个有实质内容的顶层文件。`studies/<study_package>/ARCHITECTURE.md` 是稳定入口；独立 implementation 位于同名 `src/market_research/studies/<study_package>/`。完成 authority 不自动启动 implementation 或 execution。

Study 拥有 research question / preparation objective、user request、workflow orchestration、Observation invocation / composition、Study-local Workflow Artifacts 与 optional Analysis / Evidence。Workflow steps / materialization 规则见 [Workflow authority](WORKFLOW.md)。Observation 的 population、grain、derivation、validity 和 Artifact schema 由独立 canonical owner 拥有，不属于 Study Method；Analysis 不 resolve / ensure dependencies。

## Canonical authoring workflow

```text
Research Question / Preparation Objective
    → identify required empirical facts
    → identify required Observation Artifacts
    → Observation capability exists?
        ├── no → record capability gap
        │        → design / implement Observation separately
        │        → return to Study
        └── yes → declare Artifact dependencies / invocation inputs
    → design Study-owned workflow / ordered steps
    → define materialized Workflow Artifacts / retained results
    → optional Study-local Analysis
    → optional Evidence
```

所需 Observation 尚不存在时，显式记录 required capability、需要的 empirical facts 与 gap。Study draft 可以继续整理已决定的 objective / workflow / optional Analysis / Evidence intention，但不得在 Study-local Method 中临时创建 Observation definition。缺失 Artifact shape / consumption contract 不得猜测，依赖未就绪时不进入 Study implementation。Workflow-only Study 不强制继续进入 Analysis / Evidence；要明确无此职责及完成 objective 的 retained result。

## 创建隔离与导航

Study-owned Research semantics 必须 self-contained：question、hypothesis、Analysis-specific sample selection、grouping / comparison / statistics、解释、Evidence contract 与 limitations 由当前 Study 拥有；相似 analytical code 允许重复。Observation reuse 则明确通过 Artifact public boundary 引用 canonical owner，不以创建隔离为由重复定义 empirical facts。

新建 Study 不默认扫描所有 Observations，不主动搜索 sibling Studies、其 retained evidence、既有 shared Research semantics 或 implementation 来继承研究含义 / helper。只读取意图与实际依赖指向的 Observation authority；若尚无已知 owner，记录 capability gap，再独立处理 Observation design。Sibling Study 可作为 related work / historical evidence 导航，不成为新 Study 的 semantic owner 或 runtime dependency。相似性不触发 shared 抽取或 sibling 修改。

可使用 repository runtime、Research UI、configuration、filesystem / serialization mechanics 和外部 libraries。Upstream facts 沿实际 Observation authority 进入必要的 DataLake / Snapshot public contract；不能从缺失 capability 推导内部访问权。默认写入范围是当前 Study authority 与必要导航；Observation 或 upstream gap 由对应 owner 单独 reconciliation。

| 当前任务 | 下一份 authority |
| --- | --- |
| Study semantic areas / dependencies / optional Analysis | [Schema](SCHEMA.md) |
| Steps / materialized Workflow Artifacts / complete consumption | [Workflow](WORKFLOW.md) |
| Authority 布局与阅读顺序 | [Skeleton](SKELETON.md) |
| 实现 runnable Study | [Implementation Package Contract](IMPLEMENTATION.md) |
| Completeness 与 traceability | [Review](REVIEW.md) |
| Historical reconciliation / migration / consolidation | [Compatibility](COMPATIBILITY.md) |
| 缺失 Observation capability | [Observation Authoring](../observations/AUTHORING.md) |

最小路径为 repository / module entry → 本文件 / Schema → 实际消费的 Observation authority → 当前 Study entry / 四文件 → 所需 specialized authority。创建时用 Skeleton；实现时用 Implementation；审查时用 Review；Compatibility、historical shared owners 和 sibling Studies 不在默认创建路径。

## Structured Study Intention Record

Human 可以用自然语言提供 Study Intention，不要求先填完整表单。Template Filling 前，Agent 必须整理显式 Structured Study Intention Record，未给出的项允许留空：

| 输入项 | 记录内容 |
| --- | --- |
| Research goal / question / objective | 研究或准备 / empirical collection 意图、动机与范围；hypothesis 若适用。 |
| Empirical facts / Artifact needs | 已指定的 empirical facts、Observation owner（若已知）、Artifact contracts / identity、capability gaps。 |
| Inputs / configuration | 已指定的 request、Observation invocation bindings、Analysis configuration 与 sample selection。 |
| Method intention | 已指定的步骤顺序、dependency bindings、materialization、失败 / 空结果与 optional Analysis consumption。 |
| Research product | 希望保留的 workflow results / Artifacts 和 optional Evidence / Findings / presentation。 |
| Boundaries / open decisions | 限制、non-goals 与待决研究选择。 |

各项可记录 semantic source（human decision / canonical authority）及 resolution state（decided / unresolved）。Record 是对话或工作草稿中的中间 representation，不要求新增 repository artifact，也不是最终 authority。Agent 可以规范措辞、组织已决定内容与引用 canonical facts，不能从常见做法、既有 Study、实现便利性或 human 沉默推断研究决定。非语义命名 / 排版 / 实现细节可由 Agent 整理。

## Authoring 状态与 human decision loop

| 状态 | Required action / exit condition |
| --- | --- |
| Study Intention | 提取 human 决定、事实引用与待决项，进入 Structured Study Intention。 |
| Structured Study Intention | 形成 Record，区分 known semantics、capability gap 和 missing semantic decision，再进入 Template Filling。 |
| Template Filling | 按 Skeleton 填入四文件的唯一 owner，只写已确定语义，保持 gaps / unresolved items 可见；草稿不得冒充完整 authority。 |
| Semantic Review | 执行 Review Gate；语义完整进入 Authority Complete，实质缺口进入 Semantic Decision Required。 |
| Semantic Decision Required | 向 human 表达缺失决定，取得明确 resolution 后更新 Record，返回 Template Filling 并再次完整 Review。 |
| Authority Complete | 确认 Study-owned semantics 与导航完整；不等同于 capability ready，不自动进入 implementation。 |

每个未决项记录 `unresolved field / topic`、`missing semantic decision`、`why the decision matters`、`recommended resolution`，有实质差异时再给出 `alternatives`。建议不构成默认授权；Agent 不自行选定改变研究含义的选项。

Study input 必填 / defaults、workflow 顺序 / failure、Artifact completeness / retention、retained run identity、empty result，以及适用的 hypothesis / Evidence 等缺失决定均进入该 loop。不因 Analysis / Evidence 为零而要求补出不存在的研究含义。缺少 Observation capability 要走独立 authoring，而非替当前 Study 填 Observation semantics；框架明确 deferred 的问题不在本流程自动决定。

## Publication 与 dependency handoff

**Study Authority Complete** 表示六个 areas 与关系完整，Implementer 无需重新决定 Study-owned semantics；可以先于所需 capability readiness。若所需 Observation 尚未存在，可记录足够明确的 Artifact requirement / gap；尚不能确定的 material consumption semantics 则仍是 semantic incompleteness，不能仅改名为 gap 绕过 Gate。

**Dependency Reconciled** 表示实际所需 Observation、Artifact public invocation / consumption contract 与相关 upstream capabilities 已就绪，ownership 无冲突；authority 已存在但 producer / public invocation runtime 缺失时，尚不满足此状态。**Implementation Ready** 仅在 Study Authority Complete 与 Dependency Reconciled 均成立时成立。缺失 Observation 先独立 design / implementation，再返回 Study 确认实际 contract / bindings，复核 workflow 与 retained results，以及实际存在的 Analysis / Evidence。Authority complete 可以支持下一步联合 implementation design，不代表实际 Study implementation 已可开始。

工作顺序仍为 `CREATE → RECONCILE → IMPLEMENT`；进入 implementation 按 Package Contract，完成后按 Review 独立验证 topology。这些名称区分 authoring / dependency readiness，不建立 persisted status、registry 或 engine。Existing Study reconciliation 与 human-triggered `CONSOLIDATE` 由 Compatibility 拥有，不是上述依赖核对的自动副作用。

实施某个 Analysis 时只读其 contract、实际 consumed Artifact / Observation authority 和必要机制；更深层拆分不建立 generic component interface、Artifact Registry、DAG 或 plugin framework。
