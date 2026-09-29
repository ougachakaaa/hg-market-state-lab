# Research Study Semantic Schema

本文件是 retained Study semantic structure 的唯一通用 canonical definition；创建入口见 [Authoring](AUTHORING.md)，完整性与决策流程见 [Review](REVIEW.md)，既有 Study 的适用规则见 [Compatibility](COMPATIBILITY.md)，runnable Study 的共享调用与输出约定见 [Research UI authority](../ui/ARCHITECTURE.md)。本文定义 semantic objects 与完整性，不规定文件布局，也不拥有具体 Study 语义。

## Canonical Study semantic object model

```text
Study [1]
├── Identity [1] (structural information)
└── Semantic Areas
    ├── Question [1]
    ├── Inputs [1]
    ├── Method [1]
    │   ├── Method Context [0..1]
    │   ├── Observation [1..N]
    │   └── Analysis [1..N]
    ├── Results [1]
    │   └── Evidence Product [1..N expected]
    ├── Limitations [1]
    └── Acceptance [1]
```

`Identity` 是 Study 的必备 structural information，不是第七个 research semantic area；`Semantic Areas` 只是分组标签。`Question`、`Inputs`、`Method`、`Results`、`Limitations`、`Acceptance` 仍是 Authoring 与 Review 所指的六个必答 areas。`Inputs [1]` 表示该 area 必须定义；具体输入值由 Study 确定，不要求另建 `Input` object 或统一 cardinality。`Results [1]` 必须定义 `1..N` 类预期保留的 `Evidence Product`；执行前实际产物可以是 `0`。

除 Study、具名 Observation / Analysis 和按条件定义的 component Artifact 外，本 schema 不要求其他 structural area 另有独立 ID；retained Evidence Product 须有供关系引用的 Study-local name。每个 area 与每条语义规则须有唯一 canonical owner，并能从该 Study 的 `ARCHITECTURE.md` 导航到。各 object 是语义层次，不对应固定 Markdown 或 Python 文件。

| Element | Role / ownership boundary | Required semantic fields and validity |
| --- | --- | --- |
| `Study` | 一个 bounded research question / small hypothesis 的本地 semantic authority unit，不是单独的 statistics job；上游事实及非 Research-semantic 机制仍由其 canonical owner 定义。 | 拥有 scope、六个必答 semantic areas 与 retained evidence。Study-specific 数值、公式、对象、方法和产物取舍由当前 Study authority 定义。 |
| `Identity` | Study 的 structural information，标识当前 Study 并提供稳定的 authority 入口。 | 稳定的 `study_package` identity 与 `studies/<study_package>/ARCHITECTURE.md` 入口；预期 runnable 时有 stable public Study ID。 |
| `Question` | 拥有研究意图与证据目标。 | 研究目标、hypothesis、可辨识的问题、希望产生的 evidence 类别及其适用配置范围。 |
| `Inputs` | 拥有跨 Study boundary 的请求输入与整次请求的 identity 规则，不因此接管每个值的研究含义。 | 外部事实及 canonical 来源、目标 population、样本选择与范围、数据选择及 configurable values；逐项记录 material parameter 的 owner、consumers、semantic role 和适用的取值契约。Runnable 时定义 Study-specific semantic input 的必填/可选、默认值、用户可见表达与 CLI 映射，并区分 Study-owned execution-only option。保留 evidence 时定义整次请求的 identity 参与输入、等价输入 canonicalization、必须区分的变化、排除项与 Study-owned deterministic run-key rule。 |
| `Method` | 拥有当前 Study 的 analytical graph：what is observed / analyzed and what it means。 | 显式定义共享上下文（若存在）、`1..N` 个具名 Observation、`1..N` 个具名 Analysis 及其消费关系；各组件的选择、输入与输出足以确定研究含义。 |
| `Results` | 拥有 produced evidence 的保留与 human / machine consumption、presentation；Analysis 拥有比较、计算与证据含义。 | 定义 `1..N` 类预期保留的 `Evidence Product`、必须保留的 Analysis / statistical evidence、是否独立保留组件 Artifacts，以及哪些 human / machine forms 必需。明确已有 evidence 与尚未执行的状态；无 evidence 时不填占位数值、finding 或推测结论。Filename / format 仅在构成稳定 Study contract 时锁定。 |
| `Evidence Product` | Results 下的预期保留产物；其证据含义来自 Method 中的 Analysis，不另定义计算或统计语义。 | 逐项给出稳定的 Study-local name，并以 `defined_by` 关系显式引用定义其证据含义的 `1..N` 个具名 Analysis；明确所表达的 evidence、所需 machine-readable structure、table、plot、report 或其他 visualization，以及适用的 empty bucket、missing statistic、excluded observation 等边界状态和复核必需的 metadata、exclusion counts、provenance。 |
| `Limitations` | 拥有证据的解释边界。 | 研究边界、解释限制与不得从结果推出的结论。 |
| `Acceptance` | 拥有研究设计与预期产物的验收语义。 | 设计与产物完整、可复核的条件，以及该 Study 的结果有效性与失败条件；不设全模块统一统计阈值、运行规则或 artifact schema。 |

### Parameter ownership and Study run identity

每个 material configurable Study parameter 均须可按下列关系直接读取；可用表格或具名字段表达，不要求统一序列化格式：

| Relationship | Required meaning |
| --- | --- |
| `name` | 当前 Study 内稳定、可引用的参数名称。 |
| `semantic owner` | `Study`、`Method Context`、某个具名 Observation 或某个具名 Analysis；CLI 接收位置不决定 owner。Study 拥有 population 等 Study-wide 语义，Method Context 只拥有真正跨组件共享的研究语义，组件特有参数由组件拥有。 |
| `consumers` | 实际使用该值的具名组件或 Study-level 规则；与 owner 分开记录，多个 consumers 不自动改变 owner。 |
| `semantic role` | 说明改变该值是否改变研究请求或证据含义，以及它影响的语义；identity-changing semantic parameter 必须进入 run identity。 |
| `input contract` | 适用时列出必填/可选、默认值及允许值、范围或 domain；固定且不可配置的 Study 语义不因此变成参数。 |

只控制 retained execution behavior 而不改变研究含义的值（如 `--overwrite`）应单独标为 Study-owned execution-only option，说明其执行消费位置、必填性、默认值与允许范围（适用时）；它没有 component semantic owner，也不参与 semantic run identity。`Inputs` 中的参数记录可以引用 `Method` 中唯一拥有的组件语义，不复制其定义。Observation 与 Analysis 是 Study-local semantic objects，不是跨 Study 的通用组件接口。Runnable Study 的 public ID 映射、调用入口、共享配置、output placement、collision 与 publication boundary 沿用 Research UI authority；本 schema 不规定统一 CLI 参数名、参数 schema 或 run-key 算法。Study authority 须把每个 semantic input 连接到可实现的用户提供方式。

保留 evidence 的 Study 须在 `Inputs` 明列或明确引用 run identity 关系：参与 identity 的 Study semantic inputs；不同用户表示映射至同一语义请求的 canonicalization；哪些参数变化产生不同 identity；哪些 execution-only options 被排除；以及从规范化语义请求确定 run key 的 Study-owned rule。相同 Study identity 与规范化语义请求须得到相同 run identity，不同的 identity-changing 输入须可区分。Run identity / run key 不依赖 wall-clock time、随机 UUID、偶然路径或意外的迭代顺序；具体 hash 或编码算法不由本 schema 统一规定。

### Method component contracts

`Method Context [0..1]` 由当前 Study 拥有；仅在多个 Observation / Analysis 真正共享研究语义时定义共同上下文与 method-level parameters，并说明各参数影响哪些组件。没有共享语义时不造空 Context，也不为减少重复而接管组件参数。

`Observation [1..N]` 与 `Analysis [1..N]` 均由当前 Study 本地拥有；每个具名组件有独立语义。其 contract 可按字段扫描：

| Field | Observation | Analysis |
| --- | --- | --- |
| `identity` | Stable local name / identity。 | Stable local name / identity。 |
| `purpose` | 所观察的市场现象。 | 要回答的 Question aspect / evidential purpose。 |
| `consumes` | 分别列出所消费的 Study inputs、适用的 Method Context 值（若有）与上游 canonical data / facts 及其 owner。 | 以稳定 Study-local name 显式列出所消费的 `1..N` 个具名 Observation。 |
| `parameters` | 自身 parameters。 | 自身 parameters。 |
| `semantics` | Observation semantics / derived variables。 | Grouping / comparison / statistical semantics。 |
| `validity / exclusion` | 适用的 eligibility / exclusion / validity 规则。 | — |
| `produces` | 供后续消费的语义输出。 | 产生的 evidence 语义；不重复维护 retained Evidence Product 的 Study-local name。 |
| `artifact identity` | 仅需独立物化、保留或复用时定义。 | 仅需独立物化、保留或复用时定义。 |

Analysis 的 `consumes` 以 stable local name 引用具名 Observation；`produces` 只定义 Analysis 自身的 evidence semantics。`Results` 下的 Evidence Product 唯一拥有 retained Analysis → Evidence Product mapping：每个 Evidence Product 从自身单向引用 defining Analyses，Analysis 不重复列出 Evidence Product local names。Analysis 的 `purpose` 指向其回答的 Question aspect；沿 Analysis 的 Observation 引用与 Evidence Product 的 Analysis 引用，须能恢复 Question aspect → Observation → Analysis → Evidence Product 链。一个 Evidence Product 可以汇总多个 Analyses；每个 material Analysis 都须能经 Results 中的映射追踪到 retained evidence。Evidence Product 的 local name 标识证据语义，不是表格、图形、报告的格式、filename 或 path；这些表示选择不构成依赖边。纯 request/provenance metadata 可随 evidence 保留，不因此成为独立的 Evidence Product。Local name 不采用 repository-global ID 或强制 `O-*` / `A-*` / `R-*` 前缀。

### Method dependencies and component Artifact identity

| Rule | Contract |
| --- | --- |
| Data and component flow | Study Inputs、Method Context（若有）及 upstream canonical facts → Observation；具名 Observation → 具名 Analysis；具名 Analysis → retained Evidence Product。Analysis 还可按参数的 owner / consumers 声明使用适用的 Study 或 Method Context 值，但仍须消费具名 Observation。一个 Analysis 无须消费所有 Observations；多个 Analyses 可消费同一个 Observation；多个 Observations 可独立消费相同 upstream data；一个 Evidence Product 可汇总多个 Analyses。共同输入不合并 semantic ownership。 |
| Forbidden semantic dependencies | Analysis → Observation 不合法；默认不建立 Observation → Observation semantic contract；Observation 的定义不得依赖某个 Analysis 的目标或已得结果；sibling Study → sibling Study research-semantic dependency 不合法。复用 dataframe、helper、internal function 或中间计算，以及 filesystem layout，都不创建 semantic dependency。 |
| Conditional Artifact identity | 仅当 Observation / Analysis 需要独立物化、保留或复用时，当前 Study 才定义其 component Artifact identity；不要求每个组件都有持久化 artifact。已物化的 Observation Artifact 可由语义 identity 匹配的 Analysis 复用。 |
| Observation Artifact identity | 明列 Observation identity、相关 Method Context parameters、Observation-owned semantic parameters 及相关 source / input identity。只纳入影响该 Observation 语义的输入。 |
| Analysis Artifact identity | 明列 Analysis identity、实际消费的每个 Observation 在当前 Study request 下的完整 semantic identity、相关 Method Context parameters 及 Analysis-owned semantic parameters。对已独立物化的 Observation，使用其 Artifact identity；对未物化的 Observation，纳入其 stable local identity 及全部 identity-determining semantic inputs，包括相关 Method Context / Observation-owned parameters 与 source / Study input identity。只纳入影响该 Analysis 语义的输入。 |

未物化 Observation 的 stable local name 本身不足以确定 Analysis Artifact identity；同一 Observation 的 window、source 或其他 identity-changing semantic input 不同，消费它的 Analysis Artifact identity 必须可区分。Component Artifact identity 由上述语义输入决定，不依赖运行时间、随机 UUID、偶然路径或意外的迭代顺序；它与 filesystem filename、path、serialization representation 不同。Study 可按参数构造易读文件名，具体 hash、serialization、文件名或 artifact 格式只在构成稳定 Study contract 时锁定。新增或重跑 Analysis 在语义上不要求重做未变化的 Observation；这不要求实现提供分段执行、通用 DAG executor、全局 Artifact Registry、cache framework 或 shared execution protocol。

六个 semantic areas 必须有实质内容；`TBD`、空节或“采用合适方法”不能掩盖会改变研究含义的缺失决定。非语义性的命名、排版与实现细节可由 Agent 整理，不进入 human semantic-decision loop。

## Study authority topology

Study 是一个 semantic authority unit，不等于一个 physical Markdown file。`studies/<study_package>/ARCHITECTURE.md` 始终是稳定 canonical entry：概述 Study identity、bounded Question / hypothesis、scope、stable public ID（若适用）、主要 Inputs / population、named Observations 与 Analyses 及显式消费关系、主要 retained evidence、核心 Limitations / Acceptance、upstream dependencies / gaps、implementation location，并导航到详细语义。概述不复制 specialized contract。

六个 semantic areas 可自然分配。例如 entry 拥有 Question、scope、核心 Limitations 与导航；`INPUTS.md` 拥有 input / population / parameter ownership / run identity；`METHOD.md` 拥有 Method Context 与组件图；`RESULTS.md` 拥有 retained evidence、详细结果有效性与相关 Acceptance。其他 grouping 也允许，但每条语义规则只有一个 canonical owner，且所有 owner 从 entry 可达。简单 Study 保持单文件；不要按 heading 数量拆分或产生只有几行内容的小文件。

创建复杂 Study 时，在设计阶段判断 disclosure boundary。若有多个独立 Observation / Analysis、多组参数 owner、独立组件 Artifact 或复杂结果契约，应考虑从一开始建立 entry → specialized authority。Method 复杂到实现单个 Analysis 仍需加载无关 Analysis 细节时，可由 Method 入口列出组件及显式 Observation → Analysis 消费关系，再把相关 Observation / Analysis 下沉为 Study-local authority；不要求每个组件各建一个文件。实现单个 Analysis 时，只读该 Analysis、其明确消费的 Observation 和必需的上游 contract。拆分不创建跨 Study 组件接口、DAG executor、Artifact Registry 或 plugin framework。

## Study implementation topology

一个 retained Study 是独立的 semantic authority unit；同名 executable implementation directory 也应作为小型 bounded module 组织。Study 不等于一个容纳全部逻辑的 `study.py`：简单 Study 可以使用单个 implementation module，复杂 Study 可以使用多个 Study-local modules/packages。拆分依据是 semantic responsibility 与阅读边界，而非文件数量或行数。

Study-local implementation SHOULD 足够贴近上述 Method graph，使 material Method Context、Observation construction、Analysis execution、Results / presentation 与 orchestration 的职责都能独立理解和定位。典型分解可以是 `study.py` 负责 orchestration / composition，`observations.py` 构造 Observations，`analyses.py` 执行 Analyses，`results.py` 组装、保留和呈现 evidence，`statistics.py` 保存 Study-local mathematical mechanics。这只是 decomposition pattern，不是固定目录模板；semantic boundaries 是候选拆分点，不要求每个 Observation 或 Analysis 对应一个文件，也不要求每个 Study 都有上述所有文件。Authority file 与 Python file 无须一一对应，要求的是 authority component 能追踪到易定位的 implementation responsibility。

复杂 Study 的 `study.py` 宜作为可读的 orchestration / composition entry：从 Study-level request validation，经 Observation construction、Analysis execution、canonical result assembly 到 Results retention，打开该入口应能快速理解 pipeline，而不必先阅读统计、绘图或持久化细节。若有多个具名 Observations / Analyses、独立的组件职责、大量 retained result / presentation、独立 artifact identity 或 mathematical mechanics，或 CLI、分析、绘图、持久化混于一处，应显式评估 Study-local decomposition。修改一个 material component 必须阅读大量无关实现，或单文件已无法呈现语义图，也是拆分信号；不设 LOC 阈值。

Implementation progressive disclosure 沿 `Study ARCHITECTURE.md → relevant METHOD authority → relevant Study-local module → related tests`。修改一个具名 Analysis 时，应尽可能无需理解无关 Analyses、plotting、report、retention、artifact hashing 或无关 Observation mechanics。优先在当前 Study package 内拆分；相似 helper 不构成提升至 `market_research/shared/*`、修改 sibling Studies 或创建 generic Observation / Analysis / statistics / pipeline framework 的理由。跨 Study consolidation 仍须按既有 human-triggered policy 单独进行。
