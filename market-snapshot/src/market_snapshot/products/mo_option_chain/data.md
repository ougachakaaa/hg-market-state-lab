# MO Option Chain data authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有 MO Option Chain 的产品专属 Source 需求、Raw scope、active contract universe 与 completeness。共享 Capture 身份和字段见 [../../capture/ARCHITECTURE.md](../../capture/ARCHITECTURE.md)；price、null、grouping 与 read failure 见 [read-contract.md](read-contract.md)。

---

## 1. Source Facts Required

MO Option Chain 只需要以下事实能力：

```text
option contract facts
option target-date daily facts
underlying target-date daily fact
IM ordinary monthly contract facts
target-date-active IM ordinary monthly daily facts
```

对于当前 MO / Tushare 场景，对应：

```text
opt_basic     → Source Capture mo_option_basic
opt_daily     → Source Capture mo_option_daily
index_daily   → Source Capture index_daily（000852.SH，单日）
fut_basic     → Source Capture im_futures_basic（IM 普通月合约）
fut_daily     → Source Capture im_futures_daily（目标日行情）
```

上述 Capture 的身份、Source endpoint 与公共字段语义由 [../../capture/ARCHITECTURE.md](../../capture/ARCHITECTURE.md) 拥有；本文档只锁定 MO read model 需要哪些 fact。IM 合约与 MO expiry 的匹配及选价语义见 [read-contract.md](read-contract.md)。

本数据产品**不得**因为历史 CSI1000 analysis 的需求而额外要求：

```text
120-day index history
60-day IM futures history
IM term structure history
technical derived metrics
```

underlying 只需要目标交易日**单日**的 `index_daily` fact（open / high / low / close，供 `price_type` 选价），不需要历史窗口。
IM futures reference 只需要普通月合约事实与目标交易日**单日**的 `fut_daily` fact（open / high / low / close，供同一 `price_type` 选价）；具体采集范围是第 8 节的 target-date-active IM universe，不由 MO expiry 决定。不引入历史窗口或其他 Product 的 analysis-ready artifact。

## 2. Raw Artifact boundary & scope

```text
shared Capture capability ≠ shared goal-scoped Raw Artifact
```

Capture 组件语义可复用；MO Option Chain 选择持久化自己的 goal-scoped Raw Artifact，不读取 sibling Product 的 Raw。其他 Product 是否持久化由其自身 authority 决定。

MO Chain 的最小 Raw scope：

```text
data/raw/mo-option-chain/<target_trade_date>/
  index_daily.json        # 000852.SH 单日 fact（open/high/low/close）
  mo_option_basic.json    # option contract facts（复用 mo_option_basic Capture 语义）
  mo_option_daily.json    # option 目标日 daily facts（复用 mo_option_daily Capture 语义）
  im_futures_basic.json   # 判断目标日有效生命周期所需的 IM 普通月合约事实
  im_futures_daily.json   # 目标日有效 IM 普通月合约的目标日 daily facts
```

* `<target_trade_date>` 表示该次数据准备的 target_trade_date，不是文件中所有记录共同的 trade_date。
* `index_daily.json` 是**单日** 000852.SH fact。
* `im_futures_basic.json` 保留足以判断第 8 节 IM universe 的普通月合约 Source facts；`im_futures_daily.json` 保存该 universe 在目标日由 Source 返回的 daily rows，而非只保存与 MO expiry 匹配的合约。不存在的 Source row 不得伪造或从其他日期补齐。
* `im_futures_daily.json` 只存目标日 facts，不引入 IM history 或 term structure history。MO Chain 不读取 sibling Product 的 Raw 或 analysis-ready artifact。共享 Source Capture capability 不等于共享 goal-scoped Raw。
* 每个 Raw 文件为 JSON array，元素对应一个 Source row，经 [模块架构](../../../../ARCHITECTURE.md) 允许的 minimal normalization 后写入。
* Raw 不 join basic + daily；本产品持有自己的 Raw，不读取另一个产品的 Raw。
* `data/raw/` 是运行产物，不进入版本控制。

## 3. target_trade_date availability & completeness

`target_trade_date` 的输入语义（显式、格式 `YYYY-MM-DD`、不是 today/latest）见 `ARCHITECTURE.md` 第 3 节。本文档锁定其可服务性边界。

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

这是 V1 核心 invariant（Invariant 2，见 `ARCHITECTURE.md` 第 5 节）。即：

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

本节与第 6 节讨论的是第 4 节定义的 MO option active universe；IM target-date Raw 与其 read-model 完整性边界另见第 8 节。

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

对 MO option active universe 中的每一个 contract：

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

是两个不同状态（后者见 `read-contract.md` 第 3 节的 null 语义）。

## 7. Underlying target-date fact

构造 chain 需要 underlying 目标交易日的 `index_daily` fact 存在；其 selected price 的 usable-numeric / 失败语义见 `read-contract.md` 第 4 节。

## 8. IM target-date facts

MO Chain 的 IM target-date Source Capture scope 是：

```text
exchange = CFFEX
AND product = IM
AND ordinary monthly contract
AND list_date <= target_trade_date <= delist_date
```

Capture 使用 IM 自身的 Source facts 确定这个 **target-date-active IM ordinary monthly universe**，对其中所有合约采集目标日 daily facts；不得先读取或理解 MO expiry groups，再按 expiry、主力、成交量、持仓量、流动性或分析相关性缩小采集范围。Capture 负责 Source-domain scope，Preparation 才负责 `MO expiry_date == IM delist_date` 的跨域匹配（见 `read-contract.md` 第 4 节）。

IM Raw acquisition scope 可宽于最终 read model 所需的 futures references。Capture 必须覆盖上述 universe 的目标日 Source 查询并保留实际返回的事实；Source 请求错误不得静默跳过。Preparation 对某个 MO expiry 找不到结构性匹配的 IM 合约是合法缺席，输出 `futures = null`；多个匹配则失败。某个未匹配任何 MO expiry 的 IM 合约缺少目标日 daily row，不自动构成 MO Chain read-model failure；只有唯一匹配合约的唯一 daily row 和 usable selected price 属于成功 chain 的必需事实。不得因缺席或缺价而改选其他 IM 合约，具体完整性与失败语义见 read contract 第 4、10、11 节。
