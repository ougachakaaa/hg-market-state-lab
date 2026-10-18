# CFFEX Equity Index Futures Basis History read/application contract

本文档从属于 [Product authority](ARCHITECTURE.md)。Source scope 与 observation dates 见 [data authority](data.md)；family、slot、公式、校验及排序见 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md)。

## Public Python boundary

产品从 `data_snapshot.products.cffex_equity_index_basis_history` 公开 `CFFEXEquityIndexBasisHistoryRequest`，字段为 `futures_family`、`start_trade_date`、`end_trade_date`；同一 public module 公开 `run_cffex_equity_index_basis_history(request: CFFEXEquityIndexBasisHistoryRequest) -> CFFEXEquityIndexBasisHistoryResult`。调用方只提供 semantic request，并接收 result 或 `CFFEXEquityIndexBasisHistoryError`。产品的 production execution entry 自行加载 Tushare credential、创建 Source client、组合 Capture、Preparation 与 Application Service；可注入 Source client 的 service 是产品内部测试/组合能力，不要求 Research 构造它。

`CFFEXEquityIndexBasisHistoryError` 是公开、已分类的产品失败，具有稳定的 `reason`：`invalid_request`、`source_failure`、`no_observations`、`incomplete_panel`。Credential/client construction、Source 调用或 Source 无法服务所需区间归 `source_failure`；请求字段或日期不合法归 `invalid_request`；有效区间内没有 underlying 日线观测归 `no_observations`；其余缺失、重复、冲突、不可用或无法唯一形成完整 panel 的事实归 `incomplete_panel`。错误不得发布成功 result 或 partial panel。

## Preparation 与 result

Preparation 对每个实际 observation date，将唯一的同日标的 close 与该日全部 active 合约的唯一 futures close 对齐，应用共享 CFFEX basis 语义并在全 panel 验证后排序。Preparation 不访问网络、Research、HTTP DTO 或 sibling product artifact。

每条公开 `CFFEXEquityIndexBasisObservation` 至少包含：

```text
trade_date
futures_family
underlying_code
contract_code
contract_slot
delist_date
days_to_delist
annualization_days
underlying_close
futures_close
basis_points
basis_pct
annualized_basis_pct
```

`CFFEXEquityIndexBasisHistoryResult` 至少包含 `futures_family`、`start_trade_date`、`end_trade_date`、`family_listing_date`、`first_observation_date`、`last_observation_date`、`underlying_code`、`source_identity`、`observations`。`family_listing_date` 来自共享 CFFEX basis authority；`first_observation_date` 与 `last_observation_date` 是成功 panel 的首末实际 observation dates，而非虚构日历边界。`source_identity` 稳定标识 Tushare `index_daily`、`fut_basic`、`fut_daily` 的事实来源，不暴露 credential、Raw 路径或 Source client。`observations` 是按共享 canonical order 排列的 flat records。Result 自身足以识别请求、来源、标的、实际覆盖范围和每个完整期限结构。

V1 可完全 request-scoped、in-memory；无 HTTP endpoint 或 persisted final artifact 要求。Research consumer 不得导入 Source/Capture、Raw、私有 Preparation、credential、Tushare client 或 HTTP DTO。
