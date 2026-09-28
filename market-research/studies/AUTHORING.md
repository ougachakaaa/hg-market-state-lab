# Research Study Authority Authoring

本文件是 retained Research Study authority 的固定 schema 与 authoring workflow 的唯一 canonical owner。Research 模块边界、现有 Study 入口与 authority / implementation 分离见 [market-research architecture](../ARCHITECTURE.md)；runnable Study 的共享调用与输出约定见 [Research UI authority](../ui/ARCHITECTURE.md)。本文只规定如何把 Study Intention 写成独立的 Study authority，不定义任何具体研究的语义、运行或实现。

## 1. 输入与输出

输入称为 `Study Intention`，由 human 提供，可以是自然语言。进入 `Template Filling` 前，authoring Agent 必须先将已给出的内容整理为显式的 **Structured Study Intention Record**；尚未给出的项允许留空：

| 输入项 | 记录内容 |
| --- | --- |
| Research goal / question | 想研究什么，以及已说明的动机或问题边界 |
| Inputs & population | 已指定的数据、对象、样本范围与选择条件 |
| Method intention | 已指定的比较、变换、统计或评估思路 |
| Research product | 期望保留的结果、证据或呈现形式 |
| Boundaries | 已指定的不研究内容、解释限制或约束 |
| Open decisions | human 已提出或 Agent 识别出的待决研究选择 |

Record 可以对上述每项标记 semantic source（如 `human decision` / `canonical authority`）和 resolution state（如 `decided` / `unresolved`），使事实引用、human 决定与待决选择可区分。这是 authoring workflow 的中间 representation，可以存在于对话或工作草稿中；不要求新建 repository artifact，也不是最终 Study canonical authority。

这不是要求 human 预先填写完整 authority 的表单。Agent 可以规范措辞、组织已给出的决定，并引用现有 canonical authority 中明确拥有的事实；不能从常见做法、既有 Study 或实现便利性推断未给出的研究决定。Record 中未解决的实质语义选择必须进入下述 human decision loop。

输出终态是 `market-research/studies/<study_package>/ARCHITECTURE.md` 中符合下述 schema 的 **Canonical Study Authority**。每个 retained Study 独立拥有自己的研究语义与 retained evidence；同名 `src/market_research/studies/<study_package>/` 是独立的 implementation 位置。Authoring 完成不启动 implementation、Study execution 或后续能力设计。

## 2. 固定 Study authority schema

每个新建或实质更新的 retained Study authority 使用下表六个顶层 section，按表中顺序书写。可以增加 Study 自己的子节和执行说明；不能省略、改名或用其他文档代替必需 section。一个 Study 围绕一个 bounded research question / small hypothesis，组织一个或多个具名 Observation 与一个或多个具名 Analysis，从所需的不同视角建立 evidence；它不是一个单独的 statistics job。Study-specific 数值、公式、对象、方法、产物名称及取舍只写在该 Study authority 或其明确链接的 narrow canonical owner，不写进本模板；不得以 sibling retained Study 充当可复用研究语义的 canonical owner。

| 必需 section | 必须回答的 product / research semantic 问题 |
| --- | --- |
| `Question` | 研究目标、hypothesis 与可辨识的研究问题是什么；研究希望产生哪类 evidence，其适用的配置范围是什么？ |
| `Inputs` | 哪些外部事实、数据选择与 configurable values 跨越 Study boundary 进入研究请求，其 canonical 来源、目标 population、样本选择与范围是什么？每项参数的 semantic owner 是 Study / Method、哪个具名 Observation 或哪个具名 Analysis？若 Study 预期 runnable，stable public Study ID、Study-specific semantic inputs、必填/可选项、默认值及每项的用户可见表达和 CLI 映射是什么？影响 retained execution 的 Study-owned option（如允许覆盖既有结果）如何提供？若保留 evidence，整次请求的 semantic input、等价输入 canonicalization、必须区分的变化与 Study-owned deterministic run-key rule 是什么？ |
| `Method` | Study-local analytical graph 的共同上下文、具名 Observations 与具名 Analyses 是什么；各自观察或分析什么、消费什么、产生什么，哪些选择改变其含义？已有适用的 narrow shared 或其他非 sibling canonical authority 明确拥有这些分析语义时可以直接引用。 |
| `Results` | 哪些已产生的 evidence products 必须保留，人和机器如何消费并复核？是否独立保留 Observation / Analysis Artifacts，哪些 Analysis / statistical evidence、machine-readable structure、table、plot、report 或其他 visualization 必需？empty bucket、missing statistic、excluded observation 等边界状态如何表达？哪些 metadata、exclusion counts 与 provenance 是复核所必需的？artifact filename/format 只有构成稳定 Study contract 时才须锁定；已有 evidence 与尚未执行的状态分别是什么？ |
| `Limitations` | 研究边界、解释限制及不得从结果推出的结论是什么？ |
| `Acceptance` | 什么条件表明研究设计和预期产物已完整、可复核；该 Study 的结果有效性条件在哪里明确？ |

`Inputs` 说明值如何进入请求，并记录 runnable Study 整次请求的 identity 规则，不因此拥有每个值的研究含义。同一值可以经 CLI 提供、同时由某个具名 Observation 定义其语义；Study / Method 只拥有真正定义多个组件共同研究语义的参数，不为减少重复而接管所有参数。每个参数都要能追踪到其 semantic owner、允许值及适用组件。共享 output placement、collision 与 publication boundary 由 Research UI authority 拥有。

`Method` 定义 what is observed / analyzed and what it means；`Results` 定义 which produced evidence products are retained and how humans / machines consume them。Analysis 定义比较、计算和证据含义；table、plot、report 等 visualization / presentation 由 Results 定义。`Results` 不要求 authoring 时已经运行真实研究。尚无 evidence 时如实记录该状态，不填占位数值、finding 或推测结论。`Acceptance` 是研究设计与产物的验收语义，不设全模块统一的统计阈值、运行规则或 artifact schema；具体运行有效性和失败条件由该 Study 决定。

### Method 的 Study-local analytical graph

Method 至少说明以下三个层次；它们是每个 Study 内的语义组织方式，不是跨 Study 的通用组件接口：

| 层次 | Study authority 必须明确的内容 |
| --- | --- |
| Method Context / Method-level parameters | 多个 Observation / Analysis 共同依赖的研究上下文与参数，以及各参数影响哪些组件。仅在参数确实定义共同研究语义时放在此层。 |
| Observations（`1..N`） | 每个 Observation 的 stable local name / identity、所观察的市场现象、依赖的 Study / Method inputs、自身 parameters、observation semantics / derived variables、适用的 eligibility / exclusion / validity 规则，以及供后续消费的语义输出；只有需要独立物化、保留或复用时才定义 Observation Artifact identity。 |
| Analyses（`1..N`） | 每个 Analysis 的 stable local name / identity、要回答的 Question aspect / evidential purpose、显式消费的一个或多个具名 Observation、自身 parameters、grouping / comparison / statistical semantics，以及产生的 evidence 语义；只有需要独立物化、保留或复用时才定义 Analysis Artifact identity。 |

Observation 与 Analysis 均由当前 Study 在本地拥有。不同 Observation 可以消费同一 upstream market data，但各自拥有独立的语义和适用参数；共同输入不合并其 semantic ownership。一个 Analysis 不必消费所有 Observations，多个 Analyses 可以消费同一个 Observation；若其输出已独立物化，也可以复用语义 identity 匹配的 Observation Artifact。默认不以一个 Observation 定义另一个 Observation 的语义；实现中复用 dataframe、helper 或中间计算不建立 Observation → Observation semantic contract。Observation 的定义也不得依赖某个 Analysis 的目标或已得结果。

Method 的语义依赖方向为：

```text
Study Inputs / upstream canonical data
              ↓
        Method Context
              ↓
       Observations [1..N]
              ↓
        Analyses [1..N]
              ↓
           Results
```

该图不要求通用 DAG executor。允许 Observation → Analysis；禁止 Analysis → Observation 反向语义依赖、隐式 Observation → Observation contract 与 sibling Study → sibling Study semantic dependency。

Observation 或 Analysis 需要独立物化、保留或复用时，Study authority 才定义对应的 component Artifact identity；不要求每个组件都产生持久化 artifact。Observation Artifact identity 由 Observation identity、相关 Method / Observation parameters 及 source / input identity 决定；Analysis Artifact identity 由 Analysis identity、实际消费的 Observation 语义输入（已物化时包括其 Artifact identities）及相关 Method / Analysis parameters 决定。Identity 由语义输入决定，不依赖运行时间、随机 UUID 或偶然路径。新增或重跑 Analysis 在语义上不要求重做未变化的 Observation；这不要求实现提供分段执行。Study 可按参数构造易读文件名，但 semantic artifact identity 与 filesystem filename / representation 必须区分；具体 hash、serialization 或文件名只在构成该 Study 稳定 contract 时锁定。不建立全局 Artifact Registry、cache framework 或 shared execution protocol。

当前 Study canonical authority 描述该 Study 唯一有效的 Method，不维护 `method_v1` / `method_v2` lineage 或 method version registry。历史 evidence 的兼容性通过 provenance、适用时的 artifact identity 与 execution reconciliation 判断；若两种方法需长期代表不同研究语义，先重新判断是否属于不同 Study / hypothesis。

Runnable Study 的 public ID 映射、调用入口、共享配置与 output placement 沿用 Research UI authority；本 schema 不规定统一 CLI 参数名、参数 schema、run-key 算法或 artifact 格式。Study authority 必须将自身已定义的每个 semantic input 连接到可实现的用户提供方式，不能将该决定留给 Implementation Agent。

所有六节必须具有足够的实质内容，不能用 `TBD`、空节、模糊的“采用合适方法”等文字掩盖会改变研究含义的缺失决定。非语义性的命名、排版与实现细节可以由 Agent 整理，不进入 human semantic-decision loop。

### Retained Study authority dependency

每个 retained Study 独立拥有自己的研究语义，不得将 sibling retained Study 作为可复用研究语义的 canonical owner 或必须依赖的 semantic contract。可以引用 sibling Study 的 research finding、历史 evidence、related work 或导航信息；这些引用不授予其共享语义的 ownership。相似设计也不能直接成为新 Study 的默认语义。

若两个或更多真实 Study 需要共享同一稳定研究语义，须先经过独立 semantic decision，再将其提升为 narrow shared Research authority。在 shared semantic 正式建立前，各 Study 暂时保留 Study-local semantics；不得建立隐式 Study → Study contract dependency。相似的 Observation 或 Analysis 做法本身不触发 shared Observation / Analysis framework 或 shared capability 抽取。

## 3. Authoring 状态模型

| 状态 | 进入条件 | Required action | 退出条件 | Forbidden action |
| --- | --- | --- | --- | --- |
| `Study Intention` | Human 给出研究意图，不要求符合完整 schema | 提取已给出的研究决定与明确待决项，区分事实引用和研究选择 | 进入 `Structured Study Intention` | 将沉默视为默认研究决定 |
| `Structured Study Intention` | 已提取 human 意图 | 形成上述显式 Record，标明已知 semantic source 和 resolution state | Record 足以区分已决定与未决定的语义，进入 `Template Filling` | 将未决项隐式补全，或将 Record 当作最终 authority |
| `Template Filling` | 已形成 Structured Study Intention Record，或收到待决项的 human 决定并更新该 Record | 将已确定语义放入六节；保留其 canonical 来源和未决项；草稿不冒充完整 authority | 六节形成可供语义审查的草稿 | 猜测缺失的输入、总体、方法、结果含义或边界 |
| `Semantic Review` | 六节草稿可逐项审查 | 核对语义来源、section 完整性、内部一致性、authority dependency 及模块边界；执行下述 mandatory Study Authority Completeness Gate | Gate 全部通过则进入 `Authority Complete`；有实质语义缺口则进入 `Semantic Decision Required` | 用措辞修补、实现选择或其他 Study 的惯例替代缺失决定 |
| `Semantic Decision Required` | 审查发现至少一个未解决的实质 Study/product 语义选择 | 按下述 decision record 向 human 呈现问题；收到明确决定后更新 Structured Study Intention Record | Human 决定已明确，返回 `Template Filling` 并再经 `Semantic Review` | 自行选定建议项，或将未决语义发布为完整 authority |
| `Authority Complete` | 六节满足 schema，所有实质语义决定均有明确来源，Study Authority Completeness Gate 已通过 | 将独立 Study authority 确认为 canonical，并维护导航链接 | 本 authoring workflow 终止 | 将 Gate 通过解释为 repository capability 已齐备，或跳过后续需要的 dependency reconciliation |

### Study Authority Completeness Gate

`Semantic Review` 必须逐项确认下列条件。Gate 只判断 Study-owned research / product / execution / retained-result semantics 是否完整到后续 Implementation Agent 无需重新发明业务语义；不判断 repository 是否已经具备实现该 Study 的全部 capability：

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | `Question`、`Inputs`、`Method`、`Results`、`Limitations`、`Acceptance` 均有实质内容；没有未解决的 research semantic decision。 |
| Input ownership | 每项外部 input / configurable value 的来源、允许范围、semantic owner（Study / Method 或具名 Observation / Analysis）及其消费位置明确；CLI/input 表达不替代 semantic ownership；共同参数确实定义多个组件共享的研究语义。 |
| Method graph completeness | `1..N` 个具名 Observation 与 `1..N` 个具名 Analysis 各有独立身份、目的、适用参数和语义输出；Observation 的 derived variables 与适用的 eligibility / exclusion / validity、Analysis 消费哪些 Observation 及其 grouping / comparison / statistical semantics 均已确定。只有需独立物化、保留或复用的组件才要求可由相关语义输入确定 Artifact identity；依赖方向符合 Observation → Analysis。 |
| Question-to-evidence traceability | 每个重要 Question aspect 至少有一条 Observation → Analysis → retained evidence chain；每个 retained Analysis 都说明 evidential purpose，不附带无研究目的的统计；Analysis 声称必需的 evidence 在 Results 中有可复核表达，Results 的核心 statistic / evidence 都有 Method 定义的语义。 |
| Runnable contract completeness（仅预期 runnable 的 Study） | `Inputs` 已确定 stable public Study ID、每个 Study-specific semantic input 的用户可见表达、CLI 映射、必填性和默认值，以及适用的 Study-owned execution option。若保留 evidence，`Inputs` 已确定或明确引用整次请求的 run identity 参与输入、等价输入 canonicalization、必须区分的变化与 deterministic run-key rule；调用与 output placement 能依 Research UI authority 落地。 |
| Result contract completeness | 是否独立保留 Observation / Analysis Artifacts、必须保留的 Analysis evidence、machine-readable result 的最低语义结构及 table/chart/report/visualization 等 human-readable product 的必需性已明确；边界状态、复核必需的 metadata、exclusion counts 与 provenance 均有确定表达；只有 filename/format 本身是稳定契约时才要求固定。 |
| Internal consistency | Question/hypothesis 与 Inputs 的研究空间一致；具体 default configuration 与核心 hypothesis 的关系明确；所有 configurable inputs 的允许范围均适用于 Question、Method、Results、Limitations 和 Acceptance；必填性、可选性与默认值无矛盾；Acceptance 对应前述研究；Study-local semantics 不重定义或冲突于允许引用的 canonical authority，也不依赖 sibling Study 拥有的可复用语义。 |

若 hypothesis 固定某个配置而 Inputs 允许更广范围，必须由 human 明确该配置是 default / primary hypothesis、hypothesis 适用于全部允许配置，还是输入范围需要收窄；Agent 不得自行选择解释。Gate 发现会改变 Study/product 语义的缺口时，进入 `Semantic Decision Required`；class/function 命名、代码拆分和测试布局等纯实现细节不阻止通过。

`Authority Complete` 不表示 Snapshot 已有全部所需 public capability、shared Research capability 已存在、当前 implementation 可以立即完成，或 dependency reconciliation 已完成。允许在 authority 完成后发现 capability / dependency gap，再与对应 canonical owner reconciliation，随后进入 implementation。

`Semantic Decision Required` 的每个未决项必须按以下结构表达；有实际区分价值时才列 alternatives，建议方案只供 human 决定，不构成默认授权：

| 字段 | 含义 |
| --- | --- |
| `unresolved field / topic` | 对应的 schema 字段或研究主题 |
| `missing semantic decision` | Human 仍需决定的具体问题 |
| `why the decision matters` | 不同选择如何改变研究对象、方法、证据或解释 |
| `recommended resolution` | 建议 human 如何明确该决定；若推荐具体选项，说明依据 |
| `alternatives` | 仅在有实质差异时列出可供选择的方案及其影响 |

未决项可以在 authoring 对话或工作草稿中记录，不应写成 Study canonical authority 的既定语义。输入必填性或默认值、输入的用户表达、retained run identity、empty result 表达、required artifact 等缺失的 Study/product semantic decision 同样使用上述记录格式。Human 的明确决定更新 Structured Study Intention Record 并进入对应 Study authority 后，再进行包含 Study Authority Completeness Gate 的完整 Semantic Review。

## 4. 现有 authority reconciliation

三个早于本 schema 的 retained Study authority（`im_basis_baseline`、`im_basis_forward_return_association`、`price_to_lagged_ma_distribution`）均已有六个顶层 section，但仍按研究步骤而非具名 Observation / Analysis 组织 Method，尚未逐项标注参数 owner 与组件消费关系；其中 `im_basis_baseline` 还在 Method 描述允许保留的输出。这些是历史 schema drift，不使现有 authority 失效，也不触发机械重写、重跑或改变现有研究结果。`price_to_lagged_ma_short_horizon_reversion` 是本轮按当前 schema 复核的真实 Study。

以后实质修改某个 Study authority 时，先从该 Study 已明确的研究语义整理出具名组件、参数 ownership、证据链及适用的组件 artifact identity，再按新 schema 完成 Semantic Review；真正缺失的研究决定走 human decision loop，不从现有实现或 sibling Study 猜测。只有为消除当前 authority 自相矛盾所必需时才即时修改具体 Study。本轮不要求现有 runner 具备组件分段执行或 artifact reuse；这些 implementation / migration gaps 留待对应 Study 的后续工作。
