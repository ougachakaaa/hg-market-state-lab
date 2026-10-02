# Research Study Authority Review

本文件拥有 Study Authority Completeness Gate、semantic consistency / traceability、implementation topology review 与 validation findings。必需语义由 [Schema](SCHEMA.md) 定义，文档拓扑由 [Skeleton](SKELETON.md) 定义，implementation topology 由 [Package Contract](IMPLEMENTATION.md) 定义，human semantic-decision loop 由 [Authoring](AUTHORING.md) 拥有。

## Study Authority Completeness Gate

Gate 判断 Study-owned semantics 是否完整，不代替 dependency capability readiness。对历史 Study 仅在 [Compatibility](COMPATIBILITY.md) 的明确触发范围适用，不追溯宣布 legacy Study invalid。

| 检查面 | 通过条件 |
| --- | --- |
| Research completeness | 六个 areas 均有实质内容、唯一 owner，无未解决 Study-owned research semantic decision。 |
| New Study topology | Skeleton 的四文件均存在且有实质内容，entry 直接链接其他三个 owner，细节不重复堆在 entry；只对新 Study 强制。 |
| Navigation | Entry、specialized owners 与实际 consumed Observation authority 可沿链接到达，无 orphan owner，不默认加载无关 sibling authority。 |
| Input ownership | Parameter owner / consumers / semantic role、bindings、defaults、用户表达和 semantic request identity 符合 Schema；retained run identity / execution-only output options 仅声明 retained outputs 时要求。 |
| Observation canonical ownership | 每个 dependency 有独立 Observation canonical owner / Artifact contract；未存在能力明确列为 gap。Study 不重定义 population、grain、derivation、validity、input domain 或 Artifact schema。 |
| Artifact dependencies | Observation identity、invocation inputs、canonicalization、所消费 Artifact identity 与 workflow / optional Analysis consumption 清晰；只消费 complete Artifact，不以 SQLite / run directory 识别业务对象。 |
| Method completeness | Required workflow / steps、consumes / produces、顺序、failure / empty semantics 与 materialization 符合 [Workflow](WORKFLOW.md)；optional Method Context / Analysis 若存在，contract 完整无悬空 references。 |
| Objective-to-result traceability | Objective → workflow → dependencies → execution outcome 可追踪；retained outputs / Analysis / Evidence 仅实际声明时核对其关系。Workflow Artifacts=0、Analysis=0、Evidence=0 不构成 incompleteness，不制造假对象。 |
| Retained run identity | 仅 retained-output Study 适用；等价请求与 identity-changing 输入区分一致，覆盖实际 bindings / Analysis configuration，execution-only options 不参与。Orchestration-only request identity 不映射为 filesystem run key。 |
| Runnable contract | Study input / CLI mapping、runtime outcome 与所声明 output shape 满足 [Research UI authority](../ui/ARCHITECTURE.md)；design readiness 按 [Authoring](AUTHORING.md#publication-与-dependency-handoff) 验证，runtime missing 单独记录，不以 future delivery 假装 runtime-ready。 |
| Result completeness | Runtime presentation / counts / empty / failure 完整，temporary plan / references 不自动成为 Artifact；只有具名 retained Workflow Artifact 实际存在时才要求其 shape / identity / completeness / retention。Evidence 若存在再核对 structure / sample / exclusion counts，不以 filename 替代 identity。 |
| Study semantic isolation | Study-owned Analysis / evidence semantics 不继承 sibling Study、retained evidence 或 historical shared analytical semantics；Artifact reuse 通过 Observation public boundary 合法引用。 |
| No premature abstraction | 不因重复修改 shared owners / sibling Study，不创建 reusable Analysis framework、registry 或 DAG。 |
| Dependency distinction | Required capability / owner、Study-owned workflow / result semantics 与 readiness 分开；缺失 Observation / upstream capability 有显式 gap，不在 Study Method 临时实现。缺失 material consumption decision 仍作为 semantic finding。 |
| Internal consistency | Objective 与允许 configurations 一致，hypothesis 若有再验证其关系；defaults / domain / binding 无冲突，Acceptance 对应 Method / Results；Analysis sample selection 不改写 population / validity，上游 facts 不重定义。 |

若 hypothesis 固定某配置而 Inputs 允许更广范围，返回具体 finding，由 Authoring human loop 明确关系；不自行将其解释为 default hypothesis。Class / function 命名、代码拆分与测试布局等纯实现细节不阻止 authority complete。

## Review outcome

Gate 全部通过判定 **Study Authority Complete**：Study-owned semantics 已确定，后续 Implementer 无需重新决定；该结果不表示 Observation / upstream capability ready。Dependency reconciliation 和 implementation handoff 沿 Authoring 处理。

未通过时返回具体未解决字段、引用、ownership conflict 或 missing decision，不将其写成已锁定语义。Authoring 更新 Record / 草稿后重新完整 Review；不能用实现便利性或 sibling 惯例替代 human decision。

## Runnable Study implementation topology review

实现形成后单独执行，不决定 authority complete。历史 implementation 只按 Compatibility 的触发范围适用。

| 检查面 | 不通过条件 |
| --- | --- |
| Package / entry | 新 runnable Study 是单脚本、缺少 Package Contract 必需边界，或 init docstring 不指向 canonical Study entry。 |
| Orchestration | study.py 隐藏 material statistics / plotting / complex serialization，或无法辨认 request → dependency ensure / runtime plan → outcome；实际声明 retained outputs / Analysis / Evidence 时其责任无法辨认。 |
| Observation / Analysis boundary | Study 直接调用 DataLake / Snapshot 或实现 Observation construction、读取 persistence；Analysis invoke / resolve / ensure Observation、fetch data 或重定义 empirical semantics。Only Study orchestration 的 public binding / resolve / ensure 合法。 |
| Traceability | Dependencies、步骤、runtime completion / failure 无法追踪；实际声明的 retained Workflow Artifacts / publication 或 Analysis / Evidence 无清晰责任。 |
| Focused reading | 修改一个 Analysis 需理解无关 CLI、其他 Analysis、Observation internals、报告格式或 output transaction。 |
| Mixed responsibility | 单 module 承担可独立理解的 input canonicalization、Analysis execution、evidence retention 等多个 substantial responsibilities，无清晰内聚依据。 |
| Authority drift | 实现合并、隐藏或越界重定义语义对象，无法恢复 Schema / Workflow graph；为 orchestration-only Study 强制 directory / config / Artifact，复制 market rows 建 empirical cache，或对无 Analysis / Evidence 的 Study 强制空 module。 |

按 semantic responsibility 和阅读边界处理 findings，不以 LOC、函数 / class 数量或一对象一文件代替审查。结构测试可固定 package / 必需 module / authority pointer，不能替代语义阅读；本轮未修改的旧测试差异见 [implementation reconciliation](../IMPLEMENTATION_RECONCILIATION.md)。
