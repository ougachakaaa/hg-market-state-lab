# Research Study Authority Authoring

本文件是 retained Research Study authority 的固定 schema 与 authoring workflow 的唯一 canonical owner。Research 模块边界、现有 Study 入口与 authority / implementation 分离见 [market-research architecture](../ARCHITECTURE.md)；runnable Study 的共享调用与输出约定见 [Research UI authority](../ui/ARCHITECTURE.md)。本文只规定如何把 Study Intention 写成独立的 Study authority，不定义任何具体研究的语义、运行或实现。

## 1. 输入与输出

输入称为 `Study Intention`，由 human 提供，可以是自然语言；authoring Agent 将其中已有的内容整理为以下结构，允许任何尚未给出的项留空：

| 输入项 | 记录内容 |
| --- | --- |
| Research goal / question | 想研究什么，以及已说明的动机或问题边界 |
| Inputs & population | 已指定的数据、对象、样本范围与选择条件 |
| Method intention | 已指定的比较、变换、统计或评估思路 |
| Research product | 期望保留的结果、证据或呈现形式 |
| Boundaries | 已指定的不研究内容、解释限制或约束 |
| Open decisions | human 已提出或 Agent 识别出的待决研究选择 |

这不是要求 human 预先填写完整 authority 的表单。Agent 可以规范措辞、组织已给出的决定，并引用现有 canonical authority 中明确拥有的事实；不能从常见做法、既有 Study 或实现便利性推断未给出的研究决定。

输出终态是 `market-research/studies/<study_package>/ARCHITECTURE.md` 中符合下述 schema 的 **Canonical Study Authority**。每个 retained Study 独立拥有自己的研究语义与 retained evidence；同名 `src/market_research/studies/<study_package>/` 是独立的 implementation 位置。Authoring 完成不启动 implementation、Study execution 或后续能力设计。

## 2. 固定 Study authority schema

每个新建或实质更新的 retained Study authority 使用下表六个顶层 section，按表中顺序书写。可以增加 Study 自己的子节和执行说明；不能省略、改名或用其他文档代替必需 section。Study-specific 数值、公式、对象、方法、产物名称及取舍只写在该 Study authority 或其明确链接的 narrow canonical owner，不写进本模板。

| 必需 section | 必须回答的 product / research semantic 问题 |
| --- | --- |
| `Question` | 研究目标、hypothesis 与可辨识的研究问题是什么；研究希望产生哪类 evidence，其适用的配置范围是什么？ |
| `Inputs` | 输入及其 canonical 来源是什么；目标 population、样本选择与范围如何定义？若 Study 预期 runnable，stable public Study ID、Study-specific semantic inputs、必填/可选项、默认值及每项的用户可见表达和 CLI 映射是什么？影响 retained execution 的 Study-owned option（如允许覆盖既有结果）如何提供？ |
| `Method` | 如何从输入形成研究对象、比较或统计；哪些选择会改变结果含义？若 runnable Study 保留 evidence，哪些 semantic inputs 参与 run identity、等价输入如何 canonicalize、哪些变化必须产生不同 identity，以及 Study-owned deterministic run-key rule 是什么？已有 canonical authority 明确拥有这些语义时可以直接引用。 |
| `Results` | 必须保留哪些 evidence，如何解释其内容；machine-readable result 的最低 semantic structure 是什么，table/chart/report 或 visualization 等 human-readable product 是否必需？empty bucket、missing statistic、excluded observation 等边界状态如何表达？哪些 metadata、exclusion counts 与 provenance 是复核所必需的？artifact filename/format 只有构成稳定 Study contract 时才须锁定；已有 evidence 与尚未执行的状态分别是什么？ |
| `Limitations` | 研究边界、解释限制及不得从结果推出的结论是什么？ |
| `Acceptance` | 什么条件表明研究设计和预期产物已完整、可复核；该 Study 的结果有效性条件在哪里明确？ |

`Results` 不要求 authoring 时已经运行真实研究。尚无 evidence 时如实记录该状态，不填占位数值、finding 或推测结论。`Acceptance` 是研究设计与产物的验收语义，不设全模块统一的统计阈值、运行规则或 artifact schema；具体运行有效性和失败条件由该 Study 决定。

Runnable Study 的 public ID 映射、调用入口、共享配置与 output placement 沿用 Research UI authority；本 schema 不规定统一 CLI 参数名、参数 schema、run-key 算法或 artifact 格式。Study authority 必须将自身已定义的每个 semantic input 连接到可实现的用户提供方式，不能将该决定留给 Implementation Agent。

所有六节必须具有足够的实质内容，不能用 `TBD`、空节、模糊的“采用合适方法”等文字掩盖会改变研究含义的缺失决定。非语义性的命名、排版与实现细节可以由 Agent 整理，不进入 human semantic-decision loop。

## 3. Authoring 状态模型

| 状态 | 进入条件 | Required action | 退出条件 | Forbidden action |
| --- | --- | --- | --- | --- |
| `Study Intention` | Human 给出研究意图，不要求符合完整 schema | 按输入结构提取已给出的研究决定与明确待决项，区分事实引用和研究选择 | 已整理出可用于填写模板的输入 | 将沉默视为默认研究决定 |
| `Template Filling` | 已有结构化 Study Intention，或收到待决项的 human 决定 | 将已确定语义放入六节；保留其 canonical 来源和未决项；草稿不冒充完整 authority | 六节形成可供语义审查的草稿 | 猜测缺失的输入、总体、方法、结果含义或边界 |
| `Semantic Review` | 六节草稿可逐项审查 | 核对语义来源、section 完整性、内部一致性及模块边界；执行下述 mandatory Implementation Readiness Gate | Gate 全部通过则进入 `Authority Complete`；有实质语义缺口则进入 `Semantic Decision Required` | 用措辞修补、实现选择或其他 Study 的惯例替代缺失决定 |
| `Semantic Decision Required` | 审查发现至少一个未解决的实质 Study/product 语义选择 | 按下述 decision record 向 human 呈现问题；收到明确决定后更新 Study Intention | Human 决定已明确，返回 `Template Filling` 并再经 `Semantic Review` | 自行选定建议项，或将未决语义发布为完整 authority |
| `Authority Complete` | 六节满足 schema，所有实质语义决定均有明确来源，Implementation Readiness Gate 已通过 | 将独立 Study authority 确认为 canonical，并维护导航链接 | 本 authoring workflow 终止 | 自动进入 implementation、dependency resolution、shared capability discovery 或 Study execution |

### Implementation Readiness Gate

`Semantic Review` 必须逐项确认下列条件。只有后续 Implementation Agent 可以仅依赖 repository authority 实现该 Study、无需自行决定 Study-owned 的产品、运行或 retained-result 语义时，Gate 才通过：

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | `Question`、`Inputs`、`Method`、`Results`、`Limitations`、`Acceptance` 均有实质内容；没有未解决的 research semantic decision。 |
| Runnable contract completeness（仅预期 runnable 的 Study） | Stable public Study ID 已确定；每个 Study-specific semantic input 的用户可见表达、CLI 映射、必填性和默认值足以实现；适用的 Study-owned execution option 已明确。若保留 evidence，run identity 的参与输入、等价输入 canonicalization、必须区分的变化与 deterministic run-key rule 已确定或明确引用其 canonical owner；调用与 output placement 能依 Research UI authority 落地。 |
| Result contract completeness | 必须保留的 evidence、machine-readable result 的最低语义结构及 table/chart/report/visualization 等 human-readable product 的必需性已明确；边界状态、复核必需的 metadata、exclusion counts 与 provenance 均有确定表达；只有 filename/format 本身是稳定契约时才要求固定。 |
| Internal consistency | Question/hypothesis 与 Inputs 的研究空间一致；具体 default configuration 与核心 hypothesis 的关系明确；所有 configurable inputs 的允许范围均适用于 Question、Method、Results、Limitations 和 Acceptance；必填性、可选性与默认值无矛盾；Acceptance 对应前述研究；Study-local semantics 复用而不重定义或冲突于引用的 canonical authority。 |

若 hypothesis 固定某个配置而 Inputs 允许更广范围，必须由 human 明确该配置是 default / primary hypothesis、hypothesis 适用于全部允许配置，还是输入范围需要收窄；Agent 不得自行选择解释。Gate 发现会改变 Study/product 语义的缺口时，进入 `Semantic Decision Required`；class/function 命名、代码拆分和测试布局等纯实现细节不阻止通过。

`Semantic Decision Required` 的每个未决项必须按以下结构表达；有实际区分价值时才列 alternatives，建议方案只供 human 决定，不构成默认授权：

| 字段 | 含义 |
| --- | --- |
| `unresolved field / topic` | 对应的 schema 字段或研究主题 |
| `missing semantic decision` | Human 仍需决定的具体问题 |
| `why the decision matters` | 不同选择如何改变研究对象、方法、证据或解释 |
| `recommended resolution` | 建议 human 如何明确该决定；若推荐具体选项，说明依据 |
| `alternatives` | 仅在有实质差异时列出可供选择的方案及其影响 |

未决项可以在 authoring 对话或工作草稿中记录，不应写成 Study canonical authority 的既定语义。输入必填性或默认值、输入的用户表达、retained run identity、empty result 表达、required artifact 等缺失的 Study/product semantic decision 同样使用上述记录格式。Human 的明确决定进入对应 Study authority 后，再进行包含 Implementation Readiness Gate 的完整 Semantic Review。

## 4. 现有 authority reconciliation

当前 retained Study authority 已使用 `Question`、`Inputs`、`Method`、`Results`、`Limitations`，基本研究语义与本 schema 对应；设计和结果有效性的条件散见于各自的 Method、Results 或边界说明，尚无独立 `Acceptance` section。这是历史结构差异，不改变其现有 canonical ownership，也不触发本轮大规模改写。以后实质更新某个 Study authority 时，再将其自身已确定的验收语义整理到 `Acceptance`；真正缺失的研究决定仍须走上述 human decision loop。
