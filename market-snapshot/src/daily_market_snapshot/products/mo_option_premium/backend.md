# MO Annualized Premium backend semantic authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有 MO Annualized Premium 的 `OptionMarketBasis` construction、canonical analytical model、确定性 Point Preparation、公式、null/zero/absence 与 PlaneFramer。Source requirements、Raw、universe 与 Raw completeness 由 [data.md](data.md) 拥有，product orchestration 由 [service-contract.md](service-contract.md) 拥有，HTTP transport 由 [http-contract.md](http-contract.md) 拥有。

---

## 1. Capability and Dependency Direction

MO Annualized Premium backend 的基本职责是：

> 从 option-market facts 确定性地产生可复用、自包含的 `AnnualizedPremiumPoint` analytical facts。

canonical dependency direction：

```text
Source-derived / Raw market facts
        ↓
OptionMarketBasis
        ↓
AnnualizedPremiumPoint Preparation
        ↓
AnnualizedPremiumPoint[]
        │
        ├── direct analytical consumers
        ├── historical / time-series consumers
        ├── modeling / feature preparation
        ├── future backtest workflows
        │
        └── PremiumPlaneFramer for Plane product delivery
                ↓
        AnnualizedPremiumPlane
```

禁止反向依赖：

```text
Core Point → HTTP DTO
Core Point → frontend / Plotly
OptionMarketBasis → /mo-option-chain response
OptionMarketBasis → React / Web state
Point Preparation → HTTP transport details
```

`AnnualizedPremiumPlane` 是 downstream organization，不是 backend capability 的 canonical fact owner。Direct Point consumers 不必 framing；[Premium product service](service-contract.md) 则必须调用 `PremiumPlaneFramer` 形成其 Plane result。

## 2. Observation Semantics

概念观察身份是：

```text
ObservationAnchor / as_of
```

V1 只支持 trade-date observation。当前计算中的：

```text
observation_date
=
as_of 所表示的 market-local date
```

V1 不建立 generic temporal framework、timestamp transport 或 fractional-time basis。未来 timestamp-based analytics 可以增加新的 observation 与 calculation basis，但不得静默改变本文档的 daily metric。

Premium HTTP 使用 `as_of`；MO Option Chain 继续使用 `target_trade_date`。两者在 V1 都映射到 trade date，但属于各自产品的 query naming，不做跨产品 broad rename。

## 3. OptionMarketBasis

`OptionMarketBasis` 是薄的、可复用的 option-domain market-fact boundary。Premium 使用自己的 goal-scoped Raw 构造它；其目的为：

> 收集并归一 downstream option analytics 所需的 Source-derived option-market facts，使每个 analytics 不必重复理解 Raw / Source-specific representation。

V1 Basis 至少提供：

```text
observation:
    as_of
option_product
resolved price_type

underlying:
    instrument_id
    price

option observations:
    instrument_id
    option_type
    expiry_date
    strike
    premium

expiry futures reference:
    null
    OR
    instrument_id
    price
```

`OptionMarketBasis`：

* 由 [Premium-owned Raw](data.md) 的 Source-derived facts 确定性构造；
* 可以被 Annualized Premium Point Preparation 消费，也允许 future option product 复用同一 semantic boundary；
* 不等同于、也不消费 `/mo-option-chain` HTTP response、HTTP DTO、frontend DTO 或 Web projection；
* 不计算 DTE、annualized premium 或 seller yield；
* 不预设 Python class layout、module layout 或持久化 artifact。

### 3.1 Deterministic construction

Basis construction 输入是 [data authority](data.md) 定义的完整 Premium Raw 与 normalized query。它按以下顺序形成 domain facts：

```text
determine active MO contracts from contract lifecycle facts
        ↓
join each active contract to exactly one as_of daily row by Source identity
        ↓
normalize Source fields into option-domain vocabulary
        ↓
project the resolved price_type
        ↓
attach the required underlying observation
        ↓
match nullable expiry futures references
```

允许的 deterministic analytical normalization 包括：

```text
ts_code        → instrument_id
call_put       → call | put
exercise_price → strike
maturity_date  → expiry_date
resolved price field → premium / underlying.price / futures.price
basic + daily join
legitimate expiry-futures structural matching
```

Source identity、date、lifecycle、option side 或 numeric facts 缺失、重复、malformed 或相互矛盾，且不属于已明确的合法 nullable premium/futures absence 时，不能形成合法 Basis。Basis 必须完整覆盖 active MO universe；不得删除无法 join 的 contract 或返回 partial Basis。

option selected premium 可以是 numeric（包括 `0`）或 Source 的 null/missing fact；后者归一为 `premium = null`。underlying 必须满足 [data authority](data.md) 的 positive price contract。futures 的唯一匹配价格必须 numeric，`0` 是合法事实。

### 3.2 Expiry futures matching

对 Basis 中每个 MO `expiry_date`，从 data authority 定义的 `as_of`-active IM ordinary-monthly universe 建立候选集：

```text
candidates = as_of-active IM ordinary-monthly contracts
             where IM.delist_date == MO.expiry_date

0 candidates  → futures = null
1 candidate   → use that contract
>1 candidates → explicit failure
```

唯一匹配的 IM contract 必须有恰好一条 `as_of` daily row，且 resolved selected price 必须是 usable numeric fact。row 缺失/重复，或 price 为 null/missing/malformed，均显式失败，不得转为 `futures = null`。

禁止 nearest-expiry、main-contract、liquidity-based、symbol/month guessing 或其他 price/date fallback。未匹配任何 MO expiry 的 IM contract 缺 daily row 不影响 Basis analytical completeness。

### 3.3 Calculation boundary

Basis construction 不得计算：

```text
DTE
annualized premium points
annualized time-value points
annualized seller premium yield
market judgment
HTTP projection
frontend grouping
```

前四项只属于 `AnnualizedPremiumPoint Preparation`。

它不是 `GenericBasisFramework`、analysis registry、pipeline engine、plugin system、DAG framework 或项目级抽象层级。

共享关系是：

```text
Source-derived option-market facts
             ↓
      OptionMarketBasis
        ┌────┴──────────────┐
        ↓                   ↓
future option         Annualized Premium
Preparation           Point Preparation
```

这是可复用的 semantic boundary，不是 sibling product 的当前 implementation prerequisite：本 authority 不要求从现有 Option Chain Preparation 提取共享代码，也不改变各产品的 goal-scoped Raw ownership。Premium implementation 只需从自己的 Raw 构造满足本文档的 Basis。

## 4. Canonical AnnualizedPremiumPoint

最小 canonical analytical unit 是：

```text
AnnualizedPremiumPoint
```

而不是：

```text
AnnualizedPremiumPlane
HTTP response / DTO
matrix cell
frontend point
Plotly trace
```

一个 Point 表示：

> 一个真实 option contract 在一个 observation anchor 下，连同独立解释它所需的 market references、calculation basis 与 derived annualized-premium analytics。

概念语义内容为：

```text
observation
    as_of

option identity
    instrument_id
    option_product
    option_type
    expiry_date
    strike

premium observation
    price_type
    premium

underlying reference
    instrument_id
    price

futures reference
    instrument_id
    price
    OR null

calculation basis
    dte_basis
    annualization_days
    seller_yield_denominator
    contract_multiplier

derived analytics
    dte
    annualized_premium_points
    annualized_time_value_points
    annualized_seller_premium_yield
```

这不是强制的 Python class、nesting 或 serialization layout。它是 canonical semantic contract。

## 5. Self-contained Semantics and Identity

单个 Point 从 collection、Plane、HTTP response 或 frontend context 中移除后，仍必须能回答：

```text
何时观察？
哪个真实 option contract 与 product？
Call 还是 Put？
哪个 expiry 与 strike？
哪种 resolved price semantics 与 premium？
哪个 underlying observation？
哪个 nullable expiry futures reference？
使用什么 calculation basis？
DTE 与三个 annualized metrics 是什么？
```

Point 的最小解释身份是：

```text
ObservationAnchor
+ instrument_id
+ resolved price_type
```

其 analytical coordinate 是：

```text
expiry_date
+ strike
+ option_type
```

`expiry_date + strike` 或 coordinate 本身都不是完整 Point identity；相同 coordinate 可以属于不同 observation、product、side、instrument 或 price semantics。

多个 Points 重复以下 context 是允许且有意的：

```text
observation
underlying
futures
calculation basis
```

优先级固定为：

```text
self-contained semantics
serialization independence
consumer decoupling
replayability
testability
>
storage normalization
```

consumer 不得被迫 join parent Plane context、global calculation config、expiry registry 或 external underlying context 才能解释 Point。

## 6. AnnualizedPremiumPoint Preparation

唯一确定性的 calculation responsibility 是：

```text
OptionMarketBasis
        ↓
AnnualizedPremiumPoint Preparation
        ↓
AnnualizedPremiumPoint[]
```

Preparation owns：

* DTE calculation；
* annualized premium points calculation；
* intrinsic value、time value 与 annualized time-value points calculation；
* annualized seller premium yield calculation；
* self-contained Point construction；
* calculation input 与 derived metric consistency validation。

确定性 invariant：

```text
same OptionMarketBasis
+ same calculation semantics
= same AnnualizedPremiumPoint[]
```

结果不得依赖 runtime clock、randomness、hidden mutable config、frontend state 或 HTTP transport details。

Basis 中的 contract 必须是 observation 当日的真实 active contract observation。post-expiry contract 不产生 Point；如果不兼容的 post-expiry fact 被提供给 Preparation，必须显式失败，不得 clamp DTE 或改用另一 observation。

## 7. DTE and Annualization Semantics

### 7.1 DTE

`dte_basis` 固定为：

```text
inclusive calendar days
```

公式：

```text
DTE = calendar_days(expiry_date - observation_date) + 1
```

示例：

```text
observation_date = 2026-09-21
expiry_date      = 2026-09-25
DTE              = 5
```

expiry day：

```text
DTE = 1
```

它不是 trading-day count、252-day basis、fractional year 或 hours-to-expiry。

### 7.2 Annualized premium points

`annualization_days` 固定为：

```text
365
```

公式：

```text
annualized_premium_points
= premium × 365 / DTE
```

语义是 `time-normalized premium points`。它不是 investment return、ROE、expected return、probability 或 trading signal。

### 7.3 Annualized time-value points

Intrinsic value 的唯一 calculation reference 是 Point 自包含的 underlying spot observation：

```text
Call intrinsic_value = max(underlying.price - strike, 0)
Put intrinsic_value  = max(strike - underlying.price, 0)

time_value = premium - intrinsic_value

annualized_time_value_points
= time_value × annualization_days / DTE
= time_value × 365 / DTE  # V1
```

不得用 same-expiry futures 或任何替代 reference 计算 intrinsic value。`futures = null` 不影响本 metric 的定义或计算。

`time_value` 不做 zero clamp。由供应的 market facts 计算出的 negative、zero 或 positive result 都是合法 analytical output，Preparation 必须原样保留；不得 repair、replace 或 reinterpret。

`intrinsic_value` 与 raw `time_value` 是上述确定性公式的中间量，不增加为 canonical Point fact。Point 已包含 `option_type`、`strike`、`premium`、`underlying.price`、`DTE` 与 `annualization_days`，足以独立解释并确定性复算该 metric。V1 只增加 canonical derived fact `annualized_time_value_points`。

### 7.4 Annualized seller premium yield

seller-yield denominator 固定为：

```text
underlying spot notional
```

MO calculation basis：

```text
contract_multiplier = 200 CNY / point

annualized premium cash
= annualized_premium_points × 200

underlying spot notional
= underlying.price × 200

annualized_seller_premium_yield
= annualized premium cash / underlying spot notional
= annualized_premium_points / underlying.price
```

multiplier 虽然在比率中数学抵消，仍属于经济计算语义，必须保留在 Point calculation basis。

denominator 不得改为 futures price、strike、exchange margin、strategy margin、portfolio capital 或 cash balance。未来若需要 margin return 或 capital ROE，必须增加新的 analytical metric，不得重定义本 metric。

## 8. Underlying and Futures References

### 8.1 Underlying

当前产品映射：

```text
MO → CSI1000 → 000852.SH
```

underlying 是 intrinsic value 与 seller-yield 的 analytical input，不只是 visualization metadata。它必须：

* 与 Point 使用同一 observation；
* 使用同一 resolved price type；
* 是 positive usable numeric fact。

缺少、malformed、为零或为负的 underlying price 不能成为合法 calculation reference 或 denominator，Preparation 必须显式失败。不得用 futures 替代 underlying。

### 8.2 Futures

futures 表示与 Point expiry 关联的 analytical futures reference。Premium 的合法结构性匹配条件是：

```text
candidates = as_of-active IM ordinary monthly contracts
             where IM.delist_date == MO.expiry_date

len(candidates) == 0 → futures = null
len(candidates) == 1 → 使用该合约同 observation、同 resolved price type 的 reference
len(candidates) > 1  → 显式失败
```

唯一匹配合约的目标日 daily row 必须唯一存在，selected price 必须是 usable numeric fact；缺失、重复或 malformed 时显式失败，而不是转成 `futures = null`。

futures：

* 不是 underlying；
* 不是 intrinsic-value reference；
* 不是 seller-yield denominator；
* 不是 option premium source；
* 不允许 nearest-expiry、main-contract、liquidity-based 或 price fallback。

## 9. Null, Zero, Absence and Sparse Collection

硬 invariant：

```text
0 != null
```

真实 contract observation 且：

```text
premium = 0
```

则：

```text
annualized_premium_points = 0
annualized_seller_premium_yield = 0
```

`annualized_time_value_points` 仍由 intrinsic value 公式决定：当 intrinsic value 为 `0` 时结果为 `0`；当 intrinsic value 为正时结果可以为负，不得因 `premium = 0` 而覆盖为 `0`。

真实 contract observation 且 selected premium unavailable：

```text
premium = null
annualized_premium_points = null
annualized_time_value_points = null
annualized_seller_premium_yield = null
```

该 Point 仍然存在。不得 fill zero、interpolate、fallback 到其他 price field/date 或删除 contract。

必须保持：

```text
no AnnualizedPremiumPoint
!=
AnnualizedPremiumPoint with premium = null
```

前者表示没有真实 contract observation；后者表示真实 contract observation 存在，但 selected premium fact 不可用。

active contract 缺少整个 `as_of` daily row 是 market-fact completeness failure，不得静默解释为无 Point。daily row 存在但 selected premium field 缺失，才使用 nullable premium 语义。

`AnnualizedPremiumPoint[]` 是真实 observation 的 sparse collection，不是 rectangular matrix。不同 expiry 可以有不同 strike universe；禁止创建 `expiry × all strikes` Cartesian product、synthetic null Point、synthetic contract、interpolation 或 nearest-strike substitution。

## 10. PremiumPlaneFramer

可选 downstream organizer：

```text
AnnualizedPremiumPoint[]
        ↓
PremiumPlaneFramer
        ↓
AnnualizedPremiumPlane
```

Framer 只负责：

* compatibility validation；
* grouping；
* deterministic ordering；
* coordinate framing；
* preserving sparse structure。

Framer 不得：

* 重新计算 DTE 或 financial metrics；
* interpolate、forward-fill 或 fallback；
* synthesize contract、Point 或 null cell；
* nearest-strike match；
* 覆盖或补充 Point 的 calculation context。

Points 只有在以下 shared analytical context 完全兼容时才可进入同一 Plane：

```text
ObservationAnchor
option_product
resolved price_type
calculation basis
underlying observation
```

以下内容预期可以在 Plane 内变化：

```text
expiry_date
strike
option_type
futures reference
```

不兼容 Point 必须被显式拒绝，不得静默 merge。

锁定关系：

```text
Point = analytical fact
Plane = deterministic organization of compatible Points
```

Plane 不拥有解释 child Point 所必需的唯一 calculation context。

Framer 对 direct Point consumers 是 optional downstream organizer；对 [MO Premium Plane product service](service-contract.md) 是形成成功 `AnnualizedPremiumPlane` result 的 required stage。

## 11. Consumers, HTTP Projection and Physical Representation

合法 downstream consumers 包括：

```text
PremiumPlaneFramer
TimeSeriesFramer
cross-expiry / strike-gradient analysis
historical comparison
model feature preparation
screening
backtesting
future forecasting input
```

这些 consumer 依赖 Core Points，不依赖 Web DTO。

HTTP relationship：

```text
AnnualizedPremiumPoint
!=
PremiumPlanePointDTO
```

HTTP projection 可以把重复的 underlying、DTE、futures、observation 或 calculation context 提升到 response / expiry level，但只能做无损 delivery normalization。它不得重新计算 metric、改变 analytical meaning、发明 Point 或把 wire layout 反向规定为 Core class layout。

canonical semantic model 不等于 mandatory physical execution representation。未来大规模历史分析可以使用 vectorized preparation、compact batch representation 或预先构建的 Point corpus；这些优化不得重定义 `AnnualizedPremiumPoint`。

## 12. Explicitly Deferred and Non-goals

本文档不决定：

```text
database schema
Point / Plane persistence
cache
Parquet format
historical corpus storage
materialized analytical tables
concrete Python class or module layout
FastAPI route / Pydantic DTO / OpenAPI
generated TypeScript
React / Plotly
```

Product service orchestration 与 request-scoped result boundary 已由 [service-contract.md](service-contract.md) 定义；本文档不重复其 workflow。

V1 可以完全 request-scoped + in-memory；这不是 persistence architecture 的承诺。

当前 analytical non-goals：

```text
IV / Greeks
moneyness classification
skew / volatility surface
cheap-expensive judgment / premium edge
probability forecast / trading signal
portfolio decision
margin-return analysis
generic analytical framework
```

## 13. Key Invariants

1. `AnnualizedPremiumPoint` 是最小 canonical analytical unit。
2. Point 自包含，不依赖 Plane、HTTP 或 frontend context 才可解释。
3. `OptionMarketBasis` 是薄的 reusable option-market fact boundary。
4. Premium 从自己的 goal-scoped Raw 构造 Basis，不消费 sibling Raw、`/mo-option-chain` response 或 DTO。
5. Point Preparation 唯一拥有 DTE 与三个 premium metrics 的计算，包括 intrinsic value 与 time value 中间计算。
6. DTE 使用 inclusive calendar days；expiry day 为 1。
7. annualization basis 为 365 days。
8. underlying spot 是 intrinsic-value reference；Call / Put 分别使用明确的 spot intrinsic 公式。
9. time value 不 clamp；negative、zero 与 positive result 都是合法 analytical output。
10. seller yield denominator 是 underlying spot notional。
11. futures 是 nullable expiry reference，不是 intrinsic-value reference 或 denominator。
12. zero、null 与 absence 是不同 domain states。
13. 真实 contract + missing selected premium 仍产生 Point，三个 derived metrics 均为 null。
14. active contract 缺 daily row 是 completeness failure，不是 nullable premium。
15. Point collection sparse，不要求跨 expiry strike alignment。
16. PlaneFramer 组织但不计算或合成 analytical facts。
17. 不兼容 analytical contexts 不得静默 framing。
18. Core model 独立于 HTTP、frontend 与 physical execution optimization。
19. Basis construction 只做 deterministic domain normalization；所有 premium derived calculations 只属于 Point Preparation。

## 14. Completion Check

仅阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 与本文档，应能唯一回答：

1. canonical analytical model 是什么，为什么是 Point 而不是 Plane？
2. Point 如何保持 self-contained，其 identity 与 coordinate 分别是什么？
3. Premium Raw 如何确定性构造 `OptionMarketBasis`，允许和禁止哪些 normalization？
4. Premium 为什么不依赖 Option Chain HTTP DTO？
5. DTE、annualized premium points、annualized time-value points 与 seller yield 在哪里、如何计算？
6. underlying 与 futures 分别扮演什么角色，为什么 futures 不参与 intrinsic value？
7. premium 为 zero、null，time value 为 negative，以及没有 Point 时分别表示什么？
8. strike 是否必须跨 expiry 对齐？
9. PlaneFramer 可以和不可以做什么，哪些 Points 可以共同 framing？
10. HTTP projection 为什么可以去重，却不能改变 Core semantics？
11. future backtest 是否可以使用其他 physical representation？
12. 哪些 implementation、operational 与 analytical decisions 被明确 deferred，orchestration authority 在哪里？
