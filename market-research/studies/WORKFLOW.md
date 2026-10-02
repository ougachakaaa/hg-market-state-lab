# Study Workflow 与 runtime / retained state authority

本文件拥有 Study-owned workflow steps、runtime orchestration state 与 retained Workflow Artifact 的区分、显式 retained identity 与 complete-input boundary。对象模型与 cardinality 由 [Schema](SCHEMA.md) 拥有，具体执行顺序、outcome 与声明的 artifacts 由各 Study METHOD / RESULTS 定义；创建流程见 [Authoring](AUTHORING.md)，实际 retained-output publication 见 [Research UI](../ui/ARCHITECTURE.md)。本文件不是 workflow engine 或统一 executable protocol。

## Workflow ownership 与 steps

每个 Study 必须定义自己的 workflow：objective、请求输入、步骤顺序、dependency bindings、每步 consumes / produces、完成条件、失败及空结果语义。至少有一个具名步骤；只有实际使用 Observation 时才声明 `1..N` 个 Observation dependency contracts，参数化展开可以产生零个或多个实际 invocations。

在新 Study 内，只有 Study orchestration 可以经 Observation public boundary resolve / ensure empirical dependencies，取得 complete Artifacts，再准备下游输入。Study 不直接调用 DataLake / Snapshot 或获取市场数据，不读取 Observation persistence，不重定义 Observation empirical semantics。Legacy 适用范围由 [Compatibility](COMPATIBILITY.md) 保留。

Study 拥有 input bindings、execution order、runtime plan expansion、failure / continuation semantics 与 human-facing execution outcome，不拥有 reusable empirical persistence。Workflow 可以直接在 runtime 中 `ensure Observation → expand plan → ensure more Observations → outcome`，也可以在实际明确要求 retention 时使用 `Step A → retained Artifact A → Step B`。执行顺序、依赖展开、失败后的继续 / 停止规则属于当前 Study，不能从通用习惯推断。Step 可消费已准备的 complete Observation Artifact、合法 runtime state 或明确声明的前一步 complete Workflow Artifact；runtime state 不假称 retained Artifact，failed / partial Artifact 不作 complete empirical input。

Analysis 为可选的 Study-local computation；只接收已准备好的 complete Artifacts，不能调用 DataLake / Snapshot、fetch market data、invoke / resolve / ensure Observation 或读取 Observation SQLite。Analysis 不拥有 dependency resolution，Analysis 的具体 computation / comparison / statistics 仍归 [Schema](SCHEMA.md#study-local-analysis-contracts) 及 specific Study。Observation invocation 不因被放进 Analysis 而成为合法 analytical step。

## Runtime orchestration state

Runtime plan、ordered complete Artifact references / values、temporary invocation state、counts 与 failure summaries 可以只在本次 invocation 存在，不自动成为 retained Workflow Artifact，不要求 Artifact identity / serialization / materialization / database。Orchestration-only Study 的 Observation dependencies>0、Study-local retained Workflow Artifacts=0、Analysis=0、Evidence=0 是完整合法 shape；completion 由其 declared Observation ensures 与 runtime outcome 决定。

需要重复 empirical facts 时，由 Study / future workflow 通过相同 Observation semantic request 再 ensure；consumer 不找旧 Study run、不读 Observation SQLite、不复制 market rows 建另一层 canonical cache、不自行判断 refresh。Successful Observation ensure 已 durable before return，Study 只编排这些 Artifacts。Study failure 不 rollback 已成功 Observation publication。当前不创建 Study SQLite、observation_collection.sqlite3 或 global collection DB。

## 三类 retained products

| Product | Ownership / meaning / reuse |
| --- | --- |
| Observation Artifact | Observation-owned reusable empirical facts，按 Observation identity + business inputs 定位，可跨 Study 复用。 |
| Study-local Workflow Artifact | Study-owned retained intermediate / final workflow state，属于一个 deterministic Study run，不建立跨 Study reuse。 |
| Evidence Product | Study-owned interpretation / finding；若存在，由 Results 引用 defining Analysis，不把 plan 或 manifest 称为 Evidence。 |

只有 specific Study 明确声明 retained Workflow Artifact 时，才给它当前 Study 内稳定的 local name 与以下 identity：

```text
Study-local Workflow Artifact identity
    = Study identity + deterministic Study run identity + stable artifact local name
```

Run identity 的 semantic inputs / canonicalization 由 Study INPUTS 定义。Execution timestamp、UUID、filesystem path、staging directory 或偶然变量名不成为 semantic identity。重复独立 invocation 对应同一个 semantic run，不因此获得 workflow cache / resume 权限；output collision / overwrite 由 UI 拥有。

## Materialization 与 complete consumption

Retained Workflow Artifacts 的数量为 0..N；不为满足 Schema 人为创建 expiry_plan、observation_collection、manifest DB 或空 Evidence。每个实际声明的 retained Workflow Artifact 必须明确 semantic shape、producer step、消费者、provenance references、complete 条件、empty / failure states 与 retention。METHOD 拥有 production / consumption 顺序；RESULTS 唯一拥有具名 Artifact 的 semantic shape 与 retained result contract。

实际声明为 retained Artifact 的产物必须 materialized / retained，不能仅存在于 runtime variable；在下游消费前形成对应 complete materialized state。同一次 retained-output invocation 可先写所属 run 的 staging workspace；成功后随 canonical run output 发布，遵守 [UI staging / replacement](../ui/ARCHITECTURE.md#3-shared-configuration-and-output-placement)。这些要求不适用于未声明为 Artifact 的 runtime state 或 orchestration-only outcome。Internal partial / failed state 可以存在，但不能冒充 complete final output。是否需要 retained failure diagnostics 由实际 Study authority 明确，默认不新增 partial-output publication。

Complete Study-local Artifact 不替代 Observation-owned retention 或 business identity；若确有 retained manifest，它只引用 complete Observation Artifacts，不建立 market rows 的第二份 canonical empirical persistence。Study 失败不 rollback 已成功形成的 Observation Artifacts，retained-output overwrite 不授权 Observation refresh。

## Boundaries 与 deferred decisions

本文件不规定统一 hash、serialization、database、global ID、Artifact Registry、run registry、cross-Study workflow abstraction、generic DAG、scheduler、executor、background / distributed execution 或 resume engine。跨独立 invocation 的 Workflow Artifact reuse / resume、generic invalidation 与 failure-output protocol 均未锁定；Observation refresh / evolution 继续由 [Observation deferred authority](../observations/ARCHITECTURE.md#explicitly-deferred-decisions) 拥有。
