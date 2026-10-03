# Research Study Semantic Schema

本文件是 retained Study semantic structure 的唯一通用 canonical definition；retained Study 表达值得保留的研究 / orchestration authority，不要求每次 execution 都保留 Study output。创建流程见 [Authoring](AUTHORING.md)，authority 布局见 [Skeleton](SKELETON.md)，完整性验证见 [Review](REVIEW.md)，既有 Study 适用规则见 [Compatibility](COMPATIBILITY.md)，runnable convention 见 [Research UI authority](../ui/ARCHITECTURE.md)。Observation framework 由 [Observation authority](../observations/ARCHITECTURE.md) 拥有，具体 empirical semantics 由 concrete Observation 拥有。Local / shared 提升、Observation 准入与 component caller 分工唯一见 [Shared Component authority](../shared/ARCHITECTURE.md)。

## Canonical Study semantic object model

```text
Study [1]
├── Identity [1] (structural information)
└── Semantic Areas
    ├── Question / Objective [1]
    ├── Inputs [1]
    ├── Method [1]
    │   └── Study-owned Workflow [1]
    │       ├── Workflow Step [1..N]
    │       ├── Shared Component Dependency [0..N]
    │       ├── Observation Artifact Dependency [0..N; 1..N when used]
    │       ├── Runtime Orchestration State [0..N; not retained Artifacts]
    │       ├── Study-local Workflow Artifact [0..N]
    │       ├── Method Context [0..1]
    │       └── Study-local Analysis [0..N]
    ├── Results [1]
    │   ├── Execution Outcome / Presentation [1 when runnable]
    │   ├── Retained Workflow Result [0..N]
    │   └── Evidence Product [0..N]
    ├── Limitations [1]
    └── Acceptance [1]
```

Identity 是 structural information，不是第七个 research semantic area；六个必答 areas 仍为 Question / Objective、Inputs、Method、Results、Limitations、Acceptance。各 area 必须有实质内容，`TBD`、空节或“采用合适方法”不能代替研究决定。Study 必须有 workflow，Study-local retained Workflow Artifacts、Analysis / Evidence 均可为零。Orchestration-only Study 合法拥有 Observation dependencies>0、Workflow Artifacts=0、Analysis=0、Evidence=0，以已确保 durable complete 的 Observation Artifacts 与明确 runtime outcome 完成目标；不人为创建 plan / manifest / 空 Evidence。Question area 不强制 hypothesis；若有 hypothesis 才定义其适用配置范围。Expected products 与尚未运行的 actual results 必须区分。

Study 拥有 user request、input bindings、Component invocation / Observation ensure orchestration、execution order、runtime plan expansion、failure / continuation semantics、human-facing execution result 与 optional Analysis orchestration；retained workflow outputs / Evidence 仅按实际 authority 声明。Study 不拥有 Observation definition 或 reusable empirical persistence。[Workflow authority](WORKFLOW.md) 唯一拥有 runtime state / retained Artifact distinction、steps、显式 retained Artifact identity 与 complete-input boundary。Dependencies、steps、已声明 Workflow Artifacts、Analysis 与 Evidence 具有可引用的 Study-local name；dependency local name 不替代 Observation / Artifact semantic identity，不要求 repository-global ID 或统一前缀。

| Element | Ownership 与必需语义 |
| --- | --- |
| Study / Identity | Bounded research question 或 research preparation / empirical collection objective 的 authority unit；稳定 `study_package`、`studies/<study_package>/ARCHITECTURE.md` entry，预期 runnable 时有 public Study ID。 |
| Question / Objective | 目标、范围、预期 execution outcome，以及明确需要时的 retained workflow results / evidence；hypothesis 与解释范围仅在适用时定义。 |
| Inputs | Study request / configuration、Component / Artifact invocation input bindings、Study-owned analytical sample selection、material parameter 的 owner / consumers / semantic role / input contract，以及 semantic request identity；retained run identity 仅保留 output 时要求。Observation input domain、canonicalization 与 empirical population 通过 canonical owner 引用，不重新定义。 |
| Method | Required workflow / steps、实际使用的 Component / Observation dependencies、runtime plan / references、明确声明时的 Workflow Artifact production / consumption、failure / empty semantics，以及 optional Method Context / Analysis；具体依赖展开与执行顺序由当前 Study 拥有。 |
| Results | Execution outcome / human presentation、success / empty / failure 与 counts（适用时）；明确保留 output 时另声明具名 Workflow Artifact / Evidence contract、provenance 与 consumption。不重定义 Observation 或 Analysis computation，runtime result 不自动成为 retained product。 |
| Evidence Product | 稳定 Study-local name；以 `defined_by` 关系引用定义证据含义的 `1..N` 个具名 Analysis；给出 machine-readable structure、表 / 图 / 报告、metadata、exclusion counts 和复核所需 provenance。 |
| Limitations | 观察 / workflow / 解释范围、数据 / 样本限制与不得从结果推出的结论。 |
| Acceptance | 设计、产物完整性、可复核性、研究结果有效性及失败条件；不设模块统一统计阈值或 artifact schema。 |

## Parameter ownership 与 Study run identity

每个 material configurable parameter 明确以下关系，可用表格或具名字段表达，不规定序列化格式：

| Relationship | Required meaning |
| --- | --- |
| name | Study 内稳定参数名称。 |
| semantic owner | Study、Method Context、具名 Analysis，或所引用的 Shared Component / 独立 Observation；CLI 接收位置不决定 owner。Study 负责选择 invocation 值，不接管 Observation-owned input semantics。 |
| consumers | 实际使用该值的 dependency invocation、Analysis 或 Study-level 规则；共同使用不合并 ownership。 |
| semantic role | 改变该值是否改变研究请求或证据含义，以及影响哪些语义；identity-changing inputs 进入 Study semantic request identity，并在保留 output 时进入 retained run identity。 |
| input contract | 必填 / 可选、默认值、允许值 / domain、用户表达与适用 CLI 映射。Study 可锁定所选择的配置，不能扩展或改写 Observation canonical domain / meaning。 |

Study-owned analytical sample selection 是 Analysis 对已存在 Artifact 的消费范围，不改变原 Artifact population、grain、validity 或 schema。Study 可为更窄的研究问题选择子样本、分组与比较，但这些规则须定位至 Study / Analysis，并与 Observation completeness / validity 分开。

只控制 Study run-output execution behavior 的选项（如 `--overwrite`）单独标为 Study-owned execution-only option，给出消费位置、必填性、默认值与允许范围（适用时）；不参与 semantic run identity，也不授权 Observation refresh。Inputs 引用 Method、Component 或 Observation 的唯一 canonical semantics，不复制定义。

保留 Study run output 时，Inputs 必须定义：参与整次请求 identity 的 Study semantic inputs；等价用户表达的 canonicalization；哪些变化必须区分；排除的 execution-only options；以及 Study-owned deterministic run-key semantic rule。所消费的 Observation / Artifact semantic identity 必须由 dependency bindings 可确定，并覆盖影响 workflow results / evidence 的业务输入。具体 key encoding 可以留给 implementation design，不改变已锁定 semantic identity。

Orchestration-only Study 可以只定义 semantic request tuple，表达“同一个 Study request”；它不等于 persistent run Artifact identity，不要求 filesystem run-key encoding、output directory、collision、staging 或 overwrite。仅保留 output 时，相同 Study identity 与规范化语义请求得到相同 retained run identity，不同 identity-changing inputs 必须可区分。Identity 不依赖 wall-clock time、random UUID、偶然 path 或意外迭代顺序。本 schema 不规定统一 hash、编码、参数名或 CLI schema；public ID 与 output shape、配置适用性、placement / publication 沿用 [Research UI authority](../ui/ARCHITECTURE.md)。Study identity 不等同于 Observation business key，也不定义 upstream revision / definition evolution policy。

## Shared Component Dependencies

只声明实际使用的 component，引用其 canonical owner / narrow I/O contract、purpose、Study inputs / prepared values 到 component inputs 的 bindings、pure / upstream-backed distinction、result meaning / completeness / failure 与 consumers。Component result 作为 prepared runtime input，不要求 Observation Artifact identity / durable publication / business key；不能冒充 retained product。

Study orchestration 可调用 declared resolver / reader 获取 complete result，再交下游；Analysis 只可调用 pure calculator / selector / transform 计算已准备输入，不用 helper 隐藏 fetch / persistence。多个 Studies 可以依赖同一 component mechanism，不因此共享 research question / Analysis / Evidence semantics。各 caller 自己拥有研究选择与解释，不复制 component contract。

## Observation Artifact Dependencies

每个 dependency 必须明确：

| Field | Required meaning |
| --- | --- |
| local name / purpose | Study 内的稳定引用及其支持的研究事实需求。 |
| canonical owner | 所需独立 Observation identity、canonical authority entry 与 Artifact contract。能力尚不存在时明确 required capability 和 gap，不以 Study-local 定义替代。 |
| invocation inputs | Study configuration / request 到 Observation business inputs 的绑定，包括已锁定的值与所引用的规范化规则。 |
| Artifact identity | 按 Observation-owned identity contract 确定本请求消费哪个 Artifact；不得用 Study run directory、filename 或 SQLite path 代替。 |
| resolution / consumption | Study workflow 如何经 Observation public boundary resolve / ensure complete Artifact，哪些步骤 / optional Analysis 消费它；若 public invocation runtime 尚未就绪，单独记录 runtime readiness，不据此推翻已完成的 design readiness，不从 Study CLI 推导 Observation CLI。 |

所有 dependency 必须遵守 [Observation boundary](../observations/ARCHITECTURE.md)，普通 consumer 只消费已由 Observation durable publication 的 complete Artifact。Study 不拥有 Observation population、grain、derivation、validity 或 Artifact schema，不读取 Observation SQLite、不保存其 path 定位事实，不通过 DataLake / Snapshot 补齐依赖，也不复制 market rows 建立 Study / global empirical cache。Observation Artifact reuse 只通过同一 semantic request 再 ensure，由 Observation persistence 实现；mechanism reuse 通过 component public I/O，不适用此 durable lifecycle。Observation Artifact 是 retained empirical product，不是 Study-local Workflow Artifact 或 Evidence，不以 Study 决定是否物化为前提。步骤与显式 materialization 的规则进入 [Workflow contract](WORKFLOW.md)。

## Study-local Analysis contracts

Analysis 可为零。存在时，Method Context 只在多个 Analyses 真正共享 Study-owned research semantics 时定义；不造空 Context，不接管 Observation parameters 或 facts。每个具名 Analysis 明确以下字段：

| Field | Required meaning |
| --- | --- |
| identity / purpose | Stable Study-local name，以及回答的 Question aspect / evidential purpose。 |
| consumes | 按 local names 引用 workflow 已准备的 complete Observation Artifacts、Study-local Workflow Artifacts 或已准备的 complete component results，并声明适用 Study / Method Context inputs。 |
| parameters / semantics | Analysis-owned parameters、analytical sample selection、分组、比较、变换、统计和解释规则。 |
| validity / exclusions | Analysis 层的样本限制、缺失统计、排除与失败语义；不能改变 Observation validity 或把 partial Artifact 当作有效输入。 |
| produces | 形成的 Study-specific computation / comparison / statistics 与其 workflow result 或 evidence semantics；不重复维护 Results 的 product names / shapes。 |

Analysis 可调用 pure shared component，但只计算已准备的 complete inputs，禁止调用会获取 facts 的 component、DataLake / Snapshot、fetch market data、invoke / resolve / ensure Observation 或读取 Observation persistence；dependency resolution 唯一归 Study orchestration。Analysis 的 grouping / transformation 不成为新的 retained Observation definition。一个 Analysis 无须消费所有 Artifacts，多个 Analyses 可消费同一个 Artifact；只有 Observation Artifact 拥有当前 cross-Study retained empirical reuse；shared component 复用机制与 I/O，不复用 research persistence。Study-local Workflow Artifact 不建立跨 Study reuse。共同输入不合并 ownership。

Objective 必须能追踪到 workflow、dependencies 与明确 execution outcome；仅实际声明 retained outputs 时才要求 retained-result traceability。Observation-only Study 可在此完成，不需 Workflow Artifact / Analysis / Evidence。Analysis 若存在，其 material outputs 须按实际声明经 Results 追踪到 workflow result 或 Evidence。Evidence 若存在，唯一拥有 Analysis → Evidence Product mapping，以 `defined_by` 引用 defining Analysis，并可反向追踪至已准备 Artifact。证据 local name 不等于 representation、filename 或 path；runtime plan / references / request metadata 不因此成为 Artifact 或 Evidence。Results 明确已有结果与尚未执行状态，无 Evidence 时不填占位数值或推测 finding。

## Dependency direction 与 deferred Analysis model

Canonical execution flow 为 User Study request → Study-owned orchestration → declared Component invocation / Observation public ensure → prepared complete component results / durable Observation Artifacts → execution outcome / optional Analysis。Study-local retained Workflow Artifacts 与 Evidence 只在实际声明时存在，不是强制 stage。Observation 继续独立消费 public upstream facts。Study / Analysis 不反向重定义 Observation；Observation 不依赖 Analysis 或 Study conclusion。Sibling Study research-semantic dependency 不合法；相似 analytical code 不自动触发 shared 抽取。明确跨研究复用的小领域机制可以依 component authority 提升，不能提升 Study-owned question / interpretation 为共享依赖。

当前 Analysis 仍为 Study-local semantic object。Future Analysis 若需要 empirical facts，只消费 Study orchestration 已准备的 complete inputs，不读 DataLake / Snapshot 或 Observation SQLite，不自行 ensure；Analysis persistence / cache / SQLite、cross-Study product / cross-invocation reuse 与 Evidence persistence model 均另行设计，本轮不决定。具体多步 workflow 由当前 Study 按 [Workflow authority](WORKFLOW.md) 表达，不构成 generic Analysis graph / DAG executor。Workflow 跨 invocation resume / reuse 等 deferred concern 进入该专题；旧 conditional component Artifact identity 仅按 [Compatibility](COMPATIBILITY.md) 保护历史结构，不是新 Study contract。Observation refresh / definition evolution 继续由 [Observation deferred decisions](../observations/ARCHITECTURE.md#explicitly-deferred-decisions) 记录。
