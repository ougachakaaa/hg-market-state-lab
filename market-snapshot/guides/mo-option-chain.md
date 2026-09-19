# guides/mo-option-chain.md — MO Option Chain data product authority（导航入口）

> 状态：authority（Stage 1）。本文档锁定 `MO Option Chain` 作为与 `csi1000-5d-analysis` 并列的独立 deterministic data product 的**产品定位、ownership、query identity、invariants 与导航**。
>
> 本阶段为 authority only：不实现 Python、FastAPI、HTTP endpoint、Pydantic、React、chart、tests。
>
> 层级：本文档位于 `market-snapshot/ARCHITECTURE.md` 之下，是 MO Option Chain 的入口 authority。具体 data contract（Source / Raw / universe / completeness）见 `guides/mo-option-chain-data.md`；具体 read contract（price / null / grouping / ordering / response / failure）见 `guides/mo-option-chain-read-contract.md`；HTTP transport（endpoint / DTO / error envelope / status mapping）见 `guides/mo-option-chain-http-contract.md`。本文档只承载稳定边界与导航，不重复子 Guide 的字段细节。
>
> 实现本任务的 Agent 先读本文档，再按任务所在层进入对应子 Guide。

---

## 1. 定位与架构关系

`MO Option Chain` 是 `market-snapshot` 中与现有 `csi1000-5d-analysis` **并列**的独立 deterministic data product，不是后者的 secondary projection。

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

两条 Preparation 共享底层 Source facts / Capture capability，但**互不依赖彼此的最终 artifact**；且：

```text
shared Capture capability ≠ shared goal-scoped Raw Artifact
```

即 Capture 组件语义可复用，但每个 data product 拥有自己的 goal-scoped Raw Artifact（见 `guides/mo-option-chain-data.md`）。

因此 `MO Option Chain` 不得依赖：

```text
CSI1000 120-day history completeness
IM futures completeness
CSI1000 5D derived metrics
csi1000-5d-analysis snapshot.json
```

只依赖构造目标日期 option chain 真正需要的 Source facts。

## 2. Ownership

### market-snapshot owns（数据语义）

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

### HTTP delivery owns（transport）

```text
transport
request serialization
response serialization
HTTP error representation
```

HTTP 不重新定义 market semantics。其最小 transport contract（endpoint / query 参数 / success 与 error envelope / error kind 闭集 / HTTP status mapping）落在 `guides/mo-option-chain-http-contract.md`（Stage 2）。

### web-ui owns（presentation）

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

caller input：

```text
target_trade_date   required    （显式，YYYY-MM-DD）
option_product      required    （显式；V1 唯一支持 = MO）
price_type          optional    （缺省 = close）
```

normalized query identity：

```text
target_trade_date + option_product + resolved price_type
```

* `target_trade_date` 表示用户希望查看哪个交易日的期权链状态；不是 request time / today / latest / current date，V1 要求显式输入，格式 `YYYY-MM-DD`。
* `option_product` 表示期权产品，不是 underlying（见第 4 节）。V1 唯一支持 `MO`，但保留该维度供未来 `IO` / `HO` 扩展而不改 query identity。
* `price_type` 缺省时按 authority 固定默认 `close` 解析；解析发生在任何数据准备之前。response 回显的是 **resolved price_type**，不是调用方的省略态。可用取值见 `guides/mo-option-chain-read-contract.md` 第 1 节。

因此 query identity 始终由三个**已解析**的维度确定：`target_trade_date` 与 `option_product` 必须由调用方显式给出，`price_type` 可省略但归一化后必有确定值。

## 4. Product → Underlying Mapping

`option_product` 与 underlying 的对应关系由 `market-snapshot` 拥有。

```text
MO → CSI1000 → 000852.SH
```

调用方只指定 `option_product = MO`，data product 根据 authority 确定 `underlying = 000852.SH`；不得同时指定两个可能矛盾的输入。response 必须显式返回 underlying identity（见 read contract）。

区分：

```text
MO        = option product
000852.SH = underlying instrument
IM        = futures product（不是 MO 的 underlying）
```

不得用 `IM price` 替代 `CSI1000 underlying price`。

未来可扩展 `IO → 000300.SH`、`HO → 000016.SH`，V1 不实现。

## 5. Invariants

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

## 6. V1 Non-goals

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

## 7. Delivery Boundary

本数据产品 read model 的 transport / HTTP delivery 由 HTTP delivery owns（见第 2 节）。

```text
HTTP Contract + FastAPI Foundation
```

已由 `guides/mo-option-chain-http-contract.md`（Stage 2）锁定：

```text
endpoint URL
HTTP method
request/query schema
response JSON shape
error envelope / error kind 闭集
HTTP status mapping
```

仍然 deferred：

```text
真实 Capture → Raw → MO Option Chain Preparation → read model 实现
Data Service mo-option-chain 实现
把真实 read model 接到 HTTP service boundary 上
```

## 8. Navigation

```text
mo-option-chain.md（本文档：产品定位 / ownership / query identity / invariants / navigation）
    ├→ mo-option-chain-data.md          （Source / Raw / universe / completeness）
    ├→ mo-option-chain-read-contract.md （price / null / grouping / ordering / response / failure）
    └→ mo-option-chain-http-contract.md （HTTP transport：endpoint / DTO / error / status）
```

实现 guidance：

* 实现 Source Capture / Raw Artifact 或判断 completeness / universe → 读 `mo-option-chain-data.md`。
* 实现 Preparation 的 read model 或 HTTP serialization 语义 → 读 `mo-option-chain-read-contract.md`。
* 实现 endpoint / DTO / error envelope / status mapping → 读 `mo-option-chain-http-contract.md`。
* 以上都需要先读本文档的定位与 invariants。

## 9. Deferred（下一阶段再决定）

```text
MO Option Chain Preparation 实现
Data Service mo-option-chain 实现
真实 read model provider 接入 HTTP service boundary
tests（真实数据链路）
```

Raw Artifact 组织方式已在本轮锁定（见 `mo-option-chain-data.md`），不再 deferred。
HTTP contract / FastAPI foundation 已由 `guides/mo-option-chain-http-contract.md` 锁定，不再 deferred。
