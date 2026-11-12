# hg-market-state-lab 仓库架构 authority

本文件是 repository-level architecture authority，只定义仓库定位、顶层模块、模块职责边界、repository-level Python runtime ownership、顶层数据流及下层 authority 入口。产品契约、公式、HTTP DTO、workflow 与实现状态不属于本文件。

## Naming and transition authority

Top-level business and interaction modules belong to three families: `data_*` owns data acquisition, persistence, deterministic preparation and data products; `market_*` owns research, statistical analysis, market-state modeling and strategy backtesting; `ui_*` owns CLI, HTTP and Web interaction/transport boundaries. A family grants no additional import permission and does not merge bounded modules.

Owning module directories use `snake_case`; Python namespaces match their owning module where possible. This table is the canonical mapping. Names already aligned remain unchanged; `ui_web` remains an npm project without a Python namespace. Internal co-location and Product / Dataset / Provider identities remain unchanged.

| Canonical directory | Python namespace |
| --- | --- |
| `data_lake/` | `data_lake` |
| `data_snapshot/` | `data_snapshot` |
| `market_research/` | `market_research` |
| `market_backtesting/` | `market_backtesting` |
| `market_statistics/` | `market_statistics` |
| `market_modeling/` | Reserved; no package or module authority yet |
| `ui_cli/` | `ui_cli` (executable `lab`) |
| `ui_http/` | `ui_http` |
| `ui_web/` | Not applicable; npm project |

These identities are the canonical filesystem and import paths. Historical names are not supported import surfaces. Internal co-location and public business contracts are unchanged.

All local running data, including SQLite caches, Raw Artifacts and any explicitly defined Research runtime outputs, is disposable runtime state. Each module directly uses its canonical runtime paths; historical directories and their contents must not affect current execution. Directory changes require no state migration, inheritance, compatibility or preservation mechanism. Repository tooling neither copies nor deletes historical local state. Credentials and repository runtime configuration are configured afresh through the current environment or the repository-root `.env` (tracked template `.env.example`); historical tokens are not migrated and credentials never enter Git. This filesystem policy does not relax Dataset cache compatibility/integrity or Product Raw contracts. The Research clean-slate reset retires its previous Observation persistence and Study output lifecycle; its current module authority defines the replacement boundary.

The root Python project/distribution remains `hg-market-state-lab`, with one root Poetry environment, dependency graph and worktree-local root `.venv`. Naming changes do not alter business functions, data meaning, Product identity, application services, request/result, formulas, completeness or failure semantics. `lab` remains the executable even after its owning module/package becomes `ui_cli`.

Data Snapshot directly succeeds Market Snapshot as an independent bounded module; naming does not transfer its Product, Capture, Preparation, persisted Raw or shared capabilities into DataLake. DataLake V1 remains frozen. Experimental Source validation is isolated under `data_lake/experiments/`, with no stable consumer dependency; the narrow contract is [Experiments authority](data_lake/EXPERIMENTS.md).

Stable dependencies continue to follow published boundaries: `ui_cli` delegates to owning modules; `ui_http` consumes owning module public application/product boundaries; `ui_web` consumes the published HTTP/OpenAPI contract. Business modules do not depend on these inbound adapters. Research consumes only authorized Dataset / Snapshot public contracts for market inputs, with detailed caller permissions in its UPSTREAM authority, and the independent Statistics public numerical contract for statistics. DataLake / Snapshot / Statistics / Modeling do not depend on Research; Statistics also does not depend on DataLake or Snapshot. Snapshot may consume explicitly authorized Dataset public services, never internals. Modeling remains a sibling of Research with no new internal design or import permissions inferred from renaming.

`market_backtesting` consumes DataLake public Application Services and the published pure Slot-resolution boundary of `market_research`, exactly as authorized by its case Inputs authority. It consumes no other Research semantics: not Observations, Sample Conversion, Statistics adaptation, Job/Batch execution, reports, evidence, Publication, Preflight or online runs. Research does not depend on Backtesting; DataLake / Snapshot / Research / Statistics / Modeling do not depend on Backtesting. `ui_http` may consume Backtesting's public application boundary only, and `ui_web` consumes the published HTTP/OpenAPI contract. Backtesting does not use or authorize `market_modeling`.

## 1. 仓库定位

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、策略回测、市场状态建模与结果展示的实验性系统。

## 2. 顶层模块

### `data_lake`

持久缓存并管理来自外部 Source 的 reusable source facts。DataLake 是自治 DataSet 的宿主 bounded context，拥有公共 invariants 与 shared kernel；每个 DataSet 是自治的数据产品边界，拥有自己的 authority、implementation、tests 与 source-fact persistence / cache。模块内部边界见 [data_lake/ARCHITECTURE.md](data_lake/ARCHITECTURE.md)。

DataLake 不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI。`data_snapshot` 继续拥有 Product-specific source scope、Capture orchestration、Preparation、analysis-ready result 及产品已声明的 persisted Raw Artifact；新增 DataLake 不转移这些所有权。DataSet 对外发布 public Application Service，consumer 通过 semantic request/result/view 消费，不直接访问 SQLite、Repository 或 Source adapter，也不通过 CLI 或反向解析 JSON export 获取 Python semantic result。稳定方向为 consumer → DataSet public Application Service → internal Source adapter / Repository；`lab` 的 delivery contract 见其 authority，Research consumer 权限与 capability selection 进入 [Research upstream authority](market_research/UPSTREAM.md)，具体 integration implementation 遵循已发布 boundary。

### `data_snapshot`

从外部市场数据 Source 捕捉事实，按明确数据需求进行确定性准备，并产出 analysis-ready artifacts。

职责终点是 Analysis-ready Artifact；它不负责市场状态解释、regime classification、概率判断、交易建议或 UI 展示。模块内部边界见 [data_snapshot/ARCHITECTURE.md](data_snapshot/ARCHITECTURE.md)。

### `market_modeling`

消费 analysis-ready market artifacts，负责未来明确进入本模块的市场状态建模与状态表达。

该模块尚未形成独立 authority；在出现明确需求前，不预先设计模型框架、状态 schema、信号系统、训练框架、回测或策略抽象。

### `market_research`

独立的 exploratory / statistical research bounded module，消费授权的 DataLake public facts、Snapshot analysis-ready artifacts 与 Statistics public numerical capability，拥有市场指标、empirical observations、Sample Converter、Research Executor、统计结果的业务关联与 research evidence / interpretation。Descriptive 与 Conditional 是独立演化的范式，当前只细化 Descriptive；Research 不拥有 UI presentation 或通用数值统计公式。

Research result 是 evidence / finding，不是 production market-state output。模块内部边界见 [market_research/ARCHITECTURE.md](market_research/ARCHITECTURE.md)。

### `market_backtesting`

独立的策略回测业务模块，拥有固定 strategy definition、真实合约持仓模拟、PnL 与基准核算、回测结果/证据/可视化投影，以及 case-specific read-only readiness 与 online execution。首期包含 strategy-independent Position-Driven Core V1 与唯一 case `futures_roll_long_v1`；不建立 order-driven trading framework、plugin/registry、multi-strategy framework 或未来策略 scaffold。

它的 W2 case adapter 消费 DataLake public Application Services 与 Research 已发布的 pure Slot-resolution public boundary；Core 不依赖这两个上游模块。它不拥有市场数据获取、Slot formula、Research observation/report/statistics、generic Visualization schema、HTTP DTO、Auth 或 UI。当前交付状态与剩余工作由模块 Roadmap 拥有。模块边界、case 语义与导航从 [market_backtesting/ARCHITECTURE.md](market_backtesting/ARCHITECTURE.md) 进入。

### `market_statistics`

独立、业务无关的 contract-driven 数值统计 bounded module，拥有 statistical sample legality、统计方法参数、计算契约、typed results、统计失败语义及 numerical backend result validation；当前包含 Quantile、IntervalCount 与 Mean。它不理解市场标的、金融公式、Research ObservationSet / Job / Batch，也不获取市场数据。Research 仅通过其 public Python semantic boundary 消费统计能力；Statistics 不依赖 Research、DataLake、Snapshot、Modeling 或 inbound UI，该 boundary 不表示 HTTP 服务。

独立 Python 数值 API 由根项目安装。模块边界与公共数值契约入口见 [market_statistics/ARCHITECTURE.md](market_statistics/ARCHITECTURE.md)。

### `ui_cli`

Repository-level CLI/operator interface for command parsing, routing, operational orchestration, delegation and declared delivery. It owns no business semantics. The executable remains `lab`; its Python package is `ui_cli`. Command hierarchy, arguments and exit codes remain owned by [CLI authority](ui_cli/ARCHITECTURE.md).

### `ui_http`

Repository-wide inbound HTTP delivery adapter 与 HTTP composition root，负责把各 owning module 的 application/product boundary 暴露为 HTTP。

它拥有 FastAPI application/route composition、request parsing、transport validation、HTTP DTO projection、serialization、HTTP error/status mapping、OpenAPI publication 与 HTTP runtime concerns；不拥有业务 query/command/result、semantic failure classification、产品可用性、市场语义或建模语义。模块内部边界见 [ui_http/ARCHITECTURE.md](ui_http/ARCHITECTURE.md)。

Repository HTTP access 的技术身份、认证存储与访问控制由 `ui_http` 拥有，契约从其 module authority 进入；`ui_cli` 通过公开 Auth service 委托 Operator 审批，`ui_web` 拥有 application-level 认证交互。该边界不授予业务模块反向依赖 `ui_http` 的权限。

### Visualization (logical capability)

Visualization is domain-agnostic and initially a logical capability, not a new top-level
module. Its cross-language Layer, View and Template semantic contract is
[Visualization authority](ui_web/VISUALIZATION.md); producers conform without importing
frontend code. Research owns [publication](market_research/PUBLICATION.md) and its
producer-aware adaptation. HTTP owns transport, and `ui_web` owns rendering.

### `ui_web`

展示并允许用户交互仓库产生的数据产品与市场状态结果。它不拥有 Source、Capture、业务计算或 market_modeling 语义。模块内部边界见 [ui_web/ARCHITECTURE.md](ui_web/ARCHITECTURE.md)。

## 3. Python Runtime 与 Module Boundary

Python runtime ownership is repository-level; semantic and package ownership remains module-level.

仓库只拥有一个 canonical Python project/toolchain、一个 dependency graph 与一个 dependency-resolution boundary。Canonical layout 为：

```text
Repository
    pyproject.toml
    poetry.lock
    poetry.toml
    .env / .env.example    # local configuration / tracked template
    .venv/                 # worktree-local; the only Python environment

    config/                # repository-level configuration support (lab_config)
    data_lake/             # data_lake
    data_snapshot/         # data_snapshot
    market_modeling/       # market_modeling; no new implementation implied
    market_research/       # market_research
    market_backtesting/    # market_backtesting; module-owned Python package
    market_statistics/     # market_statistics
    ui_cli/                # ui_cli; executable remains lab
    ui_http/               # ui_http
    ui_web/                # npm project; no Python namespace
```

根 `pyproject.toml`、根 `poetry.lock` 与每个 worktree 的根 `.venv` 是唯一 canonical Python runtime surface。Module-local `pyproject.toml`、module-local `poetry.lock`、module-local `.venv`、Poetry editable/path dependency，以及分别进入 Python module 目录执行 Poetry workflow 均不属于目标 architecture。

Repository runtime configuration 属于 repository-level support，不是业务模块。根 `.env` 是唯一 canonical local configuration file，根 `.env.example` 是其 tracked template；`config/src/lab_config` 拥有 repository environment configuration 的加载与校验，稳定优先级为 `process environment > root .env > defaults`。`lab_config` 可被各模块通过 public API 使用，但本身不得 import 任何业务模块，也不拥有 Auth、Tushare、Dataset、Product 或 HTTP semantics；`TUSHARE_TOKEN`、`TUSHARE_CALLS_PER_MINUTE`、`LAB_AUTH_*` 与 `LAB_RESEARCH_PUBLICATION_ROOT` 只经该 package 读取。Module-local `.env` 与各模块独立 env loader 不属于目标 architecture。

`data_lake` 拥有 canonical Python namespace `data_lake`；shared kernel 源码归顶层 `data_lake/src/`，具体 Provider 与 Dataset 的 authority、source、tests 分别 colocate 于 `data_lake/providers/<provider-id>/` 与 `data_lake/datasets/<dataset-id>/`，persistent state 仍由 Dataset 拥有，topology 由 [DataLake authority](data_lake/ARCHITECTURE.md) 拥有。Provider-local / Dataset-local source roots 同样使用 repository root 唯一 Python project、dependency graph 与根 `.venv`，不创建独立 Python runtime。Consumer 可以直接依赖具体 Dataset public Application Service；shared kernel 不依赖具体 Provider 或 Dataset，Dataset 间只允许 DataLake authority 明确声明的单向 public Application Service dependency，不开放 internal persistence。Public boundary 与 source registration / import compatibility 约束进入 DataLake authority。

Runtime unification 不合并模块、不改变源码目录 ownership，也不把所有 Python source 移入统一 `src/`。`data_lake`、`data_snapshot`、`market_modeling`、`market_research`、`ui_cli` 与 `ui_http` 是独立 namespace，由各自 semantic module 拥有。`market_statistics` 同样拥有独立 namespace 与 module-owned source root，由根项目统一安装。`market_backtesting` 同样拥有独立 namespace 与 module-owned source root，由根项目统一安装。

共享 dependency graph 或 `.venv` 不构成 cross-module import permission。模块依赖方向必须由 repository/module authority、被依赖模块发布的 public boundary 与 architecture tests 共同约束；不得因为 package 在同一环境中可 import 就绕过这些边界。

这里的 Python runtime/toolchain ownership 不改变 `ui_http` 对 HTTP application/launcher/runtime composition 的所有权，也不改变任何现有 analytical flow、Product contract 或 presentation responsibility。

## 4. 顶层 Flow 与 HTTP Topology

### 业务 / analytical flow

```text
External Market Sources
        ├──→ data_lake ───→ Public Dataset Facts ───→ market_research
        │                         │                         │
        │                         └──→ data_snapshot        └──→ Empirical Observations / Evidence
        │                                  ↑
        └──────────────────────────────────┘
                                           ↓
                                Analysis-ready Artifacts
                                   ├──→ market_research
                                   └──→ market_modeling ───→ Market-state Outputs
```

该图表达业务职责与 analytical data flow，不强制 runtime deployment topology 或 package import dependency。Dataset Facts → Snapshot 仅指明确授权的 public service consumption，不强制替换 Snapshot Capture；Research 的具体 producer 权限见 UPSTREAM。`market_research` 与 `market_modeling` 是 sibling analytical modules；Research 不是 Modeling pipeline 的强制 stage。`data_snapshot` 的产物也可以被仓库外的 analyzer 直接消费。

```text
data_lake public facts ───→ market_backtesting ───→ Backtest Results / Evidence
                                    ↑
market_research public pure Slot resolution boundary
```

`market_backtesting` 是独立 sibling analytical module，不是 Research pipeline stage，也不是 Modeling 子模块。它通过 DataLake public Application Service 获取 Calendar / Futures / Index facts，并通过 W1 case Inputs 明确授权的 symbol-level public boundary 复用 pure Slot resolution，不复制第二份算法。它不读取 Research Observation/Report、不调用 Statistics、不建立第二套行情缓存或 Provider；UI 只能经其 public application/HTTP boundary 消费结果。

`market_research` 通过 `data_snapshot` 明确支持的 public application/product boundary 消费 analysis-ready result，也可通过 DataLake public Application Service 消费 source facts；不依赖 Source Capture、Raw Artifact、product-private Preparation、upstream persistence、Dataset / Snapshot SQLite、`ui_http`、FastAPI 或 HTTP DTO。Research 内部 composition 由其 module authority 拥有，upstream producer 权限与 selection 见 [Research upstream authority](market_research/UPSTREAM.md)，具体 integration implementation 遵循该 contract。`data_lake`、`data_snapshot`、`market_statistics` 与 `market_modeling` 不得依赖 `market_research`。

Research 与 Statistics 的依赖方向如下；这是 semantic boundary，实际 readiness 见 [Research Acceptance](market_research/descriptive/ACCEPTANCE.md)：

```text
market_research
    ├──→ data_lake public API
    ├──→ data_snapshot public API (only as authorized by Research UPSTREAM)
    └──→ market_statistics public API
```

Research 构造市场观察、转换数值样本并关联返回的统计结果；Statistics 只计算数值统计，不反向获取市场事实或依赖 Research。具体转换与执行契约从 Research module authority 进入，不在根层重复定义。

Research finding 可以经以下语义决策路径促进未来 Modeling，但该路径不是 runtime dependency，也不定义 promotion framework：

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

### HTTP delivery topology

```text
data_snapshot ───────┐
                     │
market_modeling ─────┼──→ ui_http ───→ ui_web
market_backtesting ──┤   (W2 application boundary; HTTP contract in WP6)
future modules ──────┘
```

`ui_http` 是 inbound delivery boundary，不是 analytical pipeline stage。稳定依赖方向是 `ui_http` 依赖 owning module 的 public application/product boundary；`data_snapshot`、`market_research`、`market_statistics`、`market_backtesting` 与 `market_modeling` 不得依赖 `ui_http`，也不得用 FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types 定义自己的 semantic model。Research publishes Python analytical boundaries; bounded HTTP delivery belongs to `ui_http` through [its catalog](ui_http/HTTP_PRODUCTS.md), never to a Research server. Statistics 已发布独立的 public Python numerical API，不提供 HTTP 发布。Backtesting 的首个 HTTP product 与 catalog entry 由 W2 WP6 建立；不以 authority 声明代替实际 contract 发布。

## 5. Authority 导航

`workbench/` is a repository-root, agent-facing operational contract and shared
execution-evidence facility, outside the `data_*`, `market_*` and `ui_*` module
taxonomy. It is not a business module or Agent Runtime. Start at
[Workbench agent entry](workbench/AGENTS.md) and [Workbench authority](workbench/ARCHITECTURE.md);
its scripts use the existing root Python runtime without a new package or `lab` command.
Task-specific permission never expands a business module's published boundary.

Repository runtime configuration support is documented from [config Agent Rules](config/AGENTS.md)
and anchored by the root `.env` / `.env.example` files described in section 3. It is not a
business module and grants no business or cross-module import permission.

`hg-market-state-lab` 是 repository / system identity；`lab` 是安装于根 canonical Python project 的正式 repository-level CLI/operator interface。它只负责 repository-level command routing、orchestration、delegation 与已声明的 delivery，不是业务模块，也不拥有 DataSet、Snapshot、Research、Modeling、HTTP product 或 frontend 语义。其命令与转发边界见 [lab CLI authority](ui_cli/ARCHITECTURE.md)；当前本地操作方式见 [DEVELOPMENT.md](DEVELOPMENT.md)。

```text
AGENTS.md
    ↓
ARCHITECTURE.md（本文件）
    ├─ Python runtime/toolchain invariant
    │      ↓
    │  DEVELOPMENT.md
    ├─ ui_cli/ARCHITECTURE.md
    ├─ data_lake/ARCHITECTURE.md
    │      ├─ data_lake/DOMAIN_MODEL.md
    │      ├─ data_lake/APPLICATION.md
    │      ├─ data_lake/PORTS.md
    │      ├─ data_lake/COMPOSITION.md
    │      ├─ co-located Provider ARCHITECTURE.md
    │      ↓
    │  data_lake/DATASETS.md
    │      ↓
    │  co-located Dataset ARCHITECTURE.md
    ├─ data_snapshot/ARCHITECTURE.md
    │      ↓
    │  data_snapshot/CAPABILITIES.md
    │      ↓
    │  co-located product / capability ARCHITECTURE.md
    ├─ market_research/ARCHITECTURE.md
    │      ↓
    │  market_research/PUBLICATION.md
    ├─ market_backtesting/ARCHITECTURE.md
    │      ├─ market_backtesting/core/ARCHITECTURE.md
    │      ↓
    │  market_backtesting/cases/futures_roll_long/ARCHITECTURE.md
    │      ├─ STRATEGY.md
    │      ├─ PERFORMANCE.md
    │      ├─ INPUTS.md
    │      ├─ RESULT.md
    │      ├─ EVIDENCE.md
    │      ├─ ONLINE_APPLICATION.md
    │      └─ ROADMAP.md
    ├─ market_statistics/ARCHITECTURE.md
    │      ↓
    │  market_statistics/CONTRACT.md
    ├─ ui_http/ARCHITECTURE.md
    │      ↓
    │  ui_http/HTTP_PRODUCTS.md
    │      ↓
    │  HTTP product contract
    │
    └─ ui_web/ARCHITECTURE.md
           ├─ ui_web/VISUALIZATION.md (cross-language Layer contract)
           ├─ ui_web/application.md
           │      ↓
           │  ui_web/FEATURES.md
           │      ↓
           │  co-located feature ARCHITECTURE.md
           │
           └─ ui_web/contracts.md
```

CLI 语义从本文档进入 `ui_cli/ARCHITECTURE.md`；Python dependency resolution 与当前本地操作进入 `DEVELOPMENT.md`；业务语义仍进入对应 owning module。`market_modeling` 当前没有下层 authority，不得从 runtime layout、Research authority 或 Backtesting authority 推导其内部设计。`market_backtesting` 的 Core 与 case/policy/performance/result/online 语义从其 module authority 进入；authority 不等于 runtime readiness，当前状态由模块 Roadmap 记录。

上层只提供选择下一份文档所需的上下文，不复制下层语义。新增或删除单个产品通常只更新模块 catalog，不改变本文档。

## 6. 维护边界

仅在顶层模块、模块职责边界、repository-level Python runtime/CLI ownership、顶层数据流或下层 authority 入口变化时更新本文件。CLI 命令细节由 `ui_cli/ARCHITECTURE.md` 拥有；模块内部架构、产品契约、字段、公式、HTTP 行为和 UI 语义由对应下层 authority 拥有。
