# CFFEX Equity Index Futures Basis History data authority

本文档从属于 [Product authority](ARCHITECTURE.md)，拥有本产品的 Source scope、observation dates 与 completeness。公共 Source facts 见 [Capture authority](../../capture/ARCHITECTURE.md)；family 与合约语义见 [共享 CFFEX basis authority](../../cffex_equity_index_basis/ARCHITECTURE.md)。

## Source scope 与日期

对请求的一个 family，取得对应标的指数的 `index_daily`、该 family 的 CFFEX 普通月度 `fut_basic`，以及所需合约的 `fut_daily`。Capture 的合约范围须覆盖生命周期与有效请求区间相交的所有普通月度合约：`list_date <= end_trade_date` 且 `delist_date >= effective_start_trade_date`。每个合约的 daily 查询裁切到 `max(effective_start_trade_date, list_date)` 至 `min(end_trade_date, delist_date)`，两端包含。不得因成交量、持仓量、主力标记或研究偏好缩小 scope。

若 `end_trade_date` 早于 family 上市起点，有效区间为空，按 `no_observations` 失败，不发起倒置范围的 Source 查询。

Observation dates 是有效请求区间内该标的指数实际返回的不同 `index_daily.trade_date`；不扩展日历、不创建节假日 observation、不将请求边界换成附近交易日，也不做 previous-close fill。成功请求至少有一个有效观测日。每个观测日必须有且只有一条标的日线 row，close 可用。

## 完整性

每个 observation date 都必须从完整 basic facts 确定全部 active contracts，并依共享语义唯一形成四槽；每个 active contract 当日须恰有一条可用 futures daily close。重复、未知或生命周期外的 daily row、缺失或冲突的合约 identity/lifecycle、不可用的 close，以及 Source 不能服务所需区间，均不能通过删合约、删日期、填值或返回 partial panel 修复。任一必需 Source 请求失败或任一日不完整，整个 Product request 失败。

Raw 如需持久化，只能属于本产品并保留 Source facts；不承诺 Raw 路径、final persistence、缓存或跨产品 artifact。Join、完整性验证、slot、公式和结果投影属于确定性 Preparation。
