# DataLake implementation reconciliation

本文件集中记录 commit `7899ab9164f46e861b3b4ae31a6a613fd4ff9684` 的 implementation 与新 authority 的差异，作为下一阶段实现输入，不另行定义业务语义。目标 ownership、topology 与依赖方向由 [模块架构](ARCHITECTURE.md) 拥有；公共 domain / application invariants 见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 与 [APPLICATION.md](APPLICATION.md)；具体 Dataset 经 [catalog](DATASETS.md) 进入 architecture 与 SERVICE。

## 1. 基准实现状态

基准已有 shared core、Calendar service/factory 与 lab CLI vertical slice；CLI 直接调用 `data_lake.datasets.tushare_trade_calendar` public service。公共 `data_lake` facade 发布 shared results 与 InvalidRequestError / OperationError；ExportEnvelope.export_schema_version 为 int，Calendar view 固定为 1。已有实现不意味着目标 filesystem ownership 已完成。

本次 authority-only encoding 不移动 implementation 或 tests，不修改 SQLite/runtime state、`pyproject.toml` 或 package wiring。以下是显式 drift，不能作为长期 topology 的另一套 authority。

## 2. 待处理差异

| Concern | 基准实现 | 下一阶段 reconciliation 输入 |
| --- | --- | --- |
| Dataset source ownership | Calendar models、Source adapter、service composition 位于 `src/data_lake/datasets/tushare_trade_calendar/` | 将 Dataset-specific implementation 归入 `datasets/tushare_trade_calendar/src/`；顶层 src 只保留真正公共 kernel。迁移不改变 Dataset domain/service semantics |
| Test ownership | `tests/test_trade_calendar.py` 与 core tests 都在顶层；`tests/test_boundary.py` 混合 module、provider confinement 与 lab public-boundary 验证 | Dataset verification colocate 于 Dataset tests；公共 core/module verification 留在顶层，consumer-specific verification 按 owning boundary 安置，不因物理迁移削弱覆盖 |
| Persistent state | `src/data_lake/_runtime.py` 的 database_path 默认解析为 `data-lake/data/<dataset-id>.sqlite3` | Dataset composition 使用通用 storage machinery 解析到 owning Dataset 的 `data/<owned sqlite>`；kernel 不内置具体 Dataset。后续明确已有缓存的处理方式，不假定已有数据已迁移 |
| Root tooling | 根 Poetry package registration、pytest testpaths/pythonpath、Ruff src 与 mypy files/mypy_path 只登记当前顶层 DataLake roots | 在唯一根 project/environment 内登记 Dataset-local source/test roots，并确认安装、测试发现、lint/type-check 覆盖；不建立独立 Dataset project、dependency graph、plugin 或 loader |
| Public imports / composition | public surface 为 `data_lake.datasets.tushare_trade_calendar`；lab 已直接消费，公共 facade 发布 result/error contracts | 保持这些已声明 public surfaces 与语义兼容；明确 multiple source roots/package wiring，验证 installed imports 与 consumer imports。具体机制属于后续实现设计 |
| Architecture tests | test_provider_dependency_is_confined_to_calendar_source 固定旧 adapter 路径，并断言 `data-lake/datasets` 下不存在 Python 文件 | 替换与新 topology 冲突的断言，验证 provider confinement、kernel 不依赖具体 Dataset、Dataset 互不依赖及 consumer 只进入 public API；本轮不修改测试 |
| Authority navigation checks | 现有 `market-snapshot/tests/test_authority_topology.py` 检查 Markdown links，但 CONTEXT_ENTRIES 未登记完整 DataLake navigation | 本轮额外显式检查根入口 → module → 公共专题/catalog → Dataset architecture → SERVICE，以及本文件的可达性；后续需要时增强正式 topology checks |

## 3. 后续实现的边界与验收输入

- 保留 Scope / Window / FetchUnit / Record、逐日 completeness、coverage / ensure / export、failure taxonomy 与 export snapshot semantics；具体 consumer contract 仍由 Dataset SERVICE 拥有。
- 普通 consumer 不提供 SQLite path、connection、Repository、Source adapter 或 token；coverage/export 与 factory 不创建缓存、不访问 Source，ensure 仅在需要 fetch 时解析既有凭据 convention。
- 具体 SQLite filename、空目录保留与 ignore mechanics、package registration/import wiring，以及已有缓存处理方案须在下一阶段明确；真实 runtime state 默认不进入 Git。这里不预选迁移、删除或重建实际 SQLite 的策略。
- 按新的 source/test layout 更新验证命令，检查 Dataset tests discovery、public import compatibility、storage resolution、provider confinement 与依赖方向。保留 core fake Dataset/Source、Calendar fake client 和临时 SQLite 验证，不需要真实 token。

Authority 已提供进入 implementation reconciliation 所需的 ownership、public boundary、dependency direction 与稳定 semantic contracts；实际 relocation、tooling registration 与 runtime-state 处理仍属于下一阶段，不宣称已完成。
