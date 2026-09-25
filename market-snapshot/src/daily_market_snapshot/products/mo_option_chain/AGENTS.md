# MO Option Chain Agent Rules

本文件细化 [market-snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，再按任务选择 data、read 或 HTTP authority。
- `service.py` 拥有 read model；`api/` 只做 transport projection，不得重新计算 domain semantics。
- DTO/OpenAPI 改动后必须在 `web-ui/` 运行 `npm run contract:generate` 并执行 backend API 与 frontend contract checks。
