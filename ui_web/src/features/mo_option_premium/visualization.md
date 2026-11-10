# MO Premium Plane visualization authority

本文档从属于 [feature architecture](ARCHITECTURE.md)，只拥有该 frontend slice 的 V1 用户输入、presentation state、numeric sparse-plane projection、formatting、interaction 与用户可见状态。HTTP schema 与 backend analytical semantics 由 [Premium HTTP contract](../../../../ui_http/products/mo_option_premium/http-contract.md) 及其上游 authority 拥有。

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
select Reference Basis: underlying spot / same-expiry futures
    ↓
select Value Basis: total / time value
    ↓
select Time Normalization: unannualized / annualized
    ↓
select Representation: points / yield
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

只有 `as_of`、`option_product` 或 `price_type` 的 resolved value 改变才产生新 query。请求必须遵循 [ui_http HTTP contract](../../../../ui_http/products/mo_option_premium/http-contract.md)，不得增加 presentation filters。

## 3. Presentation State

```text
selectedOptionType: call | put
selectedReferenceBasis: underlying_spot | expiry_futures
selectedValueBasis: total | time_value
selectedTimeNormalization: unannualized | annualized
selectedRepresentation: points | yield
selectedExpiries: response expiry identities
```

每个新完整 response 的默认值是：

```text
selectedOptionType = call
selectedReferenceBasis = underlying_spot
selectedValueBasis = total
selectedTimeNormalization = annualized
selectedRepresentation = points
selectedExpiries = all response expiries
```

改变上述任一 presentation state 只重新投影已加载的完整 response，不发起请求、不改变 response，也不触发 backend recomputation。

四个 metric selections 唯一定位 backend 已准备的 leaf：

```text
point.metrics
    [selectedReferenceBasis]
    [selectedValueBasis]
    [selectedTimeNormalization]
    [selectedRepresentation]
```

Frontend mapping 只选择 backend fact，不计算 financial value，也不得把 coordinates 建模为 flat metric selector。四个 selectors 必须作为一个 cohesive “指标设置” control group 展示，并按以下语义组织：

```text
指标设置
    标的
        现货标的 / 同到期期货
    计算口径
        价值口径: 总价值 / 时间价值
        时间标准: 未年化 / 年化
    表示方式
        点数 / 收益率
```

Call/Put 属于独立“期权类型” control；expiry visibility 属于独立“显示到期日” control。不得把二者并入指标设置。

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

- 存在该 selected side 的真实 Point 时，cell 展示两个 axes 映射到的 backend fact；
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
| any selected points leaf | 1 decimal |
| any selected yield leaf | percentage, 2 decimals |
| DTE | integer |

Representation 唯一决定 metric formatting：points 使用 1 decimal，yield 使用 percentage 2 decimals。negative yield 保留负号，zero 按 `0.0` 或 `0.00%` 显示，null 显示 `—`。例如 `7312.45 → 7312.5`、`3825.24 → 3825.2`、`-12.34 → -12.3`、`0.0998 → 9.98%`。Formatting 只影响 display，不改变排序、reference comparison、identity、request 或 backend numeric facts。

第 7、10 节的完整 JSON 查看与复制不应用这些 display formatting；yield 保持响应 numeric ratio，不转换为百分数字符串。

Premium table 最左侧 strike header 同时显示 `response.underlying.price`，语义为“行权价 / 标的现价 · {formatted price}”。它复用上述 underlying price formatting，只是 presentation context，不重新请求或计算 market fact。

## 6. Strike Relative-to-Reference Coloring

Reference coloring 是 frontend-only visual encoding，不是 financial analytical metric。分类只使用 backend raw numeric facts，禁止使用 formatted、rounded 或 display string：

```text
strike < reference → below-reference
strike > reference → above-reference
strike = reference → at-reference
```

左侧 strike column 的 `reference` 固定为 response-level `underlying.price`。每个 expiry column 的 `reference` 固定为该 expiry 的 `futures.price`；当 `futures = null` 时，该 column 的所有 row coordinates 使用 `neutral`，不得寻找或推断替代 futures contract。

分类适用于每个展示 row strike 与 column reference 的关系，与该 coordinate 是否存在真实 Point、metric 是否为 null 无关。无 Point cell 可以具有 reference-region presentation，但仍必须保持空白，且不得因此成为 synthetic Point、null fact 或 analytical observation。

该 coloring reference 固定由 table location 决定，与 `selectedReferenceBasis` 无关；切换 metric reference 不改变颜色分类。颜色只表达：

> strike position relative to the relevant reference price.

不得将 `below-reference`、`above-reference`、`at-reference` 或 `neutral` 解释或标记为 cheap / expensive、bullish / bearish、good / bad、recommended、probability、signal、ITM 或 OTM。Call 与 Put 的 intrinsic-value direction 相反，因此不得为两个区域提供全局 ITM / OTM 标签。具体 CSS colors 属于 implementation choice。

## 7. Raw HTTP Response Inspector

成功 UI 必须提供一个默认折叠、低干扰的 Raw HTTP Response Inspector。它展示并复制当前成功 Premium HTTP request 实际收到的完整 JSON response payload，供用户直接粘贴给 GPT 或其他分析工具。

它不是 Source Raw、Tushare Raw、Premium-owned Raw Artifact、`OptionMarketBasis`、canonical Point 或 frontend table projection。Call/Put、四个 metric selections 与 expiry visibility 的变化不得修改 Inspector 内容。

API request lifecycle 必须从同一次 HTTP response 保留：

```text
HTTP JSON payload
        ↓
retain raw payload
        ↓
runtime contract validation
        ↓
validated PremiumPlane
```

只有 validation 成功时，validated plane 与其对应 raw payload 才共同进入 complete-result state。contract-invalid payload 继续进入既有 invalid-response failure path，不得作为 Inspector success data。完整 JSON serialization 遵循 [Daily Data Copy / Export authority](../../../data-copy-export.md#1-copy-json)，无需恢复 byte-identical HTTP body。

Inspector 展开后继续使用可读的完整 pretty JSON，并保留明确的“复制 JSON”能力。它与第 10 节顶部复制入口使用同一成功状态中的 `rawPayload`；复制反馈与失败边界遵循共同 authority，不另行维护过滤后的 JSON。顶部入口不要求展开 Inspector，也不替代其完整查看能力。

Raw payload 对应第 2 节完整 query identity（含固定的 `option_product=MO`）；当前结果身份由返回的 `observation.kind/value`、`option_product`、resolved `price_type` 与 underlying identity 确定，而不是读取可能已变化的输入控件。Current-result lifecycle 遵循共同 authority 与第 8 节；旧 validated response 与旧 raw payload 必须同时退出当前结果。V1 不要求展示 backend error body、历史 payload 或发起第二次请求获取 raw data。

## 8. Loading, Complete and Failure States

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

## 9. V1 Non-goals

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
generic JSON debugging framework or historical raw-response storage
market interpretation, Premium Edge, forecast or decision system
```

MO Option Chain 与 Premium Plane 保持两个独立 frontend vertical slices；本 slice 只展示 backend facts，不推导推荐 strike、cheap/expensive、交易信号或交易建议。

## 10. Daily Data Copy / Export

两种复制的格式、成功状态限制、顶部入口、Clipboard 反馈与安全边界遵循 [Daily Data Copy / Export authority](../../../data-copy-export.md)。本节只拥有 Premium Plane 特有的 source 与 context。

Copy JSON 与 Copy for GPT 的 JSON 均使用第 7 节中当前成功状态保留的完整 `rawPayload`，不使用 `projection` 或重建的 table/grid。Copy for GPT 上下文取同一次成功响应的 validated plane；二者必须对应同一 payload。Call/Put、四个 metric selections、expiry visibility、颜色和 display formatting 不改变任何复制内容；全部 Points、全部 expiries 与全部 metric leaves 均保留。

Copy for GPT 的产品名称为 `MO Premium Plane`；上下文读取响应中的 `observation.kind`、`observation.value`、`option_product`、resolved `price_type` 和 `underlying.instrument_id`，不得把当前 `as_of` 或 price-type 控件当作响应身份。

简短阅读说明限定为 [HTTP contract](../../../../ui_http/products/mo_option_premium/http-contract.md#5-absence-null-and-zero) 已确认的事实：plane 是 sparse Points；不存在的 Point 与真实 Point 内的 null metric 不等价，numeric `0` 也不等于 `null`；没有合法同到期期货 reference 时 `futures` 可以为 `null`，不得寻找替代 reference。说明不重新计算 metric 或补齐 plane。

### CSV V1

Source 为当前成功状态的完整 validated `plane`，JSON 复制仍使用同次响应 rawPayload。每个真实 `points[]` item 生成一行，不使用 projection.rows、selected metric、strike union 或 displayed cells。固定前 15 列：

```text
observation_kind, observation_value, option_product, price_type,
underlying_instrument_id, underlying_price,
expiry_date, dte, futures_present, futures_instrument_id, futures_price,
instrument_id, option_type, strike, premium
```

Observation/product/price type/underlying 来自 response-level context；expiry_date、instrument_id、option_type、strike、premium 直接取 Point。以 Point.expiry_date 查同次响应唯一 expiry context 取得 dte/futures，不重新计算 DTE；缺失或重复 context 明确失败，不补值或丢行。

随后展开全部 16 个 metric leaves，列名为 `metric_{reference_basis}_{value_basis}_{time_normalization}_{representation}`，按下列各轴嵌套顺序生成：

```text
reference_basis: underlying_spot, expiry_futures
value_basis: total, time_value
time_normalization: unannualized, annualized
representation: points, yield
```

直接读取 backend leaf，不计算 premium/time value/annualization/yield，yield 保持原始 ratio。总计 31 列。保留 backend points 顺序：expiry_date ascending → call before put → strike ascending → instrument_id ascending。行数恰为 plane.points.length；无 Point expiry 不生成行，全无 Point 为 header-only。Null、zero 与 Point absence 不混淆，不按 expiry × strike × side 生成行。

文件名为 `mo-premium-plane_{observation.value}_{price_type}.csv`，身份来自响应；编码、安全与下载遵循共同 authority。
