# MO Premium Plane 产品 authority

本文档是 MO Premium Plane 的 bounded-context 入口，只拥有产品定位、ownership、跨 data/backend/service/HTTP/presentation 的稳定 invariant 与 authority 路由。模块边界见 [data_snapshot architecture](../../../../ARCHITECTURE.md)。

## 1. 产品定位

`MO Premium Plane` 表示一个 observation anchor 下，由真实 MO 合约 analytical Point 构成的稀疏多维权利金分析平面。

它是独立于 MO Option Chain 的 analytical read product。两者可以复用 backend market facts，但产品语义与 HTTP contract 独立：Premium metrics 不追加到 `/mo-option-chain`，frontend 也不从 Option Chain DTO 自行计算这些 metrics。

本产品使用 sparse plane，不要求不同 expiry 共享 strike universe，也不把真实 Point 强制扩展成矩形 matrix。

## 2. Ownership

| Owner | Canonical knowledge |
| --- | --- |
| 本文档 | 产品身份、产品间边界、跨子契约 invariant |
| [Shared Source Capture authority](../../capture/ARCHITECTURE.md) | Capture identity、Source endpoint、公共 Source 字段与 minimal normalization |
| [Data authority](data.md) | Premium Source requirements、Capture scope、goal-scoped Raw、active universe、Raw completeness 与 canonical observation availability evidence |
| [Backend authority](backend.md) | `OptionMarketBasis` construction、canonical `PremiumPoint`、ObservationAnchor、四维 metric space、公式、单位、Preparation、null/zero/absence 与 PlaneFramer |
| [Product service authority](service-contract.md) | request orchestration、observation admission、semantic failure classification/propagation 与 result boundary |
| [ui_http HTTP contract](../../../../../ui_http/products/mo_option_premium/http-contract.md) | resource/query、success projection、sparse-plane wire shape、transport null/absence/zero 与 error/status mapping |
| [Web visualization authority](../../../../../ui_web/src/features/mo_option_premium/ARCHITECTURE.md) | presentation state、Call/Put 与 metric selection、expiry visibility、full-strike table projection、reference-relative coloring、formatting、rendering 与 interaction |

共享 Capture capability 不等于共享 goal-scoped Raw Artifact。Product service 只编排各 canonical stage；HTTP 只能投影完整 service result，不得从 DTO 反向塑造 canonical Point。Frontend 只拥有 presentation，不重新计算 premium metrics。

Premium-owned persisted Raw 是本产品选择的 Capture/Preparation 契约，request-scoped final Plane 无须持久化。Product service 即本产品的 Application Service；其 request、orchestration、result 与 classified failure 由本产品拥有。

本产品拥有 `mo-option-premium` Raw 命名空间及 `data/raw/mo-option-premium/<as_of>/` 的按目标组织路径语义；具体 Raw 文件与 completeness 仍由 [data authority](data.md) 定义。共享 artifact 基础设施仅提供通用 Raw root、文件系统与 JSON 读写机制，不定义本产品的 Raw 身份或路径。

## 3. Stable Product Invariants

1. Premium Plane 与 MO Option Chain 是两个独立产品和 HTTP contracts。
2. Plane 只包含 backend authority 定义的真实 analytical Point；不得由 transport 或 presentation 创建 synthetic contract、cell 或 interpolation。
3. 不同 expiry 可以拥有不同 strike universe；精确 Point/null/zero/absence 语义由 backend authority 唯一定义，HTTP 只保持其投影。
4. Premium metrics 是 `reference_basis × value_basis × time_normalization × representation` 四维固定空间；underlying spot、same-expiry futures、reference-relative decomposition 与 selected-reference-notional yield denominator 的 domain 角色由 backend authority 唯一定义。HTTP 只投影、frontend 只选择与展示，不计算、fallback、修复或替代。
5. HTTP Point 是 delivery projection，不是 canonical backend Point；wire identity、ordering 和 classified product failure mapping 由 HTTP contract 拥有，availability detection 与 failure classification 不属于 HTTP。
6. Call/Put、四个 metric selections 与 expiry visibility 是 presentation state，不进入 V1 product query；四个 metric axes 共同选择 backend 已准备的一个 coordinate，不构成 frontend calculation。table rows 展示所选 side 与 expiries 下全部真实 Point strikes，不拥有 strike display range。
7. Premium 拥有自己的 Raw、Basis construction 与 product orchestration，不消费 sibling product 的 Raw、read DTO 或 final artifact。
8. 成功 product result 是 request-scoped `PremiumPlane`；V1 不要求 canonical persisted final output。`annualized` 只是 time-normalization value，不定义 Point 或 Plane identity。

## 4. Navigation

- 修改共享 Source fact 或 Capture identity → [Shared Source Capture authority](../../capture/ARCHITECTURE.md)
- 修改 Premium Source requirements、Capture scope、Raw、universe、daily completeness 或 observation availability → [Data authority](data.md)
- 修改 Basis construction、domain Point、ObservationAnchor、formula、unit、Preparation、null/zero/absence 或 PlaneFramer → [Backend authority](backend.md)
- 修改 request orchestration、stage responsibility、product result 或 semantic failure propagation → [Product service authority](service-contract.md)
- 修改 endpoint、query、HTTP DTO projection、wire ordering、transport absence 或 error/status mapping → [ui_http HTTP contract](../../../../../ui_http/products/mo_option_premium/http-contract.md)
- 修改用户可见展示或交互 → [Web visualization authority](../../../../../ui_web/src/features/mo_option_premium/ARCHITECTURE.md)
- 判断产品独立性、ownership 或跨 data/backend/service/HTTP/presentation 边界 → 本文档

只读取当前任务所需分支。Backend implementation 从本文档进入 data/backend/service authority；HTTP implementation 从本文档进入 service 与 HTTP contract，并仅沿显式引用读取所需 semantics。

## 5. Authority Chain

```text
Tushare Source
        ↓
shared Source Capture
        ↓
Premium-owned goal-scoped Raw
        ↓
OptionMarketBasis construction
        ↓
PremiumPoint Preparation
        ↓
PremiumPoint[]
        ↓
PremiumPlaneFramer
        ↓
request-scoped PremiumPlane
        ↓
Premium product service result
        ↓
public application boundary
        ↓
ui_http HTTP delivery adapter
        ↓
GET /mo-option-premium-plane
```

依赖方向只能向下；HTTP、presentation 或 sibling product 不得反向定义 Source scope、Raw、Basis、Point 或 Plane semantics。
