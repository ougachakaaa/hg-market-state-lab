# Research Study Authority Authoring

本文件拥有 Study Intention 到 Canonical Study Authority 的创建流程、四文件呈现拓扑、semantic completeness / traceability gate 与 dependency handoff。Framework 入口见 [Study architecture](ARCHITECTURE.md)，必需语义见 [Schema](SCHEMA.md)，runtime / retained state 见 [Workflow](WORKFLOW.md)，runnable topology 与 implementation review 见 [Implementation Package Contract](IMPLEMENTATION.md)。Agent 不得自行发明未给出的研究语义。

## Study identity 与完成范围

Study 必须回答 Question、Inputs、Method、Results、Limitations、Acceptance 六个 areas，并实例化 `ARCHITECTURE.md`、`INPUTS.md`、`METHOD.md`、`RESULTS.md` 四个有实质内容的顶层文件。`studies/<study_package>/ARCHITECTURE.md`（module-root relative）是稳定入口；Python implementation 与 authority 在该 owner 内 colocate。完成 authority 不自动启动 implementation 或 execution。

Study 拥有 research question / preparation objective、user request、input bindings、workflow orchestration、Component invocation / Observation ensure composition、runtime state 与 execution outcome；Study-local retained Workflow Artifacts / Analysis / Evidence 仅在真实需求明确时声明。Runtime state / retained Artifact distinction 见 [Workflow authority](WORKFLOW.md)。Reusable empirical persistence、population、grain、derivation、validity 和 Artifact schema 由独立 Observation 拥有，不属于 Study Method；Analysis 不 resolve / ensure dependencies。

## Mandatory top-level topology

```text
market_research/studies/<study_package>/
├── ARCHITECTURE.md
├── INPUTS.md
├── METHOD.md
└── RESULTS.md
```

四个顶层文件均须有实质内容，单个 `ARCHITECTURE.md` 或空占位文件不能代表完整 authority。四份 authority 与 Python implementation colocate 于同一 Study owner；不要求文档与 Python files 一一对应，也不限制必要的下层 specialized authority。Runnable package 的 mandatory Python files 见 [Implementation Contract](IMPLEMENTATION.md)。

| 文件 | Canonical responsibility |
| --- | --- |
| `ARCHITECTURE.md` | 稳定入口：Identity、Question / Objective、scope / purpose、Limitations、Acceptance、workflow / dependencies / execution outcome 与明确声明的 retained outputs / optional Analysis / Evidence 概览、dependency gaps、implementation location 与导航。 |
| `INPUTS.md` | Study request / configuration、Component / Observation invocation bindings、parameter owner / consumers / semantic role、用户表达与 CLI 映射、必填性与默认值、规范化、semantic request identity；retained run identity / output execution-only options 仅适用时定义。 |
| `METHOD.md` | Required workflow / steps、Component I/O / Observation dependency owner / identity / contract references、invocation bindings、component invocation / Observation ensure orchestration、Workflow Artifact production / consumption 与 failure / empty semantics；optional Method Context / Analysis。 |
| `RESULTS.md` | Execution outcome / human output、counts / success / empty / failure；明确保留 Workflow Artifact 时另定义 shape / completeness / retention / provenance，Evidence 若存在再定义 `defined_by`、结构 / 表 / 图 / 报告、样本与排除计数。 |

六个必答 semantic areas 仍由 Schema 定义；Identity 是 structural information，Authority Navigation 是阅读路径。Observation empirical population、grain、derivation、validity 和 Artifact schema 不在上述文件重新定义。

## Entry 与 progressive disclosure

Entry 必须直接链接 `INPUTS.md`、`METHOD.md`、`RESULTS.md`，并使必要 specialized authority 可达。读者可辨认 objective、workflow、主要依赖、execution outcome、实际声明的 retained results / optional Analysis / Evidence、限制与验收，再只读相关 owner。Orchestration-only Study 保留四文件，以有实质内容的 runtime RESULTS 回答结果契约，不创建假 Workflow Artifact / Analysis / Evidence。

Detailed request / identity 归 INPUTS，workflow / step order、dependency composition 与 optional Analysis mechanics 归 METHOD，runtime outcome 与实际声明的 Workflow Artifact / retained result / Evidence structure 归 RESULTS。通用 runtime / materialization boundary 见 [Workflow](WORKFLOW.md)。Concrete implementation handoff 可以是独立 specialized authority，继承 [Package Contract](IMPLEMENTATION.md)，不替代四文件语义 owner。引用 Component / Observation semantics 时使用 summary + canonical link，不复制定义；Inputs 绑定与 Method 消费关系相互链接，不双重拥有输入含义。

更深层拆分只依据真实 concern 和阅读需求。例如复杂 Analysis 可从 METHOD 进入 `method/analyses/`；dependency composition 也可有自己的窄文档，但不建立 Study-local `method/observations/` definition。Inputs / Results 按需下沉并保留概览及导航，不机械一对象一文件。

## Canonical authoring workflow

```text
Research Question / Preparation Objective
    → identify required empirical facts
    → classify local logic / shared mechanism / independent research artifact
    → declare actual Component I/O / Observation Artifact needs
    → required capability exists?
        ├── no → record capability gap
        │        → design / implement Component or Observation separately
        │        → return to Study
        └── yes → declare Component / Artifact dependencies and input bindings
    → design Study-owned workflow / ordered steps
    → define runtime execution outcome
    → declare retained Workflow Artifacts / outputs only when required
    → optional Study-local Analysis
    → optional Evidence
```

所需 Component / Observation contract 尚不存在时，显式记录 required capability、需要的 empirical facts 与 semantic gap。Study draft 可以继续整理已决定的 objective / workflow / optional Analysis / Evidence intention，但不得在 Study-local Method 中临时创建 Observation definition。缺失 Artifact shape / consumption contract 不得猜测，semantic / design gap 未解决时不标为 Implementation Ready。已完整设计但 runtime 未实施的 dependency 单独记录，可以设计并按 producer-first 顺序实施整个 vertical slice；实际 Study 实施前仍先完成 producers 与 bindings runtime reconciliation。Orchestration-only Study 不强制 retained Workflow Artifact / Analysis / Evidence，要明确 runtime outcome 如何完成 objective。

## 创建隔离与导航

Study-owned Research semantics 必须 self-contained：question、hypothesis、Analysis-specific sample selection、grouping / comparison / statistics、解释、Evidence contract 与 limitations 由当前 Study 拥有；相似 analytical code 允许重复。Observation reuse 则明确通过 Artifact public boundary 引用 canonical owner，不以创建隔离为由重复定义 empirical facts。

新建 Study 不默认扫描所有 Observations，不主动搜索 sibling Studies、其 retained evidence、既有 shared Research semantics 或 implementation 来继承研究含义 / helper。只读取意图与实际依赖指向的 Component / Observation authority；若尚无已知 owner，先按 component classification 记录 capability gap，再独立处理正确类型的 owner。Sibling Study 可作为 related work / historical evidence 导航，不成为新 Study 的 semantic owner 或 runtime dependency。相似性不自动触发 shared 抽取或 sibling 修改；明确跨研究机制复用按 component authority 提升，不继承 sibling research semantics。

可使用 repository runtime、Research UI、configuration、filesystem / serialization mechanics 和外部 libraries。Upstream facts 沿实际 Component / Observation authority 进入必要的 DataLake / Snapshot public contract；不能从缺失 capability 推导内部访问权。默认写入范围是当前 Study authority 与必要导航；Component / Observation / upstream gap 由对应 owner 单独 reconciliation。

| 当前任务 | 下一份 authority |
| --- | --- |
| Study semantic areas / dependencies / optional Analysis | [Schema](SCHEMA.md) |
| Steps / runtime state / explicit retained Workflow Artifacts / complete consumption | [Workflow](WORKFLOW.md) |
| Authority 布局与阅读顺序 | [四文件布局](#mandatory-top-level-topology) |
| 实现 runnable Study | [Implementation Package Contract](IMPLEMENTATION.md) |
| Completeness 与 traceability | [Semantic gate](#study-authority-completeness-gate) |
| Historical reconciliation / migration / consolidation | [Compatibility](COMPATIBILITY.md) |
| Component 分类 / contract / dependency | [Shared Component authority](../shared/ARCHITECTURE.md) |
| 缺失 Observation capability | [Observation Authoring](../observations/AUTHORING.md) |

最小路径为 repository / module entry → [Study architecture](ARCHITECTURE.md) → 本文件 / Schema → 实际消费的 Component / Observation authority → 当前 Study entry / 四文件 → 所需 specialized authority。创建布局与 semantic review 使用本文件；实现及 implementation review 使用 Implementation；Compatibility、historical shared owners 和 sibling Studies 不在默认创建路径。

## Structured Study Intention Record

Human 可以用自然语言提供 Study Intention，不要求先填完整表单。Template Filling 前，Agent 必须整理显式 Structured Study Intention Record，未给出的项允许留空：

| 输入项 | 记录内容 |
| --- | --- |
| Research goal / question / objective | 研究或准备 / empirical collection 意图、动机与范围；hypothesis 若适用。 |
| Empirical facts / Artifact needs | 已指定的 empirical facts、Component / Observation owner（若已知）、Artifact contracts / identity、capability gaps。 |
| Inputs / configuration | 已指定的 request、Component / Observation invocation bindings、Analysis configuration 与 sample selection。 |
| Method intention | 已指定的步骤顺序、dependency bindings、materialization、失败 / 空结果与 optional Analysis consumption。 |
| Research product | Runtime outcome / presentation；实际明确需要时的 retained workflow results / Artifacts 和 optional Evidence / Findings。 |
| Boundaries / open decisions | 限制、non-goals 与待决研究选择。 |

各项可记录 semantic source（human decision / canonical authority）及 resolution state（decided / unresolved）。Record 是对话或工作草稿中的中间 representation，不要求新增 repository artifact，也不是最终 authority。Agent 可以规范措辞、组织已决定内容与引用 canonical facts，不能从常见做法、既有 Study、实现便利性或 human 沉默推断研究决定。非语义命名 / 排版 / 实现细节可由 Agent 整理。

## Authoring 状态与 human decision loop

| 状态 | Required action / exit condition |
| --- | --- |
| Study Intention | 提取 human 决定、事实引用与待决项，进入 Structured Study Intention。 |
| Structured Study Intention | 形成 Record，区分 known semantics、capability gap 和 missing semantic decision，再进入 Template Filling。 |
| Template Filling | 按本文件四文件布局填入各自唯一 owner，只写已确定语义，保持 gaps / unresolved items 可见；草稿不得冒充完整 authority。 |
| Semantic Review | 执行本文件 Semantic Gate；语义完整进入 Authority Complete，实质缺口进入 Semantic Decision Required。 |
| Semantic Decision Required | 向 human 表达缺失决定，取得明确 resolution 后更新 Record，返回 Template Filling 并再次完整 Review。 |
| Authority Complete | 确认 Study-owned semantics 与导航完整；不等同于 capability ready，不自动进入 implementation。 |

每个未决项记录 `unresolved field / topic`、`missing semantic decision`、`why the decision matters`、`recommended resolution`，有实质差异时再给出 `alternatives`。建议不构成默认授权；Agent 不自行选定改变研究含义的选项。

Study input 必填 / defaults、workflow 顺序 / failure、Artifact completeness / retention、retained run identity、empty result，以及适用的 hypothesis / Evidence 等缺失决定均进入该 loop。不因 Analysis / Evidence 为零而要求补出不存在的研究含义。缺少 Observation capability 要走独立 authoring，而非替当前 Study 填 Observation semantics；框架明确 deferred 的问题不在本流程自动决定。

## Study Authority Completeness Gate

Gate 判断 Study-owned semantics 是否完整，不代替 dependency capability readiness。对历史 Study 仅在 [Compatibility](COMPATIBILITY.md) 的明确触发范围适用，不追溯宣布 legacy Study invalid。

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | 六个 areas 均有实质内容、唯一 owner，无未解决 Study-owned research semantic decision。 |
| New Study topology | 本文件规定的四文件均存在且有实质内容，entry 直接链接其他三个 owner，细节不重复堆在 entry；只对新 Study 强制。 |
| Navigation | Entry、specialized owners 与实际 consumed Component / Observation authority 可沿链接到达，无 orphan owner，不默认加载无关 sibling authority。 |
| Input ownership | Parameter owner / consumers / semantic role、bindings、defaults、用户表达和 semantic request identity 符合 Schema；retained run identity / execution-only output options 仅声明 retained outputs 时要求。 |
| Observation canonical ownership | 每个 Observation dependency 有独立 Observation canonical owner / Artifact contract；未存在能力明确列为 gap。Study 不重定义 population、grain、derivation、validity、input domain 或 Artifact schema。 |
| Component dependencies | 实际 component 有 canonical I/O / dependency contract 与 bindings；upstream-backed result 由 orchestration 准备，Analysis 仅调用 pure component；不虚构 retained Artifact / business key / cache。 |
| Artifact dependencies | Observation identity、invocation inputs、canonicalization、所消费 Artifact identity 与 workflow / optional Analysis consumption 清晰；只消费 complete Artifact，不以 SQLite / run directory 识别业务对象。 |
| Method completeness | Required workflow / steps、consumes / produces、顺序、failure / empty semantics 与 materialization 符合 [Workflow](WORKFLOW.md)；optional Method Context / Analysis 若存在，contract 完整无悬空 references。 |
| Objective-to-result traceability | Objective → workflow → dependencies → execution outcome 可追踪；retained outputs / Analysis / Evidence 仅实际声明时核对其关系。Workflow Artifacts=0、Analysis=0、Evidence=0 不构成 incompleteness，不制造假对象。 |
| Retained run identity | 仅 retained-output Study 适用；等价请求与 identity-changing 输入区分一致，覆盖实际 bindings / Analysis configuration，execution-only options 不参与。Orchestration-only request identity 不映射为 filesystem run key。 |
| Runnable contract | Study input / CLI mapping、runtime outcome 与所声明 output shape 满足 [Research UI authority](../ui/ARCHITECTURE.md)；design readiness 按 [Authoring](AUTHORING.md#publication-与-dependency-handoff) 验证，runtime missing 单独记录，不以 future delivery 假装 runtime-ready。 |
| Result completeness | Runtime presentation / counts / empty / failure 完整，temporary plan / references 不自动成为 Artifact；只有具名 retained Workflow Artifact 实际存在时才要求其 shape / identity / completeness / retention。Evidence 若存在再核对 structure / sample / exclusion counts，不以 filename 替代 identity。 |
| Study semantic isolation | Study-owned Analysis / evidence semantics 不继承 sibling Study、retained evidence 或 historical shared analytical semantics；Artifact reuse 通过 Observation public boundary 合法引用；明确跨研究的小领域机制可引用 component，研究语义仍独立。 |
| No premature abstraction | 不因相似代码自动修改 shared owners / sibling Study；明确 shared 提升按 component authority，不创建 reusable Analysis framework、registry 或 DAG。 |
| Dependency distinction | Required capability / owner、Study-owned workflow / result semantics 与 readiness 分开；缺失 Component / Observation / upstream capability 有显式 gap，不在 Study Method 临时实现。缺失 material consumption decision 仍作为 semantic finding。 |
| Internal consistency | Objective 与允许 configurations 一致，hypothesis 若有再验证其关系；defaults / domain / binding 无冲突，Acceptance 对应 Method / Results；Analysis sample selection 不改写 population / validity，上游 facts 不重定义。 |

若 hypothesis 固定某配置而 Inputs 允许更广范围，返回具体 finding，由 Authoring human loop 明确关系；不自行将其解释为 default hypothesis。Class / function 命名、代码拆分与测试布局等纯实现细节不阻止 authority complete。

## Review outcome

Gate 全部通过判定 **Study Authority Complete**：Study-owned semantics 已确定，后续 Implementer 无需重新决定；该结果不表示 Observation / upstream capability ready。Dependency reconciliation 和 implementation handoff 沿 Authoring 处理。

未通过时返回具体未解决字段、引用、ownership conflict 或 missing decision，不将其写成已锁定语义。Authoring 更新 Record / 草稿后重新完整 Review；不能用实现便利性或 sibling 惯例替代 human decision。

## Publication 与 dependency handoff

**Study Authority Complete** 表示六个 areas 与关系完整，Implementer 无需重新决定 Study-owned semantics；可以先于所需 capability readiness。若所需 Component / Observation 尚未存在，可记录足够明确的 I/O / Artifact requirement / gap；尚不能确定的 material consumption semantics 则仍是 semantic incompleteness，不能仅改名为 gap 绕过 Gate。

**Research dependency contracts complete** 表示实际使用的 Component I/O / bindings / completeness / failure，以及 Observation identity / Request / Artifact / durable reuse 与 upstream capability 均明确且无 semantic gap / ownership conflict。仅所用 Observation 适用 durable lifecycle；component 不补出 Artifact identity。Contract complete 可以先于 producer runtime；缺失事实 capability 或 material consumption decision 仍是 gap，不能用 planned implementation 掩盖。

**Study implementation architecture complete** 表示 package / CLI / orchestration 分工、typed request / runtime outcome mapping、composition、output shape 与 acceptance 均明确，继承 [Package Contract](IMPLEMENTATION.md) 与 actual concrete handoff，不待 implementer 重新决定 persistence ownership、Workflow Artifact、output model 或 bindings。

**Implementation Ready** 表示 Study Authority Complete、Research dependency contracts complete 与 Study implementation architecture complete 均成立，无新 semantic gap，足以按顺序直接实施 vertical slice；这是 design readiness，不表示 producer 或 Study runtime 已存在。No retained output 是合法明确 output model，不以 runtime 缺失强制退回已完成的 authority design。

**Dependency Reconciled** 在 Study handoff 中继续表示实际 runtime dependencies / public invocation 已实施并核对 bindings；producer runtime 缺失时该 runtime 状态仍为未完成，必须与 Implementation Ready 分开记录。实际顺序为真实必要的 component / Observation mechanics → declared producers implementation / acceptance → runtime / Study bindings reconciliation → Study implementation / end-to-end acceptance；不为了顺序预建共享框架。Actual invocation / runtime readiness 不由 authority status 推断。

工作顺序仍为 `CREATE → RECONCILE → IMPLEMENT`；进入 implementation 按 Package Contract，完成后按 Implementation 的 review criteria 独立验证 topology。这些名称区分 authoring / dependency readiness，不建立 persisted status、registry 或 engine。Existing Study reconciliation 与 human-triggered `CONSOLIDATE` 由 Compatibility 拥有，不是上述依赖核对的自动副作用。

实施某个 Analysis 时只读其 contract、实际 consumed Artifact / Observation authority 和必要机制；更深层拆分不建立 generic component interface、Artifact Registry、DAG 或 plugin framework。
