# tushare_equity_index_futures Dataset architecture authority

本文件是股指期货自治 bounded-context 的稳定入口，拥有 identity、purpose、ownership、Scope / Window 与关键领域边界。继承 [DataLake architecture](../../ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)，由 [DATASETS.md](../../DATASETS.md) 导航进入。Source / Instrument mapping 进入 [FACTS.md](FACTS.md)，合约集合与 success predicate 进入 [CONTRACT_UNIVERSE.md](CONTRACT_UNIVERSE.md)，交易日 prerequisite 进入 [TRADING_DAYS.md](TRADING_DAYS.md)，consumer contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity、Source 与 ownership

Canonical identity 为 `tushare_equity_index_futures`，沿用已确定的 Tushare Dataset naming convention。本 Dataset 管理 CFFEX 股指期货真实普通月合约及其 Tushare Source 日线 facts；metadata Source 为 `fut_basic`，ordinary instrument selection 显式使用 `fut_type="1"`，daily Source 为 `fut_daily`。主力/连续序列不作为 instrument 或 records。

Source provider 为 Tushare，execution authority 为 [providers/TUSHARE.md](../../providers/TUSHARE.md)。本 Dataset adapter 拥有 endpoint / parameters、catalog / daily request strategy、pagination、product-day partition 与 facts normalization；credential、client、限流与 provider request failure conversion 归共享 Provider Runtime，遵循该 execution boundary。

本 bounded context 位于 `datasets/tushare_equity_index_futures/`，独立拥有 authority、src/、tests/ 与 data/ 中的 owned state（SQLite ownership 继承模块架构）；canonical Python namespace 归 `data_lake`，共用根唯一 project/environment。不建立旧名 compatibility implementation。

Instrument 为 Dataset-local 合约 catalog。Underlying 是稳定指数 semantic identity，不是 Index instrument_id；本 Dataset 与 Index、Options 的 storage lifecycle 分离，无 global instrument master、跨 SQLite FK、internal persistence access 或跨库事务。

## 2. Scope、Window 与 ownership unit

V1 唯一 Scope 为 `FuturesDailyScope(product_codes)`，选择 non-empty canonical 股指期货 product set。当前产品为 IF / IH / IC / IM，合法 classification 与 underlying 由 FACTS.md 的可扩展市场契约表拥有；它不是永久封闭 whitelist。新增产品须明确市场关系后扩展该表，不新增 Scope 或 registry。

Window 为 transient `start_date..end_date`，两端 inclusive。Calendar 确定开市日 D，目标 FetchUnits 为所选 products × D；不因缺 metadata、上市前日期或 Source 返回行数缩小目标。Contract、delivery month 或其他维度不构成第二套 Scope。

Canonical FetchUnit identity 为 `(product_code, trade_date)`，是 product 当日普通真实月合约完整横截面的 minimum synchronization / reconciliation / write ownership boundary。Record natural identity 为 `(contract_code, trade_date)`；contract 是 Instrument / Record identity，不是 FetchUnit。一个成功 unit owns `0..n` canonical FuturesDailyRecords；确切 expected set、空集合证明与 completeness 由 CONTRACT_UNIVERSE.md 唯一拥有。

`FetchUnit != Source Request`。Provider 可批量返回多个 products/dates，但不能把 transport batching 转成 unit grain。Records、合法 metadata/completeness 依据与 success metadata 一致原子提交；状态及默认跳过 success 继承公共 domain invariant。

## 3. Dependency 与职责终点

唯一跨 Dataset runtime dependency 为本 Dataset → Calendar public Application Service，显式采用 CFFEX 日历；具体调用、failure 与 snapshot 见 TRADING_DAYS.md。Calendar 不反向依赖 Futures；不增加 Futures → Index / Options runtime dependency。公开 boundary 只包含 coverage / ensure / export。

本 Dataset 不生成 basis、annualized basis、main-contract / continuous series、roll return、DTE、term structure 或 research features。下游通过各 Dataset public service 组合 Source facts 后计算；不消费 Snapshot 私有 Source/Capture、Raw Artifact、CLI JSON 或其他 Dataset SQLite。HTTP、Research integration 与 refresh/force/TTL 仍属于独立后续工作，不能重定已确定的业务语义。
