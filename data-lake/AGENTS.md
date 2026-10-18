# data-lake Agent Rules

## 适用范围与 context routing

本文件适用于 `data-lake/` 整棵目录，继承根 [AGENTS.md](../AGENTS.md) 的执行政策。稳定 semantic entry 是 [ARCHITECTURE.md](ARCHITECTURE.md)；先从该入口确认 owning boundary，再按任务选择下列 authority，不默认加载全部专题或 sibling Dataset。

| 任务 / 应修改的 canonical owner | 阅读路径 |
| --- | --- |
| 模块职责、ownership、public / dependency / Python boundary | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Experimental Source exploration, isolation and formal admission | [EXPERIMENTS.md](EXPERIMENTS.md) |
| Shared Kernel Domain primitives、逻辑 persistence、状态、公共 completeness / normalization invariants | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Kernel Use Cases / lifecycle、公共 request/result/view、failure taxonomy、dependency 调用与 runtime boundary | [APPLICATION.md](APPLICATION.md) |
| Source / Repository Outbound Ports、Adapter 能力与读写/失败责任 | [PORTS.md](PORTS.md) |
| FetchUnitPlanner、可选 Prerequisite Resolver、六角色接入、Composition Root | [COMPOSITION.md](COMPOSITION.md) → owning Dataset ARCHITECTURE.md → 必要 TRADING_DAYS.md |
| Batching、partition、worker/writer、cancellation、验证复用 | [EXECUTION.md](EXECUTION.md) |
| Kernel SQLite Repository Adapter、transactions / snapshots、frozen basis、rebuild-only compatibility | [PERSISTENCE.md](PERSISTENCE.md) |
| Logging / diagnostics | [DIAGNOSTICS.md](DIAGNOSTICS.md) |
| Tushare credential、client、限流与 provider execution failure | [providers/tushare/ARCHITECTURE.md](providers/tushare/ARCHITECTURE.md) |
| Dataset-specific domain / Source / completeness | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md → 所需专题 |
| Dataset-specific public service / consumer contract | owning Dataset ARCHITECTURE.md → SERVICE.md |
| CLI delivery / delegation | [lab authority](../lab/ARCHITECTURE.md) |
| 已记录的 authority / implementation 差异与后续任务 | [IMPLEMENTATION.md](IMPLEMENTATION.md) → 对应 canonical authority；状态记录不代替语义 |

普通 Dataset domain task 不默认加载 provider execution、service 或 CLI authority；涉及已声明 prerequisite 时，读取其 public contract，不加载 sibling internals。Python tooling 与当前环境操作遵循 [repository architecture](../ARCHITECTURE.md) 和 [DEVELOPMENT.md](../DEVELOPMENT.md)，从 repository root 使用唯一根环境。

## Modification rules

- 语义变更先更新 narrowest canonical authority；下层只能 specialize 或 constrain 上层 invariant。发现 authority / implementation 冲突须显式核对并报告，不能静默选择或发明另一套语义。
- 上表中的 owner 唯一拥有对应契约；其他文档通过链接继承，不复制规则或维护历史施工、commit / test evidence。Catalog 只导航。
- Implementation 遵守模块 public/dependency boundary，不穿透 consumer 或 sibling internals；共享 Python runtime 不授予额外 import permission。
- Shared Kernel / Provider / Dataset 的 authority、source 与 tests ownership 遵循模块架构；Provider 任务从 `providers/<provider-id>/ARCHITECTURE.md` 进入，Dataset storage 仍由 owning Dataset 拥有。Package wiring 保持既有 Provider execution imports 与 Dataset public imports 兼容，不创建 Provider-local / Dataset-local project 或环境。
- Kernel 结构任务先锁定模块架构的 Domain / Application / Ports / Adapters 依赖方向，再读受影响专题；Dataset 接入任务读取 COMPOSITION.md 与 owning Dataset 角色绑定，不按旧 Python 文件名推导 semantic owner。
- Runtime state 不进入 Git；验证使用临时 SQLite / fake Source，不操作真实缓存。旧目录 state 隔离遵循 PERSISTENCE.md，credential convention 遵循 provider authority。

## Verification rules

### Authority-only

核对受影响语义及下层 specialization、唯一 semantic owner、相对链接与 section anchors、从根入口逐层可达性，并审阅完整 diff。移除历史记录不能移除仍有效的 contract；authority ↔ implementation 的真实 gap 必须明确报告。

从 repository root 运行：

```bash
poetry run pytest market-snapshot/tests/test_authority_topology.py
git diff --check
```

Authority-only 不修改 source、runtime data 或根 Python 配置；只有修复 authority link / topology verification 明确必要时才修改测试登记。新增或删除 authority 时同步 catalog / navigation 与现有 topology entries；补充只读检查验证所有当前 DataLake authority 的可达性及 anchors，不以 topology green 代替 semantic review。

### Implementation

从 repository root 按受影响范围运行；共享 core/module tests 位于 `data-lake/tests/`，Provider tests 位于 `providers/<provider-id>/tests/`，Dataset tests 位于 `datasets/<dataset-id>/tests/`，CLI consumer tests 位于 `lab/tests/`：

```bash
poetry run python -c "import data_lake"
poetry run python -c "import data_lake.datasets.tushare_trade_calendar, data_lake.datasets.tushare_index_daily, data_lake.datasets.tushare_equity_index_futures, data_lake.datasets.tushare_equity_index_options"
poetry run pytest data-lake
poetry run pytest lab/tests
poetry run ruff check data-lake lab
poetry run mypy data-lake lab
poetry run pytest backend-api/tests/test_architecture.py market-snapshot/tests/test_authority_topology.py
git diff --check
```

检查公共 request/result/view、计数、逐 unit completeness / 原子提交、read-only 调用链、failure taxonomy 与 export snapshot；按受影响 execution / persistence / provider 专题验证其 invariants。Public facade tests 直接验证 attributes。Core / Dataset tests 不需要真实 credential，不调用外部 Source。

跨 Dataset contract 同时验证 producer 与 consumer；CLI integration 同时验证 owning Dataset 与 lab delivery/exit codes。根 package registration / tooling 改变时，先从根执行 `poetry install`，再验证 installed imports（包含临时 cwd 的 isolated interpreter）及 `poetry run pytest`，不能只依赖 pytest pythonpath。提交前审阅完整 diff。
