# CFFEX Equity Index Futures Basis History 产品 authority

本文件是本 Snapshot Product 的稳定入口。模块边界见 [Snapshot architecture](../../../../ARCHITECTURE.md)；CFFEX family、标的、上市边界、合约生命周期、slot、基差公式及规范顺序由 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md) 唯一拥有。

## Product identity 与 query

本产品针对一个明确的 CFFEX 股指期货 family 和显式日期区间，发布完整、analysis-ready 的历史期货基差期限结构。每次请求只服务 `IF`、`IH`、`IC`、`IM` 中一个 family；不提供 symbol、exchange 或任意期货查询。Research 如需四个 family，调用四次。

Public semantic request 为 `futures_family`、`start_trade_date`、`end_trade_date`。日期必须为真实 `YYYY-MM-DD`，含两端且 `start_trade_date <= end_trade_date`，无默认值、`today/latest` 或自动交易日替换。同一规范化三元组是同一 query identity。有效起点为请求起点与该 family 上市起点的较晚者；上市前日期不是缺失观测。

## Ownership 与导航

| Owner | Canonical knowledge |
| --- | --- |
| 本文档 | Product purpose、family scope、query identity、跨子契约 invariant |
| [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md) | family/underlying/listing facts、合约生命周期、slot、日历距离、公式、校验与规范顺序 |
| [Source Capture authority](../../capture/ARCHITECTURE.md) | Tushare endpoint、共享 Source facts 与 minimal normalization |
| [Product data authority](data.md) | 本产品 Source scope、实际观测日期及完整性 |
| [Read/application contract](read-contract.md) | Preparation projection、result、分类失败与 public Python execution |

本产品拥有自己的 Application Service；Capture 可以将 query-scoped Source facts 直接交给 Preparation。成功不要求 persisted Raw 或 final artifact。它不读取 CSI1000 IM 产品的私有 Raw、Preparation 或结果。

## Invariants 与 non-goals

每个有效标的观测日都须形成唯一、完整的 `M0/M1/Q1/Q2` active futures panel；任一日不完整则整个请求失败。相同 Source facts、query 和 Preparation Definition 必须得到语义相同的有序结果。Research 仅消费本产品 public application boundary，不参与 credential loading、Source client 或 Capture composition。

V1 不提供 HTTP endpoint、数据库、通用 derivatives framework、product registry、主力合约筛选、future return、Research 统计、信号或策略结果。
