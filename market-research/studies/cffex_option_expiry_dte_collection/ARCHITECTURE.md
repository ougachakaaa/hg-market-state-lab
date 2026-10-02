# cffex_option_expiry_dte_collection Study authority

本文件是 retained Study 的稳定 entry，拥有 identity、objective、boundaries、limitations、acceptance 与导航。继承 [Study Schema](../SCHEMA.md)、[Workflow contract](../WORKFLOW.md)、[Skeleton](../SKELETON.md) 与 [Research boundaries](../../ARCHITECTURE.md)。Inputs / run identity 进入 [INPUTS.md](INPUTS.md)，workflow / dependencies 进入 [METHOD.md](METHOD.md)，retained Artifact contracts / presentation 进入 [RESULTS.md](RESULTS.md)。

## Identity 与 objective

Study identity / future study_package 为 `cffex_option_expiry_dte_collection`，future public Study ID 为 `cffex-option-expiry-dte-collection`，遵守 [UI naming](../../ui/ARCHITECTURE.md#2-runnable-study-convention)。未来 implementation location 为同名 `src/market_research/studies/` package，本轮不创建它。

Objective 是 research preparation / empirical collection：对于一个产品、inclusive expiry window 与 target DTE，获得 observed ExpiryUniverse，并为每个 discovered expiry 收集 complete DTE-chain Observation Artifact，保留 invocation plan 与完整 collection manifest。

这是 observation / orchestration-only Study，Analysis count=0、Evidence count=0，无 hypothesis、statistical finding、图表或收益计算。完成 objective 的 retained workflow results 是 `expiry_plan` 与 `observation_collection`；不制造 Analysis / Evidence 占位。

## Dependency overview 与 ownership

Empirical discovery 由 [cffex_option_expiry_universe](../../observations/cffex_option_expiry_universe/ARCHITECTURE.md) 拥有，单 expiry 日期解析 / chain 由 [cffex_option_expiry_dte_chain](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md) 拥有。Study 只选择输入、驱动 invocation、物化计划与 compose complete references，不直接访问 DataLake / Snapshot，不读取 Observation persistence，不重新计算市场日期。

Workflow steps、binding 与失败后继续规则归 METHOD；两份具名 Workflow Artifact 的 semantic shape / completeness 归 RESULTS。Market facts 由 Observation retained Artifacts 唯一承载，collection 不复制 chain rows。

## Limitations

Universe 仅证明请求窗口的完整 historical daily facts 中实际出现的 expiry，不能推断窗口外曾挂牌的全部 expiry、未来上市计划或 provider-current freshness。Collection 不保证 actual_dte 等于 target_dte；日期与实际 DTE 是 upstream complete Artifact 的事实。

本 Study 不提供收益、PnL、统计解释、Evidence / Findings、策略、backtest 或 Modeling output。Retained collection 是当前 Study run 的 manifest，不建立跨 Study Workflow Artifact reuse。Observation refresh / evolution 与 workflow 跨 invocation resume / reuse 保持 deferred。

## Acceptance 与 readiness

- 四个 normalized semantic inputs 确定 run identity；expiry window 不被解释为 observation-date window，execution-only overwrite 不进入 identity。
- Request → Universe → materialized complete expiry_plan → 每个 planned chain → complete observation_collection 的 bindings / references 可追踪，无 empirical semantics 回流至 Study。
- 按升序尝试全部 planned expiries；某项失败不跳过、不改写计划、不宣布 complete final success，已完成 Observation 不 rollback。
- 每个 complete collection entry 恰对应一个 plan entry，引用 complete chain identity 与其 observation_date / actual_dte；不复制 chain rows。
- Complete empty Universe → complete empty plan → complete empty collection；非空计划任一 chain 或 output publication 失败，Study 不 complete。
- 输出 counts / identity / retained location 符合 RESULTS，collision / overwrite / staging 符合 UI；所有给下游的 Workflow Artifacts 先物化再消费，无 Analysis / Evidence 占位。

六个 Study semantic areas 已锁定，状态为 **Study Authority Complete**。两个 Observation authority 和 DataLake public capabilities 在语义上已核对，未发现 upstream capability gap；Observation runtime producer / public invocation implementation 尚不存在，因此按 [Authoring readiness](../AUTHORING.md#publication-与-dependency-handoff)，**Dependency Reconciled / Implementation Ready 尚未达到**。可以进入 Observation + Study implementation design，实际 Study implementation 需先补齐 dependencies。状态记录见 [Research reconciliation](../../IMPLEMENTATION_RECONCILIATION.md)。
