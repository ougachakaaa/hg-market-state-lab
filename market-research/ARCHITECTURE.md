# market-research 模块架构 authority

本文件定义 `market-research` 的稳定语义、职责边界、依赖方向与内部用途。仓库级模块关系、Python runtime ownership 与顶层 analytical flow 见 [repository architecture](../ARCHITECTURE.md)；`market-snapshot` 的确定性数据准备边界见 [market-snapshot architecture](../market-snapshot/ARCHITECTURE.md)。

## 1. Purpose 与职责终点

`market-research` 是独立的 exploratory / statistical research bounded module。它用于：

- 开放探索市场数据；
- descriptive / conditional statistics；
- research-specific slicing、joining、grouping 与 reshaping；
- exploratory visualization；
- hypothesis discovery 与 study-specific evaluation；
- 快速判断哪些现象值得进一步研究或进入 Modeling 的语义决策。

Research 可以在开始时不知道最终需要的全部数据或输出形式，也不要求先存在稳定的 production contract。Research result 可以包含 structured observations、summary statistics、tables、research findings 与 visualizations；其职责终点是 evidence / finding，不是 production market-state output、forecast、decision、signal、recommendation 或 trading strategy。

本模块不拥有 production modeling、model evaluation、forecasting、decision system、backtesting framework、research service/API 或 production Web UI。Repository `dev.py research` 是统一发现/转发入口；本模块拥有具体 retained Study 的 study-local CLI 与执行语义。这些 CLI 是本地 inbound interaction boundary，不是 production application UI。

## 2. Research UI

当前 Research UI 是一个窄义、本地、human-facing CLI：

```text
User
    ↓
Repository CLI discovery / forwarding
    ↓
Study-local CLI request parsing
    ↓
market-snapshot public application boundary
    ↓
Retained Study
    ↓
configured output location
    ↓
result / report / visualization
```

Repository CLI 拥有跨 Study 的 discovery、路径/layout 校验、进程调用与 exit-code propagation；它不 import Research implementation 或维护 Study catalog。每个 study-local CLI 拥有自己的 command parsing、用户输入校验、Research UI configuration loading、Snapshot public-boundary composition、Study invocation 与 success/failure presentation。它不拥有 Snapshot Source/Capture、其他 Study method、Modeling、Forecasting、Decision、HTTP API 或 Web UI。

CLI convention、stable Study ID derivation 与 shared output placement 见 [Research UI authority](ui/ARCHITECTURE.md)；配置 schema 与路径解析见 [Research UI configuration](ui/CONFIGURATION.md)；具体参数、用法、Method 与 result semantics 与对应 retained Study authority 共置。

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

## 4. Snapshot 消费边界

稳定依赖方向是：

```text
market-research
        ↓
market-snapshot public application / product boundary
        ↓
analysis-ready result
```

Research 必须优先消费 `market-snapshot` 明确支持的 application/product result，不得进入或依赖：

- Source implementation 或 Source Capture internals；
- Raw Artifact internals；
- product-private Analysis Preparation implementation；
- persistence layout；
- `backend-api`、FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types。

共享 repository Python runtime 不构成跨模块自由 import permission。`market-snapshot` 不得依赖 `market-research`；Research 也不得把开放统计、hypothesis semantics、市场判断或 study-specific transformation 推回 Snapshot。

Snapshot 仍拥有从 Source fact 到 Analysis-ready Artifact 的确定性准备。Research 可以为具体研究执行 arbitrary slicing、joining、grouping、reshaping、statistics 与 plotting；只有真实 Research consumer 暴露出可复用且属于 deterministic data preparation 的缺口时，才通过对应 Snapshot canonical authority 做显式 reconciliation。

当前 Snapshot 已有 product-owned Data Service / application boundaries，但没有为 Research 承诺统一的公共 Python facade。Study-local CLI 只调用对应产品拥有的 production-ready public application composition entry；它不得创建 Source client、读取 credential 或进入 Snapshot internals。真实 Research consumer 暴露的窄 public-boundary 缺口必须与对应 Snapshot owner reconciliation，不得借此设计通用 research data interface。

## 5. Scratch 与 Retained Studies

### `scratch`

`scratch` 用于快速、低约束、可能一次性的探索，可以包含临时 Python script、notebook、dataframe operation、任意绘图与 disposable analysis。

Scratch 不构成 repository semantic authority，不得成为 production dependency，也不得被其他模块视为稳定接口、数据契约或可复用业务实现。

Scratch 可以自由生成图片，但其 artifact 仍是 disposable output，不构成稳定 repository contract。

### `studies`

`studies` 用于值得保留、复查或继续推进的研究。每个 retained study 至少清楚记录：

```text
Question
Inputs
Method
Results
Limitations
```

Study-specific input selection、method、plots、findings 与 limitations 留在对应 Study authority，不进入本模块 architecture。Retained study 是 evidence record，不因被保留而成为 Snapshot、Modeling 或 production output 的 semantic authority。

Retained Study 是可保留的研究知识与 evidence record，不等同于长期 software capability。`market-research/studies/<study_package>/` 拥有该 Study 的 Question、Inputs、Method、Results、Limitations、semantic authority 与 retained evidence；`market-research/src/market_research/studies/<study_package>/` 拥有可重写或替换的 executable implementation。两侧以同名 `study_package` 对应，public Study ID 按 [Research UI authority](ui/ARCHITECTURE.md) 从 package 名映射。这种分离是有意的长期边界，不要求将 Study authority 迁入 `src`，也不机械复制 `market-snapshot` 的 co-located product authority layout。若研究对象未来形成稳定输入/输出契约、长期 runtime dependency 与 lifecycle，并演化为 production/reusable capability，须先作新的 semantic decision 与 canonical authority update。

Retained Study 可以同时保留 machine-readable result 与 human-readable visualization，例如：

```text
results/
    summary.csv
    observations.parquet
    *.png
    report.md
```

具体文件名、文件数量与图形形式由各 Study 决定；该示例不是统一 artifact schema、强制目录结构或 visualization framework。

当前由多个真实 retained study 共同使用的窄 Research semantic：

- [Empirical Distribution Research Semantics](shared/distribution/ARCHITECTURE.md)
- [IM Basis Research Semantics](shared/im_basis/ARCHITECTURE.md)

当前 retained study 入口：

- [IM Annualized Basis Baseline](studies/im_basis_baseline/ARCHITECTURE.md)
- [IM Basis Forward Return Association](studies/im_basis_forward_return_association/ARCHITECTURE.md)

本模块不预设 Experiment Engine、Study Registry、Research Repository、plugin system、统一 lifecycle 或通用 study schema。只有真实 retained study 需要时才建立最小文件结构。

## 6. Research 与 Modeling

```text
market-research != market-modeling
```

Research 不要求以 Model 为中心，`market-research` 与 `market-modeling` 是独立的 sibling analytical modules。Research implementation 不成为 Modeling 的 runtime dependency，当前也不定义 `market-modeling` 的内部结构、model research、model evaluation 或 production promotion 机制。

Research finding 可以通过以下过程促进未来 Modeling：

```text
Research
    ↓
Evidence
    ↓
Human / Agent Semantic Decision
    ↓
Authority Update
    ↓
Modeling
```

其中 semantic decision 与 authority update 是必要的边界；Research result 不会自动晋升为 production contract 或 Modeling semantics。

## 7. Authority 与维护边界

```text
repository ARCHITECTURE.md
        ↓
market-research/ARCHITECTURE.md
        ├── Research UI authority
        │       ├── configuration contract
        │       └── user command manual
        ├── scratch exploration
        ├── narrow shared Research semantics
        └── retained study materials
                ↓
        required market-snapshot product authority
```

本文件只拥有 Research 的稳定 identity、职责边界、Research UI 与 visualization ownership、依赖方向、scratch / retained-study distinction 与下层 authority 导航。两个或更多真实 Study 共用的窄 Research semantic 可以有独立 canonical owner，但不得借此建立通用 feature、statistics 或 visualization framework。具体研究问题、输入、方法、结果与限制由对应 retained study 记录；Snapshot 产品语义继续由 [market-snapshot capability catalog](../market-snapshot/CAPABILITIES.md) 所链接的 canonical owner 定义。

只有在 Research 模块定位、UI/visualization ownership、跨模块依赖、Snapshot 消费原则或 scratch/studies 边界变化时更新本文件。CLI/config/output 细节进入 UI specialized authority；不得把 study-specific 细节堆入 module-level architecture，也不得复制 Snapshot product authority。
