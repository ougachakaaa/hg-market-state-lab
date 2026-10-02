# market-research Agent Rules

## 适用范围

本文件适用于 `market-research/` 整棵目录，在根 [AGENTS.md](../AGENTS.md) 之上提供执行政策。下层 semantic authority 只能在上层 invariants 内 specialize / constrain。

## 最小 Authority 路径

先读根 [repository architecture](../ARCHITECTURE.md)，再读 [module architecture](ARCHITECTURE.md)，确认 runtime ownership、Research boundaries 与 Scratch / Observation / Study 分工。之后按任务选择：

| 任务 | 阅读路径 |
| --- | --- |
| Observation design / review | [Observation architecture](observations/ARCHITECTURE.md) → [Authoring](observations/AUTHORING.md) / [Schema](observations/SCHEMA.md) → specific Observation entry → 实际所需 upstream authority。 |
| 新 Study | [Study Authoring](studies/AUTHORING.md) / [Schema](studies/SCHEMA.md) → 仅实际消费的 Observation authority → specific Study entry；创建布局按 [Skeleton](studies/SKELETON.md)。 |
| Study implementation | Specific Study authority → consumed Artifact contracts → [Implementation Package Contract](studies/IMPLEMENTATION.md) → 同名 source package；从 implementation 进入时先读 init docstring 指向的 canonical authority。 |
| Study review / historical reconciliation | 按需 [Review](studies/REVIEW.md) / [Compatibility](studies/COMPATIBILITY.md)，再读触发范围涉及的 specific authority；不自动迁移。 |
| CLI / config / output | [Research UI authority](ui/ARCHITECTURE.md) → 其 configuration contract；具体参数与用法只读对应 Study authority。 |
| 当前 implementation / test drift | [Implementation reconciliation](IMPLEMENTATION_RECONCILIATION.md)。 |

需要 upstream facts 时，沿实际 Observation dependency 进入 [DataLake architecture](../data-lake/ARCHITECTURE.md) / [catalog](../data-lake/DATASETS.md)，或 [Snapshot architecture](../market-snapshot/ARCHITECTURE.md) / [catalog](../market-snapshot/CAPABILITIES.md)，只选实际 public contract。不默认加载 sibling products。

不得创建 Study 时扫描所有 Observations，不得为寻找可复用逻辑读取 sibling Studies、其 evidence、historical shared semantics 或 implementation。未知所需 Observation owner 时显式记录 capability gap，独立处理 Observation design，不在 Study-local Method 临时定义。

## 执行规则

- Python dependency installation、resolution 与 tooling 从 repository root 使用唯一 Poetry environment；module-local project、lock 或 virtual environment 均不创建。
- Authority / data meaning / output / responsibility / workflow changes 先落位 narrowest canonical owner，再修改实现。发现上下层或代码 drift 时显式 reconciliation，不静默选择语义。
- Research 只消费 DataLake public Application Service 或 Snapshot public application/product result；不导入 Source / Raw / private Preparation、upstream persistence、Dataset / Snapshot SQLite、backend-api、FastAPI DTO 或 frontend types。缺失 upstream capability 由 owning authority reconciliation。
- Scratch 是 disposable exploration，不形成 stable authority、retained capability 或 production dependency。
- 独立 Observation 的 inputs、key、population、grain、derivation、validity 与 Artifact contract 按其 Schema / Authoring 锁定；Agent 不补全改变业务含义的未决决定。Lifecycle、业务幂等、complete consumption 与一个 SQLite 的 ownership 由 Observation architecture 拥有，Study 不重定义。
- 新 Study 保留 Skeleton 四文件布局，拥有 Artifact composition、Analysis / Evidence；Analysis 仍 Study-local。Observation capability gap 不授权 Study 实现 Observation；依赖就绪后才进入 implementation。
- 每个新 runnable Study 必须是同名 Study-local Python package，按 Implementation Contract 保留 init、cli、study、analyses、evidence 边界；study.py 只做 readable orchestration / composition，resolve / ensure 经 Observation public boundary。不得把 Observation construction 或 persistence 放入 Study。Legacy implementation 按 Compatibility 处理。
- 新 runnable Study 提供 stable CLI Study ID、符合 UI authority 的 cli.py、canonical usage 与 CLI / output tests；不创建中央 registry、reflection、entry-point plugin 或 dynamic registration。
- 现有 `lab research` 是 Study 的 canonical 人类 discovery / forwarding 入口；Observation invocation semantics 与 CLI delivery 分开，后者尚未决定，不创建 Observation CLI / HTTP API。
- Visualization 仍由 Research 通过 Python study output 生成，默认静态图片，具体形式由真实 Study 决定。除非真实重复需求与新的 authority decision 已明确改划 ownership，不自行迁移至 backend-api、web-ui 或 Research Viewer。
- Findings 是 evidence，须 human / agent semantic decision 与 canonical update 后才可影响 Modeling，不自动形成 production contract、forecast、decision、signal 或 recommendation。未来 frontend 消费 Research semantics，不把 frontend-library configuration 写入 canonical result。
- 不创建 concrete Observation，除非该任务明确要求；不因 authority-only reconciliation 自动迁移旧 Study / evidence 或将 historical shared helpers 提升为能力。
- 不为假设需求建立 reusable Analysis、Experiment Engine、generic registry / Research Repository / Artifact DB、DAG、scheduler、executor、cache、refresh engine、promotion / backtest framework、research API 或 visualization framework。

## 验证

所有检查从 repository root 执行。Authority-only change 至少运行 Research authority topology tests、repository authority link / reachability checks 与 `git diff --check`，核对新增 owner 的可达性及完整 diff。旧 tests 固定过时 topology 时记录 reconciliation gap，不修改实现来迎合旧规范。

Implementation change 运行直接相关 tests 与 Ruff / mypy 范围；若变更 upstream producer contract，按 owning module local AGENTS 完成 producer / consumer reconciliation 和检查。完整差异必须审阅，验证失败须区分已有 baseline failure 与新变更引入问题。
