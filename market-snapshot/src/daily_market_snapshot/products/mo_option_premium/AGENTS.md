# MO Premium Plane Agent Rules

本文件细化 [market-snapshot rules](../../../../AGENTS.md)，适用于本 bounded context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入：data task 读 `data.md`，analytical/domain task 读 `backend.md`，service/orchestration task 读 `service-contract.md`，HTTP task 转入 [backend-api contract](../../../../../backend-api/products/mo_option_premium/http-contract.md)。
- implementation 必须留在本 bounded context；不得依赖 sibling product Raw、read DTO 或 final artifact。
- HTTP 只投影完整 product result，不得重算、修复或发明 analytical semantics。
