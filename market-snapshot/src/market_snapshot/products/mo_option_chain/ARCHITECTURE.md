# MO Option Chain 产品 authority

本文档是 MO Option Chain 的 bounded-context 入口，只拥有产品定位、query identity、product-to-underlying mapping、跨子契约 invariant 与 authority 路由。模块边界见 [market-snapshot architecture](../../../../ARCHITECTURE.md)。

## 1. 产品定位

`MO Option Chain` 是目标交易日完整 MO 中证1000股指期权链的 deterministic data product。它允许复用共享 Source Capture capability，但拥有自己的 goal-scoped Raw Artifact、Preparation 与 read model。

```text
shared Capture capability != shared goal-scoped Raw Artifact
```

本产品发布 market-chain facts，不计算 MO Premium Plane 指标，也不产生市场判断或交易建议。

本产品选择 persisted goal-scoped Raw 作为 Capture/Preparation 契约；其 request-scoped final read model 不要求持久化。产品内的 Application Service 拥有 orchestration、public result 与 classified failure。

## 2. Ownership

| Owner | Canonical knowledge |
| --- | --- |
| 本文档 | 产品身份、query identity、MO underlying mapping、跨子契约 invariant |
| [Shared Source Capture authority](../../capture/ARCHITECTURE.md) | Capture identity、Source endpoint、公共 Source 字段与 minimal normalization |
| [Data authority](data.md) | 产品 Source scope、goal-scoped Raw、active universe、daily completeness |
| [Read contract](read-contract.md) | selected price、null/zero、reference、grouping、ordering、semantic response 与 failure |
| [backend-api HTTP contract](../../../../../backend-api/products/mo_option_chain/http-contract.md) | endpoint、query serialization、DTO projection、error envelope 与 status mapping |
| [Web visualization authority](../../../../../web-ui/src/features/mo_option_chain/ARCHITECTURE.md) | presentation state、visual encoding、interaction 与用户可见状态 |

Transport 与 presentation 只能消费本产品准备的 facts，不得反向定义 universe、price、completeness、grouping 或 failure semantics。

## 3. Query Identity

Caller input：

```text
target_trade_date   required    explicit YYYY-MM-DD
option_product      required    V1 = MO
price_type          optional    default = close
```

Normalized query identity：

```text
target_trade_date + option_product + resolved price_type
```

- `target_trade_date` 不是 request time、`today` 或 `latest`；V1 要求调用方显式提供。
- `option_product` 表示期权产品，不是 underlying；V1 只支持 `MO`，但该维度保留在 identity 中。
- `price_type` 在数据准备前解析；response 回显 resolved value。允许值及统一选价语义由 [read contract](read-contract.md) 定义。

## 4. Product-to-Underlying Mapping

`market-snapshot` 拥有以下映射：

```text
MO -> CSI1000 -> 000852.SH
```

调用方只指定 `option_product=MO`，不得再提供可能冲突的 underlying。`IM` 是 futures product，不是 MO underlying；不得用 IM price 代替 CSI1000 underlying price。未来的 IO/HO 映射不属于 V1。

## 5. Stable Product Invariants

1. 本产品不读取 sibling Product 的最终产物。
2. `price_type` 变化不得改变 [data authority](data.md) 定义的 contract universe。
3. Option、underlying 与实际存在的 expiry futures reference 使用同一 resolved `price_type`；具体 fallback 与 absence 由 [read contract](read-contract.md) 唯一定义。
4. 缺价不得造成 contract 静默删除；null、zero、missing daily row 与合法 reference absence 的区别由 data/read authority 唯一定义。
5. Grouping、ordering、response completeness 与 semantic failure 由 read contract 准备完成；HTTP 与 web-ui 不重新推导。
6. Response 必须足以标识 query、underlying 与各 expiry context；具体 semantic shape 由 read contract 拥有，wire projection 由 HTTP contract 拥有。

## 6. V1 Non-goals

V1 不包含 IO/HO、IV、Greeks、moneyness、liquidity judgment、recommended strike、market interpretation、trading signal、volume/OI visualization、settlement-price mode、date range、latest/fallback、database、cache、auth 或 websocket。

## 7. Navigation

- 修改共享 Source fact 或 Capture identity → [Shared Source Capture authority](../../capture/ARCHITECTURE.md)
- 修改产品 Raw scope、universe 或 completeness → [Data authority](data.md)
- 修改 Preparation/read model、price、null、grouping、ordering 或 failure → [Read contract](read-contract.md)
- 修改 endpoint、DTO 或 transport error mapping → [backend-api HTTP contract](../../../../../backend-api/products/mo_option_chain/http-contract.md)
- 修改用户可见展示或交互 → [Web visualization authority](../../../../../web-ui/src/features/mo_option_chain/ARCHITECTURE.md)

只读取当前任务所需的分支；backend 任务不默认读取 visualization authority，frontend 任务不读取 Source Capture 或 Raw internals。
