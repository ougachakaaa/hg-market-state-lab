# guides/mo-option-chain-data.md — MO Option Chain data contract（Source / Raw / universe / completeness）authority

> 状态：authority（Stage 1）。本文档锁定 MO Option Chain 所需的 **Source fact、Raw Artifact boundary、active contract universe 与 completeness 语义**。
>
> 层级：本文档位于 `market-snapshot/ARCHITECTURE.md` 之下，从属于 `guides/mo-option-chain.md`（产品定位 / ownership / query identity / invariants）。price / null / grouping / ordering / response / failure 见 `guides/mo-option-chain-read-contract.md`，不在本文档重复。
>
> 实现本 Guide 任务的 Agent 先读 `guides/mo-option-chain.md`，再按本文档执行 Source Capture / Raw Artifact / universe / completeness 相关实现。

---

## 1. Source Facts Required

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
index_daily   → Source Capture index_daily（000852.SH，单日）
```

现有 Capture capability 应尽量复用。这三个 Capture 的 Source 字段语义继续由 `guides/csi1000-5d-analysis-data.md` 第 4.1、4.2、4.3 节定义；本文档只锁定 MO read model 需要哪些 fact，不重新定义 Source 字段。

本数据产品**不得**因为历史 CSI1000 analysis 的需求而额外要求：

```text
120-day index history
IM futures
technical derived metrics
```

underlying 只需要目标交易日**单日**的 `index_daily` fact（open / high / low / close，供 `price_type` 选价），不需要历史窗口。

## 2. Raw Artifact boundary & scope

```text
shared Capture capability ≠ shared goal-scoped Raw Artifact
```

Capture 组件语义可复用，但每个 data product 拥有自己的 goal-scoped Raw Artifact。MO Option Chain 不读取 `data/raw/csi1000-5d-analysis/`。

MO Chain 的最小 Raw scope：

```text
data/raw/mo-option-chain/<target_trade_date>/
  index_daily.json        # 000852.SH 单日 fact（open/high/low/close）
  mo_option_basic.json    # option contract facts（复用 mo_option_basic Capture 语义）
  mo_option_daily.json    # option 目标日 daily facts（复用 mo_option_daily Capture 语义）
```

* `<target_trade_date>` 表示该次数据准备的 target_trade_date，不是文件中所有记录共同的 trade_date。
* `index_daily.json` 是**单日** 000852.SH fact，不是 `index_daily_history.json`（120 日 history）。
* 每个 Raw 文件为 JSON array，元素对应一个 Source row，经 `market-snapshot/ARCHITECTURE.md` 第 3 节允许的 minimal normalization 后写入。
* 不 join basic + daily；不要求 120 日 / 60 日窗口。
* `data/raw/` 是运行产物，不进入版本控制。

## 3. target_trade_date availability & completeness

`target_trade_date` 的输入语义（显式、格式 `YYYY-MM-DD`、不是 today/latest）见 `guides/mo-option-chain.md` 第 3 节。本文档锁定其可服务性边界。

一个成功请求要求该日期：

```text
is a valid trading date
AND
required Source data exists for that date
AND
does not exceed the latest date for which the required option-chain Source facts are available
```

“不能是未来日期”的语义是：

```text
target_trade_date <= latest date with required Source option-chain data
```

不是简单的：

```text
target_trade_date <= system today
```

V1 不要求提前提供：

```text
latest_available_trade_date
available-date calendar
availability endpoint
```

请求日期非交易日 / 数据尚未发布 / Source 无数据时，允许请求直接失败并返回相应原因。

严格禁止：

```text
automatic fallback to previous trading day
automatic fallback to latest available date
silent date substitution
```

## 4. Complete Contract Universe

完整 MO option chain 的 universe 由 contract facts 决定：

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

这是 V1 核心 invariant（Invariant 2，见 `guides/mo-option-chain.md` 第 5 节）。即：

```text
same date + same option_product + different price_type
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

## 5. Contract Universe vs Daily Fact

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

决定；daily market facts 只是给这些 contract 添加目标交易日数据。

不得用：

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

## 6. Daily-row Completeness

对 active universe 中的每一个 contract：

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

是两个不同状态（后者见 `guides/mo-option-chain-read-contract.md` 第 3 节的 null 语义）。

## 7. Underlying target-date fact

构造 chain 需要 underlying 目标交易日的 `index_daily` fact 存在；其 selected price 的 usable-numeric / 失败语义见 `guides/mo-option-chain-read-contract.md` 第 4 节。
