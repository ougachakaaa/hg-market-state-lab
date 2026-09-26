# Index and stock daily Source contract

本文档从属于 [Capture architecture](ARCHITECTURE.md)，拥有 Tushare `index_daily` 与 `daily` 的共享 Source facts。

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
