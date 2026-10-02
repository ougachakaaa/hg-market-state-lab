# Concrete Observation Semantic Schema

本文件定义 concrete Observation authority 必须回答的最小 semantic areas，不定义所有 Observation 通用的业务字段或 row schema。Framework identity、lifecycle、idempotency、completeness、persistence 与 public boundary 由 [Observation architecture](ARCHITECTURE.md) 唯一拥有；创建流程由 [Authoring](AUTHORING.md) 拥有。

## Required semantic areas

| Area | Concrete authority 必须明确的内容 |
| --- | --- |
| Identity | 稳定 Observation identity 与 canonical authority entry；不得把执行 identity 当作 Observation identity。 |
| Purpose | 观察什么 empirical phenomenon、业务范围与职责终点，不引入 Study-specific conclusion。 |
| Inputs | 业务输入、semantic owner、必填 / 可选、允许值与适用 defaults；输入如何表达所观察的请求。 |
| Business Key / Canonicalization | Normalized business inputs 的确定性构成、等价表达的归一化、必须区分的输入变化、排除的 execution / provenance metadata；与 [framework semantic identity / lookup boundary](ARCHITECTURE.md#business-identity-与-invocation-lifecycle) 的对应关系，并遵守其 [deferred evolution constraints](ARCHITECTURE.md#explicitly-deferred-decisions)。 |
| Population | 被观察的对象集合、选择范围与 eligibility；由本 Observation 拥有，不留给 Study 重定义。 |
| Grain | 每个 empirical unit / record 代表什么，以及适用的唯一性关系。 |
| Upstream Facts | 实际消费的 DataLake / Snapshot public facts、canonical owner、required capability 与 dependency gaps。 |
| Derivation | 从 upstream facts 到 empirical output 的确定性构造、公式、业务变换及单位；不定义 statistical interpretation。 |
| Validity / Missingness | 有效性、缺失、排除与 failure semantics，包括它们怎样影响 Artifact 可消费性；不静默补值或改变 population。 |
| Artifact Contract | 供 consumer 使用的 semantic shape、字段 / 单位 / 关系、identity 可定位方式、所需 provenance 与 complete 可消费条件；实例化 [framework completeness / publication boundary](ARCHITECTURE.md#completeness-与-public-boundary)，不暴露 SQLite layout。 |
| Persistence | 实例化 framework 的 Observation-owned persistence boundary，明确该 Observation 独立拥有一个 SQLite；具体 schema / path 仅在后续设计确有需要且已决定时定义。 |
| Limitations | 观察范围、数据限制、不能从 Artifact 推出的结论。 |
| Acceptance | Inputs / key、population / grain、derivation、validity、Artifact completeness 与业务幂等的可验证条件；覆盖 [invocation reuse](ARCHITECTURE.md#business-identity-与-invocation-lifecycle)、[completion visibility](ARCHITECTURE.md#completeness-与-public-boundary) 和 [persistence boundary](ARCHITECTURE.md#persistence-ownership) 的 framework invariants。 |

每个 area 须有实质内容或明确适用性说明。空节、`TBD`、常见做法或实现便利性不能代替改变业务含义的决定。输入、population、grain、derivation、validity 和 Artifact shape 只在当前 Observation 的 narrowest canonical owner 定义；Study 引用它们，不复制定义。

## Cross-area consistency

- Purpose、Inputs、Population 与 Grain 能确定“用户要求观察什么”；canonicalization 不合并不同业务请求，也不把等价表达变成不同业务请求。
- Derivation 仅依赖已声明的 public upstream facts 和业务输入；Validity / Missingness 与 Artifact completeness 一致，failed / partial persistence 不被描述为 complete。
- Artifact Contract 足以支持独立消费和跨 Study reuse，且不混入 Analysis / Study Evidence semantics。Execution provenance 与 business key 分开表达。
- Acceptance 覆盖重复 invocation 复用 complete Artifact、未完成请求不满足 key、consumer 不进入 internal persistence 等 framework invariants。
- Refresh / invalidation 和 definition evolution 遵守 [deferred decisions](ARCHITECTURE.md#explicitly-deferred-decisions)，不为填满 schema 自行决定。

本 schema 不要求机械的一对象一文件、统一 Artifact envelope、统一 business-key 算法或 concrete SQLite schema。
