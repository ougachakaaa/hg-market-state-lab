# backend-api 模块架构 authority

本文件定义 `backend-api` 的稳定职责、依赖方向与 authority 路由。仓库级定位见 [../ARCHITECTURE.md](../ARCHITECTURE.md)；具体 HTTP product 从 [HTTP_PRODUCTS.md](HTTP_PRODUCTS.md) 进入。

## 1. Purpose

`backend-api` 是 repository-wide inbound HTTP delivery adapter 和 HTTP composition root。它把仓库内 owning module 已定义的 application/product boundary 暴露为 HTTP，不是 analytical pipeline stage、Query domain、Mutation domain 或 business service layer。

## 2. Ownership

`backend-api` 拥有：

```text
FastAPI application composition
HTTP route composition
request parsing and transport-level validation
HTTP DTO projection and serialization
HTTP error envelope projection and status mapping
OpenAPI publication
repository HTTP runtime composition and launcher concerns
```

`backend-api` 不拥有：

```text
Source / Capture / Raw Artifact / Analysis Preparation semantics
financial formulas or market product semantics
modeling or market interpretation
business Query / Command identity
application Result or semantic Failure classification
product availability classification
presentation semantics
```

核心 invariant：

```text
HTTP owns transport.
Owning modules own application and product semantics.
```

GET、POST、PUT 与 DELETE 只是 transport choices，不将业务操作所有权转移给 `backend-api`。本模块不引入 CQRS、Command Bus、Query Bus 或 generic application framework。

当前 authority 不预先设计多租户、通用 endpoint、auth、API versioning、schema registry 或 deployment topology。

## 3. Dependency Direction

```text
HTTP request
    ↓
backend-api transport adaptation
    ↓
owning module public application/product boundary
    ↓
application result OR classified semantic failure
    ↓
backend-api HTTP projection
```

`backend-api` 可依赖 `market-snapshot`、`market-modeling` 与 future owning modules 的 public application boundaries。业务模块不得反向依赖 FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types 来定义 semantic model。

## 4. Authority Routing

```text
ARCHITECTURE.md
    ↓ stable transport boundary and dependency direction
HTTP_PRODUCTS.md
    ↓ HTTP product discovery only
product HTTP contract
    ↓ endpoint, query, DTO, serialization and status mapping
owning module application/product authority
    ↓ business identity, result and classified failure semantics
implementation
```

当前 FastAPI 代码、OpenAPI exporter、dependencies 与 launcher 仍位于 `market-snapshot` 的历史实现布局中。这是待后续 migration 处理的 implementation drift，不会把 canonical HTTP ownership 转回 `market-snapshot`。

## 5. 维护边界

只在 repository HTTP transport 职责、composition boundary、dependency direction 或下层 authority routing 变化时更新本文件。单个 endpoint、DTO 或 status mapping 进入对应 product HTTP contract；业务结果和 failure classification 始终进入 owning module authority。
