# Expiry DTE Collection retained workflow results

本文件拥有 [Study](ARCHITECTURE.md) 的两个 named Study-local Workflow Artifact semantic contracts、provenance、completeness、retention 与 human output。Producer steps 与 consumption order 归 [METHOD](METHOD.md)，run identity 归 [INPUTS](INPUTS.md)；继承 [Workflow Artifact boundary](../WORKFLOW.md)。Analysis=0、Evidence Product=0，以下产物不是 Evidence。

## expiry_plan

Stable local name 为 `expiry_plan`，identity 为 Study identity + Study run identity + local name，由 METHOD STEP 2 物化。

至少保留 product_code、inclusive expiry window、target_dte、source complete Universe Artifact semantic identity，以及 ordered planned entries。每项包含 expiry_date，并明确完整 chain business inputs `(product_code, expiry_date, target_dte)`；Observation identity 指向 cffex_option_expiry_dte_chain。

Plan entries 恰对应 source Universe 的全部 sorted unique expiries，顺序一致，无过滤、额外或重复 entry。Complete 要求 source Universe complete、request context 一致、bindings 完整正确且已 materialized；empty source 对应 complete empty plan。Plan 不含 observation_date / actual_dte，不创造 empirical facts。

## observation_collection

Stable local name 为 `observation_collection`，identity 为 Study identity + Study run identity + local name，由 METHOD STEP 4 物化。它是 complete Observation Artifact manifest / composition Artifact，不是第二份 market-data copy。

至少保留 request context、source complete expiry_plan identity 和 ordered collection entries。每项能够定位 expiry_date、target_dte、chain Artifact semantic identity、该 complete chain 的 observation_date / actual_dte，以及 completion status=complete。Product 在 request context 与 chain business identity 中明确；不使用 SQLite path 或任意 execution ID 替代 semantic identity。

Complete 条件为 source Universe 与 plan complete、全部 planned chain Artifacts complete、entries 对 plan 一一完整引用、顺序一致、request / chain identities 一致、derived facts 原样来自各 complete chain，以及 collection 已 materialized。没有 missing、failed 或 partial entries 的 complete collection；complete empty plan 对应 complete empty collection。不复制 option-chain rows。

## Retention、publication 与 provenance

两个 Workflow Artifacts 属于同一个 deterministic Study run，在下游消费前先写所属 run staging workspace，成功后随整个 canonical run directory 发布。Placement、collision-before-execution、显式 overwrite、整目录 staging / replacement 与失败恢复旧输出遵守 [Research UI](../../ui/ARCHITECTURE.md#3-shared-configuration-and-output-placement)。

失败不发布 complete final run output；partial / failed internal state 不构成 retained complete result，本轮不定义额外 partial-output publication、failure-output protocol、跨 invocation resume / reuse 或 Workflow Artifact cache。已成功 Observation Artifacts 保留在其独立 boundary，Study output replacement 不管理它们。

Request / run identity、source Universe identity、plan identity、each chain identity 构成可追踪的 public provenance graph。Location 只定位 retained representation，不取代 semantic identity；serialization、filenames 与 run-key encoding 留给 design，不引入 database / global IDs。

## Human-facing output 与 counts

未来成功 / 失败 presentation 至少表达 product、expiry window、target DTE 与以下 operational counts；它们不参与 run identity：

| Field | Meaning / availability |
| --- | --- |
| discovered expiry count | complete Universe 的 expiries 数；Universe 未完成时不可用。 |
| planned observation count | complete plan entries 数；plan 未形成时不可用。 |
| completed observation count | 本次 STEP 3 已返回的 complete chain Artifacts 数，包括 reused；STEP 3 尚未执行时为 0。 |
| failed count | 本次 STEP 3 已尝试但未取得 complete Artifact 的 plan entries 数；STEP 3 尚未执行时为 0。独立说明 Universe / plan / output failure，不把它们冒充 chain failure。 |

STEP 3 结束并已尝试全部计划项时 completed+failed=planned；失败项不从 planned 中移除。Empty successful run 的四项 count 均为 0。提前失败的 unknown discovered / planned count 表达为不可用，不伪报零或最终成功。

成功必须同时给出 complete final collection semantic identity 与 canonical retained location。失败只报告实际执行状态与可读原因，不呈现 complete collection 或成功 retained location；任何 output publication failure 都是 Study failure，即使 chain failure count=0。Reused / newly-created counts 可作 operational presentation，不是 identity 或 empirical result。

不输出 mean return、win rate、distribution、chart、hypothesis result 或 Evidence / Findings。不把尚未运行状态写为已有结果，不伪造 counts。
