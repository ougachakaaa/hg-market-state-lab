# hg-market-state-lab 仓库架构 authority

本文件是 repository-level architecture authority，只定义仓库定位、顶层模块、模块职责边界、repository-level Python runtime ownership、顶层数据流及下层 authority 入口。产品契约、公式、HTTP DTO、workflow 与实现状态不属于本文件。

## 1. 仓库定位

`hg-market-state-lab` 是用于市场状态数据准备、探索研究、市场状态建模与结果展示的实验性系统。

## 2. 顶层模块

### `market-snapshot`

从外部市场数据 Source 捕捉事实，按明确数据需求进行确定性准备，并产出 analysis-ready artifacts。

职责终点是 Analysis-ready Artifact；它不负责市场状态解释、regime classification、概率判断、交易建议或 UI 展示。模块内部边界见 [market-snapshot/ARCHITECTURE.md](market-snapshot/ARCHITECTURE.md)。

### `market-modeling`

消费 analysis-ready market artifacts，负责未来明确进入本模块的市场状态建模与状态表达。

该模块尚未形成独立 authority；在出现明确需求前，不预先设计模型框架、状态 schema、信号系统、训练框架、回测或策略抽象。

### `market-research`

独立的 exploratory / statistical research bounded module，消费 analysis-ready market artifacts，负责开放探索、统计分析、可视化、假设发现与值得保留的研究。

Research result 是 evidence / finding，不是 production market-state output。模块内部边界见 [market-research/ARCHITECTURE.md](market-research/ARCHITECTURE.md)。

### `backend-api`

Repository-wide inbound HTTP delivery adapter 与 HTTP composition root，负责把各 owning module 的 application/product boundary 暴露为 HTTP。

它拥有 FastAPI application/route composition、request parsing、transport validation、HTTP DTO projection、serialization、HTTP error/status mapping、OpenAPI publication 与 HTTP runtime concerns；不拥有业务 query/command/result、semantic failure classification、产品可用性、市场语义或建模语义。模块内部边界见 [backend-api/ARCHITECTURE.md](backend-api/ARCHITECTURE.md)。

### `web-ui`

展示并允许用户交互仓库产生的数据产品与市场状态结果。它不拥有 Source、Capture、业务计算或 market-modeling 语义。模块内部边界见 [web-ui/ARCHITECTURE.md](web-ui/ARCHITECTURE.md)。

## 3. Python Runtime 与 Module Boundary

Python runtime ownership is repository-level; semantic and package ownership remains module-level.

仓库只拥有一个 canonical Python project/toolchain、一个 dependency graph 与一个 dependency-resolution boundary。目标状态固定为：

```text
Repository
    pyproject.toml
    poetry.lock
    .venv/                 # worktree-local

    market-snapshot/       # market_snapshot
    market-modeling/       # market_modeling
    market-research/       # market_research
    backend-api/           # backend_api
```

根 `pyproject.toml`、根 `poetry.lock` 与每个 worktree 的根 `.venv` 是唯一 canonical Python runtime surface。Module-local `pyproject.toml`、module-local `poetry.lock`、module-local `.venv`、Poetry editable/path dependency，以及分别进入 Python module 目录执行 Poetry workflow 均不属于目标 architecture。

Runtime unification 不合并模块、不改变源码目录 ownership，也不把所有 Python source 移入统一 `src/`。`market_snapshot`、`market_modeling`、`market_research` 与 `backend_api` 是独立 namespace，由各自 semantic module 拥有。

共享 dependency graph 或 `.venv` 不构成 cross-module import permission。模块依赖方向必须由 repository/module authority、被依赖模块发布的 public boundary 与 architecture tests 共同约束；不得因为 package 在同一环境中可 import 就绕过这些边界。

这里的 Python runtime/toolchain ownership 不改变 `backend-api` 对 HTTP application/launcher/runtime composition 的所有权，也不改变任何现有 analytical flow、Product contract 或 presentation responsibility。

## 4. 顶层 Flow 与 HTTP Topology

### 业务 / analytical flow

```text
External Market Sources
        ↓
market-snapshot
        ↓
Analysis-ready Artifacts
        ├──→ market-research ───→ Exploratory Studies / Evidence
        │
        └──→ market-modeling ───→ Market-state Outputs
```

该图表达业务职责与 analytical data flow，不强制 runtime deployment topology 或 package import dependency。`market-research` 与 `market-modeling` 是 sibling analytical modules；Research 不是 Modeling pipeline 的强制 stage。`market-snapshot` 的产物也可以被仓库外的 analyzer 直接消费。

`market-research` 只通过 `market-snapshot` 明确支持的 public application/product boundary 消费 analysis-ready result，不依赖 Source Capture、Raw Artifact、product-private Preparation、persistence layout、`backend-api`、FastAPI 或 HTTP DTO。`market-snapshot` 与 `market-modeling` 不得依赖 `market-research`。

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
market-snapshot ─────┐
                     │
market-modeling ─────┼──→ backend-api ───→ web-ui
                     │
future modules ──────┘
```

`backend-api` 是 inbound delivery boundary，不是 analytical pipeline stage。稳定依赖方向是 `backend-api` 依赖 owning module 的 public application/product boundary；`market-snapshot`、`market-research` 与 `market-modeling` 不得依赖 `backend-api`，也不得用 FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types 定义自己的 semantic model。当前 `market-research` 不提供 research service/API。

## 5. Authority 导航

`hg-market-state-lab` 是 repository / system identity；`lab` 是安装于根 canonical Python project 的正式 repository-level CLI/operator interface。它只负责 repository-level command routing、orchestration 与 delegation，不是业务模块，也不拥有 Snapshot、Research、Modeling、HTTP product 或 frontend 语义。其命令与转发边界见 [lab CLI authority](lab/ARCHITECTURE.md)；当前本地操作方式见 [DEVELOPMENT.md](DEVELOPMENT.md)。

```text
AGENTS.md
    ↓
ARCHITECTURE.md（本文件）
    ├─ Python runtime/toolchain invariant
    │      ↓
    │  DEVELOPMENT.md
    ├─ lab/ARCHITECTURE.md
    ├─ market-snapshot/ARCHITECTURE.md
    │      ↓
    │  market-snapshot/CAPABILITIES.md
    │      ↓
    │  co-located product / capability ARCHITECTURE.md
    ├─ market-research/ARCHITECTURE.md
    ├─ backend-api/ARCHITECTURE.md
    │      ↓
    │  backend-api/HTTP_PRODUCTS.md
    │      ↓
    │  HTTP product contract
    │
    └─ web-ui/ARCHITECTURE.md
           ├─ web-ui/application.md
           │      ↓
           │  web-ui/FEATURES.md
           │      ↓
           │  co-located feature ARCHITECTURE.md
           │
           └─ web-ui/contracts.md
```

CLI 语义从本文档进入 `lab/ARCHITECTURE.md`；Python dependency resolution 与当前本地操作进入 `DEVELOPMENT.md`；业务语义仍进入对应 owning module。`market-modeling` 当前没有下层 authority，不得从 runtime layout 或 Research authority 推导其内部设计。

上层只提供选择下一份文档所需的上下文，不复制下层语义。新增或删除单个产品通常只更新模块 catalog，不改变本文档。

## 6. 维护边界

仅在顶层模块、模块职责边界、repository-level Python runtime/CLI ownership、顶层数据流或下层 authority 入口变化时更新本文件。CLI 命令细节由 `lab/ARCHITECTURE.md` 拥有；模块内部架构、产品契约、字段、公式、HTTP 行为和 UI 语义由对应下层 authority 拥有。
