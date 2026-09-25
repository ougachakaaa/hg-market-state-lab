# Shared Capture common Source contract

本文档从属于 [Capture architecture](ARCHITECTURE.md)，只拥有 Capture catalog 与公共 Raw normalization。产品 scope、窗口与 completeness 由产品 authority 拥有。

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
