# Research Study Authority Review

本文件拥有 Study Authority Completeness Gate、semantic consistency / traceability checks、implementation topology review、validation findings 与 `Study Authority Complete` 的判定。必需语义由 [Schema](SCHEMA.md) 定义，Python implementation topology 由 [Implementation Package Contract](IMPLEMENTATION.md) 定义；[Authoring](AUTHORING.md) 处理 Study Intention、authoring 状态及 human semantic-decision loop。

## Study Authority Completeness Gate

`Semantic Review` 必须逐项确认下列条件。Gate 检查当前 Study authority 是否满足 Schema，以及跨对象关系是否一致；新 Study 的呈现拓扑由 [Skeleton](SKELETON.md) 定义。它不重新定义 Schema contract，也不判断 repository 是否已经具备实现该 Study 的全部 capability。对旧 Study 仅按 [Compatibility](COMPATIBILITY.md) 中显式 reconciliation 的相关范围适用，不得据此追溯宣布历史 Study invalid：

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | 核对 [Schema](SCHEMA.md) 的六个 semantic areas 在 canonical authority graph 中均有实质内容和唯一 owner，且无未解决的 research semantic decision。 |
| New Study authority topology（仅新建 Study） | 核对 [Skeleton](SKELETON.md) 规定的四个顶层文件均存在且各有实质内容；`ARCHITECTURE.md` 直接链接其他三个顶层 owner，详细语义位于相应文件而非重复堆在 entry。单文件 authority 或空占位文件不能通过。 |
| Authority navigation | 核对稳定 `ARCHITECTURE.md` entry 存在，六个 semantic areas 可从 entry 定位，所有更深层 specialized canonical owner 均可沿链接到达，且没有 orphan semantic owner；不检查标题拼写或确切措辞。 |
| Input ownership | 逐项核对外部 input、parameter ownership / consumers / semantic role、execution-only options 与 run identity 符合 Schema 的 Inputs 和 parameter contracts；检查实际消费与声明一致。 |
| Method graph completeness | 逐项核对具名 Observation / Analysis、Method Context、消费关系、语义输出及按条件定义的 component Artifact identity 符合 Schema 的 Method contracts；检查引用的组件与上游事实均存在，且依赖方向合法。 |
| Question-to-evidence traceability | 验证每个重要 Question aspect 均可沿实际 local references 追踪至 Observation → Analysis → retained Evidence Product，每个 material Analysis 均可追踪至 retained evidence；检查引用的对象存在、指向一致，无游离统计。 |
| Retained run identity（保留 evidence 时） | 核对 Inputs 的整次请求 identity 满足 Schema 的 run identity contract；验证等价表达与 identity-changing 输入的区分一致，execution-only options 未参与。 |
| Runnable contract completeness（仅预期 runnable 的 Study） | 核对 Schema 所需的 Study-specific 用户输入契约已经确定，并可按 [Research UI authority](../ui/ARCHITECTURE.md) 的调用和 output placement 约定落地。 |
| Result contract completeness | 核对 Results 与 Evidence Products 满足 Schema 的保留、呈现、边界状态及 provenance contract；逐项验证需要物化的 Observation / Analysis Artifact identity 覆盖实际语义依赖，且未把 filename、path 或 representation 当作 identity。 |
| Study semantic isolation（新 Study） | 检查当前 Study 的 Research-specific semantics 由本地拥有，未从 sibling Study、retained artifact 或既有 shared Research analytical semantics 继承。 |
| No premature abstraction（新 Study） | 检查创建工作未因重复研究逻辑而修改 shared authority / sibling Study 或引入 generic Research framework。 |
| Dependency distinction | 所需上游 canonical fact / capability 及其 owner 与 Study-owned evidence semantics 分开表达；缺失 Snapshot public Product 等 capability 已记录为 dependency gap，不被误判为 Study semantic incompleteness。 |
| Internal consistency | Question/hypothesis 与 Inputs 的研究空间一致；具体 default configuration 与核心 hypothesis 的关系明确；所有 configurable inputs 的允许范围均适用于 Question、Method、Results、Limitations 和 Acceptance；必填性、可选性与默认值无矛盾；Acceptance 对应前述研究；Study-local semantics 不重定义或冲突于所依赖的上游 canonical facts。 |

若 hypothesis 固定某个配置而 Inputs 允许更广范围，须记录该范围与 hypothesis 的不一致并返回 finding；所需语义决定由 Authoring 的 human decision loop 处理。Class/function 命名、代码拆分和测试布局等纯实现细节不阻止通过。

## Review outcome

Gate 全部通过时，判定 **Study Authority Complete**：六个 semantic areas 与跨对象关系已确定 Study-owned Research semantics，后续 Implementation Agent 无需重新决定这些语义。该判定不表示上游 capability 已备齐；后续 dependency reconciliation 与 implementation handoff 由 [Authoring](AUTHORING.md) 处理。

Gate 未通过时，返回未解决或不一致的字段、引用和依赖作为 validation findings，不将它们写成既定 Study 语义；Authoring 决定是否进入 `Semantic Decision Required`、更新草稿并重新提交完整 Review。

## Runnable Study implementation topology review

本审查在新 runnable Study implementation 形成后执行，与上方的 Study Authority Completeness Gate 分开；实现拓扑不决定 Study semantic authority 是否 complete。既有实现仅按 [Compatibility](COMPATIBILITY.md) 的触发范围审查，不追溯宣布历史实现 invalid。逐项核对：

| 检查面 | 不通过条件 |
| --- | --- |
| Package 与入口 | 新 runnable Study 被实现为 `<study_package>.py`、缺少 [Implementation Package Contract](IMPLEMENTATION.md) 的必需 package-level 边界，或 `__init__.py` 不指向当前 Study canonical authority。 |
| Orchestration | `study.py` 含有 material Observation construction 与 Analysis execution，或隐藏大块 selection、statistics、plotting、retention、复杂 provenance 逻辑，使 pipeline 不能直接辨认。 |
| Semantic component traceability | Authority 中具名 Observation / Analysis 无法映射到清晰的 Study-local implementation responsibility，或 Evidence Product 与定义它的 Analysis 在实现中难以追踪。 |
| Focused reading | 修改一个 material Analysis 必须阅读无关 CLI、evidence formatting、其他 Analysis 或无关 Observation mechanics，才能理解其实现。 |
| Mixed responsibility | 单一 module 同时拥有 input canonicalization、Observation construction、Analysis execution、evidence retention 等多个可独立理解的 substantial responsibility，且无清晰内聚性依据。 |
| Authority drift | 实现合并或隐藏 semantic components，以致 `Inputs → Observation(s) → Analysis / Analyses → Evidence Products` 的 authority graph 难以辨认。 |

对上述 finding 按 Study-local semantic responsibility 拆分或明确内聚性，不以 LOC、函数／class 数量或 one-object-one-file 规则替代审查。结构测试只固定 package、必需模块与 authority pointer 等稳定事实，不能替代阅读边界审查。以 `0dd28a641a3210fa03da9e5aa621742ac48b7cf0` 的 MO implementation 作一致性 probe：其中 `study.py` 同时实现 material Observation selection/construction 与 Analysis/statistics，按本检查不通过；这不触发对该既有 Study 的自动迁移。
