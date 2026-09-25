# MO Premium Plane visualization authority

本文档从属于 [feature architecture](ARCHITECTURE.md)，只拥有该 frontend slice 的 V1 用户输入、presentation state、numeric sparse-plane projection、formatting、interaction 与用户可见状态。HTTP schema 与 backend analytical semantics 由 [Premium HTTP contract](../../../../market-snapshot/src/daily_market_snapshot/products/mo_option_premium/http-contract.md) 及其上游 authority 拥有。

## 1. V1 Experience

V1 是 numeric sparse premium plane，不是 option-chain chart：

```text
select as_of
    ↓
select price_type
    ↓
load complete PremiumPlaneResponse
    ↓
select Call / Put
    ↓
select displayed metric
    ↓
select visible expiries
    ↓
inspect numeric premium plane
```

## 2. Query State

一次 HTTP request identity 是：

```text
as_of
option_product = MO
price_type = open | high | low | close
```

`as_of` 必须由用户显式选择；日期清空时不请求。`price_type` 默认 `close`，`option_product` 在本 slice 固定为 `MO`。V1 不定义 `today`、`latest`、automatic fallback date 或 date range。

只有 `as_of`、`option_product` 或 `price_type` 的 resolved value 改变才产生新 query。请求必须遵循 backend [HTTP contract](../../../../market-snapshot/src/daily_market_snapshot/products/mo_option_premium/http-contract.md)，不得增加 presentation filters。

## 3. Presentation State

```text
selectedOptionType: call | put
selectedMetric:
  annualized_premium_points
  | annualized_time_value_points
  | annualized_seller_premium_yield
selectedExpiries: response expiry identities
```

每个新完整 response 的默认值是：

```text
selectedOptionType = call
selectedMetric = annualized_premium_points
selectedExpiries = all response expiries
```

改变上述任一 presentation state 只重新投影已加载的完整 response，不发起请求、不改变 response，也不触发 backend recomputation。

`selectedExpiries` 默认保持 backend response 的全部 expiry identities。隐藏 expiry 只隐藏对应 column；完整 response 保留，其他 expiry 的 identity 和顺序不变，并且只要 response 含有 expiry 就至少保持一个 visible expiry。

## 4. Numeric Sparse Plane

核心 table 定义为：

```text
columns = selected expiries
rows    = strikes
cell    = selected metric of the real Point
```

Column 必须保持 backend `expiry_date ascending` identity，不按用户选择顺序重新排序。Rows 唯一定义为 `selectedOptionType + selectedExpiries` 中所有真实 Points 的 strike union，并按 raw numeric strike ascending 展示。Frontend 不因 strike 相对 reference price 的位置或任何显示范围删除真实 Point。

对每个 expiry × strike presentation coordinate：

- 存在该 selected side 的真实 Point 时，cell 展示该 Point 的 `selectedMetric`；
- coordinate 不存在 Point 时，cell 留空，表示没有 analytical observation；
- Point 存在但 selected metric 为 `null` 时，cell 显示 `—`，表示真实 Point 的该 metric unavailable；
- metric 为 `0` 时按合法 numeric value 显示，不得视为 missing。

Table 附带简短图例，明确“空白 = 无 Point；`—` = Point 存在但 metric unavailable”。不得为规则矩阵生成 analytical Point、synthetic contract 或 synthetic null fact，也不得 interpolation、nearest-strike substitution、forward fill 或 backfill。

如果当前 selected side 与 selected expiries 没有任何真实 Point，页面显示“当前选择下无 analytical observation”这一合法视图空状态，并保留 response context 与所有控件。它不是 backend failure，不得创建 placeholder Point 或转成 partial/empty success。

## 5. Context and Formatting

页面级 context 必须显示 backend 提供的：

```text
observation.value
option_product
price_type
underlying.instrument_id
underlying.price
```

每个 expiry column header 必须保持并显示 `expiry_date`、整数 `dte` 与 `futures` context。`futures` 存在时显示其 `instrument_id` 与 `price`；为 `null` 时明确显示“无合法 futures reference”，不寻找或展示替代 IM contract。

V1 formatting：

| Fact | Display |
| --- | --- |
| strike | 1 decimal |
| underlying price | 1 decimal |
| futures price | 1 decimal |
| annualized premium points | 1 decimal |
| annualized time-value points | 1 decimal |
| annualized seller premium yield | percentage, 2 decimals |
| DTE | integer |

例如 `7312.45 → 7312.5`、`3825.24 → 3825.2`、`-12.34 → -12.3`、`0.0998 → 9.98%`、points zero `→ 0.0`、yield zero `→ 0.00%`。Formatting 只影响 display，不改变排序、reference comparison、identity、request 或 backend numeric facts。

## 6. Strike Relative-to-Reference Coloring

Reference coloring 是 frontend-only visual encoding，不是 financial analytical metric。分类只使用 backend raw numeric facts，禁止使用 formatted、rounded 或 display string：

```text
strike < reference → below-reference
strike > reference → above-reference
strike = reference → at-reference
```

左侧 strike column 的 `reference` 固定为 response-level `underlying.price`。每个 expiry column 的 `reference` 固定为该 expiry 的 `futures.price`；当 `futures = null` 时，该 column 的所有 row coordinates 使用 `neutral`，不得寻找或推断替代 futures contract。

分类适用于每个展示 row strike 与 column reference 的关系，与该 coordinate 是否存在真实 Point、metric 是否为 null 无关。无 Point cell 可以具有 reference-region presentation，但仍必须保持空白，且不得因此成为 synthetic Point、null fact 或 analytical observation。

颜色只表达：

> strike position relative to the relevant reference price.

不得将 `below-reference`、`above-reference`、`at-reference` 或 `neutral` 解释或标记为 cheap / expensive、bullish / bearish、good / bad、recommended、probability、signal、ITM 或 OTM。Call 与 Put 的 intrinsic-value direction 相反，因此不得为两个区域提供全局 ITM / OTM 标签。具体 CSS colors 属于 implementation choice。

## 7. Loading, Complete and Failure States

页面至少区分：

```text
no as_of selected
loading
complete result
failure
```

- 未选择 `as_of` 时显示待选择状态且不请求。
- query identity 改变并开始新请求时，旧 response 立即退出当前结果区域；可以显示 loading，但不得继续把旧 observation 表现为当前数据。
- 每次请求关联其完整 query identity；较早请求即使更晚完成，也不得覆盖较新 query 的 loading、result 或 failure。
- 成功后只展示完整 response；frontend 不构造 partial plane。
- HTTP failure 按稳定的 `error.kind` 分支：`invalid_request`、`unsupported_query`、`date_not_available`、`premium_plane_unavailable`。`error.detail` 只作为 human-readable detail，不参与程序分支。
- 网络失败、无法解析的响应或未知 error kind 进入通用读取失败状态，不伪造 market facts。

任何失败都不得 fallback date、把 stale response 作为当前结果、构造 partial plane，或静默转成 empty table。合法的 presentation projection 空状态只允许发生在已成功加载的完整 response 上，并与 failure 明确区分。

## 8. V1 Non-goals

本 authority 不设计：

```text
React component tree
state-management library
CSS or table library
router or generic design system
backend or OpenAPI changes
contract generation implementation
cache, auth or deployment
generic Option Chain / Premium visualization framework
market interpretation, Premium Edge, forecast or decision system
```

MO Option Chain 与 Premium Plane 保持两个独立 frontend vertical slices；本 slice 只展示 backend facts，不推导推荐 strike、cheap/expensive、交易信号或交易建议。
