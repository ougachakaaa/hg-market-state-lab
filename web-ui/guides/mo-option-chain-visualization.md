# guides/mo-option-chain-visualization.md — MO option-chain visualization 的用户体验 / visualization contract authority

> 状态：authority。本文档锁定第一个 Web vertical slice 的用户可见语义与可视化契约。
>
> 层级：本文档位于 `web-ui/ARCHITECTURE.md` 之下。模块级稳定边界（职责、依赖方向、数据来源边界）以 `web-ui/ARCHITECTURE.md` 为准。本文档只锁定这个 vertical slice 的输入、展示范围、散点语义与空/错误语义，不定义 HTTP schema、React implementation 或图表库选择。

---

## 1. Vertical slice 定义

第一个明确的 Web vertical slice 是：

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
strikeHalfRangePoints
```

其中 underlying reference price 是目标交易日的 CSI1000（000852.SH）underlying 在选定 `price_type` 下的价格，作为横轴上的市场基准点。它使用与 option 相同的 `price_type`（见 `market-snapshot/guides/mo-option-chain-read-contract.md` 第 2 节）。

`strikeHalfRangePoints` 是整个页面共享的 strike viewport 半宽，第一版默认值与最小值均为 `300` points，调整步长为 `100` points。所有 expiry 图使用同一个 x-domain，以 shared underlying spot 计算：

```text
lower = floor((spot - strikeHalfRangePoints) / 100) * 100
upper = ceil((spot + strikeHalfRangePoints) / 100) * 100
```

例如 `spot = 7501`、`strikeHalfRangePoints = 300` 时，x-domain 为 `7200 .. 7900`。它至少覆盖 spot 两侧各指定距离，再向外对齐至 100-point visualization grid。`100 points` 只定义图表网格，不定义 MO contract universe。

这是 chart viewport，不是 contract filter：backend 仍返回完整 active MO chain；视窗外的 contracts 不从 response 或合约明细中删除，Web UI 也不把该范围下推为 Source、Preparation 或 HTTP 过滤规则。

### Price display precision

Web UI 中所有用户可见的 price-domain 数值统一显示 **1 位小数**：underlying price、各到期日 IM futures price、option selected price、strike、图表轴刻度、tooltip、reference label 与合约明细均适用。例如 `7312.45 → 7312.5`、`7000 → 7000.0`、`0 → 0.0`、`null → —`。

这是 presentation formatting，不是 data rounding。不得修改 backend / read model / HTTP 的 numeric fact，也不得影响计算、排序、chart coordinate 或 contract identity。

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
* 仅在该 expiry 的 `futures` 非 `null` 时显示 IM futures reference（合约 identity 与所选价格），在图中作为带标识的横轴价格参考；为 `null` 时显示“无同到期 IM 合约”，不绘制 IM 参考线或标注，也不推断替代合约；
* underlying reference price 是横轴上的市场基准点；
* 每个 scatter point 代表一个 MO option contract。

单个 option point 的 point 级字段（来自 read contract）：

```text
instrument_id
strike
selected price
```

`expiry` 与 `option_type` 由 read contract 的父级 grouping 表达（`expiries[]` 的 `expiry_date`、`calls[]` / `puts[]` 的归属），不要求每个 point 重复携带（见 `market-snapshot/guides/mo-option-chain-read-contract.md` 第 6 节）。

这里锁定的是**用户可见语义**，不是 HTTP schema。selected price 的 null / zero 语义（`0` 是数据、`null` 是缺价）由 `market-snapshot/guides/mo-option-chain-read-contract.md` 第 3 节定义；`web-ui` 不得自行 fallback、补零或删除 contract。`price=null` 的合约没有可绘制的纵坐标，因此不显示散点，但仍保留在合约明细中，并在对应到期日提示缺价数量；`price=0` 是可绘制的数值。如果某到期日全部合约缺价，页面显示无可绘制价格的状态，仍保留该到期日及其合约明细。

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

本 vertical slice 需要的事实（contract identity、expiry、option_type、strike、selected price、underlying reference price、per-expiry IM futures reference）由 `market-snapshot/guides/mo-option-chain-read-contract.md` 定义的 MO Option Chain read contract 提供；`web-ui` 不直接理解 Source 或 Raw Artifact，也不直接消费 `csi1000-5d-analysis` 的 `snapshot.json`。

active universe、option type、expiry、selected price fallback、contract completeness 等业务语义均由 read contract 拥有，`web-ui` 不自行推导（ownership 与 invariants 见 `market-snapshot/guides/mo-option-chain.md` 第 2、5 节）。

## 9. 页面状态与合约明细

用户显式选择日期后立即加载；日期清空时不请求；不预填今天、不自动寻找或回退交易日。当前页面固定请求 `option_product=MO`、`price_type=close`，不提供这两个参数的选择器。

页面区分未选择日期、加载中、完整结果、失败四种状态。新日期的请求开始时清除上一日期的结果，较早的请求不得覆盖当前选择。失败根据 HTTP contract 的 `error.kind` 展示说明；网络或异常响应作为读取失败展示，不伪造数据。

完整结果展示 response 中的日期、价格口径、underlying 标识和参考价，以及按 response 顺序排列的各到期日条件性 IM futures reference、Call / Put 数量与独立散点图。无同到期 IM 时仍正常展示该到期日和 Spot。到期日可展开分别查看 Call 与 Put 的合约标识、行权价、价格；`price=null` 在价格位置显示 `—`，数值 `0` 显示为 `0.0`。不重新组织或解释合约。

现有 HTTP contract 由 `market-snapshot/guides/mo-option-chain-http-contract.md` 锁定：

```text
GET /mo-option-chain
query: target_trade_date / option_product / price_type（默认 close）
success response = read contract 第 8 节 semantic shape
error envelope: {"error": {"kind", "detail", "param"}}
error kind 闭集 + HTTP status mapping
```

前端只能依赖该 HTTP contract 的字段与 error kind，不得自行推导 universe / underlying / expiry / option type / fallback / completeness（见第 8 节）。

散点图遵循第 4、5 节。本 Guide 不定义：

```text
API versioning
auth
CORS policy
server deployment
React component tree
state-management
chart library
```
