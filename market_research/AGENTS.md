# market_research Agent Rules

## 适用范围与最小阅读路径

本文件是 `market_research/` 的 execution policy，继承根 [AGENTS.md](../AGENTS.md)。先读 [repository architecture](../ARCHITECTURE.md) → [module architecture](ARCHITECTURE.md)，再按任务路由；下层 authority 只能在上层 invariants 内 specialize / constrain。

| 当前任务 | 下一步 |
| --- | --- |
| Component 分类 / promotion / design / review | [shared/ARCHITECTURE.md](shared/ARCHITECTURE.md) → actual concrete owner / narrow contract / handoff。 |
| Observation design / review | [observations/ARCHITECTURE.md](observations/ARCHITECTURE.md) → SCHEMA / AUTHORING → actual concrete entry / specialized contract。 |
| Observation implementation | Observation entry / Artifact / relevant specialized semantics → [observations/IMPLEMENTATION.md](observations/IMPLEMENTATION.md) → concrete handoff → actual public package。 |
| 新 Study / semantic review | [studies/ARCHITECTURE.md](studies/ARCHITECTURE.md) → AUTHORING / SCHEMA / WORKFLOW → actual dependencies → concrete 四文件 authority。 |
| Study implementation / acceptance | Study entry / consumed contracts → [studies/IMPLEMENTATION.md](studies/IMPLEMENTATION.md) → concrete handoff / owner-local src。 |
| Legacy maintenance / migration / consolidation / historical reconciliation | [studies/COMPATIBILITY.md](studies/COMPATIBILITY.md) → only triggered concrete scope；不默认迁移。 |
| CLI / configuration / retained-output handling | [ui/ARCHITECTURE.md](ui/ARCHITECTURE.md) → CONFIGURATION（适用时）→ actual Study input / result contract。 |
| 当前 authority / implementation drift | [IMPLEMENTATION_RECONCILIATION.md](IMPLEMENTATION_RECONCILIATION.md)。 |

Upstream-backed design 按 [UPSTREAM.md](UPSTREAM.md) 选择所需 public capability，再沿 DataLake / Snapshot entry 与 catalog 读取实际 owner；不默认加载 sibling Products / Datasets。新 Study 不扫描所有 Observations、sibling Studies、historical shared semantics 或 evidence 来继承研究含义。

## Authority-first execution 与 gap handling

- Data meaning、output、responsibility 或 workflow 变更先落位 narrowest canonical authority，再修改实现。缺失业务决定不得从代码、常见做法、sibling 或 human 沉默推断；按对应 AUTHORING 的 decision loop 处理。
- Observation identity / lifecycle / persistence 唯一归 [Observation architecture](observations/ARCHITECTURE.md)，不在 Study tasks 重定义；Component 分类 / caller rules 归 [Shared authority](shared/ARCHITECTURE.md)，Study object model / workflow 归 [Study entry](studies/ARCHITECTURE.md)。摘要与链接不建立第二 semantic owner。
- Upstream selection / direct producer permissions / provider prohibition / failure boundary 归 [UPSTREAM](UPSTREAM.md)；capability gap 交正确 owner reconciliation，不用 private access 或 runtime source fallback 绕过。发现 authority / implementation conflict，保留可确认 canonical semantics，明确记录 finding，不静默选择新语义。
- Authority Complete、design readiness 与 actual runtime readiness 按 [Study handoff](studies/AUTHORING.md#publication-与-dependency-handoff) 分开；获授权的 vertical slice 按 producer-first 顺序核对，不由文档完成自动启动 implementation。
- Python installation / resolution / tooling 始终从 repository root 使用唯一环境，不创建 module-local project / lock / .venv。源码入口 docstring 指回 owner authority；从代码进入任务时先回到该入口。

## 验证与范围

所有检查从 repository root 执行。Authority-only change 至少运行 Research authority topology / colocation tests、repository authority link / reachability checks 与 `git diff --check`，核对新增 owner 可达性并审阅完整 diff。仅因 topology 重组需要时机械更新相关验证，不改变业务测试或实现；失败区分 baseline 问题与新引入问题。

Implementation change 运行直接相关 tests 与 Ruff / mypy 范围；cross-module contract 变更按 producer / consumer local policy 同时检查。当前 drift register 不替代 semantic owner，也不把历史通过数当当前验收。

不因 authority 整理创建 concrete Observation、迁移 legacy Study / evidence、重算 runtime data 或提升 historical helpers。CLI、visualization 与 public delivery 变更分别遵守 UI / module authority；不自行创建 Observation CLI / HTTP API 或迁移 visualization ownership。不为假设需求建立 registry、Experiment Engine、generic Research Repository / Artifact DB、DAG、scheduler、executor、cache / refresh / retry engine、reusable Analysis / promotion / backtest / visualization framework。
