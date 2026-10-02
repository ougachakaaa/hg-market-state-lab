# Study Workflow 与 materialized Artifact authority

本文件拥有 Study-owned workflow steps、Study-local materialized Workflow Artifacts、identity 与 complete-input boundary。对象模型与 cardinality 由 [Schema](SCHEMA.md) 拥有，具体执行顺序与 artifacts 由各 Study 的 METHOD / RESULTS 定义；创建流程见 [Authoring](AUTHORING.md)，输出 publication 见 [Research UI](../ui/ARCHITECTURE.md)。本文件不是 workflow engine 或统一 executable protocol。

## Workflow ownership 与 steps

每个 Study 必须定义自己的 workflow：objective、请求输入、步骤顺序、dependency bindings、每步 consumes / produces、完成条件、失败及空结果语义。至少有一个具名步骤；只有实际使用 Observation 时才声明 `1..N` 个 Observation dependency contracts，参数化展开可以产生零个或多个实际 invocations。

在新 Study 内，只有 Study orchestration 可以经 Observation public boundary resolve / ensure empirical dependencies，取得 complete Artifacts，再准备下游输入。Study 不直接调用 DataLake / Snapshot 或获取市场数据，不读取 Observation persistence，不重定义 Observation empirical semantics。Legacy 适用范围由 [Compatibility](COMPATIBILITY.md) 保留。

Workflow 可以是具体的 `Step A → Artifact A → Step B → Artifact B`；执行顺序、依赖展开、失败后的继续 / 停止规则属于当前 Study，不能从通用习惯推断。Step 可消费已由 workflow 准备的 complete Observation Artifact 或前一步 complete Study-local Workflow Artifact；不完整、失败或中断产物不得作为 complete input。

Analysis 为可选的 Study-local computation；只接收已准备好的 complete Artifacts，不能调用 DataLake / Snapshot、fetch market data、invoke / resolve / ensure Observation 或读取 Observation SQLite。Analysis 不拥有 dependency resolution，Analysis 的具体 computation / comparison / statistics 仍归 [Schema](SCHEMA.md#study-local-analysis-contracts) 及 specific Study。Observation invocation 不因被放进 Analysis 而成为合法 analytical step。

## 三类 retained products

| Product | Ownership / meaning / reuse |
| --- | --- |
| Observation Artifact | Observation-owned reusable empirical facts，按 Observation identity + business inputs 定位，可跨 Study 复用。 |
| Study-local Workflow Artifact | Study-owned retained intermediate / final workflow state，属于一个 deterministic Study run，不建立跨 Study reuse。 |
| Evidence Product | Study-owned interpretation / finding；若存在，由 Results 引用 defining Analysis，不把 plan 或 manifest 称为 Evidence。 |

Workflow Artifacts 有当前 Study 内稳定的 local name：

```text
Study-local Workflow Artifact identity
    = Study identity + deterministic Study run identity + stable artifact local name
```

Run identity 的 semantic inputs / canonicalization 由 Study INPUTS 定义。Execution timestamp、UUID、filesystem path、staging directory 或偶然变量名不成为 semantic identity。重复独立 invocation 对应同一个 semantic run，不因此获得 workflow cache / resume 权限；output collision / overwrite 由 UI 拥有。

## Materialization 与 complete consumption

每个实际声明的 Workflow Artifact 必须明确 semantic shape、producer step、消费者、provenance references、complete 条件、empty / failure states 与 retention。METHOD 拥有 production / consumption 顺序；RESULTS 唯一拥有具名 Artifact 的 semantic shape 与 retained result contract。

Artifact 必须 materialized / retained，不能仅存在于偶然 runtime variable；在下游消费前形成对应 complete materialized state。同一次 invocation 可先写所属 run 的 staging workspace；成功后随 canonical run output 发布，遵守 [UI staging / replacement](../ui/ARCHITECTURE.md#3-shared-configuration-and-output-placement)。Internal partial / failed state 可以存在，但不能冒充 complete final output。是否需要 retained failure diagnostics 由实际 Study authority 明确，默认不新增 partial-output publication。

Complete Study-local Artifact 不替代 Observation-owned retention 或 business identity；manifest 可引用 complete Observation Artifacts，不必复制 market rows。Study 失败不 rollback 已成功形成的 Observation Artifacts，Study overwrite 不授权 Observation refresh。

## Boundaries 与 deferred decisions

本文件不规定统一 hash、serialization、database、global ID、Artifact Registry、run registry、cross-Study workflow abstraction、generic DAG、scheduler、executor、background / distributed execution 或 resume engine。跨独立 invocation 的 Workflow Artifact reuse / resume、generic invalidation 与 failure-output protocol 均未锁定；Observation refresh / evolution 继续由 [Observation deferred authority](../observations/ARCHITECTURE.md#explicitly-deferred-decisions) 拥有。
