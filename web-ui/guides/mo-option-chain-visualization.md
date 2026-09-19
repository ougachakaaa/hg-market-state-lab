# guides/mo-option-chain-visualization.md — MO option-chain visualization 的用户体验 / visualization contract authority

> 状态：authority。本文档锁定下一阶段第一个 Web vertical slice 的用户可见语义与可视化契约。
>
> 层级：本文档位于 `web-ui/ARCHITECTURE.md` 之下。模块级稳定边界（职责、依赖方向、数据来源边界）以 `web-ui/ARCHITECTURE.md` 为准。本文档只锁定这个 vertical slice 的输入、展示范围、散点语义与空/错误语义，不定义 HTTP schema、React implementation 或图表库选择。

---

## 1. Vertical slice 定义

下一阶段第一个明确的 Web vertical slice 是：

> 给定一个明确的 `target_trade_date`，用户可以在浏览器中查看该交易日完整的 MO 中证1000股指期权链价格分布。

第一版用户流程：

```text
open web UI
    ↓
select target_trade_date
    ↓
load MO option-chain data
    ↓
group contracts by expiry
    ↓
render one scatter chart per expiry
```

## 2. Input

```text
target_trade_date
```

必须显式选择日期。

完整的 read query identity 是 `target_trade_date + option_product + price_type`，其语义由 `market-snapshot/guides/mo-option-chain.md` 拥有。第一版 visualization 的固定值：`option_product = MO`（唯一支持），`price_type` 默认 `close`。

第一版不定义：

```text
latest
today
automatic fallback
date range
```

## 3. 页面共享语义

整个页面共享：

```text
target_trade_date
underlying reference price
```

其中 underlying reference price 是目标交易日的 CSI1000（000852.SH）underlying 在选定 `price_type` 下的价格，作为横轴上的市场基准点。它使用与 option 相同的 `price_type`（见 `market-snapshot/guides/mo-option-chain-read-contract.md` 第 2 节）。

## 4. Visualization scope

目标日期全部处于有效生命周期内的 MO option contracts 都属于目标展示范围。

按：

```text
expiry
```

分组。每个 expiry 一张独立 scatter chart，不把所有 expiry 混进同一张散点图。

## 5. Scatter semantics

每张图：

```text
X axis = strike / exercise price
Y axis = option selected price（默认 price_type = close）
```

并且：

* Call 与 Put 必须可视觉区分；
* 标记目标交易日的 CSI1000 underlying reference price（与 option 相同的 `price_type`）；
* underlying reference price 是横轴上的市场基准点；
* 每个 scatter point 代表一个 MO option contract。

单个 option point 的 point 级字段（来自 read contract）：

```text
instrument_id
strike
selected price
```

`expiry` 与 `option_type` 由 read contract 的父级 grouping 表达（`expiries[]` 的 `expiry_date`、`calls[]` / `puts[]` 的归属），不要求每个 point 重复携带（见 `market-snapshot/guides/mo-option-chain-read-contract.md` 第 6 节）。

这里锁定的是**用户可见语义**，不是 HTTP schema。selected price 的 null / zero 语义（`0` 是数据、`null` 是缺价）由 `market-snapshot/guides/mo-option-chain-read-contract.md` 第 3 节定义；`web-ui` 不得自行 fallback、补零或删除 contract。

## 6. 事实展示边界

Visualization 展示事实，不解释市场。

本 vertical slice 是：

```text
market facts
    ↓
deterministic data preparation
    ↓
delivery
    ↓
visualization
```

不是 market modeling。

禁止在本 vertical slice 引入：

```text
recommended strike
cheap / expensive option
mispricing
IV judgment
probability
expected range
market regime
noise zone
sell Call / Put region
trading signal
trading recommendation
```

## 7. Empty / error semantics

本文档不设计完整 UI error system。

只锁定：

> 如果目标日期无法取得支撑完整展示的数据，不得静默换日期或伪造/补齐 market facts。

## 8. 数据来源语义

本 vertical slice 需要的事实（contract identity、expiry、option_type、strike、selected price、underlying reference price）由 `market-snapshot/guides/mo-option-chain-read-contract.md` 定义的 MO Option Chain read contract 提供；`web-ui` 不直接理解 Source 或 Raw Artifact，也不直接消费 `csi1000-5d-analysis` 的 `snapshot.json`。

active universe、option type、expiry、selected price fallback、contract completeness 等业务语义均由 read contract 拥有，`web-ui` 不自行推导（ownership 与 invariants 见 `market-snapshot/guides/mo-option-chain.md` 第 2、5 节）。

## 9. 下一轮实现范围（本 Guide 不实现）

下一轮 Coding Agent 可以在不重新发明产品目标的情况下继续做：

```text
HTTP contract
FastAPI skeleton
React skeleton
scatter visualization
```

其中 HTTP contract / FastAPI skeleton 已由 `market-snapshot/guides/mo-option-chain-http-contract.md`（Stage 2）锁定：

```text
GET /mo-option-chain
query: target_trade_date / option_product / price_type（默认 close）
success response = read contract 第 8 节 semantic shape
error envelope: {"error": {"kind", "detail", "param"}}
error kind 闭集 + HTTP status mapping
```

前端只能依赖该 HTTP contract 的字段与 error kind，不得自行推导 universe / underlying / expiry / option type / fallback / completeness（见第 8 节）。

本 Guide 不定义（也不提前创建）：

```text
API versioning
auth
CORS policy
server deployment
React component tree
state-management
chart library
```
