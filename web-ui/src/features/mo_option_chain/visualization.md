# MO Option Chain visualization authority

本文档从属于 [feature architecture](ARCHITECTURE.md)，只拥有该 vertical slice 的输入、展示范围、散点语义、交互及空/错误呈现，不定义 HTTP schema、React implementation 或图表库选择。

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
select visible expiries（默认全部）
    ↓
render one combined analytical chart
```

## 2. Input

```text
target_trade_date
```

必须显式选择日期。

完整的 read query identity 由 [MO Option Chain 产品 authority](../../../../market-snapshot/src/market_snapshot/products/mo_option_chain/ARCHITECTURE.md) 拥有。第一版 visualization 固定 `option_product = MO`，`price_type = close`。

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
selectedExpiries
callColor
putColor
futuresColor
```

其中 underlying reference price 是目标交易日的 CSI1000（000852.SH）underlying 在选定 `price_type` 下的价格，作为横轴上的市场基准点。它使用与 option 相同的 `price_type`（见 `market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md` 第 2 节）。

`selectedExpiries` 与 `callColor` / `putColor` / `futuresColor` 是页面级 visualization state / preference，不属于 read query identity；其语义见第 4、5 节。

`strikeHalfRangePoints` 是整个页面共享的 strike viewport 半宽，第一版默认值与最小值均为 `300` points，调整步长为 `100` points。合图以原始 shared underlying spot 为严格中心，使用以下核心范围与实际绘图范围：

```text
core = [spot - strikeHalfRangePoints, spot + strikeHalfRangePoints]
edge_padding = 2% × core width
plot_x_range = [core lower - edge_padding, core upper + edge_padding]
```

例如 `spot = 7501`、`strikeHalfRangePoints = 300` 时，核心范围为 `7201 .. 7801`，左右各留 `12` 点绘图余量，实际 x-range 为 `7189 .. 7813`。Spot 始终位于正中心，余量使边缘圆点完整显示。Strike 网格以 `0` 为刻度起点，每 `200` 点一根灰线；网格不定义 MO contract universe。

这是 chart viewport，不是 contract filter：backend 仍返回完整 active MO chain；视窗外的 contracts 不从 response 或合约明细中删除，Web UI 也不把该范围下推为 Source、Preparation 或 HTTP 过滤规则。改变 `selectedExpiries` 不改变 `plot_x_range`。

### Price display precision

Web UI 中所有用户可见的 price-domain 数值统一显示 **1 位小数**：underlying price、各到期日 IM futures price、option selected price、strike、图表轴刻度、tooltip、reference label 与合约明细均适用。例如 `7312.45 → 7312.5`、`7000 → 7000.0`、`0 → 0.0`、`null → —`。

这是 presentation formatting，不是 data rounding。不得修改 backend / read model / HTTP 的 numeric fact，也不得影响计算、排序、chart coordinate 或 contract identity。

## 4. Visualization scope

目标日期全部处于有效生命周期内的 MO option contracts 都属于目标展示范围。

一个完整 MO Option Chain response 中，当前选中的所有 expiry 共享一张 combined analytical chart。`expiry` 保留 read contract 的 grouping identity，在 visualization 中是图内视觉分组维度，而不是独立 chart boundary：

```text
complete OptionChain → selectedExpiries → one combined chart
```

`selectedExpiries ⊆ response.expiries`，每次取得新的完整 response 时默认全选。页面提供 multi-select、checkbox 或等效控件控制每个 expiry 的完整显隐；只要 response 含有 expiry，至少保留一个选中项，不能隐藏最后一个。隐藏一个 expiry 时，其 Call / Put traces、IM futures reference、图例表示与合约明细一起隐藏。页面仍保存完整 OptionChain；`hidden != absent`。图例只用于视觉识别，不得产生与页面 `selectedExpiries` 不同步的第二套 expiry 显隐状态。

选择仅是 frontend presentation state，不成为 HTTP query、backend contract、Source Capture、Analysis Preparation 或 contract universe 的过滤条件。合图是页面主要视觉主体，应提供明显大于旧单 expiry 图的展示区域，保障 desktop-first 的多到期日叠加可读性，同时保留响应式行为；具体尺寸由实现决定。

## 5. Scatter semantics

合图：

```text
X axis = strike / exercise price
Y axis = option selected price（默认 price_type = close）
```

并且：

* 每个 selected expiry 分别有 Call / Put series，即最多两条 option traces；某一 side 没有可绘制价格时可不生成该 trace。Call / Put 分别按 read contract 的 Strike 顺序以直线连接；`price=null` 的位置断线，不跨过缺价连接，也不在该位置绘制点；`price=0` 是可绘制点；
* 颜色表达要素类型：Call、Put、IM futures 各使用用户选择的独立色系。同一类型跨 expiry 保持同一基色；Call 与 Put 仍以线型和／或 marker 形状辅助区分，视觉上必须可辨。`callColor`、`putColor`、`futuresColor` 是三个页面级 visualization preference，默认分别为蓝色 `#2563eb`、橙色 `#ea580c`、紫色 `#7c3aed`；第一版不提供逐 expiry 自定义颜色或完整 theme editor；
* `expiryOpacityScale` 表达到期日相对目标交易日的远近。按完整 response 的 `expiry_date ascending` 顺序固定 rank：若有 `N > 1` 个 expiry，第 `i` 项（从 `0` 开始）的不透明度为 `1 − 0.85 × i / (N − 1)`；只有一个时为 `1`。因此最近为 `1`、最远为 `0.15`，中间按序号线性插值，不按实际日历天数插值。即使隐藏部分 expiry，其余 expiry 的 rank 与不透明度也不重新计算；同一 expiry 的 Call / Put 线与点、IM futures 参考线和图例项使用同一不透明度。透明度不表达质量、信心、风险或重要性；
* 整张图只绘制一条目标交易日 CSI1000 Spot reference（与 option 相同的 `price_type`），以原始 underlying price 定位于横轴中心、以 1 位小数标注，并使用中性、完全不透明的颜色。Spot 标注位于绘图区下方，与图表上方的 Futures 图例分开；Price 数字刻度放在图最左侧，每 `200` 点标注一次；
* 图表上方使用独立的双侧图例区：左侧列出实际可绘制的 Call / Put series，右侧列出 IM futures reference。图例不提供独立显隐交互，窄屏下可换行或上下堆叠，但不得覆盖绘图区；
* 对每个 selected expiry，仅在其 `futures` 非 `null` 时显示 IM futures reference（合约 identity 与所选价格）：在横轴以 `futuresColor`、该 expiry 不透明度及与 option curves 可区分的虚线绘制垂直参考线，并在右侧 Futures 图例中以同色虚线样例显示 `instrument_id · price`，price 按 1 位小数格式化。参考线顶部不再放置文字标注。为 `null` 时仍让用户知晓“无同到期 IM 合约”，不绘制 IM 参考线或图例项，也不推断替代合约；隐藏 expiry 时其 reference 与图例项一起隐藏；
* Price 纵轴以 `0` 为刻度起点，每 `100` 点一根灰色虚线网格，其中每 `200` 点显示数字。唯一的 combined Y-domain 只统计 selected expiries 中、实际 `plot_x_range` 内、所选价格非 `null` 的 Call / Put 点：上限为 `ceil(可见最高价 × 1.2 / 100) × 100`，无可见正价时取 `100`；下限包含数值 `0` 并留少量显示余量，若有可见负价也须覆盖。IM 与 Spot 是横轴参考价，不参与 Y-domain 计算。改变 selection 可重新计算 Y-domain，但不改变 X viewport、backend data、expiry identity 或 opacity identity；
* underlying reference price 是横轴上的市场基准点；
* 每个 scatter point 代表一个 MO option contract。

单个 option point 的 point 级字段（来自 read contract）：

```text
instrument_id
strike
selected price
```

`expiry` 与 `option_type` 由 read contract 的父级 grouping 表达（`expiries[]` 的 `expiry_date`、`calls[]` / `puts[]` 的归属），不要求每个 point 重复携带（见 `market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md` 第 6 节）。不透明度仅使用 read contract 已定义的 expiry ordering，不依据价格、volume、OI、liquidity、选中顺序或 legend 交互重新排序。

这里锁定的是**用户可见语义**，不是 HTTP schema。selected price 的 null / zero 语义（`0` 是数据、`null` 是缺价）由 `market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md` 第 3 节定义；`web-ui` 不得自行 fallback、补零或删除 contract。`price=null` 的合约没有可绘制的纵坐标，因此不显示散点，但仍保留在被选中到期日的合约明细中，并在该到期日提示缺价数量；`price=0` 是可绘制的数值。如果某个被选中到期日全部合约缺价，页面显示该到期日无可绘制价格的状态，仍保留该到期日及其合约明细。

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

本 vertical slice 需要的事实由 [MO Option Chain read contract](../../../../market-snapshot/src/market_snapshot/products/mo_option_chain/read-contract.md) 提供；`web-ui` 不直接理解 Source 或 Raw Artifact，也不直接消费 `csi1000-5d-analysis` 的 `snapshot.json`。

active universe、option type、expiry、selected price fallback、contract completeness 等业务语义均由 backend authority 拥有，`web-ui` 不自行推导。

## 9. 页面状态与合约明细

用户显式选择日期后立即加载；日期清空时不请求；不预填今天、不自动寻找或回退交易日。当前页面固定请求 `option_product=MO`、`price_type=close`，不提供这两个参数的选择器。

页面区分未选择日期、加载中、完整结果、失败四种状态。新日期的请求开始时清除上一日期的结果，较早的请求不得覆盖当前选择。失败根据 HTTP contract 的 `error.kind` 展示说明；网络或异常响应作为读取失败展示，不伪造数据。

完整结果展示 response 中的日期、价格口径、underlying 标识和参考价，以及一张包含 selected expiries 的 combined chart 与按 response 顺序排列的 selected expiry 明细。明细保留 expiry identity、条件性 IM futures reference 或缺失状态、Call / Put 合约数量；到期日可展开分别查看 Call 与 Put 的合约标识、行权价、价格。无同到期 IM 时仍正常展示该到期日和共享 Spot；`price=null` 在价格位置显示 `—`，数值 `0` 显示为 `0.0`。不重新组织或解释合约。

前端请求、response 与 error handling 必须遵循 [MO Option Chain HTTP contract](../../../../backend-api/products/mo_option_chain/http-contract.md)。本文档不重复 endpoint、query schema、response shape、error kind 或 status mapping；前端也不得从 wire shape 反向定义 backend 业务语义。

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
