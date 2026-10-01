# DataLake 模块架构 authority

本文件是 DataLake 的稳定模块入口，只定义职责、ownership、关键模块 invariant、public boundary、依赖方向与 authority 导航。仓库级职责与 Python runtime invariant 见 [repository architecture](../ARCHITECTURE.md)；专题语义按任务从下方导航选择，不要求加载全部公共或 Dataset authority。

## 1. Ownership 与 persistence boundary

DataLake 持久缓存并管理来自外部 Source 的 reusable source facts。它不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI，也不接管 Snapshot 产品已声明的 Raw Artifact。Public service 的发布不自动建立 Research/Snapshot runtime integration；这些 consumer 的接入须独立设计。

```text
DataLake
    └── DataSet 1..n
            └── exactly one owned SQLite
```

DataSet 是独立的数据与 persistence ownership boundary；canonical Dataset identity 由其 authority 声明。一个 DataSet exactly owns 一个 SQLite database，固定 cardinality 为 `1 DataSet : 1 SQLite`。禁止多个 DataSet 共用 SQLite、一个 DataSet 跨多个 SQLite、cross-Dataset foreign key、DataLake global database 与 global instrument master。

不同 DataSet 必须能够独立存在、独立 refresh、独立删除或重建。这不定义 refresh policy。同一 instrument 可以分别存在于多个 DataSet 自己的 instrument catalog 中；不得据此合并 persistence ownership。Storage resolution 的公共调用约束见 [APPLICATION.md](APPLICATION.md)。

这里的 `DataSet` 是 DataLake ownership 概念，不改写 Snapshot 中可能作为产品名称使用的 `Dataset`，也不授权读取或迁移产品私有 Raw。

## 2. 领域关系与 public boundary

DataSet 内部以 Scope + transient Window 确定希望覆盖的 FetchUnits；FetchUnit 拥有 Records 与 coverage state，Source adapter 获取外部事实，Repository 管理 owned SQLite。公共领域与 persistence 细节由 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 拥有。

DataSet 对外发布 public Python Application Service，consumer 通过 semantic request/result/view 使用 `coverage`、`ensure`、`export`；详细 operation contract 由 [APPLICATION.md](APPLICATION.md) 拥有。稳定依赖方向为：

```text
Consumers (lab CLI / future Research / future Snapshot / future consumers)
    ↓
DataSet public Application Service
    ├─ Source Adapter → external API
    └─ Repository → owned SQLite
```

## 3. Canonical Python boundary

Canonical Python namespace 为 `data_lake`，源码 ownership 位于 `data-lake/src/data_lake/`。遵守 repository root 唯一 Python project、dependency graph 与 worktree-local 根 `.venv` invariant，不创建 module-local Python project。公开 consumer 只进入 DataSet public Application Service；Repository、SQLite adapter 与 Source adapter 是 internal implementation surface，具体内部文件拆分留给 implementation。

## 4. Authority 导航

| 当前任务 | 下一份 authority |
| --- | --- |
| Domain / persistence / Scope / Window / FetchUnit / Records / mutation flow | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Application Service / coverage / ensure / export / public result / runtime 调用约束 | [APPLICATION.md](APPLICATION.md) |
| 具体 Dataset 的 Source、identity、fields、completeness、request/view 或 CLI semantic arguments | [DATASETS.md](DATASETS.md) → owning Dataset authority |
| CLI topology / delegation / serialization / file delivery | [lab authority](../lab/ARCHITECTURE.md) |

Dataset authority 只能在模块边界及相关公共 domain/application invariant 内 specialize 或 constrain；catalog 只提供导航，不拥有 schema。具体 Dataset 任务读取与任务有关的公共 authority 和 owning Dataset authority，不默认加载 sibling Dataset。

## 5. Deferred design

本次变更仅编码 authority，不实现 Python、SQLite DDL、migration、Tushare client、CLI 或 HTTP。后续 implementation 必须实现已声明的 public contract；内部文件、具体存储类型、key serialization、canonicalization/hash、事务机制、失败恢复与 adapter batching 留给 implementation design，不得重新决定已固定的 semantic request、结果计数或 export contract。Research/Snapshot integration 须独立设计。

Refresh / force / invalidation policy、TTL、stale state、多维 Window、Dataset dependency graph、cross-Dataset query engine、Source request audit table、plugin framework 与 generic workflow engine 均不在本轮设计范围内。
