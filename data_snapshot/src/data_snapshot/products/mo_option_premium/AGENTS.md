# MO Premium Plane Agent Rules

本文件细化 [data_snapshot rules](../../../../AGENTS.md)，适用于本 bounded context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入：data task 读 `data.md`，analytical/domain task 读 `backend.md`，service/orchestration task 读 `service-contract.md`，HTTP task 读 [ui_http HTTP contract](../../../../../ui_http/products/mo_option_premium/http-contract.md)。
- Premium product/application implementation 必须留在本 bounded context，且不得依赖 sibling product Raw、read DTO 或 final artifact；本 context 不拥有 FastAPI、HTTP DTO 或 OpenAPI，HTTP transport implementation 的 canonical owner 是 `ui_http`。
- HTTP 只投影完整 product result，不得重算、修复或发明 analytical semantics。
