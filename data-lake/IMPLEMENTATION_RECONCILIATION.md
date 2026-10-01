# DataLake implementation reconciliation

本文件集中记录以 commit `8e26a5e64804a19b2228bba0feaf0b157c5ecc3a` 为基准的 implementation reconciliation，不另行定义业务语义。目标 ownership、topology 与依赖方向由 [模块架构](ARCHITECTURE.md) 拥有；公共 domain / application invariants 见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 与 [APPLICATION.md](APPLICATION.md)；具体 Dataset 经 [catalog](DATASETS.md) 进入 architecture 与 SERVICE。

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
