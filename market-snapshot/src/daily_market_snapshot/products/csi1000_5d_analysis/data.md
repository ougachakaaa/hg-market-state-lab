# CSI1000 5D Analysis data authority

本文档从属于 [ARCHITECTURE.md](ARCHITECTURE.md)，拥有 CSI1000 5D Analysis 的 Source 需求、产品专属 Capture scope、goal-scoped Raw Artifact、universe、历史窗口与 completeness。共享 Capture 身份和字段语义由 [../../capture/ARCHITECTURE.md](../../capture/ARCHITECTURE.md) 拥有；Analysis Preparation 由 [preparation-contract.md](preparation-contract.md) 拥有。

## 1. 目标与边界

本次数据使用场景：

> 以某个目标交易日为观察基准，为外部分析器提供足够的数据，使其能够分析未来约 5 个交易日的中证1000市场状态，包括可能的价格中枢、正常波动区域以及价格显著偏离后的期权反向交易候选区域。

上述描述只是**分析目的**，用于说明"为什么需要这些数据"，不是本项目要实现的业务逻辑。

边界：

* 本项目根据该分析目标**组织数据需求**，做**确定性、可复现的数据转换**，生成**方便分析器直接消费的数据结构**。
* "价格中枢"、"噪声区 / 正常波动区域"、"反向卖 Call / Put 候选区域"等结论及其判定规则属于**外部 analyzer**，不进入本项目的数据契约，也不由本项目定义或执行。
* 本项目不得输出 bullish / bearish、反转概率、交易建议、目标点位等业务结论；不得把外部 analyzer 当前可能使用的分析方法固化为项目业务规则。

## 2. 职责边界：确定性数据转换 vs 业务分析

本文档在 authority 中明确区分两类事情，避免后续 coding agent 把业务分析逻辑塞进 Analysis Preparation。

### 2.1 本项目允许（确定性数据转换）

确定性的、输入相同时结果固定的数据转换。例如（仅列举类别，本阶段不要求现在定义或实现所有这些字段）：

```text
历史收益率
rolling high / low
moving average
ATR
realized volatility

IM basis
annualized basis
calendar spread

option moneyness
days to expiry
premium normalization
IV / Greeks（若未来明确由项目计算）
```

### 2.2 本项目不负责（业务分析）

任何依赖业务解释的分析结论，例如（仅举例，非穷举）：

```text
未来5日中枢 = 7300–7450
当前处于噪声区
7600以上进入反向卖Call区域
市场处于趋势状态
市场过热
适合卖Put
未来上涨概率较高
```

这些属于 analyzer。

### 2.3 输出语义

未来输出应满足：

```text
structured
reproducible
analysis-ready
```

即外部分析器不需要重新理解 Source 的杂乱结构即可使用数据。第一阶段优先维持简单（见第 6 节），不提前设计复杂统一 schema。

## 3. Required Source Captures

本产品使用共享的 `index_daily`、`mo_option_basic`、`mo_option_daily`、`im_futures_basic` 与 `im_futures_daily`。Capture 身份、Tushare endpoint、公共字段和 minimal normalization 见 [../../capture/ARCHITECTURE.md](../../capture/ARCHITECTURE.md)。

本产品在同一 `index_daily` Capture 语义下采集 `000852.SH` 的历史窗口；这不会创建同义 Capture。以下章节只定义 CSI1000 5D 产品专属的 universe、窗口、Raw 文件与 completeness。

## 4. Universe 语义

### 4.1 完整 MO option chain

第一版 "完整 MO option chain" 定义为确定性、不含分析判断的：

> MO option chain = 在目标交易日处于有效交易生命周期内的全部 MO 中证1000股指期权合约，以及这些合约目标交易日的日行情记录。

* 生命周期判定基于 Source contract facts：`list_date <= target_trade_date <= delist_date`。
* 产品限定：MO，且 `exchange = CFFEX`。
* 不得按 strike 距离、成交量、只保留 ATM、只保留近月、只保留"有分析价值"等做过滤——这些筛选属于下游数据组织需求，不属于 Source Capture。
* 第一版 MO 只要求目标交易日完整链，暂时不要求 MO 历史多日。

交叉引用：`MO Option Chain` 现已作为与 `csi1000-5d-analysis` 并列的独立 deterministic data product 定义在 `../mo_option_chain/ARCHITECTURE.md`（产品 / query / invariants）及其子 Guide `../mo_option_chain/data.md`（universe / Raw / completeness）、`../mo_option_chain/read-contract.md`（read contract / price / grouping / failure）。本节描述的 MO universe 与 Raw 契约继续服务于本 CSI1000 分析场景的 `mo_options` 准备，语义不变；两者共享底层 Source Capture capability（但 Raw Artifact 各自 goal-scoped），MO Option Chain 不依赖 `csi1000-5d-analysis` 的 artifact。

### 4.2 IM universe

"主要可交易合约 / 有意义"这类业务解释性措辞不用于 Source Capture。IM universe 的确定性定义：

> 对目标分析窗口，采集属于 IM 产品且在相关交易日处于有效生命周期内的普通月度合约。

* 不得根据主力判断、成交量、持仓量、流动性阈值、analyzer 当前关注月份提前过滤。
* 目标是 Raw Artifact 足以让下游重建 IM term structure。

## 5. 历史窗口语义

### 5.1 CSI1000 history

* 复用 `index_daily`（`000852.SH`），Source 为 Tushare `index_daily`。
* Analysis-ready 要求：下游应能取得截至 target_trade_date 的最近 120 个实际交易日记录。
* 不为此引入交易日历 framework。
* Source Capture 可以获取一个包含不少于这些记录的历史区间/历史集合；Raw 不要求恰好 120 行。
* 精确选取 `latest 120 trading rows <= target_trade_date` 属于后续 Analysis Preparation。
* 保持边界：Capture = Source Fact acquisition；Preparation = window selection。不为"精确 120 日"在 Capture 中引入业务组织逻辑。

### 5.2 IM history

* Analysis-ready 要求：下游应能取得 target_trade_date 及之前约 60 个实际交易日的 IM term-structure-related facts。
* Source Capture 应获取足够覆盖这一窗口的 `im_futures_basic` + `im_futures_daily` Source Fact。
* Capture 不负责 basis / annualized basis / calendar spread / term structure interpretation，也不需要把 Raw 裁切成恰好 60 个交易日。
* 精确窗口选择属于后续 Preparation。

## 6. Raw 文件组织

本场景使用独立的 goal-scoped Raw 目录，避免与现有单日 daily-market-snapshot 场景的 Raw artifact 语义冲突；不修改现有 `data/raw/YYYY-MM-DD/{index_daily.json, stock_daily.json}` 语义。

```text
data/raw/
└─ csi1000-5d-analysis/
   └─ YYYY-MM-DD/
      ├─ index_daily_history.json
      ├─ mo_option_basic.json
      ├─ mo_option_daily.json
      ├─ im_futures_basic.json
      └─ im_futures_daily.json
```

* `YYYY-MM-DD` 表示该次数据准备的 target_trade_date，而不是文件中所有记录共同的 trade_date。
* 尤其 `index_daily_history.json` 与 `im_futures_daily.json` 可以自然包含多个交易日。
* 每个 Raw 文件统一为 JSON array，数组元素对应一个 Source row，经 [模块架构](../../../../ARCHITECTURE.md) 允许的 minimal normalization 后写入。
* 不在 Raw 文件中 join basic + daily。
* `data/raw/` 是运行产物，不进入版本控制。

## 7. 文件与 Source Capture 的对应关系

* `index_daily_history.json` 不是新的 Source Capture，仍属于 `index_daily`，只是本场景下对 `000852.SH` 历史 Source Fact 的 Raw artifact。不新增 `csi1000_history` 等同义 Capture。
* 其余文件与 Source Capture 一一对应：

| Raw artifact | Source Capture |
| --- | --- |
| `mo_option_basic.json` | `mo_option_basic` |
| `mo_option_daily.json` | `mo_option_daily` |
| `im_futures_basic.json` | `im_futures_basic` |
| `im_futures_daily.json` | `im_futures_daily` |

## 8. Raw completeness / failure boundary

对 target trade date 的最小明确边界：

* CSI1000：必须存在 `000852.SH`；历史 Raw 必须包含 target_trade_date 对应记录。
* MO：必须能够形成目标交易日的完整 active MO contract universe（`mo_option_basic` + `mo_option_daily`）；若 basic contract universe 与 daily facts 明显无法对应，不得静默丢弃。
* IM：必须能够识别目标窗口中的 IM 合约及其 daily facts。
* 不得：静默跳过 Source error、用其他日期自动 fallback、用分析推断补缺失 Source rows。
* 具体异常类型、CLI exit code、重试策略仍属于 implementation，可 deferred。

## 9. 与 Daily Market Snapshot 场景的关系

* 本场景的 CSI1000 历史数据**复用**现有 `index_daily` Source Capture 的 Source Fact 语义，不复制一套相同概念。
* 现有 `stock_daily` 与第一版 `breadth` 继续存在；它们不是本阶段所定义的新分析数据输入的核心组成；不删除、不扩展、不阻塞本数据需求设计。
* 本 Guide 不修改 [Daily Market Snapshot authority](../daily_market_snapshot/ARCHITECTURE.md) 已锁定的语义；本场景 Raw artifact 使用独立的 goal-scoped 目录（第 6 节），不与现有单日 Raw artifact 冲突。

## 10. Non-goals

本 Guide 定义五个 Source Capture 的产品需求、universe、窗口与 Raw artifact（第 3–6 节）；共享 Source endpoint 与字段由 [Shared Source Capture authority](../../capture/ARCHITECTURE.md) 拥有。

Derived features 与 Analysis-ready Artifact 结构由 [preparation-contract.md](preparation-contract.md) 定义；analyzer 和额外 framework 不属于本文档。

本 Guide 不新增其明确范围之外的新 Capture。
