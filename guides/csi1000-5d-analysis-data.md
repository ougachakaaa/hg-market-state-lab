# guides/csi1000-5d-analysis-data.md — CSI1000 未来约 5 个交易日市场状态分析的数据需求 authority

> 状态：本阶段为数据需求 authority（design-only，尚未进入实现）。本文档锁定"外部分析器分析从目标交易日往后约 5 个交易日的中证1000市场状态"这一场景所需的**输入数据需求**，不定义也不实现任何业务分析。
>
> 层级：本文档位于 `ARCHITECTURE.md` 之下，与 `guides/daily-market-snapshot.md` 并列。架构层面的稳定边界以 `ARCHITECTURE.md` 为准（尤其第 1.1 节职责边界、第 2 节核心架构、第 3 节 Raw/Snapshot 边界、第 4 节架构边界的执行、第 8 节 Guide 职责）；本文档不得与其冲突。
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

本文档在 authority 中明确区分两类事情，避免后续 coding agent 把业务分析逻辑塞进 Snapshot Builder。

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

即外部分析器不需要重新理解 Source 的杂乱结构即可使用数据。第一阶段优先维持简单（见第 4 节），不提前设计复杂统一 schema。

## 3. Dataset 需求

本场景围绕三组数据建立明确的数据需求 authority。

### 3.1 Dataset: index_daily（复用现有 Dataset，CSI1000 历史窗口）

* 语义名称：`index_daily`（复用 `ARCHITECTURE.md` 与 `guides/daily-market-snapshot.md` 第 4.1 节已定义的 Dataset 语义，不新建同义 Dataset）。
* 标的：`000852.SH`（中证1000指数）。
* 时间窗口：目标交易日及之前约 **120 个交易日**（第一版建议；可随分析需求调整，不是架构层永久约束）。
* 核心字段：与 `guides/daily-market-snapshot.md` 第 4.1 节一致。

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

* 现有 `fetch_index_daily.py` 按单日采集六个指数的 `index_daily`（用于第一版 Daily Snapshot）。
* 第一版 Guide 中固定的六指数 universe 属于第一版 Snapshot Definition 的输入范围，不属于 `index_daily` Dataset 语义本身；本场景在同一 Dataset 语义下，聚焦 `000852.SH` 的**历史窗口**。
* 本阶段只定义需求，**不设计具体历史采集实现方式**（例如是否按日拉取、是否使用 Source 支持的历史区间接口）；该 reconciliation 留到后续实现阶段。

### 3.2 Dataset: mo_option_daily（MO 期权链）

* 语义名称：`mo_option_daily`
* 范围：
  * MO（中证1000股指期权）；
  * 目标交易日可交易、与近期分析相关的期权合约；
  * 第一版优先保留**完整 option chain**，而不是提前筛选几个 strike；
  * 如具体 Source 能可靠提供历史数据，可保留一定历史窗口，但不在本阶段中为了未来需求过度设计。

#### Contract identity / static facts

至少考虑：

```text
contract / ts_code
option_type
strike
expiry_date
```

#### Daily market facts

至少考虑：

```text
trade_date
open
high
low
close
settlement
volume
open_interest
```

* 若数据源稳定提供 `bid` / `ask`，可作为候选字段记录，但不为了尚未确认的数据能力强制设计复杂契约。
* 本阶段**不要求** Source 直接提供 `IV`、`Delta`、`Gamma`、`Theta`、`Vega`，除非这些本身就是选定 Source 的可靠原始字段；这些量若未来需要由项目计算，属于后续明确设计的 deterministic derivation，不在本阶段中默认加入。

### 3.3 Dataset: im_futures_daily（IM 期货期限结构）

* 语义名称：`im_futures_daily`
* 范围：目标交易日所有与 IM 有关、对当前期限结构有意义的主要可交易合约。

#### 核心字段

```text
contract / ts_code
trade_date
expiry_date
open
high
low
close
settlement
volume
open_interest
```

* 时间窗口：目标交易日之前约 **60 个交易日** 的必要历史数据（第一版建议；不升级成架构层永久约束）。

#### 数据充分性

原始数据必须**足以支持**后续基于 `CSI1000 index + IM futures` 的确定性计算，例如：

```text
basis_points
basis_pct
annualized_basis
calendar_spread
open_interest_change
```

但这些派生字段属于后续实现 / Snapshot Definition 设计；本阶段只明确"原始数据必须足以支持这些确定性计算"，不定义派生字段，也不把它们解释成 bullish / bearish 或交易信号。

## 4. Raw 契约与输出语义（保持简单）

第一阶段优先维持：

```text
Raw Dataset
    ↓
deterministic transformation / assembly
    ↓
analysis-ready local files
```

* 输出应满足 `structured` / `reproducible` / `analysis-ready`。
* 具体是单文件还是多文件，由数据的自然结构决定，不在本阶段提前抽象成复杂框架。
* 本阶段**不引入**：Pipeline framework、Dataset registry、DataSource inheritance hierarchy、workflow engine、database、schema migration system、generic feature store、generic analyzer framework。

## 5. 与第一版 Daily Snapshot 的关系

* 本场景的 CSI1000 历史数据**复用**现有 `index_daily` Dataset 的 Source Fact 语义，不复制一套相同概念。
* 现有 `stock_daily` 与第一版 `breadth` 继续存在；它们不是本阶段所定义的新分析数据输入的核心组成；不删除、不扩展、不阻塞本数据需求设计。
* 本 Guide 不修改 `guides/daily-market-snapshot.md` 已锁定的语义。

## 6. Non-goals（本阶段不实现）

本阶段只做 authority，不实现：

```text
新增 MO Collector
新增 IM Collector
修改 fetch_index_daily.py 实现
实现历史窗口采集
实现 build_snapshot.py
实现 derived feature
调 Tushare 实际下载数据
实现 GPT 分析
编写交易策略
修改业务分析 prompt
引入新的架构框架
```

## 7. Deferred（留待下一阶段）

以下问题在本阶段尚未决定，留待后续实现 / Snapshot Definition 阶段：

```text
MO 具体 Source / endpoint
IM 具体 Source / endpoint
历史窗口 Collector 如何实现
Raw 文件具体组织
Snapshot / analysis-ready output 的最终文件结构
哪些 deterministic derived fields 第一版真正需要
```

只有确实尚未决定的问题才标记 deferred；本文档不替用户增加长期约束。
