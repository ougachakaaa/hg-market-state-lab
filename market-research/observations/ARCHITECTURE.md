# Research Observation authority

本文件是独立 Observation 的 framework authority，拥有 identity、lifecycle、业务幂等、persistence ownership、completeness 与 public consumption boundary。Research 模块边界见 [module architecture](../ARCHITECTURE.md)，concrete Observation 的必答语义见 [Schema](SCHEMA.md)，创建流程见 [Authoring](AUTHORING.md)。具体业务字段、公式与 Artifact shape 留在各 concrete Observation authority。

## Purpose 与职责终点

Observation 是 `market-research` 内 first-class、参数化的 retained empirical fact producer：对一组规范化业务输入，以确定性的 observation semantics 构造可长期保留、可复用的 empirical Artifact。职责终点是 **retained Observation Artifact**，不是 Study Evidence。

Canonical Python namespace 为 `market_research.observations`，仍由 `market-research` 拥有。Runnable contract / topology 唯一进入 [IMPLEMENTATION.md](IMPLEMENTATION.md)，不改变 repository root 唯一 runtime / source registration；architecture 已落位不表示 runtime package 已实现。

Observation 不属于某个 Study，不拥有 statistical interpretation、research hypothesis、Study-specific comparison、Analysis conclusion、Study Evidence、Modeling、Forecast 或 Decision。其定义不得依赖 Study question 的解释、Analysis 目标或已得结果、Study conclusion。

稳定 semantic direction 为：

```text
DataLake / Market Snapshot public facts
    → Observation
    → complete retained Observation Artifact
    → Study
    → Study-owned runtime orchestration / execution outcome
    → optional explicitly declared retained Workflow Artifacts
    → optional Study-local Analysis
    → optional Evidence / Findings
```

Study 可选择 Observation、提供 invocation semantic inputs，并由 Study orchestration resolve / ensure complete Artifact；Analysis 只消费已准备 inputs，不自行调用 / resolve / ensure Observation 或 upstream。Study / Analysis 不重新定义 Observation 的 population、grain、derivation、validity 或 Artifact schema。Artifact 可被多个 Study 复用，不因 Study 不同而重新生成或消费而失效。Observation Artifact 表达 what was observed；[Study-local Workflow Artifact](../studies/WORKFLOW.md) 表达 retained workflow state，Study Evidence 若存在表达 what was learned。

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

已有 complete Artifact 时直接复用，不重复访问上游、不重复计算、不重复生成第二个逻辑 Artifact。Successful `ensure()` return 的前提是整份合法 complete Artifact 已原子进入 Observation-owned durable persistence；不能先 return 再异步保存。Invocation 不等同于每次重新计算，不自动 refresh、overwrite 或迁移已有 Artifact。

Canonical empirical reuse 是 `semantic request → Observation public ensure boundary → retained Artifact`，由 Observation identity + normalized business inputs 定位。不同 Studies / future workflows 需要相同 facts 时，由 orchestration 再次 ensure 同一 request；Analysis 只消费其已准备的 complete Artifacts，不自行 ensure。Consumer 不通过旧 Study output、filename 或 SQLite path 定位 / 复制 empirical cache，不自行决定 upstream refresh。跨 service / process recreation 的 durable reuse acceptance 唯一见 [implementation acceptance](IMPLEMENTATION.md#durable-reuse-acceptance)。

## Completeness 与 public boundary

普通 consumer 只能消费 complete Observation Artifact。Partial persistence、interrupted execution 和 failed execution 均不等于 complete Artifact；business key 只有在完整可消费 Artifact 已形成后才算被满足。具体 completeness acceptance 由 concrete Observation authority 定义；本文件不建立完整 state machine、retry engine 或 transactional implementation。

未来 implementation 必须能够原子地区分 business key 已形成 complete Artifact 与尚未形成可消费 Artifact；consumer 不得看到未完成 persistence 被发布为 complete。这里只锁定完成状态的可见性，不决定 SQLite schema、事务算法、锁、retry 或内部状态机。

Observation Artifact contract 是 Study / Analysis / external consumer 的 public research-data boundary。每个 concrete Observation 自己拥有 Artifact semantic shape；本 framework 不规定统一 row schema、业务字段、文件格式或 serialization representation。

## Persistence ownership

每个 concrete Observation **exactly owns 一个 SQLite database**；该数据库承载多个 Observation business requests 与其 complete Artifacts，不是 one SQLite per invocation。Reusable empirical persistence 唯一归 Observation，不是 Study-owned cache。SQLite 是 Observation internal persistence；canonical placement 与 publication mapping 见 [Implementation architecture](IMPLEMENTATION.md)，SQL schema 与 transaction algorithm 留给实现。

Observation runtime SQLite 文件不应进入 Git。本 authority-only 轮不创建 runtime database 或修改 repository ignore configuration。

不建立 global `research.sqlite`、global Observation database、global Artifact DB、cross-Observation foreign key 或 Study-owned Observation persistence。Study、Analysis 与 external consumer 不直接读取 SQLite，不依赖 SQLite schema 或 path。Study evidence output 与 Observation-owned persistence 是不同边界；Study output replacement 不授予 Observation overwrite 权限。

## Upstream dependency boundary

Observation 采用 DataLake-first **design-time capability selection**：DataLake public semantic contract 足够时必须使用其 Dataset public Application Service；只有 semantic capability insufficient 才选择明确的 Market Snapshot public Product / Application boundary。Research（包括所有 Observation）绝不直接依赖 Tushare 或其他 external market-data provider，不能访问 upstream internals；共享 Python runtime 不授予内部依赖权限。

详细 sufficiency / selection、runtime failure 不换源、multi-upstream ownership、gap escalation、execution 与 provenance 规则唯一归 [UPSTREAM.md](UPSTREAM.md)。具体 upstream facts 继续由选定 canonical owner 拥有；本 framework 不承诺 runtime integration 已就绪。

## Explicitly deferred decisions

以下问题尚未锁定，Agent 不得从业务幂等或 provenance requirement 推导默认答案：

- 相同 normalized inputs 下 upstream facts 修订后，是否 refresh、overwrite 或保留 generation history。
- Observation definition / authority 演进后 old Artifact 是否继续有效、definition version 是否进入 generation identity、是否 migrate。

本轮 identity / reuse contract 以同一有效 definition 为前提，不定义 definition versioning 或 invalidation policy。这些未决项不阻塞 framework reconciliation；未来具体需求触及它们时须先作 semantic decision。

在相关 human semantic decision 明确之前，Agent 不得自行将 version、source digest、code hash 或 timestamp 加入 business key；不得以这些 implementation / provenance metadata 绕过同一业务请求的 reuse contract。本约束不决定未来 generation identity 或 evolution policy。

## Navigation 与 non-goals

从本文件先进入 [Upstream policy](UPSTREAM.md)，再按 [Schema](SCHEMA.md) / [Authoring](AUTHORING.md) 锁定 concrete semantics，沿实际所需 entry 读取必要 upstream authority：[cffex_option_expiry_universe](cffex_option_expiry_universe/ARCHITECTURE.md)、[cffex_option_expiry_dte_chain](cffex_option_expiry_dte_chain/ARCHITECTURE.md)。具体规则由各 entry / 专题拥有，Implementation handoff 进入 [framework IMPLEMENTATION](IMPLEMENTATION.md) 与 concrete IMPLEMENTATION；不创建 catalog。

不创建 generic registry、plugin system、Research Repository、Experiment Engine、DAG、scheduler、executor、cache、refresh engine、HTTP API、Web UI、Observation CLI 或 automatic migration。Analysis 的当前 ownership 与 deferred reuse model 见 [Study Schema](../studies/SCHEMA.md)；实现 / 测试差异见 [implementation reconciliation](../IMPLEMENTATION_RECONCILIATION.md)。
