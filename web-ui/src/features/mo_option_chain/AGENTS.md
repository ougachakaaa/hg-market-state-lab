# MO Option Chain Frontend Agent Rules

本文件细化 [web-ui rules](../../../AGENTS.md)，适用于本 feature。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入；视觉任务读取 [visualization.md](visualization.md)。
- 本 feature 拥有自己 `api/` 中 committed OpenAPI representation 与 generated TypeScript 的 artifact boundary；它们由 MO Option Chain `backend-api` HTTP contract 发布的 OpenAPI 生成，不与 sibling feature 合并，也不手工维护竞争性 schema。
- 修改后运行相关 Vitest；generated artifact 缺失、相对 backend contract 已 stale，或 backend HTTP DTO/OpenAPI 变化时，还必须运行 `npm run contract:generate` 与覆盖所有 frontend-consumed products 的 `npm run contract:check`。Authority-only 变更不得重写 generated contract。
