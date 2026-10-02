# Expiry DTE Collection runtime workflow authority

本文件拥有 [Study](ARCHITECTURE.md) 的 Observation dependencies、input bindings、runtime step order、complete consumption 与 failure continuation。Request / identity 归 [INPUTS.md](INPUTS.md)，runtime outcome / counts 归 [RESULTS.md](RESULTS.md)，Python composition / handoff 归 [IMPLEMENTATION.md](IMPLEMENTATION.md)。继承 [Workflow contract](../WORKFLOW.md)，无 retained Workflow Artifacts、Analysis 或 Method Context。

## Observation Artifact dependencies

| Local name / purpose | Canonical owner / Artifact contract | Invocation binding / identity |
| --- | --- | --- |
| expiry_universe：取得 observed expiry dates | [Universe entry](../../observations/cffex_option_expiry_universe/ARCHITECTURE.md) / [Artifact](../../observations/cffex_option_expiry_universe/ARTIFACT.md) | Inputs.product_code、expiry_start_date、expiry_end_date → ExpiryUniverseRequest 同名字段；Artifact identity 为该 Observation identity + 三个 normalized inputs。 |
| expiry_chains：每个 planned expiry 的完整 chain | [Chain entry](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md) / [Artifact](../../observations/cffex_option_expiry_dte_chain/ARTIFACT.md) | Inputs.product_code、runtime plan entry.expiry_date、Inputs.target_dte → ExpiryDteChainRequest 同名字段；每项 identity 为该 Observation identity + 三个 business inputs。 |

Only Study orchestration 经 concrete Observation Python public Request / create_service / service.ensure boundary 取得 complete durable Artifacts，具体接口引用 [Universe IMPLEMENTATION](../../observations/cffex_option_expiry_universe/IMPLEMENTATION.md) 与 [Chain IMPLEMENTATION](../../observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md)。不经 CLI JSON、DataLake / Snapshot、Observation SQLite 或旧 Study output 获取事实，不接管 producer derivation。当前 contracts complete，runtime producer 尚未实施，实际 bindings 验证依 IMPLEMENTATION / readiness handoff。

## Canonical workflow steps

1. **ensure_expiry_universe**：绑定 ExpiryUniverseRequest(product_code, expiry_start_date, expiry_end_date)，调用 Universe ensure。只有对应 request 的 complete durable Artifact 才进入下一步；complete hit 由 Observation reuse，failure 立即停止，不执行 chain plan。
2. **build_runtime_expiry_plan**：消费完整 Universe 的全部 sorted unique expiries，在 memory 中构造 ordered `(product_code, expiry_date, target_dte)` invocation plan，一一对应、无过滤 / 额外 / 重复项。不计算 observation_date，不赋予 plan retained Artifact identity，不写文件或 SQLite。
3. **ensure_expiry_chains**：按 plan 升序逐项构造 ExpiryDteChainRequest，调用 chain ensure；每个 planned business request 在本次 invocation 中尝试一次，成功返回即表示该 chain 已由 Observation durable published。某项 failure 保留对应 request 与 readable reason，继续尝试剩余全部 entries，不加入 Study retry loop，不改参数 / 日期、不直接调用 upstream。
4. **completion_summary**：消费实际 attempts / complete returns 的 runtime state，按 RESULTS 形成 non-persistent success / failure outcome。仅所有 planned chains complete 才 success；不 materialize collection / manifest、不复制 market rows、不发布 Study output。

Step names 是本 Study 内稳定的语义引用，不建立 generic executable interface。Runtime plan、ordered Artifact references / values、success / failure state 可以只存在于本次 invocation，用于反馈；不自动成为 Workflow Artifact 或跨 invocation reusable product。

## Empty 与 failure semantics

Complete empty Universe → empty runtime plan → 零 chain invocations → Study success；没有不必要的 chain factory / service access，不人为生成 retained empty plan / collection。

Universe operation / construction failure 停止后续 workflow；runtime plan construction failure 也不进入 chain execution。Chain invocation 的 operation / construction failure 按该 planned request 记录并继续剩余全部项；不存在同一 request 的 Study retry。全部 attempts 完成后，任一 failure 即 Study failure；不能删除失败项、把失败当作 absent expiry 或给出 fake complete collection。Counts / stage / unknown availability 唯一归 RESULTS。

成功的 Universe / chain Artifacts 继续存在于各自 Observation persistence，Study failure 不 rollback、删除或 overwrite 它们。以后同一个或其他 Study 通过 same Observation request 再 ensure 复用，不找旧 run / manifest、不读 SQLite、不自己判断 upstream refresh。没有 Study run-output publication、collision / overwrite 或 cross-invocation workflow resume。

## Analysis boundary

本 Study Analysis=0、Evidence=0，不做 sample selection、PnL、statistics 或 charts。Future Analysis 需独立 semantic decision，只消费 Study orchestration 已准备的 complete Artifacts，不自行 ensure / fetch、不调用 DataLake / Snapshot 或 persistence。本轮不预建 Analysis / Evidence persistence。
