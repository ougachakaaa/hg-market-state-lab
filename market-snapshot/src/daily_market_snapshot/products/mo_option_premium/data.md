# MO Premium Plane data authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有 MO Premium Plane 的产品专属 Source requirements、Capture scope、goal-scoped Raw、active universe、Raw completeness 与 observation availability boundary。共享 Capture 身份、Source endpoint、公共字段和 minimal normalization 见 [Shared Source Capture authority](../../capture/ARCHITECTURE.md)；Raw 到 analytical domain facts 的构造见 [backend authority](backend.md)。

---

## 1. Source Facts Required

V1 Premium Plane 是 single-observation analytical product，只需要以下 Source fact capabilities：

```text
MO option contract facts
MO option as_of daily facts
CSI1000 as_of underlying fact
IM ordinary-monthly contract facts
as_of-active IM ordinary-monthly daily facts
```

对应 shared Captures：

```text
mo_option_basic
mo_option_daily
index_daily
im_futures_basic
im_futures_daily
```

每个 Capture 的 Premium product scope 固定为：

| Capture | Premium V1 scope |
| --- | --- |
| `mo_option_basic` | CFFEX MO contract/lifecycle facts，足以按 `as_of` 确定完整 active universe |
| `mo_option_daily` | active MO universe 的 `as_of` daily observations |
| `index_daily` | `000852.SH` 的单个 `as_of` observation |
| `im_futures_basic` | CFFEX IM ordinary-monthly contract/lifecycle facts，足以确定 `as_of`-active universe |
| `im_futures_daily` | `as_of`-active IM ordinary-monthly universe 的 `as_of` daily observations |

Capture scope 表达 Source-domain acquisition requirement，不允许 Capture 执行跨 option/futures matching 或 downstream analytical filtering。

当前 product mapping：

```text
MO → CSI1000 → 000852.SH
```

option、underlying 与实际存在的 expiry futures reference 必须使用同一个 resolved `price_type`：

```text
open
high
low
close
```

默认值为 `close`。Capture 身份与 Source 字段由 [shared Capture authority](../../capture/ARCHITECTURE.md) 及其 specialized contracts 拥有，本文档不复制字段表。

V1 不要求也不得从 sibling product 引入：

```text
120-day index history
60-day IM history
term structure history
CSI1000 5D Analysis artifact
```

## 2. Premium-owned Raw Artifact

```text
shared Capture capability != shared goal-scoped Raw Artifact
```

Premium Plane 独立拥有：

```text
data/raw/mo-option-premium/<as_of>/
├─ index_daily.json
├─ mo_option_basic.json
├─ mo_option_daily.json
├─ im_futures_basic.json
└─ im_futures_daily.json
```

其中：

- `index_daily.json` 保存 `000852.SH` 的单个 `as_of` observation facts；
- `mo_option_basic.json` 保存足以确定 active MO universe 的 contract/lifecycle facts；
- `mo_option_daily.json` 保存 MO 的 `as_of` daily observations；
- `im_futures_basic.json` 保存足以确定 `as_of`-active IM ordinary-monthly universe 的 facts；
- `im_futures_daily.json` 保存该 IM universe 的 `as_of` daily observations。

每个文件是经过 shared Capture minimal normalization 的 Source-row JSON array。`<as_of>` 表示本次产品请求的 observation partition，不表示文件内缺失的 Source row 可以被合成。

Premium 不读取：

```text
data/raw/mo-option-chain/**
data/raw/csi1000-5d-analysis/**
sibling product final/read DTO or artifact
```

Raw 保持 Source fact semantics。Raw 不做：

```text
basic + daily join
Source field → analytical vocabulary rename
DTE or annualization calculation
seller-yield calculation
Plane grouping or ordering
```

## 3. Observation Availability Boundary

V1 使用现有 `index_daily` Capture 对以下精确 Source observation 执行 canonical availability probe：

```text
instrument = 000852.SH
observation = requested as_of
```

该 probe 只回答：

```text
Does 000852.SH have an observation for as_of?
```

它不验证 selected price 是否可用于 seller-yield calculation，也不判断 MO/IM completeness。probe result 是以下闭集：

| Probe evidence | Availability meaning |
| --- | --- |
| Source 请求与 `index_daily.json` Raw write 均成功，精确匹配 `000852.SH + as_of` 的 row 数为 `0` | explicit no-observation；requested observation 不可服务 |
| Source 请求与 Raw write 均成功，精确匹配 row 数为 `1` 或更多 | observation exists；admit observation，row uniqueness 与 analytical validity 随后验证 |
| Source/transport exception、timeout、malformed 或无法解释的 response、Capture failure、Raw write failure | indeterminate；没有证明 observation 不可服务 |

只有第一种完整 probe 的 explicit no-observation evidence 可以支持 product service 分类为 `date_not_available`。它覆盖 non-trading date、market observation 尚未发布或 Source 明确返回该日无 `000852.SH` observation 的情况。不得 fallback 到 previous、nearest、latest 或其他日期。

generic Source/Capture failure 不能自动解释为 unavailable date：

```text
SourceException != explicit no-observation
```

一旦至少一个精确匹配 row 使 observation 被 admitted，后续 row duplication、selected price validity、Raw completeness 与所有 product construction failure 都不得重新解释为 observation unavailable。product failure classification 由 [service contract](service-contract.md) 唯一拥有。

## 4. Active MO Contract Universe

Premium 的真实 option contract universe 只由 Source contract/lifecycle facts 决定：

```text
option_product = MO
AND exchange = CFFEX
AND list_date <= as_of <= delist_date
```

所有满足条件的真实 active contract 都属于产品 universe。不得按以下条件删除：

```text
strike distance
Call / Put
premium availability
volume or OI
liquidity
expiry preference
frontend viewport
selected expiries
```

因此 resolved `price_type` 和 presentation state 都不得改变 contract universe。不得用 `mo_option_daily` 返回的 rows 反向定义 active universe。

## 5. MO Daily Completeness

正确关系是：

```text
contract lifecycle facts
        ↓
active contract universe

active universe + as_of daily facts
        ↓
OptionMarketBasis inputs
```

对每个 active MO contract，必须有恰好一条 `as_of` daily row。缺失或重复 row 是 market-fact completeness failure；不得删除 contract、返回 partial Plane、解释为 no Point、改读其他日期或合成 row。

daily row 存在时，resolved selected premium 的状态分为：

```text
numeric, including 0 → legitimate premium fact
null or missing       → legitimate unavailable premium fact
malformed             → product completeness failure
```

null/missing selected premium 不删除 contract；它将在 Basis 和 Point 中保持为 `null`，derived premium metrics 也为 `null`。始终保持 `0 != null`。

## 6. Underlying Fact Contract

observation admission 后，成功构造 Premium analytical facts 必须有恰好一条：

```text
instrument = 000852.SH
observation = as_of
price semantics = resolved price_type
```

若 availability probe 已明确返回零个 matching rows，请使用第 3 节的 no-observation evidence，不进入 analytical construction。observation admitted 后，duplicate row，或后续 Raw/Basis 中缺失 admitted row，都是 required analytical input failure。

唯一 row 的 selected underlying price 必须 present、numeric 且 strictly positive。null/missing、malformed、zero 或 negative 都是 required analytical input failure，不是 observation absence。

不得使用 futures、strike、previous close、其他日期或其他 price field 作为 fallback。

## 7. IM Capture Scope and Analytical Completeness

IM Source acquisition scope 由 IM 自身 Source facts 决定：

```text
exchange = CFFEX
AND product = IM
AND ordinary monthly contract
AND list_date <= as_of <= delist_date
```

Capture 对这个 `as_of`-active IM ordinary-monthly universe 获取并保存实际返回的 daily facts。Capture 阶段不得读取 MO expiry 后缩小 universe，也不得按主力、成交量、持仓量、流动性或 symbol/month guessing 选择合约。

IM Raw acquisition scope 可以宽于最终 Plane 使用的 futures references。跨 MO expiry 的结构性匹配属于 [OptionMarketBasis construction](backend.md)，不属于 Capture。

未匹配任何 MO expiry 的 IM contract 缺少 daily row，不自动使 Premium Plane 失败。只有结构性唯一匹配到某个 MO expiry 的 IM contract，其唯一 `as_of` daily row 与 usable selected price 才是成功 analytical result 的必需事实。Source request 本身失败不得静默忽略。

## 8. Completion Check

仅阅读产品入口与本文档，应能唯一回答：

1. V1 使用哪些 shared Captures 和 price semantics？
2. Premium Raw 位于哪里、属于谁，是否可以读取 sibling Raw？
3. active MO universe 如何确定，是否受 price 或 presentation 影响？
4. active contract 缺 row、重复 row、selected premium null 与 zero 分别如何处理？
5. underlying 的 identity、observation、price 与失败条件是什么？
6. IM Capture scope 如何确定，何时 daily completeness 才影响 analytical result？
7. canonical availability probe 的三个结果分别是什么，哪些 evidence 可以证明 observation 不可服务？
8. underlying observation absence、duplicate row 与 invalid selected price 有何区别？
