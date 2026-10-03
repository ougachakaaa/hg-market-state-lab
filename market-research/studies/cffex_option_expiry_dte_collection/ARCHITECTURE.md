# cffex_option_expiry_dte_collection Study authority

本文件是 retained Study knowledge / orchestration authority 的稳定 entry，拥有 identity、objective、boundaries、limitations、acceptance 与导航；retained authority 不要求 retained execution output。继承 [Study Schema](../SCHEMA.md)、[Workflow contract](../WORKFLOW.md)、[Skeleton](../SKELETON.md) 与 [Research boundaries](../../ARCHITECTURE.md)。Request / semantic identity 进入 [INPUTS.md](INPUTS.md)，workflow / dependencies 进入 [METHOD.md](METHOD.md)，non-persistent outcome / presentation 进入 [RESULTS.md](RESULTS.md)，Python / CLI handoff 进入 [IMPLEMENTATION.md](IMPLEMENTATION.md)。

## Identity 与 objective

Study identity / study_package 为 `cffex_option_expiry_dte_collection`，public Study ID 为 `cffex-option-expiry-dte-collection`，遵守 [UI naming](../../ui/ARCHITECTURE.md#2-runnable-study-convention)。Authority 与 implementation 同处本 Python package directory。

Objective 是 orchestration-only research preparation：用用户选择的产品、inclusive expiry window 与 target DTE 调用 Universe shared resolver 并驱动 chain Observation，确保 observed Universe 中每个真实 expiry 都有 complete durable target-DTE chain Artifact。它不是 retained data-collection database producer。

本 Study 的 Shared Component dependency contracts=1、Observation dependency contracts=1、Study-local retained Workflow Artifacts=0、Analysis=0、Evidence=0；没有 hypothesis、statistical finding、图表或收益计算。Runtime plan / ordered references / counts 不提升为 expiry_plan 或 observation_collection Artifact，不保留 Study manifest / SQLite / run directory。

## Dependency overview 与 ownership

Expiry selection 由 [cffex_option_expiry_universe](../../shared/cffex_option_expiry_universe/ARCHITECTURE.md) 拥有，单 expiry 日期解析 / chain 由 [cffex_option_expiry_dte_chain](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md) 拥有。Successful Observation ensure 已把完整 Artifact durable published 到该 Observation 唯一 SQLite，Study 只选择输入、驱动 public invocation、扩展 runtime plan 并报告结果。

METHOD 唯一拥有 Universe → runtime plan → all chains → summary 的顺序、bindings 与失败后继续规则；RESULTS 唯一拥有 runtime outcome / counts / failure details。Study 不直接调用 DataLake / Snapshot、不读取 Observation SQLite、不复制 market rows 建第二份 empirical cache、不重新计算市场日期、不自行 refresh。Chain Artifact 跨 Study reuse 由相同 Observation request 再 ensure 实现；Universe 复用 resolver I/O，无 research cache，不经旧 Study run / manifest。

## Limitations

Universe 仅证明请求窗口的完整 historical daily facts 中实际出现的 expiry，不能推断窗口外曾挂牌的全部 expiry、未来上市计划或 provider-current freshness。Chain 不保证 actual_dte 等于 target_dte；日期与实际 DTE 来自其 complete Artifact。

Study execution outcome 是本次 invocation 的 non-persistent feedback，不是 retained collection / reusable empirical product。本 Study 不提供 PnL、统计解释、Evidence / Findings、策略、backtest 或 Modeling output；future Analysis / Evidence persistence 另行设计，Observation refresh / definition evolution 保持 deferred。

## Acceptance 与 readiness

- 四个 normalized inputs 定义同一个 semantic Study request，完整覆盖 Component / Observation bindings；不产生 persisted run identity / filesystem key，不以 option_type 重命名 product_code。
- Universe resolve 成功后才扩展 in-memory 升序 plan；Universe failure 立即停止，零 chain invocations。
- 每个 planned expiry 尝试一次 chain invocation，failure 后继续尝试剩余全部项；不删除失败项、改参数、跳日期、重试 upstream 或缩小计划。
- 全部 planned chains 返回 complete durable Artifacts 才成功；任一 failure 使最终 Study failure，已成功 Observation Artifacts 保留且可复用，不 rollback。
- Complete empty Universe → empty runtime plan → 零 chain invocations → success，四个 counts 为零；不为零计划构造不需要的 chain service。
- RESULTS 的 success / failure counts 与实际执行一致，unknown 不伪报零；只输出 request / summary / failure details，不复制 chain rows 或发布 retained output。
- CLI 不依赖 output.root / run directory / overwrite / staging；无 Workflow Artifact、Analysis、Evidence 占位。

六个 semantic areas、Research dependency contracts、orchestration semantics 与 [implementation architecture](IMPLEMENTATION.md) 完整，按 [Authoring readiness](../AUTHORING.md#publication-与-dependency-handoff) 为 **Study Authority Complete / Research dependency contracts complete / Study implementation architecture complete / Implementation Ready**。未发现 DataLake public capability / Research semantic gap；组件 Python mapping 见 [Universe IMPLEMENTATION](../../shared/cffex_option_expiry_universe/IMPLEMENTATION.md)，runtime 验证另见 reconciliation。

Chain 已按 Observation contract 实施。Universe resolver 与 Study 已使用新的 component boundary，runtime **Dependency Reconciled / Implemented / Verified**。当前验收见 [Research reconciliation](../../IMPLEMENTATION_RECONCILIATION.md#shared-component-runtime-reconciliation)，旧验收不替代此次验证。
