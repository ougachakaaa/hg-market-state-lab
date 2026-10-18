# hg-market-state-lab 仓库架构 authority

本文件是 repository-level architecture authority，只定义仓库定位、顶层模块、模块职责边界、repository-level Python runtime ownership、顶层数据流及下层 authority 入口。产品契约、公式、HTTP DTO、workflow 与实现状态不属于本文件。

## Naming and transition authority

Top-level business and interaction modules belong to three families: `data_*` owns data acquisition, persistence, deterministic preparation and data products; `market_*` owns research, statistical analysis and market-state modeling; `ui_*` owns CLI, HTTP and Web interaction/transport boundaries. A family grants no additional import permission and does not merge bounded modules.

Owning module directories use `snake_case`; Python namespaces match their owning module where possible. This table is the canonical mapping. Names already aligned remain unchanged; `ui_web` remains an npm project without a Python namespace. Internal co-location and Product / Dataset / Provider identities remain unchanged.

| Canonical directory | Python namespace |
| --- | --- |
| `data_lake/` | `data_lake` |
| `data_snapshot/` | `data_snapshot` |
| `market_research/` | `market_research` |
| `market_modeling/` | Reserved; no package or module authority yet |
| `ui_cli/` | `ui_cli` (executable `lab`) |
| `ui_http/` | `ui_http` |
| `ui_web/` | Not applicable; npm project |

These identities are the canonical filesystem and import paths. Historical names are not supported import surfaces. Internal co-location and public business contracts are unchanged.

All local running data, including SQLite caches, Raw Artifacts, Observation persistence and Research Outputs, is disposable runtime state. Each module directly uses its canonical runtime paths; historical directories and their contents must not affect current execution. Directory changes require no state migration, inheritance, compatibility or preservation mechanism. Repository tooling neither copies nor deletes historical local state. Credentials are configured afresh through the current environment or canonical `.env`; historical tokens are not migrated and credentials never enter Git. This filesystem policy does not relax Dataset cache compatibility/integrity, Product Raw contracts, Observation atomic publication/durable reuse, or Study output collision/replacement rules within canonical storage.

The root Python project/distribution remains `hg-market-state-lab`, with one root Poetry environment, dependency graph and worktree-local root `.venv`. Naming changes do not alter business functions, data meaning, Product identity, application services, request/result, formulas, completeness or failure semantics. `lab` remains the executable even after its owning module/package becomes `ui_cli`.

Data Snapshot directly succeeds Market Snapshot as an independent bounded module; naming does not transfer its Product, Capture, Preparation, persisted Raw or shared capabilities into DataLake. DataLake V1 remains frozen. Experimental Source validation is isolated under `data_lake/experiments/`, with no stable consumer dependency; the narrow contract is [Experiments authority](data_lake/EXPERIMENTS.md).

Stable dependencies continue to follow published boundaries: `ui_cli` delegates to owning modules; `ui_http` consumes owning module public application/product boundaries; `ui_web` consumes the published HTTP/OpenAPI contract. Business modules do not depend on these inbound adapters. Research consumes only authorized Dataset / Snapshot public contracts, with detailed caller permissions in its UPSTREAM authority; DataLake / Snapshot / Modeling do not depend on Research. Snapshot may consume explicitly authorized Dataset public services, never internals. Modeling remains a sibling of Research with no new internal design or import permissions inferred from renaming.

Engineering scope, remaining drift and validation responsibilities are recorded in [Implementation handoff](MODULE_MIGRATION.md); it is not a business authority.

## 1. 仓库定位

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、市场状态建模与结果展示的实验性系统。

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

独立的 exploratory / statistical research bounded module，消费 DataLake public facts 与 Snapshot analysis-ready artifacts，负责开放探索、统计分析、可视化、假设发现与值得保留的研究。

Research result 是 evidence / finding，不是 production market-state output。模块内部边界见 [market_research/ARCHITECTURE.md](market_research/ARCHITECTURE.md)。

### `ui_cli`

Repository-level CLI/operator interface for command parsing, routing, operational orchestration, delegation and declared delivery. It owns no business semantics. The executable remains `lab`; its Python package is `ui_cli`. Command hierarchy, arguments and exit codes remain owned by [CLI authority](ui_cli/ARCHITECTURE.md).

### `ui_http`

Repository-wide inbound HTTP delivery adapter 与 HTTP composition root，负责把各 owning module 的 application/product boundary 暴露为 HTTP。

它拥有 FastAPI application/route composition、request parsing、transport validation、HTTP DTO projection、serialization、HTTP error/status mapping、OpenAPI publication 与 HTTP runtime concerns；不拥有业务 query/command/result、semantic failure classification、产品可用性、市场语义或建模语义。模块内部边界见 [ui_http/ARCHITECTURE.md](ui_http/ARCHITECTURE.md)。

### `ui_web`

展示并允许用户交互仓库产生的数据产品与市场状态结果。它不拥有 Source、Capture、业务计算或 market_modeling 语义。模块内部边界见 [ui_web/ARCHITECTURE.md](ui_web/ARCHITECTURE.md)。

## 3. Python Runtime 与 Module Boundary

Python runtime ownership is repository-level; semantic and package ownership remains module-level.

仓库只拥有一个 canonical Python project/toolchain、一个 dependency graph 与一个 dependency-resolution boundary。目标状态固定为：

```text
Repository
    pyproject.toml
    poetry.lock
    .venv/                 # worktree-local

    data_lake/             # data_lake
    data_snapshot/         # data_snapshot
    market_modeling/       # market_modeling; no new implementation implied
    market_research/       # market_research
    ui_cli/                # ui_cli; executable remains lab
    ui_http/               # ui_http
    ui_web/                # npm project; no Python namespace
```

根 `pyproject.toml`、根 `poetry.lock` 与每个 worktree 的根 `.venv` 是唯一 canonical Python runtime surface。Module-local `pyproject.toml`、module-local `poetry.lock`、module-local `.venv`、Poetry editable/path dependency，以及分别进入 Python module 目录执行 Poetry workflow 均不属于目标 architecture。

`data_lake` 拥有 canonical Python namespace `data_lake`；shared kernel 源码归顶层 `data_lake/src/`，具体 Provider 与 Dataset 的 authority、source、tests 分别 colocate 于 `data_lake/providers/<provider-id>/` 与 `data_lake/datasets/<dataset-id>/`，persistent state 仍由 Dataset 拥有，topology 由 [DataLake authority](data_lake/ARCHITECTURE.md) 拥有。Provider-local / Dataset-local source roots 同样使用 repository root 唯一 Python project、dependency graph 与根 `.venv`，不创建独立 Python runtime。Consumer 可以直接依赖具体 Dataset public Application Service；shared kernel 不依赖具体 Provider 或 Dataset，Dataset 间只允许 DataLake authority 明确声明的单向 public Application Service dependency，不开放 internal persistence。Public boundary 与 source registration / import compatibility 约束进入 DataLake authority。

Runtime unification 不合并模块、不改变源码目录 ownership，也不把所有 Python source 移入统一 `src/`。`data_lake`、`data_snapshot`、`market_modeling`、`market_research`、`ui_cli` 与 `ui_http` 是独立 namespace，由各自 semantic module 拥有。

共享 dependency graph 或 `.venv` 不构成 cross-module import permission。模块依赖方向必须由 repository/module authority、被依赖模块发布的 public boundary 与 architecture tests 共同约束；不得因为 package 在同一环境中可 import 就绕过这些边界。

这里的 Python runtime/toolchain ownership 不改变 `ui_http` 对 HTTP application/launcher/runtime composition 的所有权，也不改变任何现有 analytical flow、Product contract 或 presentation responsibility。

## 4. 顶层 Flow 与 HTTP Topology

### 业务 / analytical flow

```text
External Market Sources
        ↓
data_snapshot
        ↓
Analysis-ready Artifacts
        ├──→ market_research ───→ Exploratory Studies / Evidence
        │
        └──→ market_modeling ───→ Market-state Outputs
```

该图表达业务职责与 analytical data flow，不强制 runtime deployment topology 或 package import dependency。`market_research` 与 `market_modeling` 是 sibling analytical modules；Research 不是 Modeling pipeline 的强制 stage。`data_snapshot` 的产物也可以被仓库外的 analyzer 直接消费。

`market_research` 通过 `data_snapshot` 明确支持的 public application/product boundary 消费 analysis-ready result，也可通过 DataLake public Application Service 消费 source facts；不依赖 Source Capture、Raw Artifact、product-private Preparation、upstream persistence、Dataset / Snapshot SQLite、`ui_http`、FastAPI 或 HTTP DTO。Research 内部 composition 由其 module authority 拥有，upstream producer 权限与 selection 见 [Research upstream authority](market_research/UPSTREAM.md)，具体 integration implementation 遵循该 contract。`data_lake`、`data_snapshot` 与 `market_modeling` 不得依赖 `market_research`。

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
                     │
future modules ──────┘
```

`ui_http` 是 inbound delivery boundary，不是 analytical pipeline stage。稳定依赖方向是 `ui_http` 依赖 owning module 的 public application/product boundary；`data_snapshot`、`market_research` 与 `market_modeling` 不得依赖 `ui_http`，也不得用 FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types 定义自己的 semantic model。当前 `market_research` 不提供 research service/API。

## 5. Authority 导航

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
    ├─ ui_http/ARCHITECTURE.md
    │      ↓
    │  ui_http/HTTP_PRODUCTS.md
    │      ↓
    │  HTTP product contract
    │
    └─ ui_web/ARCHITECTURE.md
           ├─ ui_web/application.md
           │      ↓
           │  ui_web/FEATURES.md
           │      ↓
           │  co-located feature ARCHITECTURE.md
           │
           └─ ui_web/contracts.md
```

CLI 语义从本文档进入 `ui_cli/ARCHITECTURE.md`；Python dependency resolution 与当前本地操作进入 `DEVELOPMENT.md`；业务语义仍进入对应 owning module。`market_modeling` 当前没有下层 authority，不得从 runtime layout 或 Research authority 推导其内部设计。

上层只提供选择下一份文档所需的上下文，不复制下层语义。新增或删除单个产品通常只更新模块 catalog，不改变本文档。

## 6. 维护边界

仅在顶层模块、模块职责边界、repository-level Python runtime/CLI ownership、顶层数据流或下层 authority 入口变化时更新本文件。CLI 命令细节由 `ui_cli/ARCHITECTURE.md` 拥有；模块内部架构、产品契约、字段、公式、HTTP 行为和 UI 语义由对应下层 authority 拥有。
