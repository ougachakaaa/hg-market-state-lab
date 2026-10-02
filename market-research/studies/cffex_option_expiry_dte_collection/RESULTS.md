# Expiry DTE Collection runtime execution outcome

本文件拥有 [Study](ARCHITECTURE.md) 的 non-persistent runtime result / CLI presentation、counts、success / empty / failure。Step names / attempts 顺序归 [METHOD.md](METHOD.md)，request identity 归 [INPUTS.md](INPUTS.md)，typed Python projection / adapter mapping 归 [IMPLEMENTATION.md](IMPLEMENTATION.md)。Study-local retained Workflow Artifacts=0、Analysis=0、Evidence=0。

## Outcome 与 counts

合法 canonical request 的 runtime result 保留四个 request fields，并表达 status=success / failure 和以下 counts：

| Field | Meaning / availability |
| --- | --- |
| product_code / expiry_start_date / expiry_end_date / target_dte | 本次合法 canonical request context，值与 INPUTS 相同。 |
| discovered_expiry_count | Complete Universe 的 expiries 数；Universe 未成功时 None / unavailable。 |
| planned_observation_count | 成功构建的 runtime plan entries 数，恰等于 discovered_expiry_count；plan 未形成时 None / unavailable。 |
| completed_observation_count | 已返回对应 complete durable chain Artifacts 的计划项数，包括 Observation reuse；chain phase 尚未执行时 0。 |
| failed_observation_count | 已尝试但未取得合法 complete chain Artifact 的计划项数，包括其 construction / operation failure；chain phase 尚未执行时 0。Universe / plan failure 不冒充 chain failure。 |

Successful non-empty outcome 满足 completed_observation_count=planned_observation_count、failed_observation_count=0；全部 chain attempts 完成时 completed+failed=planned，失败项不从 planned 中移除。Complete empty Universe success 的四项 counts 全为 0，chain invocations=0。

None 表达 unavailable，不伪报零。Universe failure 时 discovered / planned=None、completed / failed=0；Universe 已成功但 plan 未形成时 discovered 已知、planned=None、completed / failed=0。Counts 是 runtime execution facts，不是 empirical Artifact、identity 或 persisted audit history。

## Failure details 与 completion

合法 request 的 operation failure result 保留 request context、实际已知 counts 与 ordered failure details：每项有 stage、readable reason，chain failure 另有 expiry_date，由 request context + expiry_date 确定该 planned business request。Stage 使用 METHOD 的 ensure_expiry_universe / build_runtime_expiry_plan / ensure_expiry_chains；非 chain stage 的 expiry_date=None。链失败明细按 planned expiry ascending order，汇总全部实际尝试结果。

Universe / plan failure 立即停止后续阶段；chain phase failure 后仍按 METHOD 尝试剩余全部项，最后返回 failure。Expected Observation errors / 非法或不匹配的 Artifact return 不作 complete return，不把 upstream exception classes 暴露为 Study handling contract。Interruption 不伪造最终成功；不创建 retained partial result / Study DB，已成功 Observation Artifacts 独立保留。

Invalid arguments / semantic request 不进入 workflow，CLI 提供简洁可读输入错误与可用 request context，不要求为无效值制造 canonical runtime result。

## Human-facing presentation

成功仅展示四个 inputs、status 与四项 counts。失败展示 request context、失败 stage、实际 counts（None 显示 unavailable）与每个失败 expiry 的 readable reason；不要求 Python traceback。CLI exit codes 为 success=0、execution failure=1、invalid arguments / request=2，repository CLI 原样传播，不建立跨 Study numeric taxonomy。

本轮不增加 JSON / file delivery、成功逐 expiry listing、Universe / chain identities listing 或 reused / newly-produced counts；后者无法从当前 Artifact ensure return contract可靠地区分，不猜测。内部可持有 ordered complete Artifact references / values 供当前 orchestration 使用，不把它们变成 retained manifest。

Study Results do not persist market rows。没有 retained expiry_plan / observation_collection、semantic Artifact identity、manifest / collection publication、Study SQLite、canonical retained location、run key / directory / staging / overwrite。Reusable empirical persistence 只在 Observations 内；runtime summary 不是新 reusable research product。不输出统计、Evidence / Findings 或推测的尚未运行结果。
