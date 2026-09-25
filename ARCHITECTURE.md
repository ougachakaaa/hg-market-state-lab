# hg-market-state-lab 仓库架构 authority

本文件是 repository-level architecture authority，只定义仓库定位、顶层模块、模块职责边界、顶层数据流及下层 authority 入口。产品契约、公式、HTTP DTO、workflow 与实现状态不属于本文件。

## 1. 仓库定位

`hg-market-state-lab` 是用于市场状态数据准备、市场状态建模与结果展示的实验性系统。

## 2. 顶层模块

### `market-snapshot`

从外部市场数据 Source 捕捉事实，按明确数据需求进行确定性准备，并产出 analysis-ready artifacts。

职责终点是 Analysis-ready Artifact；它不负责市场状态解释、regime classification、概率判断、交易建议或 UI 展示。模块内部边界见 [market-snapshot/ARCHITECTURE.md](market-snapshot/ARCHITECTURE.md)。

### `market-modeling`

消费 analysis-ready market artifacts，负责未来明确进入本模块的市场状态建模与状态表达。

该模块尚未形成独立 authority；在出现明确需求前，不预先设计模型框架、状态 schema、信号系统、训练框架、回测或策略抽象。

### `backend-api`

Repository-wide inbound HTTP delivery adapter 与 HTTP composition root，负责将各 owning module 的 application/product boundary 暴露为 HTTP。它拥有 FastAPI application/route composition、request parsing、transport validation、HTTP DTO/serialization、error envelope/status projection、OpenAPI publication 与 HTTP runtime/launcher concerns，但不拥有业务 Query/Command/Result/Failure 语义、产品可用性分类或金融与建模语义。模块内部边界见 [backend-api/ARCHITECTURE.md](backend-api/ARCHITECTURE.md)。

### `web-ui`

展示并允许用户交互仓库产生的数据产品与市场状态结果。它不拥有 Source、Capture、业务计算或 market-modeling 语义。模块内部边界见 [web-ui/ARCHITECTURE.md](web-ui/ARCHITECTURE.md)。

## 3. 顶层流程与依赖

### 业务 / analytical flow

```text
External Market Sources
        ↓
market-snapshot
        ↓
Analysis-ready Artifacts
        ↓
market-modeling
        ↓
Market-state Outputs
```

该图表达业务职责与数据流方向，不强制 runtime deployment topology 或 package import dependency。`market-snapshot` 的产物也可以被仓库外的 analyzer 直接消费。

### HTTP delivery topology

```text
market-snapshot ─────┐
                     │
market-modeling ─────┼──→ backend-api ───→ web-ui
                     │
future modules ─────┘
```

`backend-api` 是 inbound delivery boundary，不是 `market-snapshot → market-modeling` analytical pipeline stage。稳定依赖只能从 `backend-api` 指向 owning module 的 public application/product boundary；`market-snapshot` 与 `market-modeling` 不得依赖 FastAPI、HTTP DTO/status/error envelope、OpenAPI 或 frontend types 定义自己的 semantic model。

## 4. Authority 导航

```text
AGENTS.md
    ↓
ARCHITECTURE.md（本文件）
    ├─ market-snapshot/ARCHITECTURE.md
    │      ↓
    │  market-snapshot/CAPABILITIES.md
    │      ↓
    │  co-located product / capability ARCHITECTURE.md
    │
    ├─ backend-api/ARCHITECTURE.md
    │      ↓
    │  backend-api/HTTP_PRODUCTS.md
    │      ↓
    │  product HTTP contract
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

上层只提供选择下一份文档所需的上下文，不复制下层语义。新增或删除单个产品通常只更新模块 catalog，不改变本文件。

## 5. 维护边界

仅在顶层模块、模块职责边界、顶层数据/交付流或下层 authority 入口变化时更新本文件。模块内部架构、产品契约、字段、公式、HTTP 行为和 UI 语义由对应下层 authority 拥有。
