# CSI1000 IM Basis History Agent Rules

本文件细化 [market-snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，只按任务读取 [data.md](data.md) 或 [read-contract.md](read-contract.md)。
- IM slot、remaining days 与 basis formula 只引用 [shared IM basis authority](../../preparation/im_basis/ARCHITECTURE.md)，不在本产品创建平行定义。
- Research consumer 只能使用本产品的 public application result，不得暴露 Raw、Preparation implementation 或 persistence layout。
- 修改后运行 authority link/topology test 与 `git diff --check`；实现阶段再增加产品直接测试。
