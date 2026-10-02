# market-research 模块架构 authority

本文件定义 Research 的稳定 identity、职责边界、依赖方向、visualization ownership 与下层导航。仓库模块关系与唯一 Python runtime 见 [repository architecture](../ARCHITECTURE.md)；Observation framework、Study contracts、UI details 和实现状态分别由下层 owner 定义。

## 1. Purpose 与职责终点

`market-research` 是独立 exploratory / statistical research bounded module，负责开放探索、retained empirical facts、descriptive / conditional statistics、research-specific slicing / joining / grouping / reshaping、hypothesis discovery、study-specific evaluation 与 visualization。

```text
market-research
    ├── scratch       disposable exploration
    ├── observations  reusable retained empirical facts
    ├── studies       questions + Artifact composition + Analysis + Evidence
    └── ui            current Study CLI / output support
```

Scratch、Observation、Study 具有不同生命周期。Observation 是独立 retained fact producer，Study 消费其 Artifacts 并形成 Evidence / Findings。Research 的解释职责终点仍是 evidence / finding，不是 production market-state output、forecast、decision、signal、recommendation 或 trading strategy。

本模块不拥有 production modeling、model evaluation、forecasting、decision system、backtesting framework、research service/API 或 production Web UI。Observation 是本模块内部 first-class concept，不是 repository-level bounded module；新增它不建立 generic research platform。

## 2. Research UI

当前已定义的 human-facing runnable surface 仍以 Study-local CLI 为主；repository `lab research` 拥有 discovery / forwarding，本模块拥有 Study execution 与 evidence output semantics。Observation public invocation semantics 见 [Observation authority](observations/ARCHITECTURE.md)，其 CLI delivery 尚未决定。

```text
User → repository discovery / forwarding → Study-local CLI
     → Study request / Artifact dependency composition
     → Study-local Analysis → Evidence / report / visualization
```

Repository CLI 拥有路径/layout 校验、进程调用与 exit-code propagation，不 import Research implementation 或维护 Study catalog。Study-local CLI 拥有参数、输入校验、配置、依赖 composition、Study invocation 与 success/failure presentation。新 Study 经 Observation public boundary resolve / ensure Artifacts；upstream facts 由 Observation 通过 public application boundaries 获取。Legacy Study 的直接 Snapshot composition 按 [Compatibility](studies/COMPATIBILITY.md) 保留。

CLI convention、stable Study ID、配置、output placement 与 evidence replacement 见 [Research UI authority](ui/ARCHITECTURE.md) 及 [configuration authority](ui/CONFIGURATION.md)；具体参数和用法留在 Study authority。UI output configuration 不管理 Observation SQLite。

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
    → Observation → retained Observation Artifact
    → Study → Study-local Analysis → Evidence / Findings
    → Human / Agent Semantic Decision → authority update → Modeling
```

该图表达 semantic data / decision direction，不使 Research 成为 Modeling 的强制 runtime stage。Observation upstream boundary 的完整规则由 [Observation authority](observations/ARCHITECTURE.md) 拥有；Research 只消费 DataLake public Application Service 或 Snapshot public application/product result，不进入 Source、Raw、private Preparation、upstream persistence、Dataset / Snapshot SQLite，也不依赖 backend-api、FastAPI DTO 或 frontend types。

Snapshot 继续拥有从 Source fact 到 Analysis-ready Artifact 的确定性准备；DataLake 继续拥有 reusable source facts。共享 repository Python runtime 不授予内部 import permission，Snapshot / DataLake 不得反向依赖 Research。缺失的 public capability 须记录并与对应 owner reconciliation，不把 Research interpretation 推回 upstream，也不穿透内部实现。此方向不承诺具体 integration 已完成。

## 5. Scratch、Observation 与 Study

### Scratch

`scratch` 用于低约束、可能一次性的 script / notebook / dataframe / plotting 探索。其 output 是 disposable，不形成稳定 authority、业务契约、production dependency 或 retained Observation capability。

### Observation

`observations` 拥有 reusable retained empirical products，独立于 Study 生命周期。稳定 contract 从 [Observation architecture](observations/ARCHITECTURE.md) 进入，必答 concrete semantics 与 authoring 分别进入 [Schema](observations/SCHEMA.md)、[Authoring](observations/AUTHORING.md)。本模块 entry 不拥有具体 business key、population、grain、formula、Artifact schema 或 SQLite schema。

首个 concrete authority 为 [cffex_option_expiry_dte_chain](observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md)，其 specialized contracts 从该 entry 进入。Authority readiness 与 runtime readiness 分开；当前尚未开始 Observation implementation，不从 historical shared helpers 推导已存在能力。

### Study

`studies` 用于值得保留、复查或继续推进的研究问题与 evidence record。Study 拥有 question、Observation Artifact composition、Analysis、Evidence、limitations 与 acceptance，不拥有 Observation definition。新建入口为 [Study Authoring](studies/AUTHORING.md)，semantic structure 由 [Schema](studies/SCHEMA.md) 拥有，固定四文件布局由 [Skeleton](studies/SKELETON.md) 拥有。

Study authority 位于 `studies/<study_package>/`，implementation 位于同名 `src/market_research/studies/<study_package>/`，保持研究知识与可替换 executable implementation 的长期分离，不迁入统一 src authority 或机械复制 Snapshot product layout。Public Study ID 由 UI authority 定义。

Retained Study 是研究知识与 evidence record，不等同于长期 software capability，也不因被保留而成为 Snapshot、Modeling 或 production output 的 semantic authority。若研究未来演化为 production / reusable capability，须另作 semantic decision 与 canonical authority update。

Runnable topology 由 [Implementation Package Contract](studies/IMPLEMENTATION.md) 拥有，completeness / traceability / topology review 由 [Review](studies/REVIEW.md) 拥有。Study-specific input selection、Analysis、plots、findings、limitations 与 acceptance 留在当前 Study 的 narrowest owner。相似 Analysis 不触发 sibling 修改、shared 抽取或 reusable Analysis framework；复用 empirical facts 通过 Observation Artifact boundary。

Legacy Study-local Observations、旧 evidence 与 historical shared dependencies 按 [Compatibility](studies/COMPATIBILITY.md) 保持有效；新 framework 不自动迁移它们。仅 human-triggered concrete reconciliation 才迁入 Observation-first。历史 shared owners 只沿 Compatibility 或相关 legacy authority 进入，不在新 Study 默认创建路径。

当前基线无 tracked concrete retained Study。Study output 可按研究需要保留 machine-readable result、静态图片或 report；文件名、数量、格式由 Study 定义，不建立统一 artifact schema。Observation-owned persistence 不放入 Study evidence lifecycle。

## 6. Research 与 Modeling

`market-research != market-modeling`。两者为独立 sibling analytical modules，Research 不要求以 Model 为中心，也不成为 Modeling runtime dependency。本模块不定义未来 Modeling 内部 structure、model research / evaluation 或 promotion framework。

Evidence / Findings 只有经过 human / agent semantic decision 与对应 canonical authority update 才能影响未来 Modeling。Artifact 或 finding 不自动晋升为 production semantics、forecast、decision、signal 或 recommendation。

## 7. Authority navigation 与维护边界

```text
repository ARCHITECTURE.md
    → market-research/ARCHITECTURE.md
        ├── observations/ARCHITECTURE.md
        │   ├── SCHEMA.md / AUTHORING.md
        │   └── concrete Observation entry → relevant specialized / upstream authority
        ├── studies/AUTHORING.md
        │   ├── SCHEMA.md / SKELETON.md
        │   ├── IMPLEMENTATION.md / REVIEW.md / COMPATIBILITY.md (按需)
        │   └── consumed Observation authority → concrete Study entry
        │       → INPUTS.md / METHOD.md / RESULTS.md → relevant specialized authority
        ├── ui/ARCHITECTURE.md → CONFIGURATION.md
        └── IMPLEMENTATION_RECONCILIATION.md (当前差异与交接)
```

本文件只拥有稳定 module identity / boundaries、依赖方向、用途分工、visualization ownership 与导航；Observation lifecycle / identity / persistence contract 留在 Observation owner，concrete shape 留在其具体 authority；Study framework、UI details 与当前实现差异各由 specialized owner 定义。

[Implementation reconciliation](IMPLEMENTATION_RECONCILIATION.md) 记录本次 authority-only 更新的基线、验证与 remaining drift，不取代 semantic authority。只有 module 定位、跨模块边界、内部用途分工或导航变化时更新本文件；不得上提具体 Observation / Study schema、formula、workflow 或 implementation contract。
