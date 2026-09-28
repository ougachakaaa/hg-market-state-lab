# Research Study Authority Authoring

本文件是 retained Research Study authority 的固定 schema 与 authoring workflow 的唯一 canonical owner。Research 模块边界、现有 Study 入口与 authority / implementation 分离见 [market-research architecture](../ARCHITECTURE.md)。本文只规定如何把 Study Intention 写成独立的 Study authority，不定义任何具体研究的语义、运行或实现。

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
| `Question` | 研究目标与可辨识的研究问题是什么；研究希望产生哪类 evidence？ |
| `Inputs` | 输入及其 canonical 来源是什么；目标 population、样本选择与范围如何定义？ |
| `Method` | 如何从输入形成研究对象、比较或统计；哪些选择会改变结果含义？ |
| `Results` | 预期保留什么研究产物，如何解释其内容；已有 evidence 与尚未执行的状态分别是什么？ |
| `Limitations` | 研究边界、解释限制及不得从结果推出的结论是什么？ |
| `Acceptance` | 什么条件表明研究设计和预期产物已完整、可复核；该 Study 的结果有效性条件在哪里明确？ |

`Results` 不要求 authoring 时已经运行真实研究。尚无 evidence 时如实记录该状态，不填占位数值、finding 或推测结论。`Acceptance` 是研究设计与产物的验收语义，不设全模块统一的统计阈值、运行规则或 artifact schema；具体运行有效性和失败条件由该 Study 决定。

所有六节必须具有足够的实质内容，不能用 `TBD`、空节、模糊的“采用合适方法”等文字掩盖会改变研究含义的缺失决定。非语义性的命名、排版与实现细节可以由 Agent 整理，不进入 human semantic-decision loop。

## 3. Authoring 状态模型

| 状态 | 进入条件 | Required action | 退出条件 | Forbidden action |
| --- | --- | --- | --- | --- |
| `Study Intention` | Human 给出研究意图，不要求符合完整 schema | 按输入结构提取已给出的研究决定与明确待决项，区分事实引用和研究选择 | 已整理出可用于填写模板的输入 | 将沉默视为默认研究决定 |
| `Template Filling` | 已有结构化 Study Intention，或收到待决项的 human 决定 | 将已确定语义放入六节；保留其 canonical 来源和未决项；草稿不冒充完整 authority | 六节形成可供语义审查的草稿 | 猜测缺失的输入、总体、方法、结果含义或边界 |
| `Semantic Review` | 六节草稿可逐项审查 | 核对语义来源、section 完整性、内部一致性及模块边界；仅把会改变研究含义的缺口列为 semantic decision | 无实质缺口则进入 `Authority Complete`；有缺口则进入 `Semantic Decision Required` | 用措辞修补、实现选择或其他 Study 的惯例替代缺失决定 |
| `Semantic Decision Required` | 审查发现至少一个未解决的实质研究选择 | 按下述 decision record 向 human 呈现问题；收到明确决定后更新 Study Intention | Human 决定已明确，返回 `Template Filling` 并再经 `Semantic Review` | 自行选定建议项，或将未决语义发布为完整 authority |
| `Authority Complete` | 六节满足 schema，所有实质语义决定均有明确来源，审查无未决项 | 将独立 Study authority 确认为 canonical，并维护导航链接 | 本 authoring workflow 终止 | 自动进入 implementation、dependency resolution、shared capability discovery 或 Study execution |

`Semantic Decision Required` 的每个未决项必须按以下结构表达；有实际区分价值时才列 alternatives，建议方案只供 human 决定，不构成默认授权：

| 字段 | 含义 |
| --- | --- |
| `unresolved field / topic` | 对应的 schema 字段或研究主题 |
| `missing semantic decision` | Human 仍需决定的具体问题 |
| `why the decision matters` | 不同选择如何改变研究对象、方法、证据或解释 |
| `recommended resolution` | 建议 human 如何明确该决定；若推荐具体选项，说明依据 |
| `alternatives` | 仅在有实质差异时列出可供选择的方案及其影响 |

未决项可以在 authoring 对话或工作草稿中记录，不应写成 Study canonical authority 的既定语义。Human 的明确决定进入对应 Study authority 后，再进行完整的 Semantic Review。

## 4. 现有 authority reconciliation

当前 retained Study authority 已使用 `Question`、`Inputs`、`Method`、`Results`、`Limitations`，基本研究语义与本 schema 对应；设计和结果有效性的条件散见于各自的 Method、Results 或边界说明，尚无独立 `Acceptance` section。这是历史结构差异，不改变其现有 canonical ownership，也不触发本轮大规模改写。以后实质更新某个 Study authority 时，再将其自身已确定的验收语义整理到 `Acceptance`；真正缺失的研究决定仍须走上述 human decision loop。
