# MO Option Chain Agent Rules

本文件细化 [market-snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，再按任务选择 data 或 read authority；HTTP task 进入 [backend-api HTTP contract](../../../../../backend-api/products/mo_option_chain/http-contract.md)。
- `service.py` 拥有 read model；本 context 不拥有 FastAPI、HTTP DTO 或 OpenAPI，transport implementation 必须留在 `backend-api`，且不得重新计算 domain semantics。
- DTO/OpenAPI 改动后必须按 `backend-api` 与 `web-ui` rules 运行 HTTP API、contract generation 与 frontend contract checks。
