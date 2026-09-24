# MO Premium Plane Frontend Agent Rules

本文件细化 [web-ui rules](../../../AGENTS.md)，适用于本 feature。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入；展示或交互任务读取 [visualization.md](visualization.md)。
- 只通过 Premium Plane HTTP contract 与 generated client types 消费 backend；不得消费 MO Option Chain DTO 或手工维护竞争性的 response schema。
- 不读取 Source、Raw、Preparation 或 orchestration internals，除非当前 authority 明确要求 reconciliation。
- 修改后运行相关验证；只有 backend HTTP DTO/OpenAPI 变化才运行并提交 contract generation。本 feature 的 authority-only 变更不得重写 generated contract。
