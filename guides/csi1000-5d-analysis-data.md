# guides/csi1000-5d-analysis-data.md — CSI1000 未来约 5 个交易日市场状态分析的数据需求与 Source Capture / Raw Artifact 契约 authority

> 状态：authority。本文档锁定"外部分析器分析从目标交易日往后约 5 个交易日的中证1000市场状态"这一场景所需的**输入数据需求**，以及支撑 Source Capture 直接实现的 **Source / Raw Artifact 契约**。不定义也不实现任何业务分析。
>
> 层级：本文档位于 `ARCHITECTURE.md` 之下，与 `guides/daily-market-snapshot.md` 并列。架构层面的稳定边界以 `ARCHITECTURE.md` 为准（尤其第 1.1 节职责边界、第 2 节核心架构、第 3 节 Raw/Preparation 边界、第 4 节架构边界的执行、第 8 节 Guide 职责、第 9 节项目结构）；本文档不得与其冲突。
>
> 实现本 Guide 任务的 Agent 应先阅读 `ARCHITECTURE.md` 第 1.1、2、3、4、9 节，再按本文档执行。

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

即外部分析器不需要重新理解 Source 的杂乱结构即可使用数据。第一阶段优先维持简单（见第 7 节），不提前设计复杂统一 schema。

## 3. Source 契约

本场景统一使用 **Tushare Pro**，不引入第二数据源，不引入 DataSource abstraction。

| 数据需求 | Source（Tushare endpoint） | 对应 Source Capture |
| --- | --- | --- |
| CSI1000 指数历史行情 | `index_daily` | `index_daily`（复用） |
| MO 期权合约静态/生命周期事实 | `opt_basic` | `mo_option_basic` |
| MO 期权日行情事实 | `opt_daily` | `mo_option_daily` |
| IM 期货合约静态/生命周期事实 | `fut_basic` | `im_futures_basic` |
| IM 期货日行情事实 | `fut_daily` | `im_futures_daily` |

本阶段只锁定上述 Source / Source Capture 契约，不实现 API 调用。

## 4. Source Capture 与 Raw Artifact 契约

字段语义与单位以 Tushare Source 原始定义为准；Raw 层保持 Source 字段名与语义，不做分析视角重命名或单位换算。下表仅作便于识别的最低字段清单；Source 返回的其他字段可按 `ARCHITECTURE.md` 第 3 节的 Raw 原则保留。

### 4.1 Source Capture: index_daily（复用，CSI1000 历史窗口）

* 语义名称：`index_daily`（复用 `ARCHITECTURE.md` 与 `guides/daily-market-snapshot.md` 第 4.1 节已定义的 Source Capture 语义，不新建同义 Capture）。
* 标的：`000852.SH`（中证1000指数）。
* Source：Tushare `index_daily`（支持 `ts_code` + `start_date` + `end_date` 的历史区间查询）。
* Raw artifact：`index_daily_history.json`。

#### 核心字段

与 `guides/daily-market-snapshot.md` 第 4.1 节一致：

| 字段 | 语义 | 单位/说明 |
| --- | --- | --- |
| `ts_code` | 指数代码 | 源主键 |
| `trade_date` | 交易日 | Raw 层统一为 `YYYY-MM-DD` |
| `open` | 开盘价 | 点 |
| `high` | 最高价 | 点 |
| `low` | 最低价 | 点 |
| `close` | 收盘价 | 点 |
| `pre_close` | 昨收价 | 点 |
| `change` | 涨跌额 | 点，源定义 = close − pre_close |
| `pct_chg` | 涨跌幅 | %（数值 1 表示 1%） |
| `vol` | 成交量 | 手（保留源原始单位） |
| `amount` | 成交额 | 千元（保留源原始单位） |

#### 与现有单日采集的关系

* 现有 `fetch_index_daily.py` 按单日采集六个指数的 `index_daily`（用于第一版 daily-market-snapshot 场景）。
* 第一版 Guide 中固定的六指数 universe 属于第一版场景 Definition 的输入范围，不属于 `index_daily` Source Capture 语义本身；本场景在同一 Capture 语义下，聚焦 `000852.SH` 的**历史窗口**。
* 历史窗口的输出要求与 Capture / Preparation 分工见第 6.1 节。

### 4.2 Source Capture: mo_option_basic

* 语义名称：`mo_option_basic`
* Source：Tushare `opt_basic`
* 语义：MO 期权合约自身的静态/生命周期事实。
* Raw artifact：`mo_option_basic.json`。

#### 至少保留的 Source 字段

| 字段 | 说明 |
| --- | --- |
| `ts_code` | 期权合约代码 |
| `exchange` | 交易所（MO 为 CFFEX） |
| `opt_code` | 期权合约代码/简称 |
| `call_put` | 认购/认沽（Source 字段） |
| `exercise_price` | 行权价 |
| `maturity_date` | 到期日 |
| `list_date` | 上市日期 |
| `delist_date` | 退市日期 |

* 可以保留 Source 返回的其他字段。
* Raw 层**不得**做分析视角重命名：`exercise_price` → `strike`、`maturity_date` → `expiry_date`、`call_put` → `option_type`。
* 这些更友好的字段名如果未来需要，应在 Analysis Preparation 中处理。
* Raw 层对 contract lifecycle date facts 做 minimal date normalization：`list_date` / `delist_date` / `maturity_date` 统一落地为 `YYYY-MM-DD`（与 `trade_date` 一致，见 `ARCHITECTURE.md` 第 3 节）。这只改变表示形式，不改变 Source 语义。

### 4.3 Source Capture: mo_option_daily

* 语义名称：`mo_option_daily`
* Source：Tushare `opt_daily`
* 语义：MO 期权各合约在某交易日的日行情事实。
* Raw artifact：`mo_option_daily.json`。

#### 至少保留的 Source 字段

| 字段 | 说明 |
| --- | --- |
| `ts_code` | 期权合约代码 |
| `trade_date` | 交易日 |
| `exchange` | 交易所 |
| `pre_settle` | 昨结算价 |
| `pre_close` | 昨收盘价 |
| `open` | 开盘价 |
| `high` | 最高价 |
| `low` | 最低价 |
| `close` | 收盘价 |
| `settle` | 结算价 |
| `vol` | 成交量 |
| `amount` | 成交额 |
| `oi` | 持仓量 |

* 不人为增加 `strike`、`expiry`、`call_put`、`IV`、`Greeks`——这些不是 `opt_daily` 的 Raw Fact。
* 需要这些属性时，由下游使用 `mo_option_basic` + `mo_option_daily` 确定性组合。

### 4.4 Source Capture: im_futures_basic

* 语义名称：`im_futures_basic`
* Source：Tushare `fut_basic`
* 语义：IM 股指期货合约自身的静态/生命周期事实。
* Raw artifact：`im_futures_basic.json`。

#### 至少保留的 Source 字段

至少需要能够确定：

| 字段 | 说明 |
| --- | --- |
| `ts_code` | 合约代码 |
| `exchange` | 交易所（IM 为 CFFEX） |
| `fut_code` | 合约代码/简称 |
| `list_date` | 上市日期 |
| `delist_date` | 退市日期 |

以及 Source 中能够表达合约到期/交割时间的相关字段。

* 不在 Raw 层创造分析字段。

### 4.5 Source Capture: im_futures_daily

* 语义名称：`im_futures_daily`
* Source：Tushare `fut_daily`
* 语义：IM 合约每日行情事实。
* Raw artifact：`im_futures_daily.json`。

#### 至少保留的 Source 字段

| 字段 | 说明 |
| --- | --- |
| `ts_code` | 合约代码 |
| `trade_date` | 交易日 |
| `pre_close` | 昨收盘价 |
| `pre_settle` | 昨结算价 |
| `open` | 开盘价 |
| `high` | 最高价 |
| `low` | 最低价 |
| `close` | 收盘价 |
| `settle` | 结算价 |
| `change1` | 涨跌额（Source 字段） |
| `change2` | 涨跌额（Source 字段） |
| `vol` | 成交量 |
| `amount` | 成交额 |
| `oi` | 持仓量 |
| `oi_chg` | 持仓量变化 |

* 如 Source 返回其他字段，可按照现有 Raw 原则保留。

## 5. Universe 语义

### 5.1 完整 MO option chain

第一版 "完整 MO option chain" 定义为确定性、不含分析判断的：

> MO option chain = 在目标交易日处于有效交易生命周期内的全部 MO 中证1000股指期权合约，以及这些合约目标交易日的日行情记录。

* 生命周期判定基于 Source contract facts：`list_date <= target_trade_date <= delist_date`。
* 产品限定：MO，且 `exchange = CFFEX`。
* 不得按 strike 距离、成交量、只保留 ATM、只保留近月、只保留"有分析价值"等做过滤——这些筛选属于下游数据组织需求，不属于 Source Capture。
* 第一版 MO 只要求目标交易日完整链，暂时不要求 MO 历史多日。

### 5.2 IM universe

"主要可交易合约 / 有意义"这类业务解释性措辞不用于 Source Capture。IM universe 的确定性定义：

> 对目标分析窗口，采集属于 IM 产品且在相关交易日处于有效生命周期内的普通月度合约。

* 不得根据主力判断、成交量、持仓量、流动性阈值、analyzer 当前关注月份提前过滤。
* 目标是 Raw Artifact 足以让下游重建 IM term structure。

## 6. 历史窗口语义

### 6.1 CSI1000 history

* 复用 `index_daily`（`000852.SH`），Source 为 Tushare `index_daily`。
* Analysis-ready 要求：下游应能取得截至 target_trade_date 的最近 120 个实际交易日记录。
* 不为此引入交易日历 framework。
* Source Capture 可以获取一个包含不少于这些记录的历史区间/历史集合；Raw 不要求恰好 120 行。
* 精确选取 `latest 120 trading rows <= target_trade_date` 属于后续 Analysis Preparation。
* 保持边界：Capture = Source Fact acquisition；Preparation = window selection。不为"精确 120 日"在 Capture 中引入业务组织逻辑。

### 6.2 IM history

* Analysis-ready 要求：下游应能取得 target_trade_date 及之前约 60 个实际交易日的 IM term-structure-related facts。
* Source Capture 应获取足够覆盖这一窗口的 `im_futures_basic` + `im_futures_daily` Source Fact。
* Capture 不负责 basis / annualized basis / calendar spread / term structure interpretation，也不需要把 Raw 裁切成恰好 60 个交易日。
* 精确窗口选择属于后续 Preparation。

## 7. Raw 文件组织

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
* 每个 Raw 文件统一为 JSON array，数组元素对应一个 Source row，经 `ARCHITECTURE.md` 第 3 节允许的 minimal normalization 后写入。
* 不在 Raw 文件中 join basic + daily。
* `data/raw/` 是运行产物，不进入版本控制。

## 8. 文件与 Source Capture 的对应关系

* `index_daily_history.json` 不是新的 Source Capture，仍属于 `index_daily`，只是本场景下对 `000852.SH` 历史 Source Fact 的 Raw artifact。不新增 `csi1000_history` 等同义 Capture。
* 其余文件与 Source Capture 一一对应：

| Raw artifact | Source Capture |
| --- | --- |
| `mo_option_basic.json` | `mo_option_basic` |
| `mo_option_daily.json` | `mo_option_daily` |
| `im_futures_basic.json` | `im_futures_basic` |
| `im_futures_daily.json` | `im_futures_daily` |

## 9. Raw completeness / failure boundary

对 target trade date 的最小明确边界：

* CSI1000：必须存在 `000852.SH`；历史 Raw 必须包含 target_trade_date 对应记录。
* MO：必须能够形成目标交易日的完整 active MO contract universe（`mo_option_basic` + `mo_option_daily`）；若 basic contract universe 与 daily facts 明显无法对应，不得静默丢弃。
* IM：必须能够识别目标窗口中的 IM 合约及其 daily facts。
* 不得：静默跳过 Source error、用其他日期自动 fallback、用分析推断补缺失 Source rows。
* 具体异常类型、CLI exit code、重试策略仍属于 implementation，可 deferred。

## 10. 与第一版 daily-market-snapshot 场景的关系

* 本场景的 CSI1000 历史数据**复用**现有 `index_daily` Source Capture 的 Source Fact 语义，不复制一套相同概念。
* 现有 `stock_daily` 与第一版 `breadth` 继续存在；它们不是本阶段所定义的新分析数据输入的核心组成；不删除、不扩展、不阻塞本数据需求设计。
* 本 Guide 不修改 `guides/daily-market-snapshot.md` 已锁定的语义；本场景 Raw artifact 使用独立的 goal-scoped 目录（第 7 节），不与现有单日 Raw artifact 冲突。

## 11. Non-goals

本文档不定义或实现：

```text
新增 / 修改任何 Source Capture
调用真实 Tushare API
生成测试数据
实现 Analysis Preparation
实现 derived features
实现 analyzer
引入新的抽象或 framework
```

## 12. Deferred（留待后续阶段）

以下问题在本文档中尚未决定，留待后续实现 / Preparation Definition 阶段：

```text
Analysis-ready Artifact 的最终文件结构
第一版具体 deterministic derived fields（ATR / RV / basis / option moneyness 等）
derived field 的具体数学公式
Analysis Preparation 的实现结构
CLI 的具体参数设计
Raw overwrite / retry 等运行策略
历史窗口 Capture 的具体 API 调用循环方式
```

* MO / IM 的具体 Source / endpoint 与 Raw 文件组织已锁定（第 3、7 节），不再 deferred。
* 历史窗口 Capture 的 authority 已锁定"需要提供什么 Source Fact / Raw artifact 表达什么 / 必须覆盖什么数据窗口"；deferred 的只是具体 API 调用循环方式等 implementation detail。
* 只有确实尚未决定的问题才标记 deferred；本文档不替用户增加长期约束。
