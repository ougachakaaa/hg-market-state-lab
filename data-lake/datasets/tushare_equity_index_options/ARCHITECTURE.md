# tushare_equity_index_options Dataset architecture authority

本文件是股指期权自治 bounded-context 的稳定入口，拥有 identity、purpose、ownership、Scope / Window 与关键领域边界。继承 [DataLake architecture](../../ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)，由 [DATASETS.md](../../DATASETS.md) 导航进入。Source / Instrument mapping 进入 [FACTS.md](FACTS.md)，完整合约集合与 success predicate 进入 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，交易日 prerequisite 进入 [TRADING_DAYS.md](TRADING_DAYS.md)，consumer contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity、Source 与 ownership

Canonical identity 为 `tushare_equity_index_options`，沿用 Tushare Dataset naming convention，取代此前 provider 未确定时的 `equity_index_options`。本 Dataset 管理 CFFEX 真实股指期权合约及其 Tushare Source 日线 facts；metadata Source 为 `opt_basic`，daily Source 为 `opt_daily`。不管理 synthetic chain instruments 或其他交易所期权。

Source provider 为 Tushare，execution authority 为 [providers/TUSHARE.md](../../providers/TUSHARE.md)。本 Dataset adapter 拥有 endpoint / parameters、catalog / daily request strategy、pagination、option chain / product-day partition 与 facts normalization；credential、client、限流与 provider request failure conversion 归共享 Provider Runtime，后续实现直接采用该 boundary。

本 bounded context 位于 `datasets/tushare_equity_index_options/`，自治拥有 authority、未来 src/、tests/ 和 data/ 中 exactly one SQLite，共用 repository root 唯一 Python project/environment 与 `data_lake` namespace。本次仅发布 authority，不创建 package、schema、adapter、tests implementation 或 runtime data，也不提供旧名兼容实现；实现差异统一见 [reconciliation](../../IMPLEMENTATION_RECONCILIATION.md)。

Instrument 是 Dataset-local 期权合约 catalog。Underlying relationship 通过稳定指数 identity 表达，不依赖 Index/Futures cache 存在，不引用其他库 instrument_id。Index、Futures、Options 始终分别拥有 persistence；没有跨库 FK、global instrument master、internal persistence access 或跨库事务。

## 2. Scope、Window 与 ownership unit

V1 唯一 Scope 为 `OptionsDailyScope(product_codes)`，选择 non-empty canonical product set。当前产品为 IO / HO / MO；classification 与 underlying 由 FACTS.md 的可扩展市场契约表拥有，不是永久 whitelist。未来新增产品先扩展关系表，不增加 contract、expiry、strike 或 call_put Scope。

Window 为 transient inclusive `start_date..end_date`。Calendar 确定开市日 D，目标 FetchUnits 为所选 products × D；不按 Source rows、metadata 缺口或产品生命周期自动收缩请求。

Canonical FetchUnit identity 为 `(product_code, trade_date)`，是当日该 product 全部有效 expiry × 挂牌 strike × CALL/PUT 合约横截面的 minimum synchronization / reconciliation / write ownership boundary。它是 product-level option chain，不是单 expiry chain。Record natural identity 为 `(contract_code, trade_date)`；Record 表达 expiry、strike、CALL/PUT，这些维度不进入 FetchUnit key。

一个成功 unit owns 完整 active contract Record set，cardinality 为 `0..n`；expected set、已证明空集合、缺腿/缺 strike/缺 expiry 与 required facts 的 completeness 由 CONTRACT_UNIVERSE.md 拥有。强 completeness 不由 API success、日行情返回行数或 Source batching 定义。

## 3. Dependency 与职责终点

唯一跨 Dataset runtime dependency 为 Options → Calendar public Application Service，显式使用 CFFEX；failure / snapshot / ensure 权限进入 TRADING_DAYS.md。Calendar 不反向依赖 Options，不新增 Options → Index/Futures runtime dependency。Public operation family 保持 coverage / ensure / export。

本 Dataset 不生成 IV、moneyness、DTE derived features、option risk premium、Greeks、premium 或 research statistics，不把自行计算的指标伪装为 Source facts。下游通过 public services 组合事实；不消费 Snapshot option-chain product internals/Raw，不通过共享数据库或 CLI JSON 获取数据。CLI/HTTP、Research integration、refresh/force/TTL 是后续独立工作，不重新决定本轮 domain/service contract。
