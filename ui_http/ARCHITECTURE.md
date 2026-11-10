# ui_http 模块架构 authority

本文件定义 `ui_http` 的稳定职责、依赖方向与 authority 路由。仓库级模块边界及 analytical flow 见 [repository architecture](../ARCHITECTURE.md)；具体 HTTP product contract 从 [HTTP product catalog](HTTP_PRODUCTS.md) 进入。

## Module identity

The owning module/directory and canonical Python namespace are `ui_http`. Inherit the [repository naming rules](../ARCHITECTURE.md#naming-and-transition-authority). Endpoints, DTOs, OpenAPI wire semantics, status/error projection and owning module public contracts remain unchanged.

## 1. Purpose

`ui_http` 是 repository-wide inbound HTTP delivery adapter 与 HTTP composition root。它把 repository 内各 owning module 的 application/product boundary 暴露为 HTTP，不是 analytical pipeline stage，也不是任何业务模块的子模块。

## 2. Ownership

`ui_http` 拥有：

```text
FastAPI application composition
HTTP route composition
request parsing and transport-level validation
HTTP DTO projection and serialization
HTTP error envelope projection and status mapping
OpenAPI publication
repository HTTP runtime composition
HTTP launcher/runtime concerns
technical identity, authentication persistence and HTTP access control
```

核心 invariant：

```text
HTTP owns transport.
Owning modules own application and product semantics.
```

`ui_http` 不拥有 Source、Capture、Raw Artifact、Analysis Preparation、financial formula、product/modeling semantics、business query or command identity、application result semantics、product availability classification、market interpretation 或 presentation semantics。

## 3. Request and Dependency Direction

```text
HTTP request
    ↓
ui_http transport adaptation
    ↓
owning module application/product boundary
    ↓
application result OR classified semantic failure
    ↓
ui_http HTTP projection
```

`GET`、`POST`、`PUT` 与 `DELETE` 只是 transport。Query、Command、Result 与 semantic failure classification 由 owning module 定义；本模块不引入 CQRS、Command Bus、Query Bus 或 generic application framework。

稳定依赖方向是：

```text
ui_http → data_snapshot application/product boundaries
ui_http → market_modeling application/product boundaries
ui_http → market_research public capabilities / execution / observation / association / case facades
ui_http → market_backtesting public application boundary (W2; HTTP contract authored by WP6)
ui_http → market_statistics root public Specs/results (transport construction/projection only)
```

Research delivery never imports private Research modules or DataLake services/internals.
Research and Statistics never depend on ui_http. Backtesting never depends on ui_http and
does not receive a reverse import permission. Publication delivery uses only the
[Research public reader](../market_research/PUBLICATION.md), not storage internals; reads
never execute Research, acquire facts or recompute statistics.

禁止 `data_snapshot → ui_http`、`market_backtesting → ui_http` 或 `market_modeling → ui_http`。Business modules 不得通过 FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types 定义 semantic model。W2 的 HTTP product contract、DTO 与 catalog entry 由 WP6 创建；本 authority gate 不发布 fake endpoint。

## 4. Composition Boundary

`ui_http` 可以组合多个 owning module 发布的 application boundaries，但不因此成为 Query Layer、Mutation domain 或 business service layer，也不在产品之间创建共享业务 schema。未来模块可以接入同一 HTTP composition root，而无需把 `ui_http` 插入 analytical flow。

本模块只专门拥有 HTTP inbound delivery，不建立“所有 delivery 都必须迁移到 ui_http”的规则。

HTTP access 的 Auth 能力由本模块独立拥有，公开 Python service 允许 canonical `lab auth` 委托 Operator 审批。该 service 不要求启动 HTTP server；它不属于市场产品 application semantics，也不成为跨产品业务层。所有实际 HTTP app surfaces 服从统一认证边界，产品自己的 response projection 与 semantic failure classification 继续独立。

## 5. Authority Routing

Published HTTP products (including agent-facing Research)、endpoint/query、DTO projection、wire ordering、error envelope 与 status mapping 从 [HTTP product catalog](HTTP_PRODUCTS.md) 进入对应 specialized contract。

Repository-wide 用户、审批、JWT Cookie、同源验证、限流、Auth HTTP contract 与 G1–G4 验收由 [Authentication MVP V1 authority](AUTHENTICATION.md) 唯一拥有；它是 access concern，不是市场 HTTP product。Application-level 登录交互归 [Web application authority](../ui_web/application.md)。

Owning module authority 仍唯一拥有 application/product semantics：

- Data Snapshot 产品与 application boundary：[data_snapshot architecture](../data_snapshot/ARCHITECTURE.md)
- Research capability and pure preview: [Research publication](../market_research/descriptive/RESEARCH_CAPABILITY.md)
- Backtesting application/result and online semantics: [W2 Futures Roll Long case authority](../market_backtesting/cases/futures_roll_long/ARCHITECTURE.md)
- Web presentation 与 generated-contract feedback loop：[ui_web architecture](../ui_web/ARCHITECTURE.md)

本文件不复制 endpoint、DTO、Premium metric tree、error table 或 FastAPI implementation 细节。

## 6. Maintenance Boundary

只有 repository HTTP ownership、composition boundary、稳定依赖方向或下层 HTTP authority routing 变化时更新本文件。单个 HTTP product contract 从 catalog 进入；业务语义回到 owning module，presentation 语义回到 `ui_web`。
