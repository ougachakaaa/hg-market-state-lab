# Research Study Semantic Schema

本文件拥有新建 retained Study 的通用 semantic structure；创建入口见 [Authoring](AUTHORING.md)，完整性与决策流程见 [Review](REVIEW.md)，runnable Study 的共享调用与输出约定见 [Research UI authority](../ui/ARCHITECTURE.md)。本文定义语义完整性，不规定单文件布局，也不拥有具体 Study 语义。

## Study semantic schema

每个新建 retained Study 的 canonical authority graph 必须完整回答下表六个 semantic areas；每项有明确且唯一的 canonical owner，并可从该 Study 的 `ARCHITECTURE.md` 导航到。简单 Study 可以在一个文件中按下表顺序书写六节；复杂 Study 可以将详细语义下沉到 specialized authority，不强制六节同处一个文件。既有 Study 的适用规则见 [Compatibility](COMPATIBILITY.md)。一个 Study 围绕一个 bounded research question / small hypothesis，组织一个或多个具名 Observation 与一个或多个具名 Analysis，从所需的不同视角建立 evidence；它不是一个单独的 statistics job。新 Study 的 Study-specific 数值、公式、对象、方法、产物名称及取舍写在该 Study authority，不写进本模板；上游市场事实及非 Research-semantic 机制仍由各自的 canonical owner 定义。

| Semantic area | 必须回答的 product / research semantic 问题 |
| --- | --- |
| `Question` | 研究目标、hypothesis 与可辨识的研究问题是什么；研究希望产生哪类 evidence，其适用的配置范围是什么？ |
| `Inputs` | 哪些外部事实、数据选择与 configurable values 跨越 Study boundary 进入研究请求，其 canonical 来源、目标 population、样本选择与范围是什么？每项参数的 semantic owner 是 Study / Method、哪个具名 Observation 或哪个具名 Analysis？若 Study 预期 runnable，stable public Study ID、Study-specific semantic inputs、必填/可选项、默认值及每项的用户可见表达和 CLI 映射是什么？影响 retained execution 的 Study-owned option（如允许覆盖既有结果）如何提供？若保留 evidence，整次请求的 semantic input、等价输入 canonicalization、必须区分的变化与 Study-owned deterministic run-key rule 是什么？ |
| `Method` | Study-local analytical graph 的共同上下文、具名 Observations 与具名 Analyses 是什么；各自观察或分析什么、消费什么、产生什么，哪些选择改变其含义？新 Study 在自身边界内定义这些 Research semantics。 |
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

Runnable Study 的 public ID 映射、调用入口、共享配置与 output placement 沿用 Research UI authority；本 schema 不规定统一 CLI 参数名、参数 schema、run-key 算法或 artifact 格式。Study authority 必须将自身已定义的每个 semantic input 连接到可实现的用户提供方式，不能将该决定留给 Implementation Agent。

六个 semantic areas 必须具有足够的实质内容，不能用 `TBD`、空节、模糊的“采用合适方法”等文字掩盖会改变研究含义的缺失决定。非语义性的命名、排版与实现细节可以由 Agent 整理，不进入 human semantic-decision loop。

## Study authority topology

Study 是一个 semantic authority unit，不等于一个 physical Markdown file。`studies/<study_package>/ARCHITECTURE.md` 始终是稳定 canonical entry：概述 Study identity、bounded Question / hypothesis、scope、stable public ID（若适用）、主要 Inputs / population、named Observations 与 Analyses 及显式消费关系、主要 retained evidence、核心 Limitations / Acceptance、upstream dependencies / gaps、implementation location，并导航到详细语义。概述不复制 specialized contract。

六个 semantic areas 可自然分配。例如 entry 拥有 Question、scope、核心 Limitations 与导航；`INPUTS.md` 拥有 input / population / parameter ownership / run identity；`METHOD.md` 拥有 Method Context 与组件图；`RESULTS.md` 拥有 retained evidence、详细结果有效性与相关 Acceptance。其他 grouping 也允许，但每条语义规则只有一个 canonical owner，且所有 owner 从 entry 可达。简单 Study 保持单文件；不要按 heading 数量拆分或产生只有几行内容的小文件。

创建复杂 Study 时，在设计阶段判断 disclosure boundary。若有多个独立 Observation / Analysis、多组参数 owner、独立组件 Artifact 或复杂结果契约，应考虑从一开始建立 entry → specialized authority。Method 复杂到实现单个 Analysis 仍需加载无关 Analysis 细节时，可由 Method 入口列出组件及显式 Observation → Analysis 消费关系，再把相关 Observation / Analysis 下沉为 Study-local authority；不要求每个组件各建一个文件。实现单个 Analysis 时，只读该 Analysis、其明确消费的 Observation 和必需的上游 contract。拆分不创建跨 Study 组件接口、DAG executor、Artifact Registry 或 plugin framework。

## Study implementation topology

一个 retained Study 是独立的 semantic authority unit；同名 executable implementation directory 也应作为小型 bounded module 组织。Study 不等于一个容纳全部逻辑的 `study.py`：简单 Study 可以使用单个 implementation module，复杂 Study 可以使用多个 Study-local modules/packages。拆分依据是 semantic responsibility 与阅读边界，而非文件数量或行数。

Study-local implementation SHOULD 足够贴近上述 Method graph，使 material Method Context、Observation construction、Analysis execution、Results / presentation 与 orchestration 的职责都能独立理解和定位。典型分解可以是 `study.py` 负责 orchestration / composition，`observations.py` 构造 Observations，`analyses.py` 执行 Analyses，`results.py` 组装、保留和呈现 evidence，`statistics.py` 保存 Study-local mathematical mechanics。这只是 decomposition pattern，不是固定目录模板；semantic boundaries 是候选拆分点，不要求每个 Observation 或 Analysis 对应一个文件，也不要求每个 Study 都有上述所有文件。Authority file 与 Python file 无须一一对应，要求的是 authority component 能追踪到易定位的 implementation responsibility。

复杂 Study 的 `study.py` 宜作为可读的 orchestration / composition entry：从 Study-level request validation，经 Observation construction、Analysis execution、canonical result assembly 到 Results retention，打开该入口应能快速理解 pipeline，而不必先阅读统计、绘图或持久化细节。若有多个具名 Observations / Analyses、独立的组件职责、大量 retained result / presentation、独立 artifact identity 或 mathematical mechanics，或 CLI、分析、绘图、持久化混于一处，应显式评估 Study-local decomposition。修改一个 material component 必须阅读大量无关实现，或单文件已无法呈现语义图，也是拆分信号；不设 LOC 阈值。

Implementation progressive disclosure 沿 `Study ARCHITECTURE.md → relevant METHOD authority → relevant Study-local module → related tests`。修改一个具名 Analysis 时，应尽可能无需理解无关 Analyses、plotting、report、retention、artifact hashing 或无关 Observation mechanics。优先在当前 Study package 内拆分；相似 helper 不构成提升至 `market_research/shared/*`、修改 sibling Studies 或创建 generic Observation / Analysis / statistics / pipeline framework 的理由。跨 Study consolidation 仍须按既有 human-triggered policy 单独进行。
