# guides/mo-option-premium.md — MO Premium Plane 产品 authority（导航入口）

> 状态：authority。本文档锁定 `MO Premium Plane` 的产品定位、ownership、稳定 invariants 与 progressive-disclosure 导航。
>
> 层级：本文档位于 `market-snapshot/ARCHITECTURE.md` 之下。backend semantic core 见 `guides/mo-option-premium-backend.md`；HTTP transport 见 `guides/mo-option-premium-http-contract.md`。本文档只负责产品级边界，不重复两份 specialized authority。
>
> 本轮是 authority-only：没有新增 Data Service、backend domain class、FastAPI route、Pydantic DTO、OpenAPI、generated TypeScript 或 frontend renderer。

---

## 1. 产品定位

`MO Premium Plane` 表示：

> 一个 observation anchor 下，由真实 MO 合约分析 Point 构成的稀疏年化权利金分析平面。

它是独立于 `MO Option Chain` 的分析型 read product：

```text
MO Option Chain
= market-chain read product

MO Premium Plane
= annualized-premium analytical read product
```

二者未来可以在 backend 内部复用事实，但产品语义与 HTTP contract 独立。不得把 Premium Plane 指标追加到 `/mo-option-chain`，也不得要求 frontend 从 Option Chain DTO 自行计算 Premium Plane。

本产品使用 `plane`，不使用 `matrix`：真实 Point 可以在不同 expiry 拥有不同 strike universe，不要求形成矩形网格。

## 2. Ownership

### Backend analytical authority owns

```text
canonical AnnualizedPremiumPoint
ObservationAnchor 的完整 domain 语义
annualized premium formulas and units
Point Preparation
Point completeness and metric consistency
optional PlaneFramer
legitimate futures-reference selection
```

具体语义见 `guides/mo-option-premium-backend.md`。HTTP authority 只能 transport 已准备好的 analytical facts，不得反向塑造 canonical backend domain model。

### HTTP delivery owns

```text
resource and endpoint semantics
query serialization
success response projection
sparse-plane wire representation
null / absence / zero transport semantics
HTTP error representation and status mapping
```

具体契约见 `guides/mo-option-premium-http-contract.md`。

### web-ui owns

```text
presentation state
Call / Put and metric selection
expiry visibility
strike viewport
formatting
chart rendering and interaction
```

这些 presentation state 不进入 V1 query。frontend 不重新计算 backend 已准备的 premium metrics。

## 3. Stable Product Invariants

1. Premium Plane 是独立于 MO Option Chain 的 HTTP 产品。
2. wire representation 是 `shared context + expiry contexts + sparse points`，不是矩阵。
3. 只有真实 analytical Point 才能进入 `points[]`；不得创建 synthetic contract、synthetic cell 或插值结果。
4. 不同 expiry 不要求共享 strike universe。
5. Point 缺席、Point 中 nullable fact 缺失、数值 `0` 是三个不同状态。
6. underlying 是 plane-level context；MO 当前映射到 `000852.SH`，不得用 futures 替代。
7. futures 是 nullable expiry-level reference，不是 underlying、seller-yield denominator 或 premium source。
8. HTTP Point 是 delivery projection，不是 canonical backend `AnnualizedPremiumPoint`。
9. 两个 premium metrics 随完整 plane 一次交付；Call / Put 与 metric 切换不触发另一次请求。
10. HTTP 不拥有金融公式，也不暴露 Source、Raw Artifact、Preparation 或 repository 实现结构。

## 4. Backend Architecture

backend domain authority 已锁定：

```text
OptionMarketBasis
    ↓
AnnualizedPremiumPoint Preparation
    ↓
Point[]
    ↓
optional PlaneFramer
```

本图表达 stable semantic direction；Point、formula、null/absence、compatibility 与 dependency invariants 见 `guides/mo-option-premium-backend.md`。它仍不预设具体 class、module、persistence 或 runtime orchestration。

## 5. Navigation

```text
market-snapshot/ARCHITECTURE.md
        ↓
guides/mo-option-premium.md（本文档）
        ├── guides/mo-option-premium-backend.md
        └── guides/mo-option-premium-http-contract.md
```

* 判断产品定位、ownership 或稳定 invariants → 读本文档。
* 判断 endpoint、query、HTTP DTO projection、null/absence/zero 或 error mapping → 读 HTTP contract。
* 判断 domain Point、OptionMarketBasis、公式、Preparation 或 PlaneFramer → 读 backend authority，不得从 HTTP DTO 反推。

## 6. Implementation Status

当前已锁定产品入口、backend semantic core 与 HTTP delivery contract。以下仍未实现且不属于本轮：

```text
backend domain model implementation
Preparation / PlaneFramer implementation
Data Service / provider
FastAPI route / DTO / OpenAPI
generated frontend contract
React / Plotly renderer
```
