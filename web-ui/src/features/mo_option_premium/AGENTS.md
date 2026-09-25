# MO Premium Plane Frontend Agent Rules

本文件细化 [web-ui rules](../../../AGENTS.md)，适用于本 feature。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入；展示或交互任务读取 [visualization.md](visualization.md)。
- 只通过 `backend-api` Premium Plane HTTP contract 与 generated client types 消费 backend；本 feature 拥有自己 `api/` 中 committed OpenAPI representation 与 generated TypeScript 的 artifact boundary，不得与 MO Option Chain contract 合并、消费其 DTO 或手工维护竞争性的 response schema。
- 不读取 Source、Raw、Preparation 或 orchestration internals，除非当前 authority 明确要求 reconciliation。
- 修改后运行相关验证；generated artifact 缺失、相对 backend contract 已 stale，或 backend HTTP DTO/OpenAPI 变化时，必须运行 `npm run contract:generate` 与覆盖所有 frontend-consumed products 的 `npm run contract:check`，并提交本 feature 的 generated artifacts。Authority-only 变更不得重写 generated contract。
