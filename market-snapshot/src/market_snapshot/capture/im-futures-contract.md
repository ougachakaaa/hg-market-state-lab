# CFFEX equity-index futures Source contract

本文档从属于 [Capture architecture](ARCHITECTURE.md)，拥有 Tushare `fut_basic` 与 `fut_daily` 对 CFFEX IF/IH/IC/IM 普通月度股指期货的共享 Source facts、endpoint query 和 minimal normalization。Python Capture 已做最小 family 参数化，既有 IM Capture caller 与结果保持兼容。产品自己决定 family scope、日期区间、active universe、完整性、slot 和 Preparation；本文件不定义这些产品语义。

## `fut_basic` Source facts

对一个明确 family，以 `exchange=CFFEX`、`fut_type=1` 和对应 `fut_code ∈ {IF, IH, IC, IM}` 查询普通合约；合约 identity 用 family 加交割年月识别普通月度合约，排除同 family 的 continuous/main symbol。Source 返回的合约生命周期事实保留，不根据产品日期、成交量或持仓量筛选；产品决定 query-scoped lifecycle intersection。Capture 对 in-scope 合约保留缺失或冲突的事实供显式失败，不能因为 Source 异常而静默丢弃。

至少保留能够确定合约身份与生命周期的事实：

| 字段 | 语义 |
| --- | --- |
| `ts_code` | 合约代码 |
| `exchange` | 交易所，所支持 family 为 CFFEX |
| `fut_code` | 合约代码或简称 |
| `symbol` | 普通月度合约的 family 与交割年月 identity；用于排除 continuous/main symbol |
| `list_date` | 上市日期 |
| `delist_date` | 退市日期 |

Source 中其他表达合约到期或交割时间的字段可以保留；Raw 层不创造分析字段。

## `fut_daily` Source facts

按产品指定的合约与显式日期区间取得日行情。Capture 验证返回 row 的 `ts_code` 与请求合约一致、`trade_date` 位于请求范围，并保留 Source 缺席与合法 null 的区别；它不做同日指数 join、四槽映射或基差计算。

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

## MO session bulk target-date specialization

MO session Capture supports `fut_daily(trade_date=..., exchange="CFFEX")`.
Validate the entire response date and unique contract identities; reject a
response of 2,000 or more rows as potentially truncated. Filter to the complete
active ordinary IM universe determined from basic facts, retaining absent rows
as absence. Preparation continues to decide which matched IM facts are required.
This does not change other products' per-contract/range execution contracts.
