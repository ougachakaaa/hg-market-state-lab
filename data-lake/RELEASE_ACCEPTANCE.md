# DataLake V1 Release Acceptance

本文件是 2026-10-18（Asia/Shanghai）的验收证据，不是 semantic Authority，不定义新增契约。稳定入口为 [ARCHITECTURE.md](ARCHITECTURE.md)，当前实现映射为 [IMPLEMENTATION.md](IMPLEMENTATION.md)，运行与恢复说明见 [DEVELOPMENT.md](../DEVELOPMENT.md)。

## 验收版本与结论

- Branch：`chore/datalake-authority-boundaries`。
- 审查及真实 Source 验收基线：`0f49e18f9781bbb54ee4e3f80301fedea44358fe`。
- 验收后版本：上述 HEAD 加本轮未提交的文档收尾 diff；Python source、public API、dependency graph、SQLite generation 均未修改。
- Architecture / Authority / Implementation：Frozen / Closed / Reconciled；未发现阻断性 drift。
- Verification：Passed，1038 passed、2 个非阻断 symlink 场景因系统权限 skipped；未将 skip 计作通过。
- Runtime / Release：Validated / Ready；本次约定的 V1 验收范围无剩余阻断条件。
- Merge：可以将包含本轮文档收尾的分支合并到本地 `develop`；目标审查版本为 `fb8315fb07158d1c32fcb245bc118d256b6ceb9e`，它是 HEAD 的祖先。本任务未提交、合并或发布；该结论不代替目标分支变化后的 CI / review。

## 契约审查与离线验证

审查涵盖 Kernel → Domain/Ports、Dataset → Kernel/Provider、三个行情 Dataset → Calendar public service 的依赖方向；四 Dataset 的 Planner、Resolver 权限与操作级 context、UnitRecords 验证后提交、逐 unit transaction、失败重试、只读 snapshots、frozen basis、rebuild-only compatibility，以及 CLI / installed imports / Research consumer。没有引入新接口、框架或其他模块业务语义。

| 验收关注点 | 现有验证入口 |
| --- | --- |
| Kernel / Dataset / Provider 依赖及 public imports | `data-lake/tests/test_boundary.py`、Provider/Dataset topology tests、`lab/tests/test_datalake_vertical.py` |
| Resolver 非法/不完整 view、权限、操作隔离与 Planner | `data-lake/tests/test_calendar_prerequisites.py`、四 Dataset runtime tests |
| 完整性、原子提交、幂等、失败/中断恢复 | `data-lake/tests/test_core.py`、`test_ports.py`、Dataset runtime tests |
| SQLite read-only、snapshot、hash/basis integrity、generation 3、旧库拒绝 | `data-lake/tests/test_core.py` |
| Provider 共享限流、安全失败、取消及真实 HTTP send gate | `data-lake/providers/tushare/tests`（受控本地 transport，无真实 Source） |
| CLI delivery、consumer 兼容、跨进程持久化复用 | `lab/tests`、`market-research/tests`、backend architecture checks |
| Authority 相对链接与根入口可达性 | `market-snapshot/tests/test_authority_topology.py`，另检查 DataLake 全部文档及 anchors |

实际检查（均从 repository root 使用根 Poetry 环境）：

- 基线：`poetry run pytest data-lake lab/tests backend-api/tests/test_architecture.py market-snapshot/tests/test_authority_topology.py -q`：773 passed、1 skipped。
- 最终：`poetry run pytest data-lake lab/tests market-research/tests backend-api/tests/test_architecture.py market-snapshot/tests/test_authority_topology.py -q -rs`：**1038 passed、2 skipped，41.30 秒**。
- `poetry run ruff check data-lake lab`：All checks passed；`poetry run mypy data-lake lab`：Success，62 source files。
- `poetry run python -c "import data_lake; import data_lake.datasets.tushare_trade_calendar, data_lake.datasets.tushare_index_daily, data_lake.datasets.tushare_equity_index_futures, data_lake.datasets.tushare_equity_index_options"`：通过；临时 cwd isolated interpreter imports 由 `test_all_namespaces_installed_outside_repo` 与 Provider topology test 实际执行并通过。
- 非忽略 DataLake Markdown 共 29 份：28 份从模块架构可达，另 1 份为预先读取的继承 execution policy `AGENTS.md`；本地 links / heading anchors 全部通过。忽略的用户 runtime exports 不属于 Authority 检查集合。
- `git diff --check`：通过。已审阅本轮完整 diff（含本报告）和整个分支相对本地 develop 的变更；四 Dataset public facade/models、公共 result types 无变更。没有无关重构、凭据或运行产物进入本轮 diff。

最终两个 skip 均因 Windows 缺少创建 symlink 的权限（WinError 1314），对应 `lab/tests/test_research.py::test_research_discovery_rejects_a_package_symlink` 与 `market-research/tests/test_research_execution.py::test_symlinked_study_and_run_locations_are_rejected`。它们不计作通过，不涉及 Dataset source-fact / public service 验收；本机未验证这两个 Research discovery/output-layout 的真实 symlink 场景。

## 真实 Source Smoke

日期范围固定为 **2026-10-15..2026-10-15**；使用现有合法 credential、真实 Source Adapter 和 Provider HTTP 链路。四个 Dataset 各使用一个系统临时目录内的独立 SQLite，Calendar 的 SSE/CFFEX 两个 scope 共用其唯一 owned SQLite。临时 harness 只重定向 Composition 的内部 `database_path`，并计数/限制 Provider calls；未改变公开 request 或 Provider 业务行为，未读取或修改用户默认/legacy 缓存。

预算为单进程 60 calls/min、最多 60 calls、600 秒；实际 **24 calls、23.69 秒**，全部请求成功，无自动 retry。下表请求数包含完整 metadata/daily 分页及空终页。

| Dataset / selection | Provider calls | 成功目标 units | Export records | View schema | 结果 |
| --- | ---: | ---: | ---: | ---: | --- |
| Calendar / SSE | 1 | 1 | 1 | 1 | Passed |
| Calendar / CFFEX | 1 | 1 | 1 | 1 | Passed |
| Index / 000300.SH | 10 | 1 | 1 | 1 | Passed |
| Futures / IF | 6 | 1 | 4 | 2 | Passed |
| Options / IO | 6 | 1 | 266 | 2 | Passed |

每个范围均完成 `ensure → coverage → export → repeated ensure`：coverage.complete=true，export.coverage 与 coverage 一致；重复 ensure attempted_units=records_written=0、complete=true。Coverage/export/重复 ensure 未增加 Provider calls，四个临时 SQLite 的 SHA-256 在这些操作前后保持不变。

本次未遇到真实 Provider rejection，不声称现场复现了 quota/permission/network failure；对应失败分类、无隐式 retry 与恢复通过离线受控测试验证。单日 smoke 不代表全部历史日期、所有产品或任意账号权限已验证；没有待补的本次外部 Source 验收条件。原始 Source facts、临时 SQLite、credential 和运行输出不进入 Git。

## V1 限制与发布边界

- Limiter 只保证同一 process / credential，不协调其他 processes/worktrees/machines；账号实际 endpoint 权限与配额由 operator 确认。
- 不自动 retry；失败/中断后显式重复 ensure。Success 表达成功取得时的完整事实，不保证 freshness；无 refresh/force/TTL/source-correction policy。
- SQLite 仅接受 compatible generation 3，rebuild-only，无 migration/旧库 fallback；仅 operator 可显式处理 owning Dataset cache，不能自动清理真实数据。
- 本次在 Windows native / 根 Python 3.13 环境验收；不声称已完成 Linux 或其他部署环境运行验收。

**DataLake V1 — Architecture Frozen, Implementation Reconciled, Release Ready.**

本结论适用于上述 V1 契约及验收范围，不扩大已声明平台、quota 或 freshness 保证；后续以维护、缺陷修复和新增 Dataset 为主。本任务不执行 commit、merge 或 deployment。
