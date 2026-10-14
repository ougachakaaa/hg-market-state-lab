# tushare_equity_index_futures Dataset architecture authority

本文件是股指期货自治 bounded-context 的稳定入口，拥有 identity、purpose、ownership、Scope / Window 与关键领域边界。继承 [DataLake architecture](../../ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)，由 [DATASETS.md](../../DATASETS.md) 导航进入。Source / Instrument mapping 进入 [FACTS.md](FACTS.md)，合约集合与 success predicate 进入 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，交易日 prerequisite 进入 [TRADING_DAYS.md](TRADING_DAYS.md)，consumer contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity、Source 与 ownership

Canonical identity 为 `tushare_equity_index_futures`，沿用已确定的 Tushare Dataset naming convention。本 Dataset 管理 CFFEX 股指期货真实普通月合约及其 Tushare Source 日线 facts；metadata Source 为 `fut_basic`，ordinary instrument selection 显式使用 `fut_type="1"`，daily Source 为 `fut_daily`。主力/连续序列不作为 instrument 或 records。

Source provider 为 Tushare，execution 继承 [providers/tushare/ARCHITECTURE.md](../../providers/tushare/ARCHITECTURE.md)。本 Dataset Source Adapter 拥有 endpoint / parameters、catalog / daily request strategy、pagination 与 product-day partition；facts normalization 与 completeness 规则由 Dataset Domain authority 拥有。

本 bounded context 位于 `datasets/tushare_equity_index_futures/`；authority、`src/`、`tests/` 与 `data/` 的 ownership、colocation 和 Python boundary 继承 [模块架构](../../ARCHITECTURE.md)。不建立旧名 compatibility implementation。

Instrument 为 Dataset-local 合约 catalog。Underlying 是稳定指数 semantic identity，不是 Index instrument_id；本 Dataset 与 Index、Options 的 storage lifecycle 分离，无 global instrument master、跨 SQLite FK、internal persistence access 或跨库事务。

## 2. Scope、Window 与 ownership unit

V1 唯一 Scope 为 `FuturesDailyScope(product_codes)`，选择 non-empty canonical 股指期货 product set。当前产品为 IF / IH / IC / IM，合法 classification 与 underlying 由 FACTS.md 的可扩展市场契约表拥有；它不是永久封闭 whitelist。新增产品须明确市场关系后扩展该表，不新增 Scope 或 registry。

Window 为 transient `start_date..end_date`，两端 inclusive。Calendar 确定开市日 D，目标 FetchUnits 为所选 products × D；不因缺 metadata、上市前日期或 Source 返回行数缩小目标。Contract、delivery month 或其他维度不构成第二套 Scope。

Canonical FetchUnit identity 为 `(product_code, trade_date)`，是 product 当日普通真实月合约完整横截面的 minimum synchronization / reconciliation / write ownership boundary。Record natural identity 为 `(contract_code, trade_date)`；contract 是 Instrument / Record identity，不是 FetchUnit。一个成功 unit owns `0..n` canonical FuturesDailyRecords；确切 expected set、空集合证明与 completeness 由 CONTRACT_UNIVERSE.md 唯一拥有。

`FetchUnit != Source Request`。Provider 可批量返回多个 products/dates，但不能把 transport batching 转成 unit grain。Records、合法 metadata/completeness 依据与 success metadata 一致原子提交；状态及默认跳过 success 继承公共 domain invariant。

## 3. Dependency 与职责终点

唯一跨 Dataset runtime dependency 为本 Dataset → Calendar public Application Service，显式采用 CFFEX 日历；具体调用、failure 与 snapshot 见 TRADING_DAYS.md。Calendar 不反向依赖 Futures；不增加 Futures → Index / Options runtime dependency。公开 boundary 只包含 coverage / ensure / export。

本 Dataset 不生成 basis、annualized basis、main-contract / continuous series、roll return、DTE、term structure 或 research features。下游通过各 Dataset public service 组合 Source facts 后计算；不消费 Snapshot 私有 Source/Capture、Raw Artifact、CLI JSON 或其他 Dataset SQLite。具体 HTTP / Research integration implementation 遵循已冻结 public service boundary；当前不引入 refresh/force/TTL，也不重定已确定的业务语义。

## 4. Dataset Composition 与职责组织

本 Dataset 按公共 [COMPOSITION.md](../../COMPOSITION.md) 接入 Kernel；六角色绑定如下：

| Role | 本 Dataset 绑定 / canonical owner |
| --- | --- |
| FetchUnitPlanner | 本文件第 2 节：canonical products × 固定 D → `(product_code, trade_date)`；CFFEX Calendar view 与权限归 [TRADING_DAYS.md](TRADING_DAYS.md) |
| Source Port / Adapter | 本 Dataset 的 fut_basic/fut_daily Adapter，含 type-2 exclusion evidence 请求；[FACTS.md](FACTS.md) 拥有请求范围/映射与 bounded strategy，Provider 只执行请求 |
| Normalizer | Futures Domain；[FACTS.md](FACTS.md) 拥有 ordinary family、Instrument、daily facts 与 underlying mapping |
| Completeness Validator | Futures Domain；[CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md) 拥有完整 catalog 证明、inclusive lifecycle expected set、observed multiset、零 Records success 与历史 basis predicate，结合 FACTS.md 校验全部字段 |
| Export Projector | Futures Domain 的业务 view projection；[SERVICE.md](SERVICE.md) 唯一拥有 `futures_daily` V2、fields、ordering 与 wire meaning |
| Repository Port / Adapter | Kernel 标准 SQLite Adapter；Futures Composition Root 绑定自己的 identity/source/storage context，basis 存储与 snapshot 机制归 [PERSISTENCE.md](../../PERSISTENCE.md) |

本 Dataset 有一个 Dataset-owned Calendar Prerequisite Resolver，按 [TRADING_DAYS.md](TRADING_DAYS.md) 将合法 Futures request + operation permission 转为已验证 CFFEX Calendar context（由匹配 Window 的完整 view 验证得到的固定 D）。Composition Root 绑定该 Resolver、Calendar public service、上述六角色与 Adapters，发布 FuturesDailyService / create_service()。Public Service 先验证 request，再调用 Resolver；纯 FetchUnitPlanner 消费 request/context 展开 products × D，不读库、不调用 Calendar/Source、不按缓存或 catalog lifecycle 缩小目标；Kernel 随后检查缓存并选择待执行 units。

Normalizer 按 FACTS.md 将 product-day daily facts、合法 ordinary Instruments 和 invocation catalog basis 转为 UnitRecords；Validator 按 CONTRACT_UNIVERSE.md 验证完整横截面（含已证明为空的零 Records），通过后才经 Repository Port 原子提交。Catalog/exclusion evidence 在 selected units 的 Source 执行阶段取得，用于业务 completeness，不作为额外跨 Dataset Resolver 或裁剪目标的 Planning Context。交接与历史 basis 的读校验继承 [PORTS.md](../../PORTS.md)；Kernel 不解释 CFFEX、普通月合约或 expected set。

新 attempts 的 catalog acquisition 由 Source Adapter 执行，catalog 是否完整、可排除 family、每次 invocation basis 与 success 历史解释归 CONTRACT_UNIVERSE.md；这些不成为 Kernel Repository 或 Provider 规则。Source 保持有界响应，Domain Validator/索引的复用遵守 EXECUTION.md 与本 Dataset completeness authority。BatchPlanner 的产品日分组/bounds 归 FACTS.md；prefetch/单 writer 属于 Kernel 执行配置。

目标职责区分 Dataset Domain（目标展开、family/metadata/daily normalization、catalog/逐 unit validation、projection）、Source Adapter（请求、分页、partition）、Composition Root / Public Service（request / Calendar 编排、实例绑定、Kernel delegation）。Domain 不依赖 Provider、SQLite 或 sibling internals；public namespace 与 request/result/view 保持 SERVICE.md 契约，不创建另一套通用 persistence 或 ensure engine。
