# tushare_equity_index_options Dataset architecture authority

本文件是股指期权自治 bounded-context 的稳定入口，拥有 identity、purpose、ownership、Scope / Window 与关键领域边界。继承 [DataLake architecture](../../ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)，由 [DATASETS.md](../../DATASETS.md) 导航进入。Source / Instrument mapping 进入 [FACTS.md](FACTS.md)，完整合约集合与 success predicate 进入 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，交易日 prerequisite 进入 [TRADING_DAYS.md](TRADING_DAYS.md)，consumer contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity、Source 与 ownership

Canonical identity 为 `tushare_equity_index_options`，沿用 Tushare Dataset naming convention。本 Dataset 管理 CFFEX 真实股指期权合约及其 Tushare Source 日线 facts；metadata Source 为 `opt_basic`，daily Source 为 `opt_daily`。不管理 synthetic chain instruments 或其他交易所期权。

Source provider 为 Tushare，execution 继承 [providers/tushare/ARCHITECTURE.md](../../providers/tushare/ARCHITECTURE.md)。本 Dataset Source Adapter 拥有 endpoint / parameters、catalog / daily request strategy、pagination 与 option chain / product-day partition；facts normalization 与 completeness 规则由 Dataset Domain authority 拥有。

本 bounded context 位于 `datasets/tushare_equity_index_options/`；authority、`src/`、`tests/` 与 `data/` 的 ownership、colocation 和 Python boundary 继承 [模块架构](../../ARCHITECTURE.md)。不提供旧名兼容实现。

Instrument 是 Dataset-local 期权合约 catalog。Underlying relationship 通过稳定指数 identity 表达，不依赖 Index/Futures cache 存在，不引用其他库 instrument_id。Index、Futures、Options 始终分别拥有 persistence；没有跨库 FK、global instrument master、internal persistence access 或跨库事务。

## 2. Scope、Window 与 ownership unit

V1 唯一 Scope 为 `OptionsDailyScope(product_codes)`，选择 non-empty canonical product set。当前产品为 IO / HO / MO；classification 与 underlying 由 FACTS.md 的可扩展市场契约表拥有，不是永久 whitelist。未来新增产品先扩展关系表，不增加 contract、expiry、strike 或 call_put Scope。

Window 为 transient inclusive `start_date..end_date`。Calendar 确定开市日 D，目标 FetchUnits 为所选 products × D；不按 Source rows、metadata 缺口或产品生命周期自动收缩请求。

Canonical FetchUnit identity 为 `(product_code, trade_date)`，是当日该 product 全部有效 expiry × 挂牌 strike × CALL/PUT 合约横截面的 minimum synchronization / reconciliation / write ownership boundary。它是 product-level option chain，不是单 expiry chain。Record natural identity 为 `(contract_code, trade_date)`；Record 表达 expiry、strike、CALL/PUT，这些维度不进入 FetchUnit key。

一个成功 unit owns 完整 active contract Record set，cardinality 为 `0..n`；expected set、已证明空集合、缺腿/缺 strike/缺 expiry 与 required facts 的 completeness 由 CONTRACT_UNIVERSE.md 拥有。强 completeness 不由 API success、日行情返回行数或 Source batching 定义。

## 3. Dependency 与职责终点

唯一跨 Dataset runtime dependency 为 Options → Calendar public Application Service，显式使用 CFFEX；failure / snapshot / ensure 权限进入 TRADING_DAYS.md。Calendar 不反向依赖 Options，不新增 Options → Index/Futures runtime dependency。Public operation family 保持 coverage / ensure / export。

本 Dataset 不生成 IV、moneyness、DTE derived features、option risk premium、Greeks、premium 或 research statistics，不把自行计算的指标伪装为 Source facts。下游通过 public services 组合事实；不消费 Snapshot option-chain product internals/Raw，不通过共享数据库或 CLI JSON 获取数据。具体 HTTP / Research integration implementation 遵循已冻结 public service boundary；当前不引入 refresh/force/TTL，也不重新决定既定 domain/service contract。

## 4. Dataset Composition 与职责组织

本 Dataset 按公共 [COMPOSITION.md](../../COMPOSITION.md) 接入 Kernel；六角色绑定如下：

| Role | 本 Dataset 绑定 / canonical owner |
| --- | --- |
| FetchUnitPlanner | 本文件第 2 节：canonical products × 固定 D → `(product_code, trade_date)`；CFFEX Calendar view 与权限归 [TRADING_DAYS.md](TRADING_DAYS.md) |
| Source Port / Adapter | 本 Dataset 的 opt_basic/opt_daily Adapter；[FACTS.md](FACTS.md) 拥有 Source mapping / bounded strategy，Provider 只执行请求 |
| Normalizer | Options Domain；[FACTS.md](FACTS.md) 拥有 anchored identity / product normalization、Instrument、underlying 与 daily facts mapping |
| Completeness Validator | Options Domain；[CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md) 拥有完整 catalog、全部 active expiry/strike/CALL-PUT expected set、observed multiset、零 Records success 与历史 basis；nullable 条件只由 FACTS.md 拥有 |
| Export Projector | Options Domain 的业务 view projection；[SERVICE.md](SERVICE.md) 唯一拥有 `options_daily` V2、fields、ordering 与 wire meaning |
| Repository Port / Adapter | Kernel 标准 SQLite Adapter；Options Composition Root 绑定自己的 identity/source/storage context，basis 存储与 snapshot 机制归 [PERSISTENCE.md](../../PERSISTENCE.md) |

本 Dataset 有一个 Dataset-owned Calendar Prerequisite Resolver，按 [TRADING_DAYS.md](TRADING_DAYS.md) 将合法 Options request + operation permission 转为已验证 CFFEX Calendar context（由匹配 Window 的完整 view 验证得到的固定 D）。Composition Root 绑定该 Resolver、Calendar public service、上述六角色与 Adapters，发布 OptionsDailyService / create_service()。Public Service 先验证 request，再调用 Resolver；纯 FetchUnitPlanner 消费 request/context 展开 products × D，不读库、不调用 Calendar/Source、不按 expiry、strike、CALL-PUT、缓存、缺 metadata 或 Source rows 改变目标；Kernel 随后检查缓存并选择待执行 units。

Normalizer 按 FACTS.md 将 product-day daily facts、合法 Instruments 和 invocation catalog basis 转为 UnitRecords；Validator 按 CONTRACT_UNIVERSE.md 验证全部 active expiry/strike/CALL-PUT 横截面（含已证明为空的零 Records），通过后才经 Repository Port 原子提交。Catalog acquisition 在 selected units 的 Source 执行阶段进行，用于业务 completeness，不作为额外跨 Dataset Resolver 或裁剪目标的 Planning Context。交接与历史 basis 的读校验继承 [PORTS.md](../../PORTS.md)；Kernel 只负责目标确定后的通用生命周期。

Source Adapter 执行完整 catalog acquisition 与 daily 请求；metadata 是否完整、身份/市场关系、inclusive list_date/delist_date、chain completeness 和 nullable facts 都归 Dataset Domain，不移入 Provider / Kernel。Domain Validator/索引的复用遵守 EXECUTION.md 与本 Dataset completeness authority，不能按新 catalog 重判旧 success。BatchPlanner 的产品日分组/bounds 归 FACTS.md，prefetch/单 writer 属于 Kernel 执行配置。

目标职责区分 Dataset Domain（目标展开、identity/metadata/daily normalization、catalog/逐 unit validation、projection）、Source Adapter（请求、分页、partition）、Composition Root / Public Service（request / Calendar 编排、实例绑定、Kernel delegation）。Domain 不依赖 Provider、SQLite 或 sibling internals；public namespace 与 request/result/view 保持 SERVICE.md 契约，不创建第二套通用 persistence 或 ensure engine。
