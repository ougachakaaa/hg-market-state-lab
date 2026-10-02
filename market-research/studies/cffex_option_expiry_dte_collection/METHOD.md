# Expiry DTE Collection workflow authority

本文件拥有 [Study](ARCHITECTURE.md) 的 Observation dependencies、input bindings、四步执行顺序、complete consumption 与 failure orchestration。Request 值与 run identity 归 [INPUTS](INPUTS.md)，具名 Artifact shape / retention 与输出归 [RESULTS](RESULTS.md)。继承 [Workflow contract](../WORKFLOW.md)，不存在 Analysis 或 Method Context。

## Observation Artifact dependencies

| Local name / purpose | Canonical owner / Artifact contract | Invocation binding / identity |
| --- | --- | --- |
| expiry_universe：取得 empirical expiry dates | [Universe entry](../../observations/cffex_option_expiry_universe/ARCHITECTURE.md) / [Artifact](../../observations/cffex_option_expiry_universe/ARTIFACT.md) | Inputs.product_code、expiry_start_date、expiry_end_date；Artifact identity 为 Observation identity + 这三个 normalized inputs。 |
| expiry_chains：每个 planned expiry 的完整 chain | [Chain entry](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md) / [Artifact](../../observations/cffex_option_expiry_dte_chain/ARTIFACT.md) | Inputs.product_code、plan entry.expiry_date、Inputs.target_dte；每项 identity 为 chain Observation identity + 这三个 business inputs。 |

Only Study orchestration 经 Observation public boundary resolve / ensure complete Artifacts。上述 bindings 的 Python mapping 见 [Universe IMPLEMENTATION](../../observations/cffex_option_expiry_universe/IMPLEMENTATION.md) 与 [Chain IMPLEMENTATION](../../observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md)：Study orchestration 直接 import concrete Request / create_service，并消费 ensure 返回的 owned Artifact；不改变本文件 workflow。Producer runtime 尚未实现，实际 handoff 前必须 readiness reconciliation。Study 不经 CLI JSON、DataLake / Snapshot 或 persistence 获取这些事实。

## Canonical workflow steps

1. **ensure_expiry_universe**：以 request bindings ensure / resolve complete Universe Artifact。只有 complete Artifact 才进入下一步，complete hit 按 Observation contract 复用。
2. **materialize_expiry_plan**：消费 complete Universe 和 request，按 Universe 升序 dates 生成一一对应的 chain invocation entries。物化 [expiry_plan](RESULTS.md#expiry_plan) 为 complete，再供 STEP 3 消费。Plan 不计算 observation_date。
3. **ensure_expiry_chains**：消费 complete plan，按 entries 顺序逐一 invocation chain，每项在本次 workflow 中调用一次，不增加 Study retry loop。某项失败记录该项 operational failure，继续尝试剩余全部 planned entries；不能删除该项、缩小计划、改参数或跳日重试。Complete returns 可来自 Observation reuse。
4. **materialize_observation_collection**：仅所有 planned chain Artifacts complete 后，消费 plan 和 complete chain returns，物化 [observation_collection](RESULTS.md#observation_collection)。每项引用原 chain identity，并从该 Artifact 读取 observation_date / actual_dte，不重新计算、不复制 market rows。成功后按 UI contract 发布整个 run output；发布成功才是 Study completion。

步骤 names 是当前 Study 内的稳定语义引用，不建立通用 executable step interface。Workflow Artifacts 在所属 run staging workspace 中先物化再被下游消费，成功后保留于 canonical run output。

## Empty 与 failure semantics

Complete empty Universe 产生 complete empty plan；STEP 3 零 invocations，STEP 4 complete empty collection。Empty 不是统计 finding 或失败。

Universe failure 不生成 complete plan；plan materialization failure 不进入 chain execution。STEP 3 任一 chain failure 即使其他项成功，也不能生成 / 发布 complete final collection。STEP 4 materialization 或 run-output publication failure 同样不 complete。Internal partial / failed state 可以存在，不作为 complete input 或 final output。

已成功 Observation Artifacts 持续独立存在，不因 Study failure 或 staging output failure rollback；不授予跨 invocation Workflow Artifact resume / reuse。Counts 的 availability / presentation 归 RESULTS；Study output collision 在任何 workflow / Observation invocation 前由 UI contract 处理。

## Analysis boundary

本 Study Analysis=0、Evidence=0，不做 sample selection、收益、PnL、statistics 或 charts。未来若新增 Analysis，须独立 semantic decision；其输入只能是 workflow 已准备的 complete Artifacts，不得自行调用 Observation / DataLake / Snapshot 或 persistence。本轮不为它预建 abstraction。
