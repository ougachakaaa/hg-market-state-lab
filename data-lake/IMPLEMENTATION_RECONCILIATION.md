# DataLake implementation reconciliation

本文件集中记录 DataLake implementation reconciliation；当前实现状态由第 11 节性能增量、第 10 节执行/存储基准及第 9 节 provider/facts 修复共同描述，第 1–8 节保留历史 reconciliation/evidence，不代表当前未完成的 gaps。初始记录以 commit `8e26a5e64804a19b2228bba0feaf0b157c5ecc3a` 为基准，不另行定义业务语义。目标 ownership、topology 与依赖方向由 [模块架构](ARCHITECTURE.md) 拥有；公共 domain / application invariants 见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 与 [APPLICATION.md](APPLICATION.md)；具体 Dataset 经 [catalog](DATASETS.md) 进入 architecture 与 SERVICE。

## 1. Source roots 与稳定 public namespace

根 Poetry `packages` 显式登记 `data-lake/src` 与 `data-lake/datasets/tushare_trade_calendar/src` 两个 `data_lake` package portions。Shared kernel 保留 `data_lake/__init__.py` 公共 facade，通过标准库 `pkgutil.extend_path(__path__, __name__)` 连接 source roots；`data_lake.datasets` 使用无 marker 的 implicit namespace，Calendar 在自身 `src/data_lake/datasets/tushare_trade_calendar/` 拥有 public package marker 与实现。

这是标准 Python package mechanics，不是 custom loader、runtime registry 或 Dataset manager；kernel 不 import Dataset。Public import 仍为 `data_lake.datasets.tushare_trade_calendar`，lab production import 无需改变。公共 facade 的显式 aliases、result/error contracts 与 Calendar semantic contracts 保持兼容。Repository 仍只有一个根 project、lockfile、dependency graph 与根 `.venv`；没有 Dataset-local project 或 editable/path subproject dependency。

## 2. Dataset-local storage 与 legacy state

Shared `database_path(dataset, storage_root)` 只验证 canonical filename identity 并拼接 caller 提供的 storage context，不再提供全局默认 root，也不创建目录或 SQLite。Calendar composition 从其 repository-installed source location 定位 owning Dataset，显式提供该 context 的 `data/`；默认文件为 `data-lake/datasets/tushare_trade_calendar/data/tushare_trade_calendar.sqlite3`。具体 storage contract 见 [SERVICE.md](datasets/tushare_trade_calendar/SERVICE.md)。

旧 `data-lake/data/*.sqlite3` 是 untouched legacy runtime state：不自动移动、复制、删除、覆盖，不作为 factory、coverage/export 或 ensure 的 fallback，不双写。旧文件与新 Dataset-local cache 分离，不建立 legacy compatibility layer。根 `.gitignore` 同时忽略旧 data root 与所有 Dataset-local `data/`，包含 SQLite journal / WAL 等 runtime files。Missing local cache 的 read-only 操作继续表达 missing 与空 view，不 materialize storage；ensure 仅写本地 owned cache。

未创建空 `data/` placeholder；目录只在有权写入的 operation 需要时 materialize。如未来需要保留旧缓存内容，须另行设计显式 migration / import operation；本次没有执行该操作。

## 3. Tooling 与验证 ownership

- 根 pytest testpaths/pythonpath、Ruff src、mypy files/mypy_path 同时覆盖 kernel 与 Dataset-local roots；mypy 启用 namespace packages / explicit package bases。根 Poetry install 提供 installed runtime imports，isolated interpreter subprocess 从临时 cwd 验证 import，不借助 pytest pythonpath 或 PYTHONPATH。
- Shared core/fake Dataset 与 module dependency tests 保留在 `data-lake/tests/`；Calendar tests 与 provider/import/storage verification 位于 `datasets/tushare_trade_calendar/tests/`；lab public-boundary verification 归 `lab/tests/`。旧禁止 datasets 下 Python 文件的断言已替换为新 source ownership / dependency checks。
- Architecture checks 验证 kernel 不依赖 Dataset/provider、Dataset 不依赖 siblings、Calendar 使用 shared kernel、provider confinement、consumer 只访问 public API、root tooling coverage 与 runtime ignore。现有 repository authority topology checks 已登记 DataLake 的全部入口。
- Storage tests 使用临时 SQLite 与 fake client，验证缺失本地缓存不 materialize、legacy 完整缓存不作为 fallback、ensure 只写新目录、新旧缓存共存时读写仍使用本地缓存、旧文件字节/mtime 与目录内容不变。Credential environment precedence 与 `market-snapshot/.env` fallback、已有 coverage/ensure/export 业务验证保留。

## 4. Reconciliation 状态与未扩展能力

本轮已对齐 source/test colocation、installed public namespace、唯一根 tooling、Dataset-local storage 和 dependency/topology verification。未发现本轮范围内需要新业务决策的 semantic gap。旧 cache 留存是显式安全规则，不是未完成的自动迁移工作。

Scope / Window / FetchUnit / Record、逐日 completeness、coverage / ensure / export、result fields、failure taxonomy、export snapshot、credential convention 与 CLI product semantics 均未重新设计。HTTP、Research/Snapshot integration、schema migration、refresh/TTL/force、cross-Dataset dependency/query 与显式 legacy import 仍不属于本轮实现范围。

本轮验证：Poetry install、普通及 isolated installed imports、wheel build、DataLake/lab/相关 architecture checks（228 passed、1 skipped）、受影响模块 Ruff 与分模块 mypy、diff whitespace 均通过。真实 legacy SQLite 的 SHA-256、大小与 mtime 前后相同。额外全仓 pytest 为 829 passed、2 skipped、1 failed：未修改的 MO Option Chain Windows crash-lock recovery test 单独运行及空 pytest config 下均复现；无参数根 mypy 被基准已存在的空 `market-snapshot/scripts` files entry 阻断。这些仓库级验证问题未在本轮 DataLake reconciliation 中修改。

## 5. 三个新 Dataset 的 authority-only 增量

本节记录基于 `67e7b067c0e80c2b948e888282f9ec0b38fb529d` 的后续 authority 增量；上文 implementation/verification 是历史基准，不是三个新 Dataset 的实现证据。

- 当轮 [Index](datasets/tushare_index_daily/ARCHITECTURE.md) 已确定完整 domain/service、Source facts 与 Calendar prerequisite contract；Futures / Options 当时只锁定稳定边界与 operation family，Scope/Window、FetchUnit/Record identity、completeness 及相应 request/payload details 待人工决定。它们现已重命名，当前契约由 [Futures](datasets/tushare_equity_index_futures/ARCHITECTURE.md) / [Options](datasets/tushare_equity_index_options/ARCHITECTURE.md) 拥有，后续定稿见第 6 节；本节保留历史增量含义。
- 原 repository/module/policy 的“Dataset 当前互不依赖”已显式协调为默认禁止、仅允许已声明的单向 public service dependency。本轮唯一新增 permission 为 Index → Calendar；Calendar service/domain 不变，underlying relationship 不授予 Futures/Options runtime dependency。Storage ownership、kernel direction、read-only、公共 result/errors、snapshot 与 root runtime invariant 均保留。
- 新三个 bounded contexts 只有 authority：没有 source/test/storage directories、Python package/factory、SQLite schema、Source adapter、CLI registration 或 runtime integration。不修改根 Python registration/configuration，不执行 Source 请求或真实 cache migration。
- 现有 architecture tests 仍按旧 implementation 验证 Dataset 不依赖 siblings；Index implementation 开始前须将 dependency check 收紧为明确 public boundary permission，而不是全面取消 sibling 限制，并验证只读/Calendar failure/两库独立 state。此为 implementation reconciliation 输入，本轮不修改 tests。
- 现有 authority topology test 的 fixed CONTEXT_ENTRIES 不含本轮新增八个 authority 文件；本轮通过 catalog 显式登记、现有全仓 relative-link 检查与补充只读 root reachability 检查验证这些 entries。后续 implementation verification 应登记新 entries，不能将旧 test 的 green 视为新 contract 行为已被验证。

当轮没有剩余上下层 authority conflict；当时 Futures/Options 待决语义是有意保留的设计边界，后由第 6 节定稿。Index 后续仅需按既定语义 reconciliation/实现、细化事务与 batching 等 implementation concern，不借此重新决定 FetchUnit 或新增 public verbs。

本次 authority 验证：现有 authority topology 检查 13 passed，DataLake boundary 检查 5 passed；补充只读检查确认新增八份 authority 从根入口可达、相对链接合法，全部十四个新增/修改文件均为 Markdown，新增 Dataset 目录只有 authority。`git diff --check` 与新增文件 whitespace 检查通过，已审阅包含新增文件的完整 diff。以上证明文档 topology 与现有边界未受破坏，不证明尚不存在的新 Dataset runtime 行为。

## 6. Futures / Options implementation-ready authority

本节记录基于 commit `c3c9432a71eb2976967ab548598596aad3376ee6` 的后续 authority-only 定稿，不把前述历史 implementation/verification 当作新 Dataset 的实现证据。

- Canonical identity 与目录从 equity_index_futures / equity_index_options 改为 tushare_equity_index_futures / tushare_equity_index_options；provider 已确定为 Tushare。Catalog、module navigation 和现存 authority links 已协调，不发布旧名 compatibility package。
- 各 bounded context 采用 ARCHITECTURE 稳定入口 → FACTS（Source / Instrument / underlying）→ 按任务选择 CONTRACT_UNIVERSE（catalog proof / completeness）、TRADING_DAYS（Calendar prerequisite）、SERVICE（public request/result/view）。专题各有唯一 semantic owner，不在模块入口复制 schema 或 Source workflow。
- Scope 唯一为 canonical product_codes set，inclusive date Window；FetchUnit=(product_code,trade_date)，Record=(contract_code,trade_date)。Futures 使用 fut_basic ordinary type-1 / fut_daily；Options 使用 opt_basic / opt_daily，全 active expiry/strike/CALL-PUT 横截面。Expected 由完整 Dataset-local catalog 的 list_date <= day <= delist_date 证明，不能以 daily rows、maturity_date 或未知 catalog 猜 expected。
- 已确认每次存在 missing/non-success attempts 的 ensure 重新完整取得 catalog，并在 invocation 冻结；全 success / 零目标和 read-only 不刷新。Observed 必须与 expected 恰一致且每合约 exactly one valid daily row；已证明空 expected 加已确认空 observed 可零 Records success。成功 Records、合法 metadata/completeness basis 与 success metadata 原子一致保留；后续 catalog 不重判或替换旧成功依据，freshness deferred。
- 已确认 Options Source volume=amount=0 时，open/high/low 可分别合法 None，已有零照保留；正成交时空价格、缺 row/field 或其他 required facts 缺席仍失败。Futures delv_settle 显式请求并保留合法 None；Options last_ddate 可合法 None。具体字段、types 与单位归各自 FACTS/SERVICE。
- 唯一新增 runtime permissions 为 Futures → Calendar public service、Options → Calendar public service，均显式 CFFEX；Index 原有 SSE prerequisite 不变。目标未知导致整个 OperationError，已知单位的可恢复 catalog/daily failures 进入产品日 UnitFailure。禁止 derivative → Index、Futures ↔ Options、sibling internals、共享 SQLite / FK / 跨库事务；underlying 是 Source identity/authority-owned 市场关系，无 global master。
- Coverage/ensure counters 统计产品日，records_written 统计本次成功提交合约日 rows，不计 metadata/Calendar/已有成功。V1 flat records views 为 futures_daily / options_daily；export_schema_version=1，排序与所有 typed fields 已定稿，partial 仅 success units，coverage/Records/关联 metadata 来自同一 owned-cache snapshot。Historical/daily 共用 ensure，不新增 public verbs。

设计阶段只读 Source evidence 已落在各自 FACTS.md：普通期货样本 product-day 和两日期权完整 expected/observed 匹配，opt_basic 分页样本无重复且与完整请求一致，确认 underlying identity 与零成交空价格等真实 representation。样本不是永久分页/无截断 guarantee，也不替代运行时 catalog 完整性证明；未存 token、provider dump 或 runtime data。未发现需要放宽 strong completeness 或新增人工 semantic decision 的 gap。

后续 implementation 输入：新增两个 Dataset-local package/factory、storage/schema/adapter、public types、逐 unit 原子写入与保留成功 basis、provider exhaustion/partition 策略；根唯一 Python project 的 package/source registration；CLI adapter registration 如另行授权。现有 sibling import checks 须仅允许三个已声明的 Calendar public namespace edges，仍禁止其 internals/反向依赖；fixed authority CONTEXT_ENTRIES 须登记新/重命名 entries。行为验证须覆盖 producer Calendar 与三个 consumers 的既定 contracts、完整 catalog/empty/duplicate/extra/zero-volume/partial/snapshot/counter/failure 情形。这些是实现与验证任务，不是未决定的业务语义。

本轮不修改 Python source/tests、schema、runtime cache、CLI 或根 Python 配置；Domain shared kernel、Calendar 与 Index authority 保持原契约。事务机制、批量大小、SQLite filename 等留在 implementation concern；refresh/force/TTL、Research/HTTP integration、migration 和通用 dependency engine 继续 deferred。

本轮验证：authority topology 13 passed、DataLake boundary 5 passed、Calendar producer tests 68 passed。补充只读导航检查确认十份新 authority 从根入口可达、93 份可达文档的相对文件链接合法；十八个新增/修改/删除路径均为 Markdown，新目录各只有五份 authority、旧目录为空后移除，无旧路径导航。`git diff --check` 和包含 untracked 新文档的 whitespace 检查通过，完整改动已审阅；没有剩余上下层 semantic conflict。这些检查验证文档 topology 与现有实现边界，不证明尚未实现的 Futures/Options runtime 行为。

## 7. Tushare Provider Runtime authority-only 增量

本节记录基于 commit `886e4a5f728d2ebb4f1170cf79b55923d6f11464` 的 authority-only 落位。Tushare execution 的唯一 canonical owner 为 [providers/TUSHARE.md](providers/TUSHARE.md)；前述 implementation / verification 是历史状态，不代表共享 Provider Runtime 已实现。

- 原模块架构及 AGENTS 的“顶层 src 仅拥有 kernel”已协调为 provider-agnostic kernel 与独立 provider infrastructure 共处顶层 src；未来 namespace 为 `data_lake.providers.tushare`。Provider 只复用 kernel 的 provider-neutral errors，不依赖 Dataset / Service / Repository / FetchUnit semantics；kernel 不依赖 provider，consumer 不直接调用 Executor。Source adapter 保留 endpoint / parameters、batching / pagination、partition、normalization 与 completeness。
- 原 APPLICATION 与四个 Dataset SERVICE 的 Dataset-owned credential convention 已协调为 provider authority 集中拥有 resolution / client / execution；Dataset architecture 声明 Source provider 与 execution authority，SERVICE 通过链接消费共享 contract。Public request/result/view、failure taxonomy、Dataset persistence ownership、Calendar prerequisite permissions 与 domain facts 保持原契约。
- 当前 Calendar `_source.py` 仍在 `prepare_source()` 内解析 environment / `market-snapshot/.env` 并调用 `tushare.pro_api(token)`，在 `TradeCalSource.fetch()` 内转换 SDK 请求异常；没有共享 request-start limiter。这些是新目标下的 implementation drift，本轮不修改该 Source 或其 tests。后续迁移仅转移 credential / client / throttling / provider request exception conversion；trade_cal selection、parameters、partition 与 Calendar-specific validation 继续归 adapter。
- Index / Futures / Options 仍只有 authority，没有 runtime package / adapter；后续实现直接采用共享 provider boundary，不复制 Calendar 当前做法。共享调度、lazy lifecycle 与请求错误转换的目标 contract 已固定，具体 Python naming、client reuse 与同步机制属于后续实现，不建立大型 endpoint facade 或 retry framework。
- 现有 `test_shared_kernel_has_no_dataset_or_provider_dependencies` 扫描整个顶层 src，尚不能区分目标 provider subtree；后续须分开验证 kernel / provider ownership，保留 kernel 禁止 provider / Dataset、provider SDK confinement 与禁止具体 Dataset / Repository semantics 的约束。现有 consumer check 只按 underscore internals 拦截，未来须显式禁止 consumer 直接依赖 provider namespace，不能因为新增目录而全面放开 SDK / internal import。
- 后续 runtime checks 须覆盖跨 Dataset / service / operation / 并发共享 schedule、实际 starts 至少 120ms、response latency 解耦、失败请求计入 starts、无隐式 retry、原样 response、统一 failure conversion 与 adapter-owned target mapping。验证 factory / coverage / export / 无需 Source I/O 的全缓存或零目标 ensure 不解析凭据、不创建 client，并保留 credential precedence / blank / fallback cases。V1 不保证 cross-process / worktree / machine quota coordination。
- Fixed authority `CONTEXT_ENTRIES` 尚未登记新 provider entry；后续 implementation verification 须登记 `providers/TUSHARE.md`。本轮采用补充只读 root reachability / relative-link / anchor 检查，不修改 tests implementation，也不把现有测试 green 当作 runtime 行为验证。

本轮仅新增 provider authority 并协调模块、政策、公共 Application、四个 Dataset architecture / SERVICE 与本 reconciliation；不创建 Executor / limiter / source directories，不修改 Python source/tests、root tooling、CLI、schema 或 runtime data，不调用真实 provider 或操作 legacy cache。Provider execution 形成独立 stable concern，单份专题通过模块入口与 Dataset Source entry 按需发现；不预建 provider catalog，不把详细 contract 复制到上层。

本轮验证：从 repository root 执行现有 authority topology 13 passed、DataLake boundary 5 passed。补充只读检查确认 provider authority、公共专题、reconciliation 与四个 Dataset architecture / SERVICE 从根入口可达，共 94 份可达文档；受影响链接合法，本轮没有新增或修改 anchor reference。全部十三个新增/修改路径均为 Markdown，新增文件 whitespace 与 `git diff --check` 通过，已审阅包含新 authority 的完整 diff；没有剩余上下层 semantic conflict。这些检查验证文档 topology 与现有实现边界，不证明共享 Executor / limiter 已实现或其 runtime 行为已通过验证。


## 8. 四个 Dataset 的集中 implementation reconciliation

本节记录初次落地状态；当前 provider 修正见第 9 节，当前执行和存储优化见第 10 节。

本次为 implementation task，基于 `ff53cec755e6868ae90b02cf1f19bda79cc08aec`，未重新决定 Scope、Window、FetchUnit、completeness、provider 或 export semantics。第 5–7 节所述缺少 runtime、provider execution、CLI registration、package/tooling 与 topology registration 的 gaps 已关闭。

### 当前 runtime 与 delivery

| Dataset / public namespace 后缀 | Public service | FetchUnit | CLI operations |
| --- | --- | --- | --- |
| tushare_trade_calendar | TradeCalendarService | exchange / cal_date | coverage / ensure / export |
| tushare_index_daily | IndexDailyService | index_code / trade_date | coverage / ensure / export |
| tushare_equity_index_futures | FuturesDailyService | product_code / trade_date | coverage / ensure / export |
| tushare_equity_index_options | OptionsDailyService | product_code / trade_date | coverage / ensure / export |

每个 package 在 owning Dataset 的 src/data_lake/datasets/<id>/ 下发布 SERVICE 规定的 Range、Row/Record、Export、Service 与 create_service()；public aliases 显式 re-export，不使用 __all__。根 Poetry、pytest、Ruff、mypy 显式登记全部 Dataset roots；installed isolated interpreter 验证四个 public namespaces，不借 pytest pythonpath。标准 namespace wiring 保持不变，未创建 registry/manager。根 tooling 同步移除已无 Python source 的 market-snapshot/scripts registration，避免默认 mypy 在扫描空目录时提前退出。

lab explicit wiring 登记四个 Dataset，selection parsing 按 [lab authority](../lab/ARCHITECTURE.md)；CLI 只通过 public service 构造 semantic request、读取结果和交付文件。无 SQLite/adapter/Executor access、coverage 重算、token/db arguments 或 terminal record dump。使用示例见 [lab usage](../lab/README.md)。

### Provider execution 与 Dataset composition

`data_lake.providers.tushare` 的 lazy Executor 集中解析 environment 优先 / market-snapshot/.env fallback credential，创建 SDK client，并按 process/credential 复用 execution state。线程同步的 monotonic request-start schedule 保证 120ms 平滑间隔；response completion 不持有 limiter lock，失败请求计入 starts，无自动 retry。Initialization 转 OperationError，SDK request failures 转 safe ExecutionFailure(source_request)，response 原样交给 adapter。Calendar 已移出 token/client/SDK error conversion，仅保留 trade_cal params、batching、partition 与 facts validation。

三个 consumer 每次 operation 固定 Calendar public export 的完整交易日 view；Index 使用 SSE，Futures/Options 使用 CFFEX，只有 ensure 在 prerequisite incomplete 时调用 Calendar ensure。未知目标为带 Calendar context 的 OperationError，不先写自己的 pending units。目标为空或全 success 时不初始化 Source。

Index 在需要的 selected units 上复用合法本地 index metadata，缺失时显式查询 provider 声明的 markets 的 index_basic；code suffix 不作为 market 推断依据。逐 index-day 查询 index_daily 并验证 exactly-one，保留 Source units，无派生指标。

Futures/Options 有 attempts 时取得并冻结完整 catalog；offset/limit pagination 继续到明确空 terminal page，检测重复/不前进 page、重复 metadata 与无法证明 exhaustion 的响应，不以短页或经验数量声称完整。Daily 同样检查分页 exhaustion，同 invocation 的同日响应在产品间复用；Futures 只用合法 type-2 metadata 排除连续/主力。可确认属于其他产品的 metadata defect 隔离到对应产品。逐 product-day 验证 observed multiset 与 lifecycle expected 恰一致；duplicate、extra、missing 或非法 facts 均使整个 unit non-success，零 expected 仍须确认空 observed。

### Persistence 与 snapshot

每个 Dataset 默认只解析自己的 data/<id>.sqlite3。Shared Repository 的成功事务原子保存 Records、本地 instrument association、Dataset-owned JSON completeness basis 与 success metadata；Futures/Options basis 保留 invocation 中该产品完整合法 catalog，Records 保留当次 metadata。后续 catalog 不能替换旧成功依据；export 使用保存的 facts。Index basis 保留合法 instrument metadata，后续日期可复用。

Internal SQLite generation 现为 2，增加 nullable basis storage；旧 generation 明确报 incompatible，不进行自动迁移、fallback 或双写。没有操作真实旧 SQLite。Migration 仍 out of scope；正常新建缓存和本次隔离 runtime 已验证。

Coverage/export 通过 read-only SQLite committed snapshot 检查成功 completeness，无缓存不创建库；export 的 coverage、records 与 metadata 来自同一个 snapshot。失败事务回滚整个产品日的 records/instruments/basis，不暴露 partial chain。真实 runtime state 不进入 Git。

### 验证 evidence 与剩余边界

隔离测试覆盖 Calendar、三个 consumers、credential lazy lifecycle、共享并发 schedule、失败无 retry、metadata reuse、catalog exhaustion、ignored offset、duplicate/extra/missing、完整 chain 与缺 expiry/strike/leg、零成交 nullable prices、空 expected、partial counters、read-only bytes、snapshot、旧成功 basis preservation 和 transaction rollback。四个 Dataset 均通过 fake SDK 的 CLI → public service → Calendar/source/owned persistence → export 全链路验证。

使用本地有效凭据额外执行 2026-09-30 的最小真实 CLI smoke，所有 SQLite/export 位于临时目录：Calendar SSE 1 条、Index 000300.SH 1 条、Futures IF 4 条、Options IO 236 条；四者 ensure/coverage/export 均 exit 0 / complete=true，临时文件已随测试清理。该单日证据不构成 provider 永久可用、catalog 数量或 freshness 保证。

Repository root 验证结果：

- poetry install 与 -I isolated public import 成功，四个 namespaces 可安装、可 import。
- poetry run pytest -q：928 passed、2 skipped；包含 DataLake、lab、architecture/topology 和其余 producer/consumer regression。现有 FastAPI/httpx deprecation warning 不来自本次改动。
- poetry run ruff check data-lake lab backend-api market-snapshot/tests/test_authority_topology.py：通过。
- poetry run mypy data-lake lab backend-api：69 files 通过；poetry run mypy market-snapshot/src market-snapshot/tests market-research：111 files 通过。分组保持独立 test-support namespaces，未排除或削弱任何相关检查。
- git diff --check、所有新增文件 UTF-8 / whitespace / Python syntax 检查通过；已审阅包含新增 source/tests 的完整改动。

额外尝试默认整仓 mypy 时，原有 market-snapshot/tests/support 与 backend-api/tests/support 同名 module 冲突仍存在；ruff check . 仍报告未修改的 web-ui/scripts/export_contracts.py import ordering。两者是既有整仓 tooling 问题，相关范围的上述检查已全部通过；没有为了 green 删除 boundary 或跳过相关 tests。

没有阻止既定四个 Dataset 正常新建缓存使用的 implementation gap。Research/Modeling/Snapshot/HTTP/UI integration、refresh/force/TTL、Source correction、legacy migration、cross-process limiter 与通用 registry/workflow 继续按任务边界 deferred。


## 9. 2000 积分历史运行与 diagnostics reconciliation（2026-10-02）

本轮响应真实 2026 年至今抓取暴露的问题；公共 operation family、DataSet-local SQLite、只读/原子写入/完整横截面 invariant 与无自动 retry 保持不变。

- Provider rate 由 TUSHARE_CALLS_PER_MINUTE 控制，默认 180/min，对应 2000 积分账号 200/min 额度的余量；仍是 process/credential 共享平滑调度，最大 500/min。非法配置仅在需要 Source I/O 时失败。配置不得在同 process 已建立 state 后静默重置 schedule。
- 受控 HTTP client 替代 SDK query 的不受控失败行为，检查 status/envelope/provider code，成功仍返回 DataFrame。请求 failure 不成为空 response / terminal page；safe endpoint/kind/numeric code 进入 source_request，远端原文和 credential 不记录。
- 独立 [DIAGNOSTICS.md](DIAGNOSTICS.md) 拥有日志事件与脱敏；provider 记录 DEBUG 请求/等待/耗时与安全失败，kernel 记录 INFO ensure progress / summary 和单元失败，lab 提供 --log-level / --log-file delivery，调用后恢复并关闭 handler。
- Futures/Options 的历史异常由新日志定位到首次挂牌没有前收盘价；Futures 首日 oi_chg 也合法缺席。经 Source 与 list_date 核对后更新各自 FACTS/SERVICE，再实现狭窄 nullable 条件；不补零、不覆盖其他字段。两个 export schema 升为 2，旧 finite cached facts 保持可读；SQLite generation 不变。
- 根唯一依赖图明确登记现已由 HTTP client 直接使用的 pandas；锁定版本未改变。Poetry install、check 与 isolated installed imports 均通过。

真实验证范围 2026-01-01..2026-10-02：SSE/CFFEX 各 275 自然日，4 个指数 724 条 / 724 units，IF/IH/IC/IM 2,896 条 / 724 units，IO/HO/MO 126,754 条 / 543 units，全部 coverage.complete=true、无 missing/pending/failed。缓存 operations 在空 Token / 非法 rate 配置下仍通过，ensure attempts=0。重新请求 Source 比对全部日历/指数与三个期货、三个期权日期，共 3,330 条记录逐字段一致；包括上市首日与零成交样本。该历史范围与抽样 evidence 不构成未来 provider freshness 或任意范围永远可用的保证。

运行文件位于 owning Dataset data/exports/2026-01-01_to_2026-10-02/，保持 Git 忽略；日志无 credential/raw transport dump。隔离回归覆盖 lower account rate、concurrency、错误分类/脱敏、HTTP failure vs empty success、坏 envelope、首日缺席/非首日拒绝、缺字段/无穷/boolean、handler lifecycle 与 log delivery failure；对应 authority topology 已登记 diagnostics entry。单进程额度仍不协调其他程序或 worktree。

最终验证：全仓 pytest 821 passed、2 skipped；DataLake/lab Ruff 与 mypy（50 files）通过，diff whitespace 通过。全仓首次检查发现已删除 Study package 的 ignored .pyc-only 残留被当作 implementation；仅将这些无 tracked/source 文件的缓存目录移到本地临时 quarantine，未改 Research source 或 tests，之后全仓检查通过。

扩展历史验证范围 2024-01-01..2026-10-02：SSE/CFFEX 各 1,006 自然日，4 个指数 2,664 条 / 2,664 units，IF/IH/IC/IM 10,656 条 / 2,664 units，IO/HO/MO 484,646 条 / 1,998 units。全部 ensure.complete=true；新增目标为日历各 731、指数/期货各 1,940、期权 1,455，新增抓取无失败。使用同一 process 的 180/min 共享额度；本次未引入额外实现变更。运行文件位于各自 data/exports/2024-01-01_to_2026-10-02/，继续保持 Git 忽略。

扩展范围的 coverage/export 同样 complete=true、missing/pending/failed 均为 0。全部导出记录通过日期范围、身份唯一性、有限数值与 nullable 条件检查，CLI JSON 与 public export 相同；空凭据/非法 rate 下全缓存 ensure attempts=0，原 2026 年成功 facts 与原导出逐条相同。重新请求 Source 对比全部日历/指数、跨 2024/2025/2026 的 10 个期货日期及 9 个期权日期，共 11,094 条逐字段一致；包含上市首日与年末样本。请求日志共 3,892 次启动，任意 60 秒最多 180 次，日志时间戳最小启动间隔 0.333 秒，无请求/单元失败和 credential。全仓 pytest 仍为 821 passed、2 skipped，Ruff/mypy、installed imports 与更新后的 authority topology/whitespace 检查通过。


## 10. Bounded execution 与 generation 3 optimization

基于 `8d770c5` 完整实现已确认的优化。新的独立 execution / persistence concern 分别落在 [EXECUTION.md](EXECUTION.md) 和 [PERSISTENCE.md](PERSISTENCE.md)，模块入口、DOMAIN_MODEL/APPLICATION 与 policy 导航同步；Dataset SERVICE 唯一拥有未来行情日期拒绝和具体批窗口，CONTRACT_UNIVERSE 链接冻结 basis 的执行/存储契约，lab 唯一拥有增量 JSON / atomic file delivery。前述历史的 schema migration deferred 收窄为通用 framework/旧目录 import 仍 deferred，明确的 generation 2 → 3 兼容升级已实现。

- 三种行情 request/service 在 Calendar/Source I/O 前拒绝超过 Asia/Shanghai today 的 end_date，不静默裁剪；Calendar 仍允许已发布未来日历。
- Index 在同 code/自然年内每批最多 250 selected 交易日；Futures/Options 按日期合并 selected products，最多 5/3 selected 交易日且自然日跨度不超过 31 日。全部请求到空终页，不把短页当终止，不改变 FetchUnit。响应先按日期 partition；非法可寻址 daily row 只影响自己的 unit，无法寻址或分页不可靠则批失败。Source 不再保留整段历史 daily cache。
- Operation-local catalog checker 重用同一内部 immutable basis 的完整 metadata validation/contract index；每条 Record、每个 expected/observed 集合和 instrument association 仍核对。每个 read snapshot 重用相同 basis JSON，逐 unit hash/count 未移除。
- ensure 复用 thread-local writer connection，executemany instruments/records 和批量 instrument lookup；每个 unit 仍独立提交。结构/identity/全库 FK 校验位于 writer entry/exit 和 read snapshot，短事务核对 identity；网络期间没有写事务。可选单 Source worker 提前一批，三个行情 Dataset 启用，主线程单 writer；失败/中断保留已提交 success 与可重试 pending，不启动第三批。
- 每个 Dataset generation 3 内容寻址去重 basis。合法 generation 2 read/cached ensure 保持只读；有实际 write selection 才备份后事务升级，失败回滚，未知 generation 拒绝。没有改写 legacy 目录；真实验证只升级隔离复制库，生产旧库 SHA-256 保持不变。
- lab 使用浅 dataclass JSON default 和 incremental dump，UTF-8 同目录 temporary file flush/fsync 后原子替换；编码/同步/替换失败清理 temporary file、保留旧 output。Public envelope、payload、日期、null、ordering 不变。

真实验证使用 2024-01-02..2024-01-12 的 9 个交易日，在完整历史库的隔离副本中移除目标再 ensure：Index 36 units/36 rows，Futures 36 units/144 rows，Options 27 units/5,964 rows，全部成功且与原缓存逐字段相同，未选中历史 units 的 hash/count/status/所有时间 metadata 一致。行情请求 Index 36 → 8，Futures 18 → 4，Options 18 → 6，Futures/Options metadata 各 4 calls；仍有空终页。三库实际升级至 generation 3，完整 generation-2 backup 可读且 FK 检查通过。

完整 2024-01-01..2026-10-02 验证保留 Index 2,664、Futures 10,656、Options 484,646 rows，coverage.complete=true。空 token/非法 rate 的 cached ensure attempts=0、SQLite bytes 不变，无 Source starts；完整 JSON 与旧交付内容的统一换行 SHA-256 一致。内部 basis 内容字符数 Index 482,184 → 724，Futures 115,240,644 → 173,034，Options 3,473,171,352 → 5,214,972；这是逻辑去重体积，不是 SQLite file shrink。测得完整 Options coverage 28.81s、public export 39.71s、incremental JSON delivery 24.14s；单机样本不是稳定性能承诺。证据/script/log/隔离库位于 Calendar owned data/exports/optimization-2026-10-02/，Git 忽略，不提交 credential 或 runtime data。

最终 Source 版本再次补数核对上述 9 日全部样本，并完成 484,646 rows 的完整 Options export：耗时 38.14s、JSON delivery 24.60s，进程 peak working set 3,595,468,800 bytes（约 3.35 GiB）；保持原 Windows 换行后的 JSON 为 487,126,801 bytes，与原交付 raw SHA-256 完全一致。Cancellation guard 补充验证已进入的 call 可以收束、后续分页/metadata calls 不启动；不会取消已发出 HTTP 或隐藏重试。

最终验证：全仓 pytest 861 passed、2 skipped；DataLake/lab Ruff 与 mypy（50 source files）、installed isolated imports、authority topology 和 whitespace 检查通过。完整 diff 与八项优化逐项核对；未放宽逐 unit completeness、hash/count、空终页、原子提交或 read-only boundary，无 remaining implementation drift。
## 11. 第二轮性能审查落地（2026-10-02）

本轮在 section 10 的实现上完成六项优化；canonical contracts 分别先落位于 Index FACTS、公共 EXECUTION / PERSISTENCE 和 lab authority，不改变 public request/result/view 或降低成功完整性。

- Index metadata 按最多 64 codes 的 symbol 多值请求查询全部相关 markets，仍按完整 ts_code 唯一匹配并完整分页；可识别 code 的 metadata 问题隔离，批请求/分页失败影响该批。已有 local metadata 只读取、校验所选 code 的最新成功代表 unit，坏代表不静默 fallback。
- 三种行情 Dataset 在单次 export 内复用已验证的 typed row，并预计算固定字段集合；缓存保留 private Record 身份且 facts 不变，不跨 operation，也不在 coverage/ensure 保留整窗 typed rows。Kernel 不知道具体行类型。
- Snapshot 同一 read transaction 内每 64 units 批量读取，records join 复用 instrument facts，取消重复 DISTINCT join；逐 unit hash/count、metadata、关联、basis 和 Dataset completeness 验证仍执行。
- Futures/Options 横截面一次按日期及产品分类，保留无法归属及产品日错误隔离；已验证 catalog 的生命周期事件索引精确保留 inclusive 边界和倒序访问语义，不重复扫描完整 catalog。
- lab 将增量 JSON 片段合并成有界字符缓冲后写临时文件，维持原 wire bytes、flush/fsync、原子替换和失败时原 output 保全。

根环境全仓库 pytest：878 passed、2 skipped；DataLake/lab Ruff、mypy 50 files、isolated installed public imports 与 whitespace 检查通过。新增 17 项回归覆盖 typed row 操作边界、metadata 分组/跨市场冲突/失败、坏代表、SQL 跨批次及损坏、生命周期边界/倒序、产品错误隔离和多缓冲 JSON 失败保全；全仓库包含 producer/consumer architecture 与 authority topology 验证。

相对上一版 5ab4ac1，2024-01-02..2024-01-12 四 Dataset 空库真实运行（统一 180/min、每版 3 轮取中位数，含 ensure/coverage/export/JSON，不含进程启动）耗时 22.01 → 13.69 秒，减少 37.8%；总请求 60 → 36，Index metadata 32 → 8。所有六轮输出内容及原始 JSON SHA256 一致、完整且零失败。

2024-01-01..2026-10-02 同一 schema 3 验证副本的全量期权只读导出，独立进程每版一次：484,646 行，public export 37.26 → 23.77 秒，JSON 23.87 → 20.55 秒，合计 61.13 → 44.32 秒（减少 27.5%），峰值 working set 3.34 → 3.11 GiB。两版输出均 487,126,801 bytes、SHA256 一致。单次全量对比不是三次中位数，也不承诺其他数据规模同等收益。

运行证据位于 Git 忽略的 `datasets/tushare_trade_calendar/data/exports/optimization-2026-10-02/round2-*`；原生产库保留。当前 coverage 仍完整校验目标事实，ensure 头尾仍检查整个目标范围；status-only coverage、跨 operation 证明复用和减少此整窗检查需要后续独立 semantic decision，未以性能理由静默实现。
