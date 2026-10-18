# market_research 模块架构 authority

本文件是 Research 的稳定入口，拥有 module identity、职责终点、顶层关系、依赖方向、Research / Modeling 边界与 visualization ownership。仓库模块关系及唯一 Python runtime / dependency environment 见 [repository architecture](../ARCHITECTURE.md)；专题 contract 和 implementation details 由下层 owner 定义。

## Module identity

The owning module/directory and canonical Python namespace are `market_research`. Inherit the [repository naming rules](../ARCHITECTURE.md#naming-and-transition-authority). Existing co-location, Study-local CLI and Research visualization ownership remain unchanged; the `ui_*` family does not relocate these internal concerns.

## Purpose 与职责终点

`market_research` 是独立 exploratory / statistical research bounded module，负责开放探索、retained empirical facts、descriptive / conditional statistics、research-specific slicing / joining / grouping / reshaping、hypothesis discovery、study-specific evaluation 与 visualization。Research 的解释职责终点是 evidence / finding。

## Research paradigms 与 authority scope

本模块并存两个研究范式，均继承本文件的 module / upstream / Modeling / visualization 边界：

- **V1（现有范式）**：下表及 Shared Component → Observation → Study / Study-local Analysis 的组织、caller 与 retained lifecycle 规则，继续由原路径拥有；既有 authority、实现、CLI、配置与输出契约保持不变。
- **V2（新设计）**：[v2/ARCHITECTURE.md](v2/ARCHITECTURE.md) 独立拥有 Conditional Forward Return Research 的领域语义。目前只有 Semantic Authority，不表示 runtime readiness，不替换或迁移 V1。

V2 不自动继承 V1 的 Study / Observation object model、四文件模板、持久化或 caller 分工，也不因此获得新的 upstream import permission。跨范式复用须按实际 public contract 单独确认；同名 Analysis 或观察事实不代表相同 identity / lifecycle。下表是 **V1 导航**，不是 V2 的必经设计路径。

| Area | 高层职责与下一步 |
| --- | --- |
| Scratch | Disposable script / notebook / dataframe / plotting exploration；不形成稳定 authority、retained capability 或 production dependency。 |
| Shared Component | 小领域 reusable mechanism；产生 ephemeral Component Result；不拥有 retained research Artifact lifecycle。分类、提升与 caller rules 进入 [shared/ARCHITECTURE.md](shared/ARCHITECTURE.md)。 |
| Observation | 最小独立 retained empirical artifact boundary，而非最小计算单元；独立于 Study 生命周期。Identity / durable reuse / persistence 进入 [observations/ARCHITECTURE.md](observations/ARCHITECTURE.md)。 |
| Study / Analysis | Study 拥有 request、bindings、orchestration 与 runtime outcome；Analysis 是可选的 Study-local computation。Retained workflow outputs / Evidence 仅明确声明时存在。进入 [studies/ARCHITECTURE.md](studies/ARCHITECTURE.md)。 |
| UI | Study-local CLI 与窄 configuration / retained-output support。进入 [ui/ARCHITECTURE.md](ui/ARCHITECTURE.md)。 |

Observation 是本模块内部 first-class concept，不是 repository-level bounded module。Retained Study 是值得保留的研究 / orchestration authority，不要求每次 execution 保留 output，也不自动成为长期 software capability。

## Dependency direction

以下内部链及 Study / Analysis caller 分工适用于 V1；V2 的概念执行主线见其独立入口。模块对外的依赖方向、公开边界与禁止事项适用于两者。

```text
DataLake public facts / Snapshot public analysis-ready results
    → declared ephemeral Component Results / Observation-owned retained Artifacts
    → Study orchestration → prepared complete inputs / runtime outcome
    → optional Study-local Analysis → optional Evidence / Findings
```

Research upstream selection 与 public consumption 唯一进入 [UPSTREAM.md](UPSTREAM.md)：DataLake-first 是 design-time capability selection；runtime failure 不授权换源；Research 不直接依赖 Tushare 或其他 external market-data provider。DataLake 继续拥有 source facts，Snapshot 继续拥有 canonical deterministic Product preparation；Research 不访问它们的 private persistence、Source / Capture / Raw / Preparation internals。

Study / Analysis 不直接消费 DataLake / Snapshot；Study 通过声明的 Component / Observation public boundary 准备输入，Analysis 只计算已准备好的 complete inputs。Caller 分工及 legacy 适用范围分别沿 Shared / Study framework entry 进入，不从共享 Python runtime 推导内部 import 权限。DataLake / Snapshot / Modeling 不反向依赖 Research；Research 不依赖 ui_http、FastAPI / HTTP DTO 或 frontend types。

## Research 与 Modeling

Research 与 Modeling 是独立 sibling analytical modules，Research 不是 Modeling 的强制 runtime stage，也不要求以 Model 为中心。

```text
Research Evidence / Findings
    → Human / Agent Semantic Decision → canonical authority update → Modeling
```

Finding 不自动成为 production market-state output、forecast、decision、signal、recommendation 或 trading strategy。本模块不拥有 production modeling、model evaluation、forecasting、decision system、backtesting framework、research service/API 或 production Web UI，也不预先定义未来 Modeling 内部设计或 promotion framework。

## Visualization ownership

Research 的最终消费者首先是人。Visualization 是 Research Result 的 human-facing representation，用于观察、比较、发现 pattern 和形成 hypothesis，不是 production UI contract。

当前 visualization 继续由 `market_research` 拥有，默认是 Python-generated study output，以静态图片保留；具体形式和合适 Python library 由真实 Study 决定，不为 framework 预建复杂 visualization stack、Chart API、Generic Chart DTO、Dashboard Framework 或 Visualization Protocol。

在新的 canonical semantic decision 明确取代本决定前，不因 `ui_web` 已存在而迁移到 ui_http、ui_web 或 Research Viewer。多个真实 Study 持续形成稳定重复 pattern 后，才可经新的 semantic decision 重新评估通用交互展示 ownership。即使未来迁移，canonical result 仍表达 Research semantics，frontend 决定呈现方式；Plotly config、ECharts option、React chart props 等 library configuration 不成为 canonical Research Result。

## Progressive disclosure 与维护

```text
repository ARCHITECTURE.md
    → market_research/ARCHITECTURE.md
        ├── v2/ARCHITECTURE.md → DECISIONS.md（待决专题，不是已发布 Contract）
        ├── shared/ARCHITECTURE.md → concrete Component → narrow contract / handoff
        ├── observations/ARCHITECTURE.md → SCHEMA / AUTHORING / IMPLEMENTATION
        │   └── concrete Observation → relevant specialized authority
        ├── studies/ARCHITECTURE.md → AUTHORING / SCHEMA / WORKFLOW
        │   └── concrete Study → INPUTS / METHOD / RESULTS → implementation handoff
        └── ui/ARCHITECTURE.md → CONFIGURATION.md
```

两种范式的 upstream-backed design 按需进入 [UPSTREAM.md](UPSTREAM.md)，只读实际所需 public contracts；不默认扫描 sibling owners。V1 Study implementation、legacy maintenance 与 migration 的专题选择由 Study entry 路由。V2 后续专题由其独立入口导航，不在本文件扩展具体 contract。

执行政策见 [AGENTS.md](AGENTS.md)；已关闭的 reconciliation 与验证证据保留在 Git history，不作为 semantic design 阅读前提。各 owner 的 authority 与 implementation colocate；具体 source / package / output topology 归各 implementation contract。

仅在 module identity、职责边界、顶层关系、依赖方向、visualization ownership 或导航变化时更新本文件；concrete capability 状态、schema、公式、workflow、readiness 和历史 evidence 不进入本入口。
