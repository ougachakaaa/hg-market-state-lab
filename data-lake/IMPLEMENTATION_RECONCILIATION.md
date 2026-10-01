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

- [Index](datasets/tushare_index_daily/ARCHITECTURE.md) 已确定完整 domain/service、Source facts 与 Calendar prerequisite contract；[Futures](datasets/equity_index_futures/ARCHITECTURE.md) / [Options](datasets/equity_index_options/ARCHITECTURE.md) 只锁定稳定边界与 operation family，Scope/Window、FetchUnit/Record identity、completeness 及相应 request/payload details 仍显式待人工决定。
- 原 repository/module/policy 的“Dataset 当前互不依赖”已显式协调为默认禁止、仅允许已声明的单向 public service dependency。本轮唯一新增 permission 为 Index → Calendar；Calendar service/domain 不变，underlying relationship 不授予 Futures/Options runtime dependency。Storage ownership、kernel direction、read-only、公共 result/errors、snapshot 与 root runtime invariant 均保留。
- 新三个 bounded contexts 只有 authority：没有 source/test/storage directories、Python package/factory、SQLite schema、Source adapter、CLI registration 或 runtime integration。不修改根 Python registration/configuration，不执行 Source 请求或真实 cache migration。
- 现有 architecture tests 仍按旧 implementation 验证 Dataset 不依赖 siblings；Index implementation 开始前须将 dependency check 收紧为明确 public boundary permission，而不是全面取消 sibling 限制，并验证只读/Calendar failure/两库独立 state。此为 implementation reconciliation 输入，本轮不修改 tests。
- 现有 authority topology test 的 fixed CONTEXT_ENTRIES 不含本轮新增八个 authority 文件；本轮通过 catalog 显式登记、现有全仓 relative-link 检查与补充只读 root reachability 检查验证这些 entries。后续 implementation verification 应登记新 entries，不能将旧 test 的 green 视为新 contract 行为已被验证。

没有剩余的上下层 authority conflict；Futures/Options 待决语义是有意保留的设计边界，不是被另一份 authority 隐式覆盖的契约。Index 后续仅需按既定语义 reconciliation/实现、细化事务与 batching 等 implementation concern，不借此重新决定 FetchUnit 或新增 public verbs。

本次 authority 验证：现有 authority topology 检查 13 passed，DataLake boundary 检查 5 passed；补充只读检查确认新增八份 authority 从根入口可达、相对链接合法，全部十四个新增/修改文件均为 Markdown，新增 Dataset 目录只有 authority。`git diff --check` 与新增文件 whitespace 检查通过，已审阅包含新增文件的完整 diff。以上证明文档 topology 与现有边界未受破坏，不证明尚不存在的新 Dataset runtime 行为。
