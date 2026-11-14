# MO Option Chain Agent Rules

本文件细化 [data_snapshot rules](../../../../AGENTS.md)，适用于本 context。

- 从 [ARCHITECTURE.md](ARCHITECTURE.md) 进入，再按任务选择 data 或 read authority；HTTP task 进入 [ui_http HTTP contract](../../../../../ui_http/products/mo_option_chain/http-contract.md)。
- `service.py` 拥有 read model；本 context 不拥有 FastAPI、HTTP DTO 或 OpenAPI，transport implementation 必须留在 `ui_http`，且不得重新计算 domain semantics。
- DTO/OpenAPI 改动后必须按 `ui_http` 与 `ui_web` rules 运行 HTTP API、contract generation 与 frontend contract checks。

## Verification scope override

The [root verification policy](../../../../../AGENTS.md#verification-policy-user-decision-2026-11-14) governs execution.
Only directly changed behavior gets targeted tests; full/system/browser/platform checks
are manual only. Earlier verification examples are not mandatory task gates.
