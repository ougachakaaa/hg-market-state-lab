# guides/mo-option-chain.md — MO Option Chain deterministic data product 与 read contract authority

> 状态：authority（Stage 1）。本文档锁定 `MO Option Chain` 作为与 `csi1000-5d-analysis` **并列**的独立 deterministic data product 的业务语义，以及它与未来 HTTP delivery / `web-ui` 之间的稳定 read contract。
>
> 本阶段为 **authority only**：不实现 Python、FastAPI、HTTP endpoint、Pydantic、React、chart、tests。
>
> 层级：本文档位于 `market-snapshot/ARCHITECTURE.md` 之下，与 `guides/csi1000-5d-analysis-data.md`、`guides/csi1000-5d-analysis-snapshot.md`、`guides/data-services.md` 并列。架构层面的稳定边界以 `market-snapshot/ARCHITECTURE.md` 为准（尤其第 0 节术语、第 2 节核心架构、第 3 节 Raw/Preparation 边界、第 8 节 Guide 职责）。本文档是后续 MO Option Chain implementation 的主要 authority。
>
> 实现本 Guide 任务的 Agent 应先阅读 `market-snapshot/ARCHITECTURE.md` 第 2、3 节，再按本文档执行。

---

## 1. 定位与架构关系

`MO Option Chain` 不再作为：

```text
csi1000-5d-analysis/snapshot.json
    ↓
secondary projection
```

存在。

它是 `market-snapshot` 中与现有 CSI1000 analysis preparation **并列**的独立 deterministic data product。

```text
External Sources
      ↓
Shared Source Capture capabilities
      │
      ├──────────────────────────────┐
      ↓                              ↓
CSI1000 5D Analysis            MO Option Chain
Preparation                    Preparation
      ↓                              ↓
analysis-ready artifact        option-chain read model
                                      ↓
                                HTTP delivery（future）
                                      ↓
                                   web-ui
```

两条 Preparation 可以共享底层 Source facts / Capture capability，但**互不依赖彼此的最终 artifact**。

因此 `MO Option Chain` 不得依赖：

```text
CSI1000 120-day history completeness
IM futures completeness
CSI1000 5D derived metrics
csi1000-5d-analysis snapshot.json
```

只依赖构造目标日期 option chain 真正需要的 Source facts。

## 2. Ownership

### 2.1 market-snapshot owns（数据语义）

```text
option product identity
option product → underlying mapping

contract universe
contract lifecycle
contract identity

option type
strike
expiry

target-date option market facts
target-date underlying market facts

deterministic grouping
deterministic ordering

selected price semantics
null / zero semantics
completeness semantics
```

### 2.2 HTTP delivery owns（transport）

```text
transport
request serialization
response serialization
HTTP error representation
```

HTTP 不重新定义 market semantics。

### 2.3 web-ui owns（presentation）

```text
presentation
chart rendering
visual distinction
interaction
layout
```

`web-ui` 不得自行推导：

```text
which contracts are active
which underlying belongs to MO
expiry
option type
selected price fallback
contract completeness
```

## 3. Query Identity

一个 MO Option Chain query 由三个业务输入共同确定：

```text
OptionChainQuery =
    target_trade_date
    + option_product
    + price_type
```

三者共同决定一次 read 请求的完整语义；缺少或隐式推导其中任何一项都不属于 V1 contract。

## 4. target_trade_date

`target_trade_date` 表示：

> 用户希望查看哪个交易日的期权链状态。

它不是：

```text
request time
today
latest
current date
```

V1 要求**显式输入**。

格式：

```text
YYYY-MM-DD
```

一个成功请求要求该日期：

```text
is a valid trading date
AND
required Source data exists for that date
AND
does not exceed the latest date for which the required option-chain Source facts are available
```

这里的“不能是未来日期”不是简单定义为：

```text
target_trade_date <= system today
```

而是语义上：

```text
target_trade_date <= latest date with required Source option-chain data
```

V1 不要求提前提供：

```text
latest_available_trade_date
available-date calendar
availability endpoint
```

如果请求日期：

```text
不是交易日
数据尚未发布
Source 无数据
```

允许请求直接失败并返回相应原因。

严格禁止：

```text
automatic fallback to previous trading day
automatic fallback to latest available date
silent date substitution
```

## 5. option_product

请求必须显式表达期权产品：

```text
option_product
```

V1 唯一支持：

```text
MO
```

但 contract 从第一版就保留 `option_product` 这一维度，使未来能够扩展：

```text
IO
HO
...
```

而不重新设计 query identity。

### 5.1 Product is not underlying

必须区分：

```text
MO
```

和：

```text
CSI1000 / 000852.SH
```

其中：

```text
MO        = option product
000852.SH = underlying instrument
```

同样：

```text
IM
```

是 futures product，不是 MO 的 underlying。

不得使用：

```text
IM price
```

替代：

```text
CSI1000 underlying price
```

除非未来另外定义 futures reference semantic。

## 6. Product → Underlying Mapping

`option_product` 与 underlying 的对应关系由 `market-snapshot` 拥有。

V1：

```text
MO
→
CSI1000
→
000852.SH
```

调用方不需要同时指定：

```text
option_product = MO
underlying = 000852.SH
```

避免产生两个可能互相矛盾的输入。

query 只指定：

```text
option_product = MO
```

data product 根据 authority 确定：

```text
underlying = 000852.SH
```

response 必须显式返回 underlying identity，使结果自解释。

未来可以自然扩展：

```text
MO → 000852.SH
IO → 000300.SH
HO → 000016.SH
```

但 V1 不要求现在实现 IO / HO。

## 7. Source Facts Required by MO Option Chain

MO Option Chain 只需要以下事实能力：

```text
option contract facts
option target-date daily facts
underlying target-date daily fact
```

对于当前 MO / Tushare 场景，对应：

```text
opt_basic     → Source Capture mo_option_basic
opt_daily     → Source Capture mo_option_daily
index_daily   → Source Capture index_daily（000852.SH）
```

现有 Capture capability 应尽量复用。这三个 Capture 的 Source / Raw Artifact 契约继续由 `guides/csi1000-5d-analysis-data.md` 第 4.1、4.2、4.3 节定义；本文档不重新定义其 Source 字段或 Raw 语义。

本数据产品**不得**因为历史 CSI1000 analysis 的需求而额外要求：

```text
120-day index history
IM futures
technical derived metrics
```

underlying 只需要目标交易日单日的 `index_daily` fact（供 `price_type` 选价使用），不需要历史窗口。

## 8. Complete Contract Universe

完整 MO option chain 的 universe 由 contract facts 决定。

V1：

```text
option_product = MO
AND
exchange = CFFEX
AND
list_date <= target_trade_date <= delist_date
```

这定义：

```text
active contract universe
```

必须保留目标日期所有属于该 universe 的 contract。

不得按以下条件过滤：

```text
strike distance
ATM distance
volume
open interest
price availability
liquidity
expiry preference
Call / Put
market interpretation
```

因此：

> contract universe 独立于用户选择的 `price_type`。

这是 V1 的核心 invariant（见第 25 节 Invariant 2）。

即：

```text
same date
+ same option_product
+ different price_type
```

必须产生完全相同的：

```text
contract identities
expiry groups
Call / Put membership
strikes
```

只有：

```text
price
```

允许发生变化。

## 9. Contract Universe vs Daily Fact

必须区分：

```text
contract exists
```

和：

```text
contract has a usable selected price
```

contract universe 由：

```text
contract facts + lifecycle
```

决定。

daily market facts 只是给这些 contract 添加目标交易日数据。

因此不得使用：

```text
opt_daily returned rows
```

反向定义 contract universe。

正确关系：

```text
contract facts
    ↓
active universe

active universe + daily facts
    ↓
complete target-date chain
```

## 10. Daily-row Completeness

对于 active universe 中的每一个 contract：

```text
必须存在 target_trade_date 对应的 daily fact row
```

如果：

```text
active contract + no daily row
```

这是：

```text
chain completeness failure
```

整个 request 必须失败。

不得：

```text
silently drop contract
return partial chain
infer price
read another date
```

因此：

```text
missing contract daily row
```

和：

```text
daily row exists but selected field is null
```

是两个不同状态（后者见第 13 节）。

## 11. price_type

V1 支持：

```text
open
high
low
close
```

默认：

```text
close
```

`volume` 不属于 `price_type`，因为：

```text
volume is not a price
```

V1 也不支持：

```text
settle
pre_close
pre_settle
```

这些以后有明确需求时再增加。尤其 `settle` 暂不进入 V1，因为 underlying index 没有与期权 settlement 完全对称的统一 reference semantic。

## 12. Unified Price Semantics

同一次 query 中：

```text
options
AND
underlying
```

必须使用相同的：

```text
price_type
```

例如 `price_type = close`：

```text
option.price     ← option close
underlying.price ← CSI1000 close
```

`price_type = high`：

```text
option.price     ← option high
underlying.price ← CSI1000 high
```

不得产生：

```text
option high + underlying close
```

这种混合语义。

因此整个 response 表示的是：

> 目标交易日在同一种 daily price semantics 下的 option chain 与 underlying reference。

## 13. Selected Price Null Semantics

必须区分：

```text
0
```

和：

```text
null
```

### 13.1 Numeric zero

如果 Source 返回：

```text
0
```

这是一个合法 numeric fact，必须原样返回：

```text
price = 0
```

不得解释为 missing。

### 13.2 Null / missing selected field

如果 active contract：

```text
daily row exists
```

但选定的 `price_type` 对应字段没有 Source fact：

```text
null
or
missing
```

则：

```text
price = null
```

contract 仍然保留在 response 中。

不得：

```text
fill zero
fallback to close
fallback to settle
fallback to previous date
drop contract
```

因此：

```text
Contract Completeness ≠ Selected Price Availability
```

一个 contract 可以：

```text
exist in complete chain
AND
price = null
```

## 14. Underlying Price

与 option contract 不同，underlying 是整个 visualization 的共享 reference。

因此成功 response 要求：

```text
underlying selected price
```

必须存在且是 usable numeric fact。

如果目标日期的 underlying `price_type`：

```text
不存在
或 malformed
```

则：

```text
request fails
```

不得返回一个没有有效 underlying reference 的 successful chain。

## 15. Contract Business Identity

每个 option contract 必须携带稳定业务 identity。

read contract 使用：

```text
instrument_id
```

表达这一概念。

V1 可以直接使用现有 Source `ts_code` 的值，例如：

```text
MO2609-C-7000.CFE
```

但 read contract 的业务语义是：

```text
stable option instrument identity
```

而不是：

```text
frontend must understand Tushare ts_code semantics
```

因此未来即使 Source 改变，也不需要修改 read contract 中 identity 这一业务概念。

underlying 的 identity 同样使用：

```text
instrument_id = "000852.SH"
```

## 16. Grouping

response 不返回需要 React 自行解释的 flat chain。

Preparation 必须完成 deterministic organization。

一级：

```text
group by expiry
```

二级：

```text
group by option type
```

逻辑结构：

```text
expiries[]
    expiry_date

    calls[]
    puts[]
```

Call / Put grouping 属于数据 contract，不属于 React 的业务判断；`option_type` 由 `calls[]` / `puts[]` 的数组归属表达，不要求 read contract 在每个 contract 上重复携带 `option_type` 字段。

## 17. Ordering

deterministic ordering 属于 contract。

### 17.1 Expiry

```text
expiry_date ascending
```

### 17.2 Inside Call / Put group

```text
strike ascending
```

如果出现相同 strike 的多个 instrument：

```text
instrument_id ascending
```

作为稳定 tie-break。

整体：

```text
expiry_date ascending
    ↓
option_type grouping
    ↓
strike ascending
    ↓
instrument_id ascending
```

React 不需要自行决定业务顺序。

## 18. Read Contract（semantic shape）

推荐 V1 semantic response：

```json
{
  "target_trade_date": "2026-09-17",
  "option_product": "MO",
  "price_type": "close",

  "underlying": {
    "instrument_id": "000852.SH",
    "price": 7312.45
  },

  "expiries": [
    {
      "expiry_date": "2026-09-25",

      "calls": [
        {
          "instrument_id": "MO2609-C-7000.CFE",
          "strike": 7000.0,
          "price": 356.4
        },
        {
          "instrument_id": "MO2609-C-7200.CFE",
          "strike": 7200.0,
          "price": null
        }
      ],

      "puts": [
        {
          "instrument_id": "MO2609-P-7000.CFE",
          "strike": 7000.0,
          "price": 41.8
        }
      ]
    }
  ]
}
```

这是 semantic authority。

不是：

```text
Pydantic definition
HTTP schema implementation
OpenAPI definition
```

这些属于下一阶段。

字段到 Source 的确定性投影（Preparation 职责，非 web-ui 职责）：

```text
instrument_id   ← Source ts_code
strike          ← Source exercise_price（numeric）
expiry_date     ← Source maturity_date（已归一化为 YYYY-MM-DD）
price           ← Source opt_daily 的 price_type 字段
underlying.price← Source index_daily（000852.SH）的 price_type 字段
```

`call_put → calls[] / puts[]` 的归属是 Preparation 的确定性组织，`web-ui` 不参与该判断。

## 19. Response Must Be Self-describing

任何成功 response 单独存在时，都必须可以回答：

```text
哪一天？
哪个期权产品？
使用什么价格？
underlying 是谁？
有哪些 expiry？
有哪些 contracts？
```

因此必须返回：

```text
target_trade_date
option_product
price_type
underlying identity
```

不得依赖 React 的 local state 才知道这些信息。

## 20. Success Semantics

成功表示：

```text
query identity is valid
+
underlying target-date fact exists
+
active option universe can be determined
+
every active contract has its target-date daily row
+
structural contract facts are complete
```

selected option price：

```text
可以为 null
```

而不会破坏 chain completeness。

因此即使：

```text
some contracts
or even all contracts
have price = null
```

data product 仍然可以在结构上返回完整 chain。

这表示：

```text
chain exists
selected price facts unavailable
```

而不是：

```text
contracts do not exist
```

## 21. Failure Semantics

以下属于 failure：

```text
invalid target_trade_date format

target_trade_date cannot be served by Source
non-trading / unavailable date

unsupported option_product

unsupported price_type

cannot determine product → underlying

cannot determine active contract universe

active contract missing target-date daily row

duplicate / inconsistent contract identity

required structural field missing or malformed

underlying selected price unavailable or malformed
```

V1 暂不锁定：

```text
HTTP status code
error JSON shape
exception class
```

只锁 semantic categories。

Stage 2 再映射 transport semantics。

## 22. No Silent Recovery

任何 failure 均不得通过以下方式隐藏：

```text
fallback date
nearest trade date
latest available date
previous close
settlement substitution
zero fill
contract dropping
partial chain
fabricated instrument
```

## 23. 与 CSI1000 5D Analysis 的关系

现有：

```text
csi1000-5d-analysis
```

保持原有 authority，本轮不修改其：

```text
120-day window
IM semantics
derived fields
snapshot structure
```

新的 MO Option Chain 与其关系是：

```text
shared Source / Capture capabilities
```

而不是：

```text
MO Option Chain depends on CSI1000 analysis artifact
```

即：

```text
Raw / Source facts
      ├→ CSI1000 5D Analysis
      └→ MO Option Chain
```

## 24. V1 Non-goals

本阶段不进入：

```text
IO / HO implementation

IV
Greeks
moneyness
ATM / OTM / ITM
liquidity judgment
recommended strike
market interpretation
trading signals

volume visualization
open-interest visualization
settlement-price mode

date range
latest shortcut
automatic fallback

database
cache
auth
websocket
```

## 25. Invariants

后续实现至少必须满足以下 invariants。

### Invariant 1 — Product identity

```text
MO determines CSI1000 / 000852.SH
```

React 不维护该映射。

### Invariant 2 — Universe independence

```text
changing price_type must not change contract universe
```

### Invariant 3 — Complete active universe

所有 target date active MO contracts 均进入 chain。

### Invariant 4 — No silent dropping

selected price 为 null 不允许删除 contract。

### Invariant 5 — Daily completeness

active contract 没有对应 daily row → fail。

### Invariant 6 — Zero is data

```text
0 != null
```

### Invariant 7 — Unified price semantics

options 和 underlying 使用相同 `price_type`。

### Invariant 8 — Deterministic organization

```text
expiry ascending
→ Call / Put group
→ strike ascending
→ instrument_id tie-break
```

### Invariant 9 — Self-describing response

response 自身携带：

```text
date
product
price type
underlying
```

### Invariant 10 — No dependency on CSI1000 5D artifact

MO Option Chain 不依赖：

```text
csi1000-5d-analysis/snapshot.json
```

## 26. Delivery Boundary

本数据产品的 read model 的 transport / HTTP delivery 由 HTTP delivery owns（见第 2.2 节），并属于下一阶段：

```text
HTTP Contract + FastAPI Foundation
```

本阶段只锁定 semantic read contract 与 failure semantic categories，不定义：

```text
endpoint URL
HTTP method
request schema
response JSON schema
OpenAPI model
status code
```

## 27. Deferred（下一阶段再决定）

```text
HTTP contract / FastAPI foundation
MO Option Chain Preparation 实现
Data Service mo-option-chain 实现
tests

MO read model 的 Raw Artifact 组织方式
（复用 csi1000-scoped Raw 目录，还是专用 goal-scoped Raw 目录）
```

上述 Raw Artifact 组织方式属于 implementation，本阶段只锁定：MO read model 需要哪些 fact capability、不依赖 csi1000-5d-analysis output、且不要求历史窗口 / IM / 派生指标。

## 28. 完成自检

仅阅读本 Guide（及其引用的 `market-snapshot/ARCHITECTURE.md`）应能明确回答：

1. MO 是不是 underlying？
2. MO 对应哪个 underlying？
3. 什么定义 complete option chain？
4. active universe 从哪里来？
5. daily row 缺失怎么办？
6. selected price null 怎么办？
7. 0 怎么办？
8. 有哪些 price_type？默认是什么？
9. underlying 使用什么 price semantics？
10. 如何 group expiry？
11. 如何 group Call / Put？
12. 如何排序？
13. contract identity 是什么？
14. MO Chain 是否依赖 CSI1000 5D snapshot？

这些语义全部应能从本文档直接得到答案。达到该状态后，Stage 1 完成，下一阶段才进入 implementation。
