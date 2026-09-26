# backend-api Agent Rules

## 适用范围

本文件适用于 `backend-api/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 HTTP inbound delivery、composition root 与 owning module application boundary 的关系。
2. 通过 [HTTP product catalog](HTTP_PRODUCTS.md) 进入当前 HTTP product contract。
3. 只有 contract 明确依赖业务语义时，才沿链接读取 owning module 的 product、read、backend 或 service authority；不要默认读取 sibling product。
4. Frontend contract 或 presentation reconciliation 再进入 `web-ui/` authority。

## 执行规则

- `backend-api` 只拥有 HTTP transport、FastAPI composition、DTO projection、serialization、HTTP error/status mapping、OpenAPI publication 与 HTTP runtime concerns。
- Query、Command、Result、semantic failure classification 与产品可用性由 owning business module 定义；不得在 transport 中重算、修复或重新分类。
- 不引入 CQRS、Command Bus、Query Bus、generic application framework 或跨产品 business service layer。
- FastAPI implementation、HTTP product adapters 与 launcher 位于本模块；不得在 owning business module 中恢复 competing runtime。
- HTTP DTO 或 OpenAPI 发生变化时，必须按 [web-ui rules](../web-ui/AGENTS.md) 执行 generated-contract feedback-loop；authority relocation 本身不得重写 generated artifacts。

## 验证

- 检查根 authority 能经本模块 architecture 与 catalog 到达所有 HTTP contracts。
- 检查所有 Markdown 相对链接、旧 canonical contract 路径与重复 authority。
- 若 wire contract 未改变，不生成 OpenAPI 或 TypeScript；提交前运行 `git diff --check` 并审阅完整 diff。
