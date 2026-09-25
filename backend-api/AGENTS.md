# backend-api Agent Rules

## 适用范围

本文件适用于 `backend-api/` 整棵目录，并在根 [../AGENTS.md](../AGENTS.md) 之上提供模块级执行规则。

## 最小 Authority 路径

1. 先读 [ARCHITECTURE.md](ARCHITECTURE.md)，确认 HTTP transport ownership、composition boundary 与 owning-module dependency direction。
2. 通过 [HTTP_PRODUCTS.md](HTTP_PRODUCTS.md) 选择具体 HTTP product contract。
3. 只在 contract 明确引用时进入 owning business module 的 product/application authority；HTTP 任务不默认读取 Source、Raw 或无关 product authority。

## 执行规则

- HTTP 只解析与校验 transport input，调用 owning module 的 public application/product boundary，再投影 result 或 classified failure。
- 不在 router、DTO、error mapper 或 OpenAPI 中发明 Query/Command identity、产品可用性、金融公式、建模或 presentation 语义。
- HTTP contract 变更必须同时检查 owning-module semantics 与 [web-ui contract feedback loop](../web-ui/contracts.md)；仅 authority relocation 不得重生成 OpenAPI 或 TypeScript。
- 当前 FastAPI 实现、launcher 与 dependencies 仍在 `market-snapshot` 内，这是已知 implementation drift，不改变本模块的 canonical ownership。

## 验证

变更 authority 时至少验证 repository Markdown links、root reachability、无重复 HTTP canonical contract，以及受影响 product 的 wire semantics 未被意外改写。
