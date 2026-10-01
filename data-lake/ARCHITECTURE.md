# DataLake 模块架构 authority

本文件是 DataLake 的稳定模块入口，只定义职责、ownership、关键模块 invariant、public boundary、依赖方向与 authority 导航。仓库级职责与 Python runtime invariant 见 [repository architecture](../ARCHITECTURE.md)；专题语义按任务从下方导航选择，不要求加载全部公共或 Dataset authority。

## 1. Ownership 与 persistence boundary

DataLake 是多个自治 DataSet 的宿主 bounded context，拥有 DataLake-wide invariants 与 shared kernel；具体 DataSet 持久缓存并管理来自外部 Source 的 reusable source facts。DataLake 不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI，也不接管 Snapshot 产品已声明的 Raw Artifact。Public service 的发布不自动建立 Research/Snapshot runtime integration；这些 consumer 的接入须独立设计。

```text
DataLake
    └── DataSet 1..n
            └── exactly one owned SQLite
```

DataSet 是自治的数据产品边界，拥有自己的 semantic authority、implementation、tests 与 persistent runtime state；canonical Dataset identity 由其 authority 声明。一个 DataSet exactly owns 一个 SQLite database，固定 cardinality 为 `1 DataSet : 1 SQLite`。禁止多个 DataSet 共用 SQLite、一个 DataSet 跨多个 SQLite、cross-Dataset foreign key、DataLake global database 与 global instrument master。

目标 filesystem ownership 为：

```text
data-lake/
├── <DataLake-level authority documents>
├── src/                        # shared kernel implementation
├── tests/                      # shared kernel / module boundary verification
└── datasets/
    └── <dataset-id>/
        ├── <Dataset authority documents>
        ├── src/                # Dataset implementation and composition
        ├── tests/              # Dataset verification
        └── data/<owned sqlite> # Dataset persistent runtime state
```

Colocation 让同一 Dataset 的语义、代码、验证与持久化 state 由同一 bounded context 拥有，避免将 authority 与 implementation 拆成两棵长期 ownership tree。真实 SQLite/runtime state 默认不进入 Git；具体 filename 与目录保留机制属于 implementation concern。此树定义稳定 ownership；当前 source/storage registration 与 legacy state 处理见 [implementation reconciliation](IMPLEMENTATION_RECONCILIATION.md)。

不同 DataSet 的 owned state 必须能够独立存在、独立 refresh、独立删除或重建；public service 的必要事实依赖不合并 storage lifecycle，也不保证 prerequisite 缺失时 operation 仍可执行。这不定义 refresh policy。同一 instrument 可以分别存在于多个 DataSet 自己的 instrument catalog 中；不得据此合并 persistence ownership。Storage resolution 的公共调用约束见 [APPLICATION.md](APPLICATION.md)。

这里的 `DataSet` 是 DataLake ownership 概念，不改写 Snapshot 中可能作为产品名称使用的 `Dataset`，也不授权读取或迁移产品私有 Raw。

## 2. 领域关系与 public boundary

DataSet 内部以 Scope + transient Window 确定希望覆盖的 FetchUnits；FetchUnit 拥有 Records 与 coverage state，Source adapter 获取外部事实，Repository 管理 owned SQLite。公共领域与 persistence 细节由 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 拥有。

每个 DataSet 自己拥有并发布 transport-neutral Public Application Service，作为该 Dataset 的唯一 canonical consumer boundary；Python consumer 直接通过 semantic request/result/view 使用 `coverage`、`ensure`、`export`，CLI / HTTP 只是 adapter，不拥有 Dataset 业务语义。直接消费具体 Dataset public API 是合法依赖，不是穿透 DataLake boundary；DataLake 不要求 consumer 经过 DataLakeService、DatasetManager 或 Registry。详细公共 operation contract 由 [APPLICATION.md](APPLICATION.md) 拥有。稳定依赖方向为：

```text
Consumers (lab CLI / future HTTP API / Research / Snapshot-Preparation / Python consumers)
    ↓
Dataset public Application Service
    ↓
DataLake shared kernel
```

Dataset 内部组合 Source adapter 与 Repository 来访问 external API 和 owned SQLite。Consumer 禁止直接依赖 Dataset Repository internals、Source adapter internals、SQLite schema / connection、Dataset `data/` 文件或内部 FetchUnit / Record persistence identity。

允许 `Dataset → DataLake shared kernel`；禁止 `DataLake shared kernel → specific Dataset`。Dataset 间默认禁止依赖；唯一已声明的 service dependency 为 `tushare_index_daily → tushare_trade_calendar public Application Service`，用于目标交易日展开。Calendar 不反向依赖 Index；Futures / Options 的 underlying index relationship 只表达稳定 semantic identity，不授予 runtime dependency。禁止 cycles、跨 Dataset internal import、共享 SQLite 或跨库事务。公共 dependency 调用与 failure invariant 见 [APPLICATION.md](APPLICATION.md)，具体 prerequisite 见 Index 的 [交易日契约](datasets/tushare_index_daily/TRADING_DAYS.md)。Catalog 不构成 runtime registry。

## 3. Canonical Python boundary

Canonical Python namespace 仍为 `data_lake`。顶层 `data-lake/src/` 只拥有真正跨 Dataset 的 shared kernel：公共 domain primitives / invariants、Scope / Window / FetchUnit / Record 机制、coverage / ensure / export 通用 machinery、共享 persistence machinery、公共 result / error contracts、通用 serialization / hash 及 runtime / storage resolution infrastructure。顶层 `tests/` 验证这些公共能力与模块边界，使用 test-local fake Dataset / Source。

Kernel 不得知道具体 Dataset、provider endpoint、instrument family、Dataset-specific Scope、completeness rule 或 export payload。只因一个具体 Dataset 存在的代码默认归 owning Dataset；其 service composition、Source adapter、领域 specialization 与相关 tests 归 `datasets/<dataset-id>/src/` 和 `tests/`。

Dataset-local source root 不创建独立 Python project、Poetry environment 或 dependency graph；所有 source roots 遵守 repository root 唯一 Python project 与 worktree-local 根 `.venv` invariant。Filesystem ownership 不决定 public import path，已有 Dataset public import surface 保持兼容。Multiple source roots registration 与 import/package wiring 属于 implementation concern，当前机制见 reconciliation 文档，不为此建立 plugin system 或 custom package loader。

## 4. Authority 导航

| 当前任务 | 下一份 authority |
| --- | --- |
| Domain / persistence / Scope / Window / FetchUnit / Records / mutation flow | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Application Service / coverage / ensure / export / public result / runtime 调用约束 | [APPLICATION.md](APPLICATION.md) |
| 具体 Dataset 的 Source、identity、fields、completeness | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md |
| Dataset-specific consumer request/result/view、public Python surface | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md → SERVICE.md |
| CLI topology / delegation / serialization / file delivery | [lab authority](../lab/ARCHITECTURE.md) |
| 当前实现与目标 ownership 的差异、后续迁移输入 | [IMPLEMENTATION_RECONCILIATION.md](IMPLEMENTATION_RECONCILIATION.md) |

Dataset authority 只能在模块边界及相关公共 domain/application invariant 内 specialize 或 constrain；catalog 只提供导航，不拥有 schema。具体 Dataset 任务读取与任务有关的公共 authority 和 owning Dataset authority，不默认加载 sibling Dataset。

## 5. Deferred design

首个 Dataset service 与 CLI vertical slice、source/test/storage ownership 的实现状态由 [implementation reconciliation](IMPLEMENTATION_RECONCILIATION.md) 集中记录。HTTP、schema migration 与其他 consumer integration 继续 deferred。内部文件、具体存储类型、key serialization、canonicalization/hash、事务机制、失败恢复与 adapter batching 属于 implementation design，不得重新决定已固定的 semantic request、结果计数或 export contract。Research/Snapshot integration 须独立设计。

Refresh / force / invalidation policy、TTL、stale state、多维 Window、Dataset dependency graph、cross-Dataset query engine、Source request audit table、plugin framework 与 generic workflow engine 均不在本轮设计范围内。
