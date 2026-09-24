# Shared Data Service authority

本文件是共享 Data Service bounded context 的入口。模块分层见 [market-snapshot architecture](../../../ARCHITECTURE.md)，产品语义从 [Capability Catalog](../../../CAPABILITIES.md) 进入。

## Ownership

本 context 只拥有 shared delivery boundary、CLI executable catalog/request/dispatch、公共失败边界与 persisted output delivery。Repository product/capability discovery 由 [Capability Catalog](../../../CAPABILITIES.md) 拥有；每个 Data Service 的 semantic identity、query/result、Capture orchestration、Preparation、read model 和 HTTP projection 由对应产品 authority 拥有。

必须区分：

```text
repository Product / Capability Catalog → CAPABILITIES.md
Data Service semantic identity          → product authority
CLI executable catalog                  → catalog.py / dms
```

HTTP-only request-scoped service 仍是 Data Service，但不因此成为 `dms get`-compatible persisted service。

## Navigation

- Data Service semantic inventory、CLI executable catalog、canonical persisted output 与 delivery 规则：[delivery.md](delivery.md)
- `csi1000-5d-analysis` orchestration：[CSI1000 product](../products/csi1000_5d_analysis/ARCHITECTURE.md)
- MO Option Chain request-scoped read service：[MO Option Chain product](../products/mo_option_chain/ARCHITECTURE.md)
- MO Premium Plane request-scoped analytical service：[MO Premium Plane product](../products/mo_option_premium/ARCHITECTURE.md)
