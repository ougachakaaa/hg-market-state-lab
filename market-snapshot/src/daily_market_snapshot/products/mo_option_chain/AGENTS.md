# MO Option Chain Agent Rules

本文件细化 [market-snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，再按任务选择 data 或 read authority；HTTP 任务转入 [backend-api contract](../../../../../backend-api/products/mo_option_chain/http-contract.md)。
- `service.py` 拥有 read model；`api/` 只做 transport projection，不得重新计算 domain semantics。
- DTO/OpenAPI 改动属于 `backend-api`；改动后必须在 `web-ui/` 运行 `npm run contract:generate` 并执行 backend API 与 frontend contract checks。
