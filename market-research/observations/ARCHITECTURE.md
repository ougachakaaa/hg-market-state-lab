# Research Observation authority

本文件是独立 Observation 的 framework authority，拥有 identity、lifecycle、业务幂等、persistence ownership、completeness 与 public consumption boundary。Research 模块边界见 [module architecture](../ARCHITECTURE.md)，concrete Observation 的必答语义见 [Schema](SCHEMA.md)，创建流程见 [Authoring](AUTHORING.md)。具体业务字段、公式与 Artifact shape 留在各 concrete Observation authority。

## Purpose 与职责终点

Observation 是 `market-research` 内 first-class、参数化的 retained empirical fact producer：对一组规范化业务输入，以确定性的 observation semantics 构造可长期保留、可复用的 empirical Artifact。职责终点是 **retained Observation Artifact**，不是 Study Evidence。

未来 Python implementation 的 canonical namespace 预留为 `market_research.observations`，仍由 `market-research` 拥有。本决定只预留 namespace ownership，不创建 Python package、不规定 concrete implementation topology，也不改变 repository root 的唯一 runtime / source registration。

Observation 不属于某个 Study，不拥有 statistical interpretation、research hypothesis、Study-specific comparison、Analysis conclusion、Study Evidence、Modeling、Forecast 或 Decision。其定义不得依赖 Study question 的解释、Analysis 目标或已得结果、Study conclusion。

稳定 semantic direction 为：

```text
DataLake / Market Snapshot public facts
    → Observation
    → complete retained Observation Artifact
    → Study
    → Study-local Analysis
    → Evidence / Findings
```

Study 可选择 Observation、提供 invocation semantic inputs、resolve / ensure Artifact 并消费它；Study / Analysis 不重新定义 Observation 的 population、grain、derivation、validity 或 Artifact schema。Artifact 可被多个 Study 复用，不因 Study 不同而重新生成，也不因被消费过而失效。Observation Artifact 表达 what was observed；Study Evidence 表达 what was learned from observations。

## Business identity 与 invocation lifecycle

每个 concrete Observation 自己定义业务输入及其 canonicalization：

```text
business_key = normalized business inputs
Observation Artifact semantic identity
    = Observation identity + normalized business inputs
```

Business identity 表达用户要求观察什么；execution / provenance metadata 表达 Artifact 如何、何时、基于哪些 upstream facts 生成。Wall-clock time、random UUID、filesystem path、execution attempt、temporary directory、调用次数或执行顺序不得自动进入 business key。

不得用 arbitrary repository-global Artifact ID 替代上述 semantic identity。Hash 可以作为 persistence / lookup 的 implementation technique，但 hash 本身不是业务语义；本 framework 不规定 hash 算法。

在同一有效 Observation definition 下，相同 Observation identity 与 normalized business inputs 表示同一个业务请求。普通 invocation 的语义是“确保请求对应的 Artifact 存在并返回它”：

```text
Observation definition + normalized business inputs
    ↓ business key
lookup Observation-owned persistence
    ├── complete Artifact exists → return existing Artifact
    └── no complete Artifact → execute → produce Artifact
                                      → persist complete → return Artifact
```

已有 complete Artifact 时直接复用，不重复访问上游、不重复计算、不重复生成第二个逻辑 Artifact。Invocation 不等同于每次重新计算，不自动 refresh、overwrite 或迁移已有 Artifact。

## Completeness 与 public boundary

普通 consumer 只能消费 complete Observation Artifact。Partial persistence、interrupted execution 和 failed execution 均不等于 complete Artifact；business key 只有在完整可消费 Artifact 已形成后才算被满足。具体 completeness acceptance 由 concrete Observation authority 定义；本文件不建立完整 state machine、retry engine 或 transactional implementation。

未来 implementation 必须能够原子地区分 business key 已形成 complete Artifact 与尚未形成可消费 Artifact；consumer 不得看到未完成 persistence 被发布为 complete。这里只锁定完成状态的可见性，不决定 SQLite schema、事务算法、锁、retry 或内部状态机。

Observation Artifact contract 是 Study / Analysis / external consumer 的 public research-data boundary。每个 concrete Observation 自己拥有 Artifact semantic shape；本 framework 不规定统一 row schema、业务字段、文件格式或 serialization representation。

## Persistence ownership

每个 concrete Observation **exactly owns 一个 SQLite database**；该数据库承载该 Observation 的业务请求及 Artifacts，不是 one SQLite per invocation。SQLite 是 Observation internal persistence，具体 schema、path 与 implementation 留给后续 concrete design / implementation。

Observation runtime SQLite 文件不应进入 Git。本轮不创建 runtime database，也不为此预设文件路径或修改 repository ignore configuration。

不建立 global `research.sqlite`、global Observation database、global Artifact DB、cross-Observation foreign key 或 Study-owned Observation persistence。Study、Analysis 与 external consumer 不直接读取 SQLite，不依赖 SQLite schema 或 path。Study evidence output 与 Observation-owned persistence 是不同边界；Study output replacement 不授予 Observation overwrite 权限。

## Upstream dependency boundary

Observation 可以消费 DataLake public Application Service 或 Market Snapshot 明确支持的 public application / product result。共享 Python environment 不授予跨模块内部访问权。

不得依赖 Source / Raw internals、private Preparation、upstream persistence、Dataset SQLite、Snapshot SQLite、`backend-api`、FastAPI DTO 或 frontend types，也不得通过 CLI / JSON export 反向获取 Python semantic result。Upstream fact semantics 继续由对应 canonical owner 拥有。

若 concrete Observation 需要尚不存在的 upstream capability，应在其 authority 记录 dependency gap，再与 owning upstream authority reconciliation；不得穿透 upstream boundary 作为稳定方案。本 framework 不承诺具体 Dataset / Snapshot integration 已就绪。

## Explicitly deferred decisions

以下问题尚未锁定，Agent 不得从业务幂等或 provenance requirement 推导默认答案：

- 相同 normalized inputs 下 upstream facts 修订后，是否 refresh、overwrite 或保留 generation history。
- Observation definition / authority 演进后 old Artifact 是否继续有效、definition version 是否进入 generation identity、是否 migrate。

本轮 identity / reuse contract 以同一有效 definition 为前提，不定义 definition versioning 或 invalidation policy。这些未决项不阻塞 framework reconciliation；未来具体需求触及它们时须先作 semantic decision。

在相关 human semantic decision 明确之前，Agent 不得自行将 version、source digest、code hash 或 timestamp 加入 business key；不得以这些 implementation / provenance metadata 绕过同一业务请求的 reuse contract。本约束不决定未来 generation identity 或 evolution policy。

## Navigation 与 non-goals

从本文件进入 [Schema](SCHEMA.md) 确认 concrete semantic areas，再按 [Authoring](AUTHORING.md) 锁定设计，沿具体 Observation entry 读取必要 specialized / upstream authority。首个 concrete entry 为 [cffex_option_expiry_dte_chain](cffex_option_expiry_dte_chain/ARCHITECTURE.md)；具体业务规则由该 entry 及其专题 contracts 拥有，本 framework 不预设 implementation topology。

不创建 generic registry、plugin system、Research Repository、Experiment Engine、DAG、scheduler、executor、cache、refresh engine、HTTP API、Web UI、Observation CLI 或 automatic migration。Analysis 的当前 ownership 与 deferred reuse model 见 [Study Schema](../studies/SCHEMA.md)；实现 / 测试差异见 [implementation reconciliation](../IMPLEMENTATION_RECONCILIATION.md)。
