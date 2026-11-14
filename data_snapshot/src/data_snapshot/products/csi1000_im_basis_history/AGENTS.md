# CSI1000 IM Basis History Agent Rules

本文件细化 [data_snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，只按任务读取 [data.md](data.md) 或 [read-contract.md](read-contract.md)。
- IM Product 专属 scope 与兼容说明见 [产品内兼容 authority](im-basis-semantics.md)；共用 family、slot、remaining days、basis formula 与 ordering 由 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md) 唯一定义。
- Research consumer 只能使用本产品的 public application result，不得暴露 Raw、Preparation implementation 或 persistence layout。
- 修改后运行 authority link/topology test 与 `git diff --check`；实现阶段再增加产品直接测试。

## Verification scope override

The [root verification policy](../../../../../AGENTS.md#verification-policy-user-decision-2026-11-14) governs execution.
Only directly changed behavior gets targeted tests; full/system/browser/platform checks
are manual only. Earlier verification examples are not mandatory task gates.
