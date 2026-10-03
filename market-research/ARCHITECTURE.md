# market-research 模块架构 authority

本文件定义 Research 的稳定 identity、职责边界、依赖方向、visualization ownership 与下层导航。仓库模块关系与唯一 Python runtime 见 [repository architecture](../ARCHITECTURE.md)；Shared Component contracts、Observation framework、Study contracts、UI details 和实现状态分别由下层 owner 定义。

## 1. Purpose 与职责终点

`market-research` 是独立 exploratory / statistical research bounded module，负责开放探索、retained empirical facts、descriptive / conditional statistics、research-specific slicing / joining / grouping / reshaping、hypothesis discovery、study-specific evaluation 与 visualization。

```text
market-research
    ├── scratch       disposable exploration
    ├── shared        small reusable research mechanisms
    ├── observations  independent retained empirical research artifacts
    ├── studies       objectives + orchestration / outcome + optional retained outputs
    └── ui            current Study CLI / output support
```

Scratch、Shared Research Component、Observation、Analysis / Study 有不同职责与生命周期。Component 复用小领域机制，不拥有 research artifact lifecycle；Observation 是最小独立 research artifact boundary，不是最小计算单元。Observation 唯一拥有 durable reusable empirical persistence；Study 拥有 user request / bindings、runtime orchestration / invocation / composition 与 execution outcome，并可按明确目标声明 retained workflow outputs / optional Analysis / Evidence。Retained Study 是值得保留的 research / orchestration authority，不要求 retained execution output。Orchestration-only Study 可以没有 Workflow Artifacts / Analysis / Evidence；Research 的解释职责终点仍是 evidence / finding，不是 production market-state output、forecast、decision、signal、recommendation 或 trading strategy。

本模块不拥有 production modeling、model evaluation、forecasting、decision system、backtesting framework、research service/API 或 production Web UI。Observation 是本模块内部 first-class concept，不是 repository-level bounded module；新增它不建立 generic research platform。

## 2. Research UI

当前已定义的 human-facing runnable surface 仍以 Study-local CLI 为主；repository `lab research` 拥有 discovery / forwarding，本模块拥有 Study execution 与 evidence output semantics。Observation public invocation semantics 见 [Observation authority](src/market_research/observations/ARCHITECTURE.md)，其 CLI delivery 尚未决定。

```text
User → repository discovery / forwarding → Study-local CLI
     → Study-owned request / workflow / Observation invocation
     → runtime state / execution outcome / optional retained workflow outputs
     → optional Study-local Analysis / Evidence / visualization
```

Repository CLI 拥有路径/layout 校验、进程调用与 exit-code propagation，不 import Research implementation 或维护 Study catalog。Study-local CLI 拥有参数、输入校验、配置、依赖 composition、Study invocation 与 success/failure presentation。新 Study orchestration 经 Observation public boundary ensure Artifacts，也可调用已声明的 shared resolver / reader 准备输入；upstream facts 由 Observation 或 component 通过 public application boundaries 获取。Legacy Study 的直接 Snapshot composition 按 [Compatibility](src/market_research/studies/COMPATIBILITY.md) 保留。

CLI convention、stable Study ID、orchestration-only / retained-output execution shapes 见 [Research UI authority](src/market_research/ui/ARCHITECTURE.md)；配置与 run-output placement / replacement 仅明确保留 outputs 时适用，见 [configuration authority](src/market_research/ui/CONFIGURATION.md)。具体参数和用法留在 Study authority。Orchestration-only runner 不依赖 output.root / directory；UI 不管理 Observation SQLite。

## 3. Research Result 与 Visualization

Research 的最终消费者首先是人。Visualization 是 Research Result 的 human-facing representation，用于帮助人观察、比较、发现 pattern 并形成下一步 hypothesis；它不是 market state、forecast、decision output 或 production UI contract。

当前阶段的责任与默认实现方向是：

```text
market-research
    ↓
research computation
    ↓
research result
    ↓
Python-generated study visualization
```

Research visualization 由 `market-research` 拥有，并默认以 Python 生成的静态图片保留。Study 可以根据真实研究问题选择 time-series plot、distribution / histogram、scatter plot、grouped / bucket comparison、heatmap 或其他 study-specific visualization；可以使用仓库已有或真实 Study 明确需要的合适 Python visualization library，例如 `matplotlib`，但不得仅为本 authority 预先引入复杂 visualization stack。

该选择是阶段性但正式有效的 authority decision，不是永久产品架构。当前 Study 类型和 visualization pattern 尚未稳定，优先目标是研究迭代速度，而不是提前建立 Research UI Platform。因此本阶段不抽象 Research Chart API、Generic Chart DTO、Research Dashboard Framework 或 Generic Visualization Protocol。

在新的 canonical authority 明确取代本决定前，Research visualization 必须继续由 `market-research` 通过 Python study output 生成；不得仅因 `web-ui` 已存在而把该责任迁移至 `backend-api`、`web-ui` 或所谓 Research Viewer。现有 production / business UI 不因此成为 Research Viewer。

当多个真实 Study 持续出现稳定、重复的 visualization pattern 时，可以通过新的 semantic decision 与 authority update，重新评估是否将部分通用交互式展示能力提升到 `backend-api` 与 `web-ui`。未来即使发生该迁移，Research backend / module 也应输出 `BasisAssociationResult`、`CorrelationResult`、`QuantileStatistics`、`TimeSeriesObservations` 等 research semantics，由 Frontend 决定如何交互式呈现；Plotly config、ECharts option、React chart props 或其他 frontend-library configuration 不得成为 canonical Research Result。

## 4. Upstream 与 canonical dependency direction

```text
DataLake public Application Service / Market Snapshot public result
    → Shared Research Component result / Observation retained Artifact
    → Study-owned runtime orchestration → prepared complete inputs / outcome
    → optional Study-local Analysis → optional Evidence / Findings
Evidence / Findings → Human / Agent Semantic Decision → authority update → Modeling
```

该图表达 semantic data / decision direction，不使 Research 成为 Modeling 的强制 runtime stage。Observation / upstream-backed component 先审查 DataLake public semantic capability，足够时必须使用 Dataset public Application Service；只有 semantic capability insufficient 才选明确 Snapshot public Product / Application boundary，详细规则直接进入 [Public upstream policy](UPSTREAM.md)；Observation lifecycle 另归其 authority。这是 design-time selection，不是 runtime failover；Research（包括所有 Observation）不直接依赖 Tushare / external market-data provider，不访问 upstream internals、credential / transport、backend-api 或 FastAPI DTO。Study orchestration 可消费 component result；Analysis 只计算已准备 inputs / 调用纯计算 component，不通过 helper 隐藏获取事实。具体分工见 component authority 与 Study Schema；legacy Study composition 按 Compatibility 保留。

Snapshot 继续拥有从 Source fact 到 Analysis-ready Artifact 的确定性准备；DataLake 继续拥有 reusable source facts。共享 repository Python runtime 不授予内部 import permission，Snapshot / DataLake 不得反向依赖 Research。缺失的 public capability 须记录并与对应 owner reconciliation，不把 Research interpretation 推回 upstream，也不穿透内部实现。此方向不承诺具体 integration 已完成。

## 5. Scratch、Shared Component、Observation 与 Analysis / Study

### Scratch

`scratch` 用于低约束、可能一次性的 script / notebook / dataframe / plotting 探索。其 output 是 disposable，不形成稳定 authority、业务契约、production dependency 或 retained Observation capability。

### Shared Research Component

shared 拥有跨研究明确复用的窄领域机制；resolver / reader 可以消费 authoritative DataLake public facts，calculator / transform 可以计算已准备输入。Local / shared 提升、Observation 准入、caller 分工与新 helper 判断唯一进入 [Shared Component authority](src/market_research/shared/ARCHITECTURE.md)。当前 [Expiry Universe resolver](src/market_research/shared/cffex_option_expiry_universe/ARCHITECTURE.md) 的具体 I/O / dependency 下沉该 owner；不建立大 utility layer。

### Observation

`observations` 拥有最小独立 empirical research semantics 与持久化 Artifact，输出值得 Analysis / Study 独立消费和解释，独立于 Study 生命周期。可调用 shared component / 包含 local logic；复用本身不足以成为 Observation。稳定 contract 从 [Observation architecture](src/market_research/observations/ARCHITECTURE.md) → [Public upstream policy](UPSTREAM.md) 进入，再读 [Schema](src/market_research/observations/SCHEMA.md) / [Authoring](src/market_research/observations/AUTHORING.md) 与实际 concrete entry。本模块不拥有 concrete business key、population、grain、formula、Artifact schema 或 SQLite schema。

当前 concrete Observation 为 [cffex_option_expiry_dte_chain](src/market_research/observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md)。Runnable contract 进入 [Observation IMPLEMENTATION](src/market_research/observations/IMPLEMENTATION.md) 与其 concrete handoff。Universe 已改为 shared resolver；新的 resolver / Study runtime 已 reconciliation；当前验证见 [reconciliation](IMPLEMENTATION_RECONCILIATION.md#shared-component-runtime-reconciliation)。

### Study

`studies` 用于值得保留、复查或继续推进的 research question / preparation objective。Study 拥有 user request / input bindings、Observation invocation orchestration、runtime plan / order / failure continuation、execution outcome 与 optional Analysis orchestration；retained Workflow Artifacts / Evidence 仅按实际目标明确声明。Study 不拥有 Observation definition 或 reusable empirical persistence，不复制 market rows 建 canonical cache。新建入口为 [Study Authoring](src/market_research/studies/AUTHORING.md)，对象模型由 [Schema](src/market_research/studies/SCHEMA.md) 拥有，runtime / retained state 与 complete-input boundary 进入 [Workflow](src/market_research/studies/WORKFLOW.md)，固定四文件布局由 [Skeleton](src/market_research/studies/SKELETON.md) 拥有。

Study authority 与 Python implementation colocate 于 `src/market_research/studies/<study_package>/`，同一 semantic owner 只有一个 canonical physical directory。知识 contract 与 executable responsibilities 仍分别由 authority 与 implementation 承担，物理共置不改变研究语义。Public Study ID 由 UI authority 定义。

Retained Study 是研究知识与 evidence record，不等同于长期 software capability，也不因被保留而成为 Snapshot、Modeling 或 production output 的 semantic authority。若研究未来演化为 production / reusable capability，须另作 semantic decision 与 canonical authority update。

Runnable topology 由 [Implementation Package Contract](src/market_research/studies/IMPLEMENTATION.md) 拥有，completeness / traceability / topology review 由 [Review](src/market_research/studies/REVIEW.md) 拥有。Study-specific input selection、Analysis、plots、findings、limitations 与 acceptance 留在当前 Study 的 narrowest owner。Analysis 仍为 Study-local，可调用已声明的纯计算 component；只有明确跨研究机制复用才按 component authority 提升，不从相似代码继承 sibling 的研究语义或创建 reusable Analysis framework。持久化 empirical artifacts 仍通过 Observation boundary 复用。

Legacy Study-local Observations、旧 evidence 与 historical shared dependencies 按 [Compatibility](src/market_research/studies/COMPATIBILITY.md) 保持有效；新 framework 不自动迁移它们。仅 human-triggered concrete reconciliation 才迁入 Observation-first。历史 shared owners 的适用范围仍沿 Compatibility 或相关 legacy authority 进入；新 component 分类从 shared authority 进入，不自动加载 historical semantics。

当前 [cffex_option_expiry_dte_collection Study](src/market_research/studies/cffex_option_expiry_dte_collection/ARCHITECTURE.md) 组合 Universe component 与 chain Observation；具体 objective、bindings、workflow、outcome 与 handoff 由该 Study authority 拥有。当前 runtime 验证见 [reconciliation](IMPLEMENTATION_RECONCILIATION.md#shared-component-runtime-reconciliation)，readiness 定义见 [Authoring](src/market_research/studies/AUTHORING.md#publication-与-dependency-handoff)。

## 6. Research 与 Modeling

`market-research != market-modeling`。两者为独立 sibling analytical modules，Research 不要求以 Model 为中心，也不成为 Modeling runtime dependency。本模块不定义未来 Modeling 内部 structure、model research / evaluation 或 promotion framework。

Evidence / Findings 只有经过 human / agent semantic decision 与对应 canonical authority update 才能影响未来 Modeling。Artifact 或 finding 不自动晋升为 production semantics、forecast、decision、signal 或 recommendation。

## 7. Authority navigation 与维护边界

Canonical Python runtime/package root 保持 `market-research/src/market_research`。Shared / Observation / Study / UI framework 与具体 capability 的 authority 和 implementation 按 narrowest semantic owner 共置于该 root 下；module AGENTS / ARCHITECTURE / UPSTREAM 留在 module root，tests 仍位于 `market-research/tests`。Scratch 是 disposable exploration，不因本 topology 获得 authority。

```text
repository ARCHITECTURE.md
    → market-research/ARCHITECTURE.md
        ├── UPSTREAM.md (共用 public fact contract)
        ├── src/market_research/shared/ARCHITECTURE.md
        │   └── concrete Component entry → narrow I/O / dependency contract
        ├── src/market_research/observations/ARCHITECTURE.md
        │   ├── UPSTREAM.md → SCHEMA.md / AUTHORING.md → IMPLEMENTATION.md
        │   └── concrete Observation entry → relevant specialized / upstream authority
        ├── src/market_research/studies/AUTHORING.md
        │   ├── SCHEMA.md / WORKFLOW.md / SKELETON.md
        │   ├── IMPLEMENTATION.md / REVIEW.md / COMPATIBILITY.md (按需)
        │   └── actual Component / Observation authority → concrete Study entry
        │       → INPUTS.md / METHOD.md / RESULTS.md → relevant specialized authority
        ├── src/market_research/ui/ARCHITECTURE.md → CONFIGURATION.md
        └── IMPLEMENTATION_RECONCILIATION.md (验证 evidence，非 semantic owner)
```

本文件只拥有稳定 module identity / boundaries、依赖方向、用途分工、visualization ownership 与导航；Component I/O / upstream bindings 留在具体 component owner；Observation lifecycle / identity / persistence contract 留在 Observation owner，concrete shape 留在其具体 authority；Study framework、UI details 与当前实现差异各由 specialized owner 定义。

[Implementation reconciliation](IMPLEMENTATION_RECONCILIATION.md) 记录当前 topology / runtime reconciliation 的基线、验证与 remaining gaps；历史详细 ledger 从指定 Git baseline 查看，不取代 semantic authority。只有 module 定位、跨模块边界、内部用途分工或导航变化时更新本文件；不得上提具体 Observation / Study schema、formula、workflow 或 implementation contract。
