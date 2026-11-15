# ui_http Agent Rules

## 适用范围

本文件适用于 `ui_http/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 HTTP inbound delivery、composition root 与 owning module application boundary 的关系。
2. 通过 [HTTP product catalog](HTTP_PRODUCTS.md) 进入当前 HTTP product contract。
3. 只有 contract 明确依赖业务语义时，才沿链接读取 owning module 的 product、read、backend 或 service authority；不要默认读取 sibling product。
4. Frontend contract 或 presentation reconciliation 再进入 `ui_web/` authority。

## 执行规则

- `ui_http` 拥有 HTTP transport、FastAPI composition、DTO projection、serialization、HTTP error/status mapping、OpenAPI publication 与 HTTP runtime concerns；Repository HTTP access 的技术身份、独立认证存储和 Operator 审批 service 是明确的 runtime specialization，遵循 [Authentication authority](AUTHENTICATION.md)，不扩展为市场业务 service。
- Query、Command、Result、semantic failure classification 与产品可用性由 owning business module 定义；不得在 transport 中重算、修复或重新分类。
- 不引入 CQRS、Command Bus、Query Bus、generic application framework 或跨产品 business service layer。
- FastAPI implementation、HTTP product adapters 与 launcher 位于本模块；不得在 owning business module 中恢复 competing runtime。
- HTTP DTO 或 OpenAPI 发生变化时，必须按 [ui_web rules](../ui_web/AGENTS.md) 执行 generated-contract feedback-loop；authority relocation 本身不得重写 generated artifacts。

## Scoped verification

Follow the [root verification policy](../AGENTS.md#verification-policy-user-decision-2026-11-14).
Select only directly affected business test files/cases. No default full-module or
cross-module regression, topology, browser, live-data or deployment acceptance.
Retain business invariants and fixtures; record unavailable checks as NOT VERIFIED.
Do not modify real market data or caches to satisfy tests.
