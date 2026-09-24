# MO Premium Plane 产品 authority

本文档是 MO Premium Plane 的 planned bounded-context 入口，只拥有产品定位、ownership、跨 backend/HTTP/presentation 的稳定 invariant 与 authority 路由。模块边界见 [market-snapshot architecture](../../../../ARCHITECTURE.md)。当前没有 runtime implementation；未来实现必须落在本目录并遵循本 authority。

## 1. 产品定位

`MO Premium Plane` 表示一个 observation anchor 下，由真实 MO 合约 analytical Point 构成的稀疏年化权利金分析平面。

它是独立于 MO Option Chain 的 analytical read product。两者可以复用 backend market facts，但产品语义与 HTTP contract 独立：Premium metrics 不追加到 `/mo-option-chain`，frontend 也不从 Option Chain DTO 自行计算这些 metrics。

本产品使用 sparse plane，不要求不同 expiry 共享 strike universe，也不把真实 Point 强制扩展成矩形 matrix。

## 2. Ownership

| Owner | Canonical knowledge |
| --- | --- |
| 本文档 | 产品身份、产品间边界、跨子契约 invariant |
| [Backend authority](backend.md) | `OptionMarketBasis`、canonical `AnnualizedPremiumPoint`、ObservationAnchor、公式、单位、Preparation、Point completeness、null/zero/absence 与可选 PlaneFramer |
| [HTTP contract](http-contract.md) | resource/query、success projection、sparse-plane wire shape、transport null/absence/zero 与 error/status mapping |
| future web-ui authority | presentation state、Call/Put 与 metric selection、expiry visibility、viewport、formatting、rendering 与 interaction |

HTTP 只能投影 backend 已准备的 analytical facts，不得从 DTO 反向塑造 canonical Point。Frontend 只拥有 presentation，不重新计算 premium metrics。

## 3. Stable Product Invariants

1. Premium Plane 与 MO Option Chain 是两个独立产品和 HTTP contracts。
2. Plane 只包含 backend authority 定义的真实 analytical Point；不得由 transport 或 presentation 创建 synthetic contract、cell 或 interpolation。
3. 不同 expiry 可以拥有不同 strike universe；精确 Point/null/zero/absence 语义由 backend authority 唯一定义，HTTP 只保持其投影。
4. Underlying、futures reference、premium metrics 与 seller-yield denominator 的 domain 角色由 backend authority 唯一定义，HTTP 和 frontend 不 fallback 或替代。
5. HTTP Point 是 delivery projection，不是 canonical backend Point；wire identity、ordering 和 error mapping 由 HTTP contract 拥有。
6. Call/Put、metric、expiry visibility 与 viewport 是 presentation state，不进入 V1 product query。

## 4. Navigation

- 修改 domain Point、ObservationAnchor、market-fact boundary、formula、unit、Preparation、null/zero/absence 或 PlaneFramer → [Backend authority](backend.md)
- 修改 endpoint、query、HTTP DTO projection、wire ordering、transport absence 或 error/status mapping → [HTTP contract](http-contract.md)
- 判断产品独立性、ownership 或 backend/HTTP/presentation 边界 → 本文档

Backend 实现只需本文档与 backend authority；HTTP 实现先读本文档与 HTTP contract，并仅沿其显式引用读取所需 backend semantics。
