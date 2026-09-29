# Research Study Authority Authoring

本文件是新建 retained Study 的稳定入口，拥有 Study Intention 到 Canonical Study Authority 的 authoring workflow。Research 模块边界与现有 Study 入口见 [market-research architecture](../ARCHITECTURE.md)；runnable Study 的共享调用与输出约定见 [Research UI authority](../ui/ARCHITECTURE.md)。Study 的必需语义见 [Schema](SCHEMA.md)，完整性判定见 [Review](REVIEW.md)；Agent 不得自行发明未给出的研究语义。

## Study identity 与完成范围

新 Study 的 canonical authority 必须回答 [Schema](SCHEMA.md) 中 Question、Inputs、Method、Results、Limitations、Acceptance 六个 semantic areas。Study 可以由单个或多个 Markdown 文件构成；`studies/<study_package>/ARCHITECTURE.md` 始终是稳定入口。独立的 implementation 位置是同名 `src/market_research/studies/<study_package>/`；完成 authority 不自动启动 implementation 或 Study execution。

## 创建隔离与导航

新建 Study 必须 Research-semantic self-contained：研究问题、population、predictor、target、regime、grouping、Observation、Analysis、统计解释和 evidence contract 中定义研究证据含义的语义，均由当前 Study 本地拥有，即使与既有定义相同也须在当前 Study 明确写出。创建时不得主动搜索 sibling Studies、其 retained artifacts、既有 `market-research/shared/*` 或 implementation 来继承 Research semantics / helper。Sibling Study 可作为 related work、历史 evidence 或导航被引用，但不成为 semantic owner 或 dependency。研究语义、公式、分组逻辑及 Study-local analytical code 允许有意重复；相似性不触发 shared 抽取、跨 Study 依赖或对 sibling 的修改。偶然发现的重复只可作为非 canonical 的未来建议，不阻止当前 Study 完成。不得因共用机制而共享研究语义。

可以使用 repository runtime、Research UI、配置、filesystem/output/serialization mechanics、外部 libraries，以及 Snapshot public application/product boundary 提供的 canonical deterministic facts。上游事实由其 canonical owner 定义；如何选择、变换和解释事实以形成 evidence 仍由当前 Study 拥有。不得重定义上游事实，或以缺失的 Snapshot capability 为由越过其 public boundary。默认写入范围是当前 Study authority 与必要的最小导航条目；缺失的上游 contract / gap 在当前 Study 中记录，随后由对应 owner reconciliation。不得顺手修改 sibling Study、既有 shared Research semantics、无关 implementation 或 generic Research framework。

| 当前任务 | 下一份 authority |
| --- | --- |
| 确定 Study 必需语义及组件关系 | [Schema](SCHEMA.md) |
| 审查已形成的 Study authority | [Review](REVIEW.md) |
| 对既有 Study 做 reconciliation、migration 或 consolidation | [Compatibility](COMPATIBILITY.md) |

创建路径为 repository / module entry → 本文件 → Schema → 新 Study `ARCHITECTURE.md` → 仅所需 specialized authority → 必需的上游 authority。Review 在 authoring / reconciliation 需要验证时进入；Compatibility、历史 Study 与 shared Research semantics 不在默认创建路径中。

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

非语义性的命名、排版与实现细节可由 Agent 整理，不进入 human semantic-decision loop。

## Authoring 状态模型

| 状态 | 进入条件 | Required action | 退出条件 | Forbidden action |
| --- | --- | --- | --- | --- |
| `Study Intention` | Human 给出研究意图，不要求符合完整 schema | 提取已给出的研究决定与明确待决项，区分事实引用和研究选择 | 进入 `Structured Study Intention` | 将沉默视为默认研究决定 |
| `Structured Study Intention` | 已提取 human 意图 | 形成上述显式 Record，标明已知 semantic source 和 resolution state | Record 足以区分已决定与未决定的语义，进入 `Template Filling` | 将未决项隐式补全，或将 Record 当作最终 authority |
| `Template Filling` | 已形成 Structured Study Intention Record，或收到待决项的 human 决定并更新该 Record | 将已确定语义放入六个 semantic areas；保留其 canonical 来源和未决项；草稿不冒充完整 authority | 六个 semantic areas 形成可供语义审查的草稿 | 猜测缺失的输入、总体、方法、结果含义或边界 |
| `Semantic Review` | 六个 semantic areas 的草稿可逐项审查 | 依 [Review](REVIEW.md) 执行 Study Authority Completeness Gate | Gate 全部通过则进入 `Authority Complete`；有实质语义缺口则进入 `Semantic Decision Required` | 用措辞修补、实现选择或其他 Study 的惯例替代缺失决定；因重复而提前抽取 shared Research semantics |
| `Semantic Decision Required` | Review 返回至少一个未解决的实质 Study/product 语义 finding | 按下述 decision record 向 human 呈现问题；收到明确决定后更新 Structured Study Intention Record | Human 决定已明确，返回 `Template Filling` 并再经 `Semantic Review` | 自行选定建议项，或将未决语义发布为完整 authority |
| `Authority Complete` | [Review](REVIEW.md) 判定 Study Authority Complete | 将独立 Study authority 确认为 canonical，并维护导航链接 | 本 authoring workflow 终止 | 将 Gate 通过解释为 repository capability 已齐备，或跳过后续需要的 dependency reconciliation |

## Human semantic-decision loop

`Semantic Decision Required` 的每个未决项必须按以下结构表达；有实际区分价值时才列 alternatives，建议方案只供 human 决定，不构成默认授权：

| 字段 | 含义 |
| --- | --- |
| `unresolved field / topic` | 对应的 schema 字段或研究主题 |
| `missing semantic decision` | Human 仍需决定的具体问题 |
| `why the decision matters` | 不同选择如何改变研究对象、方法、证据或解释 |
| `recommended resolution` | 建议 human 如何明确该决定；若推荐具体选项，说明依据 |
| `alternatives` | 仅在有实质差异时列出可供选择的方案及其影响 |

未决项可以在 authoring 对话或工作草稿中记录，不应写成 Study canonical authority 的既定语义。输入必填性或默认值、输入的用户表达、retained run identity、empty result 表达、required artifact 等缺失的 Study/product semantic decision 同样使用上述记录格式。Human 的明确决定更新 Structured Study Intention Record 并进入对应 Study authority 后，再进行包含 Study Authority Completeness Gate 的完整 Semantic Review。

例如 hypothesis 固定某个配置而 Inputs 允许更广范围时，应由 human 明确该配置是 default / primary hypothesis、hypothesis 适用于全部允许配置，还是输入范围需要收窄；Agent 不得自行选择解释。

## Authority publication 与后续交接

[Review](REVIEW.md) 判定 Study Authority Complete 后，将当前 Study authority 及其导航确认为 canonical。该判定可以先于上游 capability readiness；缺失 Snapshot Product 不迫使完整的 Study-owned semantics 保持 incomplete。将所需上游 contract 与 gap 记录清楚后，由对应 canonical owner 核对 required upstream capability 与 ownership boundary。**Dependency Reconciled** 表示这些能力已存在且边界无冲突；**Implementation Ready** 仅在 Study Authority Complete 与 Dependency Reconciled 均成立时成立。工作顺序为 `CREATE → RECONCILE → IMPLEMENT`；这里的 dependency reconciliation 不等于 [Compatibility](COMPATIBILITY.md) 拥有的 existing Study reconciliation，后者也拥有 `CONSOLIDATE` 的显式触发与历史兼容规则。这些名称只表达 authoring / dependency contract distinction，不是 persisted status、registry 或 lifecycle engine。不得以假设的 shared Research capability 填补上游缺口。

## Study authority topology

Study 是一个 semantic authority unit，不等于一个 physical Markdown file。`studies/<study_package>/ARCHITECTURE.md` 作为稳定 canonical entry：概述 Study identity、bounded Question / hypothesis、scope、stable public ID（若适用）、主要 Inputs / population、named Observations 与 Analyses 及显式消费关系、主要 retained evidence、核心 Limitations / Acceptance、upstream dependencies / gaps、implementation location，并导航到详细语义。概述不复制 specialized contract。

六个 semantic areas 可自然分配。例如 entry 拥有 Question、scope、核心 Limitations 与导航；`INPUTS.md` 拥有 input / population / parameter ownership / run identity；`METHOD.md` 拥有 Method Context 与组件图；`RESULTS.md` 拥有 retained evidence、详细结果有效性与相关 Acceptance。其他 grouping 也允许，但每条语义规则只有一个 canonical owner，且所有 owner 从 entry 可达。简单 Study 保持单文件；不要按 heading 数量拆分或产生只有几行内容的小文件。

创建复杂 Study 时，在设计阶段判断 disclosure boundary。若有多个独立 Observation / Analysis、多组参数 owner、独立组件 Artifact 或复杂结果契约，应考虑从一开始建立 entry → specialized authority。Method 复杂到实现单个 Analysis 仍需加载无关 Analysis 细节时，可由 Method 入口列出组件及显式 Observation → Analysis 消费关系，再把相关 Observation / Analysis 下沉为 Study-local authority；不要求每个组件各建一个文件。实现单个 Analysis 时，只读该 Analysis、其明确消费的 Observation 和必需的上游 contract。拆分不创建跨 Study 组件接口、DAG executor、Artifact Registry 或 plugin framework。
