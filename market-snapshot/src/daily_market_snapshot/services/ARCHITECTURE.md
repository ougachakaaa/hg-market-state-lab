# Shared Data Service authority

本文件是共享 Data Service bounded context 的入口。模块分层见 [market-snapshot architecture](../../../ARCHITECTURE.md)，产品语义从 [Capability Catalog](../../../CAPABILITIES.md) 进入。

## Ownership

本 context 只拥有静态 Data Service catalog、CLI request/dispatch、公共失败边界与 persisted output delivery。每个产品拥有自己的 Capture orchestration、Preparation、read model 和 HTTP projection。

## Navigation

- CLI、catalog、canonical persisted output 与 delivery 规则：[delivery.md](delivery.md)
- `csi1000-5d-analysis` orchestration：[CSI1000 product](../products/csi1000_5d_analysis/ARCHITECTURE.md)
- MO Option Chain request-scoped read service：[MO Option Chain product](../products/mo_option_chain/ARCHITECTURE.md)
- MO Premium Plane request-scoped analytical service：[MO Premium Plane product](../products/mo_option_premium/ARCHITECTURE.md)
