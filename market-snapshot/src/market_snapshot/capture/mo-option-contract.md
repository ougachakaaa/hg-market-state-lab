# MO option Source contract

本文档从属于 [Capture architecture](ARCHITECTURE.md)，拥有 Tushare `opt_basic` 与 `opt_daily` 的共享 Source facts。

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
