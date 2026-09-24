# MO Option Chain Frontend Agent Rules

本文件细化 [web-ui rules](../../../AGENTS.md)，适用于本 feature。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入；视觉任务读取 [visualization.md](visualization.md)。
- `api/` 的 OpenAPI JSON 与 generated TypeScript 由 backend contract 生成，不手工维护竞争性 schema。
- 修改后运行相关 Vitest；contract 或 DTO 变化还必须运行 `npm run contract:generate` 与 `npm run contract:check`。
