# MO Premium Plane HTTP transport contract authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，只拥有 MO Premium Plane 的 HTTP resource、V1 query、success projection、sparse-plane wire semantics、presentation-state boundary 与 error mapping。Source/Raw/universe 由 [data.md](data.md) 拥有，Canonical Point、Preparation、公式与 PlaneFramer 由 [backend.md](backend.md) 拥有，product orchestration、result 与 semantic failures 由 [service-contract.md](service-contract.md) 拥有。

---

## 1. HTTP Resource

resource 表示：

> 一个 observation anchor 下的稀疏 MO annualized-premium analytical plane。

V1 endpoint：

```text
GET /mo-option-premium-plane
```

* 使用 GET，无 request body。
* V1 不增加 API version prefix。
* path 不携带 observation、product 或 price type；它们属于 query identity。
* 这是与 `GET /mo-option-chain` 独立的产品 surface，不扩展、包装或复用 Option Chain response。
* resource 名称固定使用 `plane`，不得改称 `matrix`。

## 2. V1 Request Identity

| query 参数 | required | 类型 | 语义 |
| --- | --- | --- | --- |
| `as_of` | required | string | trade-date observation，格式 `YYYY-MM-DD` |
| `option_product` | required | string | option product；V1 唯一支持 `MO` |
| `price_type` | optional | string | 取价口径；省略时解析为 `close` |

V1 支持的 `price_type`：

```text
open
high
low
close
```

示例：

```text
GET /mo-option-premium-plane?as_of=2026-09-21&option_product=MO
GET /mo-option-premium-plane?as_of=2026-09-21&option_product=MO&price_type=high
```

`as_of` 是更广义 `ObservationAnchor` 的 V1 HTTP 表达；V1 只接受 trade date，不设计 timestamp transport、generic temporal framework、latest 或 date range。

`as_of` 是本产品有意采用的 query 名称。它不修改 MO Option Chain 已有的 `target_trade_date` contract；两个独立产品无需共享 query 字段名。

HTTP query 是闭集。以下均不是 query 参数：

```text
selected expiries
side / Call / Put selection
selected metric
server-side strike filtering
chart size
color / theme
visibility state
underlying
```

## 3. Success Response

HTTP 200 返回一个无外层 envelope 的 `PremiumPlaneResponse` JSON object：

```json
{
  "observation": {
    "kind": "trade_date",
    "value": "2026-09-21"
  },
  "option_product": "MO",
  "price_type": "close",
  "underlying": {
    "instrument_id": "000852.SH",
    "price": 7312.5
  },
  "expiries": [
    {
      "expiry_date": "2026-09-25",
      "dte": 5,
      "futures": {
        "instrument_id": "IM2609.CFE",
        "price": 7301.6
      }
    },
    {
      "expiry_date": "2026-10-23",
      "dte": 33,
      "futures": null
    }
  ],
  "points": [
    {
      "instrument_id": "MO2609-C-7000.CFE",
      "expiry_date": "2026-09-25",
      "option_type": "call",
      "strike": 7000.0,
      "premium": 52.4,
      "annualized_premium_points": 3825.2,
      "annualized_time_value_points": -18987.3,
      "annualized_seller_premium_yield": 0.5231,
      "annualized_time_value_yield": -2.5966
    },
    {
      "instrument_id": "MO2610-P-7050.CFE",
      "expiry_date": "2026-10-23",
      "option_type": "put",
      "strike": 7050.0,
      "premium": null,
      "annualized_premium_points": null,
      "annualized_time_value_points": null,
      "annualized_seller_premium_yield": null,
      "annualized_time_value_yield": null
    }
  ]
}
```

示例数值只用于说明 wire shape，不定义金融计算结果。

### 3.1 Response-level context

成功 response 必须包含：

```text
observation.kind = trade_date
observation.value = resolved as_of
option_product
resolved price_type
underlying.instrument_id
underlying.price
```

MO 的 current underlying identity 是 `000852.SH`。`underlying.price` 必须是 usable numeric fact；缺少必要 underlying observation 时不得成功，也不得改用 futures 作为 denominator/reference。

response 回显 resolved `price_type`。`underlying.price`、每个 present `futures.price` 与 Point 的 `premium` 都使用该同一取价口径；HTTP 不允许混合 price type，也不执行价格 fallback。

### 3.2 Expiry-level context

每个 `expiries[]` item 必须包含：

```text
expiry_date
dte
futures
```

`expiry_date` 是 `points[]` 与 expiry context 的 join key。`dte` 是 backend 已准备好的整数事实；HTTP 不定义其公式。

`futures` 的 wire shape：

```text
null

OR

{
  instrument_id: string,
  price: number
}
```

无 legitimate futures reference 时使用 `null`。不得使用 nearest-expiry、main-contract、liquidity-based substitution 或 fallback price。futures 不是 underlying、intrinsic-value reference、seller-yield denominator 或 premium source。

### 3.3 Sparse Point projection

每个 `points[]` item 必须包含：

```text
instrument_id: string
expiry_date: string
option_type: call | put
strike: number
premium: number | null
annualized_premium_points: number | null
annualized_time_value_points: number | null
annualized_seller_premium_yield: number | null
annualized_time_value_yield: number | null
```

Point coordinate 是：

```text
expiry_date × strike × option_type
```

`instrument_id` 与 coordinate fields 共同使 projection 自描述。frontend 可以直接使用 `X = expiry_date`、`Y = strike` 放置真实 Point，不需要先对齐不同 expiry 的 strikes。

每个 Point 的 `expiry_date` 必须恰好匹配一个 `expiries[]` context；`expiries[]` 中的 `expiry_date` 不得重复，同一 `expiry_date × strike × option_type` coordinate 也不得重复。

五个 nullable numeric fields 的合法组合及金融一致性由 [backend.md](backend.md) 决定。HTTP 只保持已准备 facts，不计算、不补值，也不从一个 metric 推导另一个 metric。尤其不得在 delivery adapter 中计算 intrinsic value、time value、annualization 或任一 yield；两个 time-value facts 只能投影 canonical Point 已准备的值。

`annualized_seller_premium_yield` 与 `annualized_time_value_yield` 均以 numeric ratio 交付：

```text
0.0998 = 9.98%
```

不得交付 `"9.98%"` 等 formatted string；格式化属于 frontend。

## 4. Sparse-plane Semantics

`points[]` 是 canonical sparse representation。不同 expiry 不需要共享 strike universe，例如：

```text
2026-09-25: 7000, 7100, 7200, 7300
2026-10-23: 7050, 7150, 7250, 7350
```

这是合法平面。wire contract 禁止：

```text
rows[][] / cells[][] / matrix[][]
expiry × all strikes Cartesian product
strike interpolation
expiry interpolation
nearest-strike substitution
synthetic null cells
synthetic contracts
forward fill
fallback price generation
```

transport 只描述实际 prepared analytical observations，不创建不存在的 analytical fact。

## 5. Absence, Null and Zero

### 5.1 No Point

某 coordinate 没有真实合约或 analytical Point 时，`points[]` 中没有对应 item。不得为了矩形网格创建 `premium: null` 的 synthetic Point。

### 5.2 Point with null facts

真实合约 Point 存在但 premium 不可用时，Point 保留，nullable numeric facts 按 backend prepared result 序列化为 `null`。不得省略 nullable 字段、补零或删除 Point。

```text
absence of Point != Point with null fact
```

### 5.3 Zero

所有 numeric field 均保持：

```text
0 != null
```

数值为零时必须序列化为 `0` / `0.0`，不得视作 missing。

### 5.4 Empty plane

V1 成功 response 必须至少包含一个真实 analytical Point。合法 request 无法产生任何真实 Point 时，不返回 `200 + points=[]`，而映射为 `503 premium_plane_unavailable`。

## 6. Delivery Projection, Not Domain Model

HTTP Point DTO 是 delivery projection，不是 canonical backend domain Point：

```text
Core AnnualizedPremiumPoint
!=
PremiumPlanePointDTO
```

projection 可以为减少 transport repetition 而：

* 把 shared underlying 提升到 response level；
* 把 DTE 与 futures 提升到 expiry level；
* 在 Point 中保留 contract-specific identity、coordinate 与 metrics。

这种 normalization 不得改变 analytical meaning。不得从本文档推导 canonical domain class 的字段布局，也不得通过 wire contract 暴露：

```text
OptionMarketBasis
repository class
Source / Raw Artifact
Preparation / Framer class
Tushare schema
internal cache
```

HTTP adapter 从 [product service](service-contract.md) 接受完整的 request-scoped `AnnualizedPremiumPlane` 或 classified product semantic failure。它不得直接调用 Source、构造 Raw/Basis、计算 DTE、intrinsic value、time value、annualization 或 premium metrics，也不得修复 incomplete Point/Plane。

## 7. Ordering and Identity

deterministic serialization order：

```text
expiries:
expiry_date ascending

points:
expiry_date ascending
→ option_type: call before put
→ strike ascending
→ instrument_id ascending as stable tie-break
```

ordering 是 transport convenience，不是 analytical identity。consumer 必须使用 fields 识别 expiry 与 Point，不得把 array index 当作 identity。

## 8. Presentation-state Boundary

一次成功 response 同时交付 Call / Put、全部 expiries 与完整 2 × 2 premium metric space 的 sparse projection。以下交互不得触发 backend recomputation 或新的 HTTP request：

```text
Call / Put toggle
total / time value selection
points / yield selection
expiry visibility
```

本文档不规定 Plotly trace、CSS、marker、color、tooltip、layout、component hierarchy 或 formatting precision；这些属于未来 frontend visualization authority。

## 9. Error Envelope and Status Mapping

非 2xx response 复用现有 HTTP error envelope：

```json
{
  "error": {
    "kind": "premium_plane_unavailable",
    "detail": "MO Premium Plane cannot be produced for the requested observation",
    "param": null
  }
}
```

| 字段 | required | 语义 |
| --- | --- | --- |
| `error.kind` | required | 本产品的闭集 error kind；consumer 据此分支 |
| `error.detail` | required | 人类可读、非稳定文本，不用于程序判断 |
| `error.param` | optional, nullable | 可归因到已声明 query 参数时为参数名，否则为 `null` |

V1 closed mapping：

| error kind | HTTP status | Adapter input / owner |
| --- | --- | --- |
| `invalid_request` | 400 | 缺少 required 参数；`as_of` 格式无效；query 值不在 HTTP 输入闭集；携带未知 query 参数 |
| `unsupported_query` | 400 | application/domain boundary 明确报告形态合法但 V1 不支持的 observation/product/price query |
| `date_not_available` | 404 | Product service 已按 [service contract](service-contract.md) 分类的同名 failure |
| `premium_plane_unavailable` | 503 | Product service 已按 [service contract](service-contract.md) 分类的同名 failure |

transport validation 直接拒绝 `option_product != MO` 与不支持的 `price_type`，使用 `invalid_request` 并把 `param` 设为对应字段。`unsupported_query` 只用于 application/domain boundary 显式报告的合法但未支持 query，不由 HTTP adapter 自行发明。

`date_not_available` 与 `premium_plane_unavailable` 的 product semantic classification 由 [service contract](service-contract.md) 唯一决定。HTTP 只做上述 status/envelope mapping；它不执行 availability probe，不解释 Source response，不判断 product completeness，也不根据 partial facts 重新分类。

未知 query 参数使用 `invalid_request`，且 `param = null`，由 `detail` 指出未知参数。产品整体不可用时 `param = null`。

本产品不使用 MO Option Chain 专属的 `option_chain_unavailable`，也不把 bootstrap implementation state `service_not_wired` 纳入 semantic contract。

error response 不携带 partial plane、underlying、expiry、Point 或替代 observation。不得把产品不可用静默降级为 empty success。

## 10. Relationship to MO Option Chain

| | MO Option Chain | MO Premium Plane |
| --- | --- | --- |
| resource | market-chain read product | annualized-premium analytical read product |
| endpoint | `GET /mo-option-chain` | `GET /mo-option-premium-plane` |
| observation query | `target_trade_date` | `as_of`（V1 trade date） |
| canonical wire organization | per-expiry Call / Put groups | shared context + expiry contexts + sparse points |
| product unavailable kind | `option_chain_unavailable` | `premium_plane_unavailable` |

Premium Plane 不扩展 `/mo-option-chain`，也不是 frontend-side Option Chain DTO derivative。现有 Option Chain 的 query、response、futures completeness 与 error contract 保持不变。

## 11. V1 Non-goals

```text
timestamp observation transport
generic temporal framework
date range / latest shortcut
pagination / server-side presentation filters
auth / versioning / cache / websocket
canonical backend domain model
financial formulas
Point Preparation / PlaneFramer
FastAPI route / Pydantic DTO / OpenAPI
generated TypeScript
React / Plotly renderer
```

## 12. Completion Check

仅阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 与本文档，应能唯一回答：

1. endpoint、method 与 V1 query 是什么？
2. response、expiry context 与 sparse Point 分别包含什么？
3. 为什么它不是矩阵，非对齐 strike 如何表达？
4. Point 缺席、nullable fact 与 zero 有何区别？
5. 两个 yield metrics 的 wire unit 是什么？
6. 哪些状态属于 frontend presentation，不进入 query？
7. HTTP 是否可以插值、补 cell、fallback underlying/futures 或返回 partial plane？
8. HTTP Point 是否等同 canonical backend Point？
9. error envelope、闭集 kind 与 status mapping 是什么？
10. Premium Plane 与 MO Option Chain 为什么是两个独立产品？
