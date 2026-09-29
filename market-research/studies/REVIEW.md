# Research Study Authority Review

本文件拥有 Study Authority Completeness Gate、semantic consistency / traceability checks、validation findings 与 `Study Authority Complete` 的判定。必需语义由 [Schema](SCHEMA.md) 定义；[Authoring](AUTHORING.md) 处理 Study Intention、authoring 状态及 human semantic-decision loop。

## Study Authority Completeness Gate

`Semantic Review` 必须逐项确认下列条件。Gate 检查当前 Study authority 是否满足 Schema，以及跨对象关系是否一致；它不重新定义 Schema contract，也不判断 repository 是否已经具备实现该 Study 的全部 capability。对旧 Study 仅按 [Compatibility](COMPATIBILITY.md) 中显式 reconciliation 的相关范围适用，不得据此追溯宣布历史 Study invalid：

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | 核对 [Schema](SCHEMA.md) 的六个 semantic areas 在 canonical authority graph 中均有实质内容和唯一 owner，且无未解决的 research semantic decision。 |
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
