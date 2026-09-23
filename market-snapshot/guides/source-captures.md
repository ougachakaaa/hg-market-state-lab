# Shared Source Capture authority

本文档拥有 `market-snapshot` 中可被多个产品复用的 Source Capture 身份、Source endpoint、公共字段语义与 minimal normalization。模块分层以 [../ARCHITECTURE.md](../ARCHITECTURE.md) 为准；产品自己的 query scope、窗口、universe、goal-scoped Raw 文件名与 completeness 仍由产品 data authority 拥有。

当前 Source 为 Tushare Pro。字段含义与单位以 Source 定义为准；Raw 层保持 Source 字段名和事实语义，Source 返回的其他字段也可以按架构 Raw 原则保留。

## 1. Capture Catalog

| Source Capture | Tushare endpoint | Source fact |
| --- | --- | --- |
| `index_daily` | `index_daily` | 指数日行情 |
| `stock_daily` | `daily` | A 股未复权日行情 |
| `mo_option_basic` | `opt_basic` | MO 期权合约静态与生命周期事实 |
| `mo_option_daily` | `opt_daily` | MO 期权合约日行情事实 |
| `im_futures_basic` | `fut_basic` | IM 期货合约静态与生命周期事实 |
| `im_futures_daily` | `fut_daily` | IM 期货合约日行情事实 |

相同 Capture 名称表示相同 Source fact 语义，但不同产品可以有不同采集范围并写入各自的 goal-scoped Raw Artifact。

## 2. 公共 Raw 规则

- 每个 Raw record 对应一个 Source row。
- 允许 DataFrame → JSON records、日期统一为 `YYYY-MM-DD`、numpy scalar → JSON scalar。
- Raw 不做分析视角重命名、单位换算、跨 Source join、派生指标或业务判断。
- `trade_date` 以及 contract lifecycle 的 `list_date`、`delist_date`、`maturity_date` 在 Raw 中统一为 `YYYY-MM-DD`；这只改变表示形式，不改变 Source 语义。

## 3. `index_daily`

Tushare `index_daily` 支持按 `ts_code` 与单日 `trade_date` 或 `start_date + end_date` 历史区间取得指数日行情。具体指数 universe 和时间范围由产品 authority 决定。

核心字段：

| 字段 | 语义 | 单位/说明 |
| --- | --- | --- |
| `ts_code` | 指数代码 | Source 主键 |
| `trade_date` | 交易日 | `YYYY-MM-DD` |
| `open` | 开盘价 | 点 |
| `high` | 最高价 | 点 |
| `low` | 最低价 | 点 |
| `close` | 收盘价 | 点 |
| `pre_close` | 昨收价 | 点 |
| `change` | 涨跌额 | 点，Source 定义为 `close - pre_close` |
| `pct_chg` | 涨跌幅 | %，数值 1 表示 1% |
| `vol` | 成交量 | 手 |
| `amount` | 成交额 | 千元 |

单日或历史区间、指数 universe 与 Raw 文件名均由消费该 Capture 的产品 authority 决定。

## 4. `stock_daily`

Tushare `daily` 可以按 `trade_date` 取得该日 A 股日线事实。它是未复权日行情；停牌期间不会返回对应股票数据。`pre_close` 是昨收价（除权价），除权除息日按交易所口径给出除权参考价。`pct_chg` 保持 Source 提供的事实，不在 Raw 层重算。

核心字段：

| 字段 | 语义 | 单位/说明 |
| --- | --- | --- |
| `ts_code` | 股票代码 | Source 主键 |
| `trade_date` | 交易日 | `YYYY-MM-DD` |
| `open` | 开盘价 | 元，未复权 |
| `high` | 最高价 | 元，未复权 |
| `low` | 最低价 | 元，未复权 |
| `close` | 收盘价 | 元，未复权 |
| `pre_close` | 昨收价（除权价） | 元 |
| `change` | 涨跌额 | 元，Source 定义为 `close - pre_close` |
| `pct_chg` | 涨跌幅 | %，数值 1 表示 1% |
| `vol` | 成交量 | 手 |
| `amount` | 成交额 | 千元 |

## 5. `mo_option_basic`

至少保留：

| 字段 | 语义 |
| --- | --- |
| `ts_code` | 期权合约代码 |
| `exchange` | 交易所，MO 为 CFFEX |
| `opt_code` | 期权合约代码或简称 |
| `call_put` | Source 认购/认沽字段 |
| `exercise_price` | 行权价 |
| `maturity_date` | 到期日 |
| `list_date` | 上市日期 |
| `delist_date` | 退市日期 |

Raw 层不得把 `exercise_price`、`maturity_date`、`call_put` 重命名为 `strike`、`expiry_date`、`option_type`；这些属于 Analysis Preparation。

## 6. `mo_option_daily`

至少保留：

| 字段 | 语义 |
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

`strike`、`expiry`、`option_type`、IV 和 Greeks 不是 `opt_daily` Raw fact；需要时由下游结合 contract facts 确定性准备。

## 7. `im_futures_basic`

至少保留能够确定合约身份与生命周期的事实：

| 字段 | 语义 |
| --- | --- |
| `ts_code` | 合约代码 |
| `exchange` | 交易所，IM 为 CFFEX |
| `fut_code` | 合约代码或简称 |
| `list_date` | 上市日期 |
| `delist_date` | 退市日期 |

Source 中其他表达合约到期或交割时间的字段可以保留；Raw 层不创造分析字段。

## 8. `im_futures_daily`

至少保留：

| 字段 | 语义 |
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
| `change1` | Source 涨跌额字段 |
| `change2` | Source 涨跌额字段 |
| `vol` | 成交量 |
| `amount` | 成交额 |
| `oi` | 持仓量 |
| `oi_chg` | 持仓量变化 |

## 9. Ownership Boundary

本文档不决定产品需要哪些 Capture、采集多少日期或合约、Raw 目录、完整性、join、选价或输出结构。上述规则必须从 [../CAPABILITIES.md](../CAPABILITIES.md) 进入对应产品 authority。
