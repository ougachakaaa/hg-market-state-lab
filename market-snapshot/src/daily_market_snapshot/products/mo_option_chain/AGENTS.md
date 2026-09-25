# MO Option Chain Agent Rules

本文件细化 [market-snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，再按任务选择 data 或 read authority；HTTP task 进入 [backend-api HTTP contract](../../../../../backend-api/products/mo_option_chain/http-contract.md)。
- `service.py` 拥有 read model；当前仍位于本 context 的 `api/` 是待迁移 transport implementation，只做 projection，不得重新计算 domain semantics。
- DTO/OpenAPI 改动后必须按 `backend-api` 与 `web-ui` rules 运行 HTTP API、contract generation 与 frontend contract checks。
