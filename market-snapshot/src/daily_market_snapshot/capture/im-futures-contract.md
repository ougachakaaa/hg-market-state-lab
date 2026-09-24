# IM futures Source contract

本文档从属于 [Capture architecture](ARCHITECTURE.md)，拥有 Tushare `fut_basic` 与 `fut_daily` 的共享 Source facts。

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
