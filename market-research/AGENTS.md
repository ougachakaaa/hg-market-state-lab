# market-research Agent Rules

## 适用范围

本文件适用于 `market-research/` 整棵目录，在根 [AGENTS.md](../AGENTS.md) 之上提供执行政策。下层 semantic authority 只能在上层 invariants 内 specialize / constrain。

## 最小 Authority 路径

先读根 [repository architecture](../ARCHITECTURE.md)，再读 [module architecture](ARCHITECTURE.md)，确认 runtime ownership、Research boundaries 与 Scratch / Observation / Study 分工。之后按任务选择：

| 任务 | 阅读路径 |
| --- | --- |
| Observation design / review | [Observation architecture](observations/ARCHITECTURE.md) → [Upstream policy](observations/UPSTREAM.md) → [Authoring](observations/AUTHORING.md) / [Schema](observations/SCHEMA.md) → specific Observation entry → 实际所需 upstream authority。 |
| Observation implementation | Specific entry / Artifact（chain 按需 DATE_RESOLUTION）→ [framework IMPLEMENTATION](observations/IMPLEMENTATION.md) → concrete IMPLEMENTATION → public package；依赖选择仍遵守 UPSTREAM。 |
| 新 Study | [Study Authoring](studies/AUTHORING.md) / [Schema](studies/SCHEMA.md) → [Workflow](studies/WORKFLOW.md) → 仅实际消费的 Observation authority → specific Study entry；创建布局按 [Skeleton](studies/SKELETON.md)。 |
| Study implementation | Specific Study authority → consumed Artifact contracts → [Implementation Package Contract](studies/IMPLEMENTATION.md) → concrete IMPLEMENTATION（存在时）→ 同名 source package；从 implementation 进入时先读 init docstring 指向的 canonical authority。 |
| Study review / historical reconciliation | 按需 [Review](studies/REVIEW.md) / [Compatibility](studies/COMPATIBILITY.md)，再读触发范围涉及的 specific authority；不自动迁移。 |
| CLI / config / output | [Research UI authority](ui/ARCHITECTURE.md) → 其 configuration contract；具体参数与用法只读对应 Study authority。 |
| 当前 implementation / test drift | [Implementation reconciliation](IMPLEMENTATION_RECONCILIATION.md)。 |

Observation upstream design 先按 Upstream policy 审查 [DataLake architecture](../data-lake/ARCHITECTURE.md) / [catalog](../data-lake/DATASETS.md) 的实际 public Dataset contract；只有 semantic capability insufficient 才进入 [Snapshot architecture](../market-snapshot/ARCHITECTURE.md) / [catalog](../market-snapshot/CAPABILITIES.md) 选择 explicit public Product。不默认加载 sibling products，不以 runtime failure 换源。

不得创建 Study 时扫描所有 Observations，不得为寻找可复用逻辑读取 sibling Studies、其 evidence、historical shared semantics 或 implementation。未知所需 Observation owner 时显式记录 capability gap，独立处理 Observation design，不在 Study-local Method 临时定义。

## 执行规则

- Python dependency installation、resolution 与 tooling 从 repository root 使用唯一 Poetry environment；module-local project、lock 或 virtual environment 均不创建。
- Authority / data meaning / output / responsibility / workflow changes 先落位 narrowest canonical owner，再修改实现。发现上下层或代码 drift 时显式 reconciliation，不静默选择语义。
- Research 不直接依赖 Tushare / external market-data provider。Observation 按 [Upstream policy](observations/UPSTREAM.md) DataLake-first 选择 public semantic capability，insufficient 时才选明确 Snapshot public Product；不访问 upstream internals、provider credentials / transport、backend-api / FastAPI DTO 或 frontend types。Capability gap 交对应 owner reconciliation，不建立 runtime failover。
- Scratch 是 disposable exploration，不形成 stable authority、retained capability 或 production dependency。
- 独立 Observation 的 inputs、key、population、grain、derivation、validity 与 Artifact contract 按其 Schema / Authoring 锁定；Agent 不补全改变业务含义的未决决定。Lifecycle、业务幂等、complete consumption 与一个 SQLite 的 ownership 由 Observation architecture 拥有，Study 不重定义。
- 新 Study 保留 Skeleton 四文件布局，拥有 user request / bindings、required workflow、Observation invocation orchestration、runtime plan / state / outcome；retained Workflow Artifacts / Analysis / Evidence 仅按明确目标声明，三者均可为 0。Observation 唯一拥有 reusable empirical persistence，Study 不复制 rows 建第二 canonical cache。Observation gap 不授权 Study 实现 Observation；design-ready vertical slice 可依 [Authoring handoff](studies/AUTHORING.md#publication-与-dependency-handoff) 按 producer-first 顺序实施，实际 Study 实施前复核 producers / runtime bindings。
- 每个新 runnable Study 是同名 Study-local Python package；mandatory init、cli、study，analyses / evidence 按实际职责 conditional，按 Implementation Contract 拆分复杂 helper。study.py 拥有 orchestration / outcome，只在声明 retained outputs 时驱动物化 / publication；Only Study orchestration ensure Observations。Analysis 只计算已准备的 complete Artifacts，不调用 Observation / DataLake / Snapshot、不 fetch data 或读 persistence。Study 不直接消费 DataLake / Snapshot，不把 Observation Artifact construction / persistence 放入 Study；Legacy 按 Compatibility 保留。Orchestration-only CLI 不加载 output config、不要求 run-key / directory / overwrite / staging。
- 新 runnable Study 提供 stable CLI Study ID、符合 UI authority 的 cli.py、canonical usage 与 CLI / output tests；不创建中央 registry、reflection、entry-point plugin 或 dynamic registration。
- 现有 `lab research` 是 Study 的 canonical 人类 discovery / forwarding 入口；Observation invocation semantics 与 CLI delivery 分开，V1 仅 Python public ensure boundary，见 [Observation IMPLEMENTATION](observations/IMPLEMENTATION.md)；不创建 Observation CLI / HTTP API。
- Visualization 仍由 Research 通过 Python study output 生成，默认静态图片，具体形式由真实 Study 决定。除非真实重复需求与新的 authority decision 已明确改划 ownership，不自行迁移至 backend-api、web-ui 或 Research Viewer。
- Findings 是 evidence，须 human / agent semantic decision 与 canonical update 后才可影响 Modeling，不自动形成 production contract、forecast、decision、signal 或 recommendation。未来 frontend 消费 Research semantics，不把 frontend-library configuration 写入 canonical result。
- 不创建 concrete Observation，除非该任务明确要求；不因 authority-only reconciliation 自动迁移旧 Study / evidence 或将 historical shared helpers 提升为能力。
- 不为假设需求建立 reusable Analysis、Experiment Engine、generic registry / Research Repository / Artifact DB、DAG、scheduler、executor、cache、refresh engine、promotion / backtest framework、research API 或 visualization framework。

## 验证

所有检查从 repository root 执行。Authority-only change 至少运行 Research authority topology tests、repository authority link / reachability checks 与 `git diff --check`，核对新增 owner 的可达性及完整 diff。旧 tests 固定过时 topology 时记录 reconciliation gap，不修改实现来迎合旧规范。

Implementation change 运行直接相关 tests 与 Ruff / mypy 范围；若变更 upstream producer contract，按 owning module local AGENTS 完成 producer / consumer reconciliation 和检查。完整差异必须审阅，验证失败须区分已有 baseline failure 与新变更引入问题。
