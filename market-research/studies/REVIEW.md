# Research Study Authority Review

本文件拥有 Study Intention 结构化、authoring state machine、semantic decision 与 completeness review。六个 semantic areas 的定义见 [Schema](SCHEMA.md)；新建入口见 [Authoring](AUTHORING.md)。

## Structured Study Intention Record

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

## Authoring 状态模型

| 状态 | 进入条件 | Required action | 退出条件 | Forbidden action |
| --- | --- | --- | --- | --- |
| `Study Intention` | Human 给出研究意图，不要求符合完整 schema | 提取已给出的研究决定与明确待决项，区分事实引用和研究选择 | 进入 `Structured Study Intention` | 将沉默视为默认研究决定 |
| `Structured Study Intention` | 已提取 human 意图 | 形成上述显式 Record，标明已知 semantic source 和 resolution state | Record 足以区分已决定与未决定的语义，进入 `Template Filling` | 将未决项隐式补全，或将 Record 当作最终 authority |
| `Template Filling` | 已形成 Structured Study Intention Record，或收到待决项的 human 决定并更新该 Record | 将已确定语义放入六个 semantic areas；保留其 canonical 来源和未决项；草稿不冒充完整 authority | 六个 semantic areas 形成可供语义审查的草稿 | 猜测缺失的输入、总体、方法、结果含义或边界 |
| `Semantic Review` | 六个 semantic areas 的草稿可逐项审查 | 核对语义来源、semantic area 完整性、内部一致性、authority dependency 及模块边界；执行下述 mandatory Study Authority Completeness Gate | Gate 全部通过则进入 `Authority Complete`；有实质语义缺口则进入 `Semantic Decision Required` | 用措辞修补、实现选择或其他 Study 的惯例替代缺失决定；因重复而提前抽取 shared Research semantics |
| `Semantic Decision Required` | 审查发现至少一个未解决的实质 Study/product 语义选择 | 按下述 decision record 向 human 呈现问题；收到明确决定后更新 Structured Study Intention Record | Human 决定已明确，返回 `Template Filling` 并再经 `Semantic Review` | 自行选定建议项，或将未决语义发布为完整 authority |
| `Authority Complete` | 六个 semantic areas 满足 schema，所有实质语义决定均有明确来源，Study Authority Completeness Gate 已通过 | 将独立 Study authority 确认为 canonical，并维护导航链接 | 本 authoring workflow 终止 | 将 Gate 通过解释为 repository capability 已齐备，或跳过后续需要的 dependency reconciliation |

### Study Authority Completeness Gate

`Semantic Review` 必须逐项确认下列条件。Gate 只判断 Study-owned research / product / execution / retained-result semantics 是否完整到后续 Implementation Agent 无需重新发明业务语义；不判断 repository 是否已经具备实现该 Study 的全部 capability。新增的 creation isolation 检查适用于新 Study；对旧 Study 仅按 [Compatibility](COMPATIBILITY.md) 中显式 reconciliation 的相关范围适用，不得据此追溯宣布历史 Study invalid：

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | `Question`、`Inputs`、`Method`、`Results`、`Limitations`、`Acceptance` 在 canonical authority graph 中均有实质内容和唯一 owner；没有未解决的 research semantic decision。 |
| Input ownership | 每项外部 input 的来源及 canonical owner 明确；每个 material configurable Study parameter 的名称、允许值或范围、semantic owner（Study / Method Context / 具名 Observation / Analysis）、consumers、semantic role 及适用的必填性和默认值明确。Execution-only option 单独标识并说明消费位置，不混入 semantic identity；CLI/input 表达不替代 semantic ownership，组件参数不因重复使用而提升 owner。 |
| Method graph completeness | `1..N` 个具名 Observation 与 `1..N` 个具名 Analysis 各有独立身份、目的、适用参数和语义输出；Observation 逐项列出所消费的 Study inputs、适用 Method Context 值及上游 canonical facts，Analysis 以合法的 stable local name 列出实际消费的 `1..N` 个 Observation。Derived variables、适用的 eligibility / exclusion / validity 及 grouping / comparison / statistical semantics 均已确定；只有需独立物化、保留或复用的组件才要求明列其相关 semantic Artifact identity inputs，依赖方向符合 Schema。 |
| Question-to-evidence traceability | 每个重要 Question aspect 至少有一条可由 local references 追踪的 Observation → Analysis → retained Evidence Product chain；每个 material Analysis 都说明 evidential purpose，并由自己的 `produces` 定义 evidence semantics，不附带无研究目的的统计。每个 retained Evidence Product 有稳定 Study-local name，单向引用定义其证据含义的一个或多个 Analysis；从 Results 的这组映射能找到每个 material Analysis 的 retained evidence，无须 Analysis 重复维护 Evidence Product name。 |
| Retained run identity（保留 evidence 时） | `Inputs` 已确定或明确引用整次请求的全部 identity-changing semantic inputs、等价输入 canonicalization、必须区分的变化、被排除的 execution-only options 与 deterministic run-key rule；相同规范化语义请求确定相同 identity。 |
| Runnable contract completeness（仅预期 runnable 的 Study） | `Inputs` 已确定 stable public Study ID、每个 Study-specific semantic input 的用户可见表达、CLI 映射、必填性和默认值，以及适用的 Study-owned execution option；调用与 output placement 能依 Research UI authority 落地。 |
| Result contract completeness | 是否独立保留 Observation / Analysis Artifacts、必须保留的 Analysis evidence、machine-readable result 的最低语义结构及 table/chart/report/visualization 等 human-readable product 的必需性已明确；条件式 Observation / Analysis Artifact identity 均覆盖 Schema 指定的实际语义依赖：Analysis 消费已物化 Observation 时使用其 Artifact identity，消费未物化 Observation 时覆盖其全部 identity-determining semantic inputs，而非只有 local name；identity 与 filename、path 和 representation 分离。边界状态、复核必需的 metadata、exclusion counts 与 provenance 均有确定表达；只有 filename/format 本身是稳定契约时才要求固定。 |
| Study semantic isolation（新 Study） | 所有 Research-specific semantics 由当前 Study 本地拥有；未把 sibling Study、其 retained artifact 或既有 shared Research analytical semantics 用作定义或语义输入。 |
| No premature abstraction（新 Study） | 未因研究逻辑重复而创建 shared Research semantic、修改 shared authority / sibling Study，或抽象 generic Research framework。 |
| Dependency distinction | 所需上游 canonical fact / capability 及其 owner 与 Study-owned evidence semantics 分开表达；缺失 Snapshot public Product 等 capability 已记录为 dependency gap，不被误判为 Study semantic incompleteness。 |
| Internal consistency | Question/hypothesis 与 Inputs 的研究空间一致；具体 default configuration 与核心 hypothesis 的关系明确；所有 configurable inputs 的允许范围均适用于 Question、Method、Results、Limitations 和 Acceptance；必填性、可选性与默认值无矛盾；Acceptance 对应前述研究；Study-local semantics 不重定义或冲突于所依赖的上游 canonical facts。 |

若 hypothesis 固定某个配置而 Inputs 允许更广范围，必须由 human 明确该配置是 default / primary hypothesis、hypothesis 适用于全部允许配置，还是输入范围需要收窄；Agent 不得自行选择解释。Gate 发现会改变 Study/product 语义的缺口时，进入 `Semantic Decision Required`；class/function 命名、代码拆分和测试布局等纯实现细节不阻止通过。

**Study Authority Complete** 表示六个 semantic areas 和 Gate 已确定 Study-owned Research semantics，包括 question、population、inputs、Observation / Analysis、evidence contract、limitations 与 acceptance；Implementation Agent 无需重新决定这些研究语义。**Dependency Reconciled** 表示所需上游 canonical capabilities（如 Snapshot public Product、public application boundary 或其他外部确定性事实 owner）已经存在，且 ownership boundary 无冲突。**Implementation Ready** 仅在 Study Authority Complete 与 Dependency Reconciled 均成立时成立；Implementation Agent 不必发明 Study 或上游 Product 语义即可实现。三者是 authoring / dependency contract distinction，不是新的 persisted status、registry 或 lifecycle engine。

工作顺序是 `CREATE → RECONCILE → IMPLEMENT`；`CONSOLIDATE` 的显式触发与历史兼容规则见 [Compatibility](COMPATIBILITY.md)。Study Authority Complete 可以先于上游 capability readiness；缺失 Snapshot Product 不迫使完整的 Study-owned semantics 保持 incomplete。将所需上游 contract 和 gap 记录清楚后，再由对应 canonical owner 处理 dependency reconciliation，不以假设的 shared Research capability 填补缺口。

`Semantic Decision Required` 的每个未决项必须按以下结构表达；有实际区分价值时才列 alternatives，建议方案只供 human 决定，不构成默认授权：

| 字段 | 含义 |
| --- | --- |
| `unresolved field / topic` | 对应的 schema 字段或研究主题 |
| `missing semantic decision` | Human 仍需决定的具体问题 |
| `why the decision matters` | 不同选择如何改变研究对象、方法、证据或解释 |
| `recommended resolution` | 建议 human 如何明确该决定；若推荐具体选项，说明依据 |
| `alternatives` | 仅在有实质差异时列出可供选择的方案及其影响 |

未决项可以在 authoring 对话或工作草稿中记录，不应写成 Study canonical authority 的既定语义。输入必填性或默认值、输入的用户表达、retained run identity、empty result 表达、required artifact 等缺失的 Study/product semantic decision 同样使用上述记录格式。Human 的明确决定更新 Structured Study Intention Record 并进入对应 Study authority 后，再进行包含 Study Authority Completeness Gate 的完整 Semantic Review。
