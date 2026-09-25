# MO Premium Plane product service authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有 MO Premium Plane 的 request/application orchestration、stage ordering、stage responsibility、semantic failure propagation 与 product result boundary。Source/Raw/universe 见 [data authority](data.md)，domain normalization、financial calculation 与 framing 见 [backend authority](backend.md)，transport 见 [HTTP contract](http-contract.md)。

---

## 1. Request and Result Boundary

V1 product service 接受 normalized query：

```text
as_of
option_product = MO
resolved price_type = open | high | low | close
```

省略 `price_type` 时在进入 orchestration 前解析为 `close`。产品成功结果是：

```text
request-scoped AnnualizedPremiumPlane
```

V1 final Plane 可以只存在于内存中，不要求 canonical persisted final output、database、cache、Parquet 或 materialized Point corpus。Premium-owned Raw 仍按 [data authority](data.md) 持久化，以形成 Capture 与 deterministic Preparation 之间的契约。

## 2. Canonical Orchestration

每个请求严格按以下方向执行：

```text
normalized query
(as_of + option_product + resolved price_type)
        ↓
run canonical observation availability Capture
(index_daily: 000852.SH + as_of)
and write index_daily.json
        ↓
explicit no-observation → date_not_available
observation exists      → admit observation
indeterminate failure   → premium_plane_unavailable
        ↓ admitted observation only
run remaining required shared Source Captures
with Premium-owned product scopes
        ↓
write remaining Premium goal-scoped Raw
        ↓
construct OptionMarketBasis
        ↓
AnnualizedPremiumPoint Preparation
        ↓
AnnualizedPremiumPoint[]
        ↓
PremiumPlaneFramer
        ↓
AnnualizedPremiumPlane
        ↓
return product result to HTTP delivery adapter
```

所需 Captures 是：

```text
mo_option_basic
mo_option_daily
index_daily
im_futures_basic
im_futures_daily
```

availability probe 复用 `index_daily` Capture，并把其 result 写入 Premium-owned `index_daily.json`；不得为 probe 创建另一套 Capture identity、临时 semantic source 或替代 observation。Source response 成功但该 Raw write 失败时，probe 未成功完成，分类为 `premium_plane_unavailable`。probe admission 后，其他 Capture 的实际调用可以按 Source API 约束调度，但不得改变上图的 semantic dependency：Basis 只能消费完整 Premium Raw，Point Preparation 只能消费合法 Basis，Framer 只能消费 prepared Points，HTTP 只能消费完整 product result。

## 3. Stage Ownership

| Stage | Owns | Must not own |
| --- | --- | --- |
| Product service | request orchestration、availability-result admission、semantic failure classification/propagation、result boundary | Source fields、financial formulas、HTTP DTO |
| Source Capture | Source calls、product-declared Source-domain scope、minimal normalization、Premium Raw production | Basis join、analysis formulas、Plane framing |
| Basis construction | deterministic joins、domain vocabulary normalization、unified price projection、legitimate futures matching | DTE、annualization、seller yield、HTTP projection |
| Point Preparation | DTE、annualized premium points、annualized time-value points、seller yield、self-contained Points | Capture、transport、presentation |
| PremiumPlaneFramer | compatibility validation、sparse organization、deterministic framing | recalculation、interpolation、synthetic facts |
| HTTP adapter | query serialization/transport validation、product result projection、status/envelope mapping | Source calls、Raw construction、domain repair or calculation |

Product service 不得用 sibling product Raw、read model、DTO 或 final artifact 代替任何 stage。

## 4. Product Semantic Failures

Service 必须按已知 data/domain condition 分类 failure；不得把所有异常笼统解释为同一个未分类的 `catch Exception → 503`。具体 exception class 不属于本 authority。

### 4.1 `date_not_available`

只表示：

```text
query shape valid
AND product/query supported
AND canonical availability probe completed successfully
AND exact 000852.SH + as_of observation count = 0
```

这是 requested trade-date observation 本身不可服务的唯一 V1 evidence。不得用 generic missing data、Source/Capture exception、incomplete product facts 或 analytical failure 产生此 kind。不得 fallback 到 nearest、previous、latest 或其他日期，也不得返回替代 observation。

### 4.2 `premium_plane_unavailable`

表示 canonical probe 没有明确证明 observation 不可服务，或 observation admitted 后无法构造合法、完整、非空的 analytical Plane，包括：

```text
availability probe Source/transport exception or indeterminate response
Capture or Raw write failure
cannot determine active MO universe
active MO contract missing or duplicate daily row
malformed selected option premium
duplicate or inconsistent structural facts
admitted underlying later missing from Raw/Basis
underlying duplicate row or selected price null, malformed, zero or negative
multiple legitimate IM matches
matched IM daily row missing or duplicate
matched IM selected price unavailable or malformed
OptionMarketBasis incompatible or incomplete
Point Preparation consistency failure
Plane framing compatibility failure
zero real analytical Points
```

合法的 option selected premium null 不属于 failure；它产生 premium 与 derived metrics 为 null 的真实 Point。无 legitimate IM match 也不属于 failure；它产生 `futures = null`。两者与上述 required-fact failures 不得混淆。

observation 一旦 admitted，任何 downstream failure 都不得重新降级为 `date_not_available`。

### 4.3 Decision Table

| Condition | Product result |
| --- | --- |
| query invalid or unsupported | transport/application input rejection；不进入 availability decision |
| canonical probe 成功且精确匹配 observation 为零 | `date_not_available` |
| availability probe 发生 generic Source/transport/Capture/Raw-write failure，或 response indeterminate | `premium_plane_unavailable` |
| observation exists but underlying row duplicate，或 selected price null/malformed/zero/negative | `premium_plane_unavailable` |
| observation admitted 后 underlying row 在 Raw/Basis 缺失 | `premium_plane_unavailable` |
| active MO daily row missing or duplicate | `premium_plane_unavailable` |
| active MO row 存在且 selected option premium 为 null | success Point with `premium = null` and null derived metrics |
| no legitimate IM expiry match | success with `futures = null` |
| legitimate matched IM daily fact missing/duplicate，或 selected price null/malformed | `premium_plane_unavailable` |
| Basis、Point Preparation 或 Framer fails | `premium_plane_unavailable` |
| complete non-empty Plane | success `AnnualizedPremiumPlane` |

## 5. Atomic Result and Delivery Handoff

失败 response 不携带 partial Raw interpretation、partial Points、partial Plane 或替代 observation。任何 stage failure 都终止 result construction 并传播明确的 product semantic failure。

HTTP adapter 的输入只能是二者之一：

```text
complete request-scoped AnnualizedPremiumPlane
OR
classified product semantic failure
```

HTTP status 与 error envelope 由 [HTTP contract](http-contract.md) 映射。HTTP adapter 不重试或修复 analytical facts，不直接调用 Source，也不重建 Basis、Point 或 Plane；它不得重新执行 availability detection 或改变 product service 已分类的 failure kind。

## 6. Non-goals

本文档不设计：

```text
generic workflow or pipeline engine
DAG or registry
retry/cache framework
scheduler
database or persisted final Plane
Python class/module layout
FastAPI route or DTO
```

## 7. Completion Check

仅阅读产品入口与本文档，应能唯一回答：

1. 谁按什么顺序编排 Capture、Basis、Point、Framer 与 delivery？
2. 每个 stage 拥有和禁止拥有什么？
3. service 成功时向 HTTP 交付什么，final Plane 是否必须持久化？
4. 哪一个 exact fact 是 observation availability probe，什么结果才是 `date_not_available`？
5. generic Source exception 与 observation admission 后的 failure 如何分类？
6. missing underlying observation 与 invalid underlying analytical fact 如何区分？
7. null option premium 与 null futures 为什么不是 product failure？
8. 失败时是否允许 partial Plane、fallback date、HTTP repair 或 reclassification？
