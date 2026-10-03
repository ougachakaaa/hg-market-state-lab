# Expiry DTE Collection runtime workflow authority

本文件拥有 [Study](ARCHITECTURE.md) 的 Component / Observation dependencies、bindings、step order、complete consumption 与 failure continuation。Request 归 [INPUTS](INPUTS.md)，outcome / counts 归 [RESULTS](RESULTS.md)，composition handoff 归 [IMPLEMENTATION](IMPLEMENTATION.md)。继承 [Workflow contract](../WORKFLOW.md)，无 retained Workflow Artifacts、Analysis 或 Method Context。

## Research dependencies

| Local name / purpose | Canonical owner / contract | Binding / result |
| --- | --- | --- |
| expiry_universe：resolve observed expiry dates | [Shared resolver entry](../../shared/cffex_option_expiry_universe/ARCHITECTURE.md) / [I/O contract](../../shared/cffex_option_expiry_universe/CONTRACT.md) | Inputs.product_code、expiry_start_date、expiry_end_date 原样绑定同名 inputs；取得对应请求的 complete component result，无 Observation business key / Artifact identity / durable publication。 |
| expiry_chains：每个 planned expiry 的 retained chain | [Chain entry](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md) / [Artifact](../../observations/cffex_option_expiry_dte_chain/ARTIFACT.md) / [public implementation](../../observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md) | Inputs.product_code、runtime plan expiry_date、Inputs.target_dte → ExpiryDteChainRequest 同名字段；Artifact identity 为 Observation identity + 三个 business inputs。 |

Only Study orchestration 调用 resolver public I/O / chain public ensure，分别取得 complete result / durable Artifact。不经 CLI JSON、DataLake / Snapshot、SQLite 或旧 Study output 获取事实，不接管 derivation。Contracts complete；现有 wiring 已 reconciliation 为 resolver + chain Observation，见 [当前验证](../../../../IMPLEMENTATION_RECONCILIATION.md#shared-component-runtime-reconciliation)。

## Canonical workflow steps

1. **resolve_expiry_universe**：原样绑定三个 inputs，调用 shared resolver。只有对应请求的合法 complete result 才进入下一步；无 research cache lookup / durable-hit。Resolver construction / operation failure 立即停止，零 chain execution。
2. **build_runtime_expiry_plan**：消费 result 全部 sorted unique expiries，在 memory 中构造 ordered `(product_code, expiry_date, target_dte)` plan，一一对应、无过滤 / 额外 / 重复项。不计算 observation_date、不赋予 plan retained identity、不写文件或 SQLite。
3. **ensure_expiry_chains**：按 plan 升序逐项构造 ExpiryDteChainRequest、调用 ensure。每个 planned request 本次尝试一次，successful return 表示 chain durable published。某项 construction / operation failure 保留对应 request / readable reason，继续剩余全部 entries；无 retry、不改参数 / 日期、不直接调用 upstream。
4. **completion_summary**：按 RESULTS 形成 non-persistent outcome。仅所有 planned chains complete 才 success；不 materialize collection / manifest、不复制 market rows、不发布 Study output。

Step names 是 Study-local 语义引用，不建立 generic executable interface。Resolver result、plan、Artifact references / values 与 failure summaries 不自动成为 retained products。

## Empty、failure 与 repeated invocation

Complete empty Universe result → empty plan → 零 chain invocations → success；无不必要的 chain factory / service access、不生成 retained empty plan / collection。

Resolver / plan failure 停止后续 workflow；chain failure 后继续全部项，完成 attempts 后任一 failure 即 Study failure。不能删失败项、当作 absent expiry 或 fake complete collection；counts / unknown availability 归 RESULTS。

已成功 chain Artifacts 留在该 Observation persistence，Study failure 不 rollback、删除或 overwrite。再次运行仍 resolve Universe，DataLake 自己管理 cache reuse；同一 chain request 再 ensure 可 durable reuse。整个 Study 不承诺重复 invocation 零 upstream calls，不寻找旧 Universe Artifact / run / manifest，不迁移旧 state 或自行 refresh。无 Study cache、run-output publication 或 workflow resume。

## Analysis boundary

Analysis=0、Evidence=0，不做 sample selection / PnL / statistics / charts。Future Analysis 需独立 semantic decision，只计算已准备的 complete inputs，可调用 pure component，不自行 ensure / fetch、调用 reader / resolver、DataLake / Snapshot 或 persistence。本轮不预建 Analysis / Evidence persistence。
