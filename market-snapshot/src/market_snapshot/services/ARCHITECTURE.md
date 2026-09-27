# Shared CLI and persisted delivery authority

本文件是共享 CLI binding、dispatch 与 persisted output delivery 的入口。Product ownership 见 [market-snapshot architecture](../../../ARCHITECTURE.md)，产品语义从 [Capability Catalog](../../../CAPABILITIES.md) 进入。外层 `services/` 不是所有 Product Application Service 的归属目录。

## Ownership

本 context 只拥有 `dms` CLI executable catalog、CLI request parsing/dispatch、CLI-level errors 与共享 persisted output delivery convention。Repository Product/capability discovery 由 [Capability Catalog](../../../CAPABILITIES.md) 拥有；每个 Product 的 semantic identity、application request/result、Capture orchestration、Preparation、public entry 与 classified semantic failure 由对应 Product authority 拥有。HTTP projection 由 [backend-api](../../../../backend-api/ARCHITECTURE.md) 拥有。

必须区分：

```text
repository Product / Capability Catalog → CAPABILITIES.md
Product / Data Service semantic identity → product authority
CLI executable catalog                   → catalog.py / dms
```

“Data Service” 只是可请求的 Product Application Service 角色，不是第二套 Product hierarchy。通过 HTTP 或 Python 暴露的 request-scoped Product service 不因此成为 `dms get`-compatible persisted service；其 public semantic contract 和 HTTP transport 均不由本 context 拥有。

## Navigation

- CLI executable catalog、canonical persisted output 与 delivery 规则：[delivery.md](delivery.md)
- Product request/result/orchestration/public contract：从 [Capability Catalog](../../../CAPABILITIES.md) 进入 owning Product。
