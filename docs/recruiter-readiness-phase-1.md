# Recruiter readiness — Phase 1 audit

2026-11-17 · baseline `e5e79535c9ffd29ebb3fc016e717741b2c537b12` · branch `feat/recruiter-readiness`.
这是一次文档与仓库导航审阅记录，不是业务 authority、运行验收或招聘评分指南。
当前业务语义从 [根架构](../ARCHITECTURE.md) 进入；本文只映射证据及记录本次处理。

## Findings

Severity：高＝公开入口可能产生错误能力判断；中＝局部状态或导航误导；信息＝保留或后续事项。

| Finding / classification | Evidence | Severity | Treatment |
| --- | --- | --- | --- |
| Confirmed factual drift：目录契约仍称七 Bundle、八路由、发布前失败 | 基线 `ui_web/STRUCTURE.md`；[Manifest](../ui_web/demo/bundles/manifest.json)、[路由清单](../ui_web/src/app/routeInventory.ts)、[历史发布记录](../ui_web/demo/build/HANDOFF.md#first-public-execution-and-online-acceptance) | 高 | 修正目录契约，状态与成员清单导航至 Demo owner，不维护第二份发布结论 |
| Navigation/discoverability problem：README 的能力表缺少实现/验证路径，遗漏 EmpiricalPercentile | [README](../README.md)、[Statistics dispatch](../market_statistics/src/market_statistics/api.py) | 中 | 增加能力证据入口，区分实现、历史验收与本次未执行项；修正架构图使 Demo 经正式 HTTP capture 获取结果 |
| Confirmed factual drift：Statistics README 仍将 WP4 视为未实现，根架构重复维护不完整方法列表 | [Statistics README](../market_statistics/README.md)、[Calendar Spread Roadmap](../market_research/descriptive/cases/futures_calendar_spread/ROADMAP.md#baseline-and-status) | 中 | 标明 WP3 的历史范围；根架构委托模块方法目录 |
| Historical information requiring clarification：迁移与旧 Demo 入口容易被当作当前 BLOCKED／采集未验证 | [结构迁移](../ui_web/STRUCTURAL_MIGRATION.md)、[旧入口](../ui_web/src/demo/ARCHITECTURE.md) | 中 | 历史标注与当前 evidence 路由；保留迁移证据 |
| Confirmed factual drift：DDB-05 handoff 引用了已不存在的部署指南锚点 | 基线 handoff 的 `manual-demo-pages-release-ddb-05`；[当前部署指南](../ui_web/deploy/README.md#verified-demo-pages-release-ddb-06) | 中 | 改为现有 DDB-06 命令入口，明确旧手动流程已被替代 |
| Historical information requiring clarification：W2 当前审计混入原始交付与存储阶段记录 | [当前 reconciliation](../market_backtesting/cases/futures_roll_long/RECONCILIATION.md)、[历史记录](../market_backtesting/cases/futures_roll_long/ACCEPTANCE_HISTORY.md) | 中 | 保留当前 inventory/review/drift；原 authority change matrix 与执行记录完整迁至同目录历史文件；更新所有入链 |
| Historical information requiring clarification：Storage、Issue #13 入口未就近指出最终验收边界 | [Storage](../market_research/STORAGE_RECONCILIATION.md#current-storage-status)、[自动准备](../market_research/descriptive/cases/futures_calendar_spread/AUTO_PREPARATION_RECONCILIATION.md#current-delivery-and-evidence) | 中 | 增加当前摘要和最终证据链接，阶段命令与结论保持原样 |
| Confirmed factual drift：Research 摘要的无前端/报告表述未限定 scalar 路径；Segmentation 已实现却仍写 future implementation tests | [Research acceptance](../market_research/descriptive/ACCEPTANCE.md#current-status)、[Segmentation](../market_research/descriptive/cases/price_segmentation/ARCHITECTURE.md#reconciliation-and-acceptance) | 中 | 明确 scalar、Publication reader、独立 case 的适用范围；修正过期时态，不改变 integration 权限 |
| No change needed：#15 原始问题中的 BLOCKED README、预期构建失败、全量自动 CI 和旧 Demo authority 链接已在基线修正 | [Issue #15](https://github.com/ougachakaaa/hg-market-state-lab/issues/15)、基线 README | 信息 | 保留正确内容，逐项复核，补充明确的 CI 与发布证据边界 |
| No change needed：历史验收仍有独有证据；未找到可无损整份删除的过时文档 | [DDB-00](../ui_web/DDB_00_ACCEPTANCE.md)、[Storage WP6](../market_research/STORAGE_RECONCILIATION.md#storage-wp6-execution-evidence)、W2 历史记录 | 信息 | 未删除整份文档；仅清除当前入口中的冗余过期声明，迁移时不丢弃原始证据 |
| Authority/implementation conflict requiring human decision | 本次入口与能力审计未发现需要新业务决策的冲突 | 信息 | 无 `HUMAN_DECISION_REQUIRED`；这不是对全部业务实现的完整语义证明 |

## Capability evidence

以下文件证明实现、契约或历史执行证据可定位；测试文件存在不等于本次运行通过。

| README capability | Concrete implementation / contract | Representative verification / boundaries |
| --- | --- | --- |
| 四个 DataLake Dataset、SQLite/Coverage | [Dataset public contracts](../data_lake/DATASETS.md)、[Futures service](../data_lake/datasets/tushare_equity_index_futures/src/data_lake/datasets/tushare_equity_index_futures/_service.py)、[persistence contract](../data_lake/PERSISTENCE.md) | [Futures runtime tests](../data_lake/datasets/tushare_equity_index_futures/tests/test_futures_runtime.py)；外部 Source、凭证和 Coverage 条件仍适用 |
| MO Option Chain / Premium Plane 与历史 Snapshot 产品 | [Product contracts](../data_snapshot/CAPABILITIES.md)、[Option Chain service](../data_snapshot/src/data_snapshot/products/mo_option_chain/service.py) | [Option Chain tests](../data_snapshot/tests/test_mo_option_chain_service.py)、[Premium tests](../data_snapshot/tests/test_mo_option_premium_backend.py) |
| Trailing Return、Single Job / Batch | [Executor](../market_research/src/market_research/descriptive/execution/api.py)、[Batch](../market_research/src/market_research/descriptive/execution/batch.py) | [Job tests](../market_research/tests/test_job_execution.py)、[Batch tests](../market_research/tests/test_batch_execution.py)、[bounded acceptance](../market_research/descriptive/ACCEPTANCE.md)；不能推广至任意 case |
| Research Publication / Explorer | [Publication store](../market_research/src/market_research/publication/store.py)、[HTTP reader](../ui_http/src/ui_http/products/research_publication/endpoint.py) | [Publication tests](../market_research/tests/test_publication.py)、[storage limits](../market_research/PUBLICATION_STORAGE.md)；显式发布独立于 Run |
| Futures Basis 六节报告与在线执行 | [Report producer](../market_research/src/market_research/descriptive/cases/futures_basis/report.py)、[online application contract](../market_research/descriptive/cases/futures_basis/ONLINE_APPLICATION.md) | [Roadmap](../market_research/descriptive/cases/futures_basis/ROADMAP.md)、[WP9 evidence](../market_research/descriptive/cases/futures_basis/WP9_ACCEPTANCE.md)；平台结论须结合后续 Storage 记录 |
| Calendar Spread 日常／历史相对价值与显式执行 | [Queries](../market_research/src/market_research/descriptive/cases/futures_calendar_spread/queries.py)、[Preparation](../market_research/src/market_research/descriptive/cases/futures_calendar_spread/preparation.py) | [Query tests](../market_research/tests/test_calendar_spread_queries.py)、[execution tests](../market_research/tests/test_calendar_spread_execution.py)、[Issue #13 bounded evidence](../market_research/descriptive/cases/futures_calendar_spread/AUTO_PREPARATION_RECONCILIATION.md#current-delivery-and-evidence) |
| Price Segmentation Python case | [Public service](../market_research/src/market_research/descriptive/cases/price_segmentation/service.py)、[case contract](../market_research/descriptive/cases/price_segmentation/ARCHITECTURE.md) | [Observation tests](../market_research/tests/test_segmentation_observation.py)；无 HTTP/Web、Statistics 或 scalar capability integration |
| 四种 Statistics 数值方法 | [Public dispatch](../market_statistics/src/market_statistics/api.py)、[method contracts](../market_statistics/ARCHITECTURE.md) | [Public API tests](../market_statistics/tests/test_public_api.py)、[Percentile tests](../market_statistics/tests/test_empirical_percentile.py)；独立 Python API，无 HTTP 服务 |
| Position-Driven Core、M1/Q1 与回测结果/证据 | [Core accounting](../market_backtesting/src/market_backtesting/core/accounting.py)、[Analyzer](../market_backtesting/src/market_backtesting/cases/futures_roll_long/performance.py)、[Result/Evidence contracts](../market_backtesting/ARCHITECTURE.md#case-navigation) | [Accounting tests](../market_backtesting/tests/test_core_accounting.py)、[Performance tests](../market_backtesting/tests/test_futures_roll_performance.py)、[historical real acceptance](../market_backtesting/cases/futures_roll_long/WP8_ACCEPTANCE.md)；gross 结果不含真实费用/滑点 |
| FastAPI/Auth、generated contracts 与 Web | [HTTP composition](../ui_http/src/ui_http/app.py)、[Auth contract](../ui_http/AUTHENTICATION.md)、[Web routes](../ui_web/src/app/routeInventory.ts)、[generated contract example](../ui_web/src/features/calendar_spread_relative_value/api/relativeValue.generated.ts) | [Auth tests](../ui_http/tests/test_auth_http.py)、[Web routing tests](../ui_web/src/app/routes.test.tsx)；Production 指完整应用模式，不是投产宣告 |
| 九 Bundle／十页面静态 Demo | [Registry](../ui_web/demo/build/registry.ts)、[Manifest](../ui_web/demo/bundles/manifest.json)、[StaticWorkspace](../ui_web/demo/runtime/StaticWorkspace.tsx)、[offline build](../ui_web/demo/build/build.mjs) | [Local delivery](../ui_web/demo/CALENDAR_SPREAD_ACCEPTANCE.md)、[historical eight-route release](../ui_web/demo/build/HANDOFF.md#first-public-execution-and-online-acceptance)；本次不验证线上版本 |

## Unfamiliar reviewer simulation

1. **用途**：README 首段和能力表定位为市场数据准备、描述性研究、持仓回测及结果阅读；没有模型预测或实盘能力声明。
2. **已实现什么**：能力表进入上面的契约、代码与测试，不必先读完整 authority 树。Calendar Spread 与 Statistics 方法不再被旧阶段状态掩盖。
3. **未完成／未验证什么**：Modeling 预留、Conditional 未实现、Segmentation 无 HTTP/Web、回测 gross 限制，以及历史真实数据／平台验收范围均有入口。原生非 WSL Linux 存储验收仍 NOT RUN。
4. **代码如何组织**：README 架构图 → 根架构 → owning module → narrow contract；共享根 Python 环境不表示允许任意跨模块 import。
5. **如何检查正确性**：能力证据表给代表性测试和历史验收；[CI](../.github/workflows/demo-compatibility.yml) 将普通 changed-source 检查与手动回归分开，绿灯不证明全套通过。
6. **如何体验 Demo**：[公开 URL](https://ougachakaaa.github.io/hg-market-state-lab/) 进入匿名只读站点；README 的 build/preview 命令供本地查看。当前分支与线上版本是否一致，本次 NOT_VERIFIED。
7. **技术审阅下一步**：按感兴趣的能力进入上表源码、测试和窄契约；需要历史执行结论时再读验收记录。

剩余弱点：主要文档为中文；部分验收证据依赖记录中的本机临时路径，不能保证外部审阅者可取得；历史部署不证明今天的线上状态；本次没有重新运行业务测试。作者贡献与 AI 协作证据留给 Phase 2。

## Changed documents

| Area | Updated files (repository-relative) |
| --- | --- |
| Root | `README.md`, `ARCHITECTURE.md` |
| Web / Demo | `ui_web/STRUCTURE.md`, `ui_web/STRUCTURAL_MIGRATION.md`, `ui_web/demo/build/HANDOFF.md`, `ui_web/src/demo/ARCHITECTURE.md` |
| W2 | `market_backtesting/ARCHITECTURE.md`; `market_backtesting/cases/futures_roll_long/` 下的 `RECONCILIATION.md`, `ROADMAP.md`, `ONLINE_STORAGE.md` |
| Research | `market_research/STORAGE_RECONCILIATION.md`, `market_research/descriptive/ACCEPTANCE.md`; `market_research/descriptive/cases/futures_calendar_spread/` 下的 `AUTO_PREPARATION_RECONCILIATION.md`, `ROADMAP.md`; `market_research/descriptive/cases/price_segmentation/ARCHITECTURE.md` |
| Statistics | `market_statistics/README.md` |

新增：本审计记录与 `market_backtesting/cases/futures_roll_long/ACCEPTANCE_HISTORY.md`。
整份删除文件：无。断链修复：DDB-05 部署指南锚点；历史迁移另更新 W2 原章节的全部入链。

## Verification and follow-up

| 本次实际检查 | 结果 |
| --- | --- |
| 完整文档 diff 与语义审查；README 对照源码、authority、命令与 CI 配置 | PASS；修正客观漂移，无新业务决策或 runtime 行为改动 |
| Markdown 相对文件目标、锚点与显式引用式链接检查 | PASS；249 份 Markdown、2,141 个本地目标；排除代码片段与 `_temp_docs/`，无失效目标；无显式引用式链接使用 |
| README 到架构、开发、模块、Demo、历史与审计入口的链接可达性 | PASS；14 个选定入口可达；同时完成上面的七问审阅模拟 |
| Manifest / Registry 和共享 / Static 路由源码身份对照 | PASS；九 Bundle、十页面一致；这是静态身份核对，不是 Bundle admission 或构建验收 |
| W2 历史迁移与指定基线比较 | PASS；authority change matrix 与全部移出执行记录共 49,244 字节逐字保留 |
| 变更范围与 `git diff --check` | PASS；18 个变更／新增路径均为 Markdown，无空白错误；未删除整份文档或运行数据 |

检查使用本次临时只读脚本与人工审查，没有新增永久检查或运行架构测试。
业务测试、构建、契约 freshness、浏览器、真实行情与线上部署均为 `NOT_VERIFIED`（本次未运行）。

[Issue #15](https://github.com/ougachakaaa/hg-market-state-lab/issues/15) 与 [#17](https://github.com/ougachakaaa/hg-market-state-lab/issues/17)
按原始验收项复核，具体提交和关闭结果由 GitHub 评论及交接报告记录，不在本文预先声明关闭。
性能度量/窗口扩展、产品可读性等后续事项沿现有 [#11](https://github.com/ougachakaaa/hg-market-state-lab/issues/11)、[#12](https://github.com/ougachakaaa/hg-market-state-lab/issues/12) 跟踪，本次不实施、不新建重复 Issue。

建议仓库元数据（仅建议，未修改设置）：Description `Personal market-data, descriptive research and position-driven backtesting lab with a read-only demo`；Homepage 使用 README 的 Demo URL；Topics `python`, `typescript`, `fastapi`, `react`, `quantitative-finance`, `backtesting`, `data-engineering`。
