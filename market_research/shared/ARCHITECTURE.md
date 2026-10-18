# Shared Research Component authority

本文件拥有 Research 内 component / local logic 的分类、提升规则、依赖与 authoring / review 准入。继承 [module boundaries](../ARCHITECTURE.md)；Observation 的 artifact lifecycle 仍唯一归 [Observation authority](../observations/ARCHITECTURE.md)，Study / Analysis 语义归 [Study Schema](../studies/SCHEMA.md)。具体 I/O、公式、选择规则与 upstream bindings 归各 component 的 narrowest authority。

## 定义与判断边界

Shared Research Component 是可跨研究复用的小领域 resolver、selector、reader、accessor、calculator、transform 或 helper，拥有稳定、可独立测试的输入输出。它可以调用 DataLake 已发布的 authoritative public service，但不拥有独立 research artifact、Observation execution / cache / SQLite / 幂等业务键生命周期。Component invocation 产生 **Component Result**：ephemeral prepared runtime value，不是 retained research Artifact。它没有 research Artifact identity、business-key lifecycle、component-owned SQLite、durable research cache 或 cross-invocation retained reuse guarantee；重复相同 inputs 不承诺零上游或零计算。

Observation 是拥有最小独立研究语义、形成持久化 empirical artifact，且输出值得 Analysis / Study 独立消费和解释的研究单元。它是 **最小 research artifact boundary，不是最小计算单元**。可复用、确定、纯函数、被多处调用、返回日期列表、调用 DataLake 或计算量大，均不足以使 helper 成为 Observation。Observation 可以调用 component、包含 local logic、消费 public upstream facts；其输入 / business key、幂等与 lifecycle 由 Observation framework / concrete owner 约束。

Analysis 拥有 Study-local computation / comparison / statistics / interpretation；Study 拥有目标、inputs、workflow、orchestration、outcome 与明确声明的 retained outputs。抽出机制不转移其 research question、sample decision、解释或 evidence ownership，也不创建 reusable Analysis framework。

Local logic 只服务一个 Study 或 Observation，可 colocate 于其 implementation；复杂时按内聚性拆为 local helper。代码整洁、潜在复用或相似名称不是 shared 提升理由。

## Local → shared 提升与 Observation 准入

| 判断 | 应落位 |
| --- | --- |
| 仅一个 Study / Observation 使用，含其局部 bindings、sample selection、derivation 或 workflow | 保留 local logic；Observation-owned artifact construction / publication 不抽成独立 component lifecycle。 |
| 明确的跨研究需求需要同一小领域机制，I/O 稳定、可测试，能独立于某个 Study question / outcome 使用 | 提升 Shared Research Component；先锁定 narrow contract，再 reconciliation 实际 consumers。无须为了证明复用先创建第二个 Study。 |
| 需要最小独立 empirical observation semantics，持久化结果值得 Analysis / Study 独立消费与解释，并能完整回答 Observation Schema | 进入 Observation authoring，明确 artifact boundary、inputs / business key、completeness / validity / provenance 与独立 SQLite / 幂等生命周期。 |
| 只有“以后可能复用”、消除重复、缓存方便、昂贵计算或已有 ensure / SQLite 代码 | 不足以提升 shared 或准入 Observation；先判断当前真实语义，现有实现不反向定义分类。 |

创建 helper 时先判断 local / 明确 shared，再判断是否确实需要独立 retained research artifact。两道判断分别回答 mechanism reuse 与 research artifact ownership，**Reuse does not imply Observation**。没有独立 artifact 需求时不得为 helper 增设 Observation business key / persistence；有独立 artifact 需求也不能只用 component 名称绕过 Observation lifecycle。

## Dependency direction 与 public boundary

| Caller | 合法 dependency |
| --- | --- |
| Shared component | 显式声明的 DataLake Dataset public service / semantic export，必要且明确选择的 Snapshot public Product；较小的 shared components 仅在真实 contract 需要时单向调用。不得依赖 Study / Analysis / Evidence / Observation artifact lifecycle 或反向读取它们的内部实现。 |
| Observation | Public upstream facts、shared components 与 Observation-local logic；仍独立拥有其完整 Artifact construction / publication / persistence。调用 helper 不把自身 lifecycle 转交 helper。 |
| Study orchestration | Observation public ensure / complete Artifacts；按已声明 contract 调用 shared resolver / reader，准备 runtime inputs / plan。不得直接调用 DataLake / Snapshot；不复制 empirical cache。 |
| Analysis | 已准备的 complete inputs、pure calculator / selector / transform / helper。不得调用会获取 upstream facts 的 reader / resolver、ensure Observation、读 persistence 或隐藏 I/O；依赖准备由 Study orchestration 完成。 |

Component Result 可以作为 Study runtime 输入或由 Observation 纳入自己的 artifact derivation；它自身没有 retained artifact identity。Study 若明确要求把 workflow 中间结果物化并长期保留，产物成为 [Study-owned Workflow Artifact](../studies/WORKFLOW.md#materialization-与-complete-consumption)，不获得 Component-owned persistence 或 Observation lifecycle。Analysis 若需要某个 resolver / reader 的 result，由 orchestration 先准备，METHOD 明确 binding / meaning / completeness，不把 helper 的事实读取放进 Analysis。具体 Study 对其 inputs 的选择与解释继续归该 Study。

DataLake / Snapshot 不依赖 Research。Component 只消费 public semantic contract；Source facts、field meaning、单位、nullable rules、coverage、cache、export snapshot、provider execution / credentials 均归 upstream owner。DataLake-first selection 与 Research consumer constraints 继承 [UPSTREAM](../UPSTREAM.md)；Dataset operation 定义唯一引用 [DataLake APPLICATION](../../data_lake/APPLICATION.md)。[Observation lifecycle](../observations/ARCHITECTURE.md) 不适用于 component。

跨研究共享是窄领域机制的显式依赖，不是大 shared utility layer。不创建 generic MarketDataProvider / Gateway、registry、DI / executor framework、shared business schema 或 cross-component research database。Framework-internal mechanical primitives 仍归其 framework owner，不因 shared 字样成为领域 component。

## Component contract 与 review

每个实际提升的 component authority 必须回答 purpose / scope、真实复用理由、inputs / domains、outputs / ordering / units、deterministic rule、validity / missingness / failure、dependency owner / exact public contract、side effects 与 acceptance。Public operation 的副作用遵守 [DataLake APPLICATION](../../data_lake/APPLICATION.md)，不产生 component-owned research persistence。Contract 既可 colocate 单文件，也可按独立 concern 下沉；不机械建立 schema / implementation 模板。

Review 核对：能从稳定入口发现唯一 owner；I/O 可独立测试；调用方向正确；Study-specific semantics 未被共享；无隐藏 I/O / partial-as-complete / silent substitution；无独立 research artifact / lifecycle。具体 readiness 与 Python mapping 留在 concrete owner，不在 framework 记录 runtime status。每个 component 的 authority / narrow contracts 与同名 package implementation colocate 于一个 canonical owner，保持既有 public import path / names；不保留 shadow authority directory，无 framework mechanics 时不建空 src。

## Authority navigation

Component task 从本文件分类与 review rules 进入 actual concrete owner，再按需读 narrow contract / implementation handoff；upstream-backed design 另读 [UPSTREAM](../UPSTREAM.md)。若所需的是 independent retained empirical artifact，进入 [Observation Authoring](../observations/AUTHORING.md)，不在 component 中创建该 lifecycle。

Concrete resolver：[cffex_option_expiry_universe](cffex_option_expiry_universe/ARCHITECTURE.md) → CONTRACT / IMPLEMENTATION；具体 I/O、dependencies 和 readiness 留在该 owner。

Historical shared owners 仅沿 [Compatibility](../studies/COMPATIBILITY.md#method-与-consolidation) 进入，不在新 Study 默认路径，不因分类 framework 自动提升或扫描 sibling Studies。
