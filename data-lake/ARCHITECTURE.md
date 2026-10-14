# DataLake 模块架构 authority

本文件是 DataLake 的稳定模块入口，只定义职责、ownership、Shared Kernel 架构、关键模块 invariant、public boundary、依赖方向与 authority 导航。仓库级职责与 Python runtime invariant 见 [repository architecture](../ARCHITECTURE.md)；专题语义按任务从下方导航选择，不要求加载全部公共或 Dataset authority。

## 1. Ownership 与 persistence boundary

DataLake = **Shared Kernel + Autonomous Datasets + Provider Infrastructure**。Kernel 提供通用领域模型、Application Use Cases、Outbound Ports 与持久化机制；Dataset 是拥有独立事实语义的自治领域边界，通过 Composition 发布自己的 Public Application Service；Provider 提供跨 Dataset 的外部请求执行能力。具体 DataSet 持久缓存并管理来自外部 Source 的 reusable source facts；persistence 是可重建 cache，不维护 schema migration。DataLake 不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI，也不接管 Snapshot 产品已声明的 Raw Artifact。Public service 的发布不自动建立 Research/Snapshot runtime integration；这些 consumer 的实际接入 implementation 须遵循已发布 boundary，Research 选择与调用权限由 [Research UPSTREAM](../market-research/UPSTREAM.md) 拥有。

```text
DataLake
    └── DataSet 1..n
            └── exactly one owned SQLite
```

DataSet 是自治的数据产品边界，拥有自己的 semantic authority、implementation、tests 与 persistent runtime state；canonical Dataset identity 由其 authority 声明。一个 DataSet exactly owns 一个 SQLite database，固定 cardinality 为 `1 DataSet : 1 SQLite`。禁止多个 DataSet 共用 SQLite、一个 DataSet 跨多个 SQLite、cross-Dataset foreign key、DataLake global database 与 global instrument master。

Filesystem ownership 为：

```text
data-lake/
├── <DataLake-level authority documents>
├── providers/
│   └── <provider-id>/
│       ├── ARCHITECTURE.md     # Provider execution authority
│       ├── src/data_lake/providers/<provider-id>/
│       │                      # Provider-specific infrastructure
│       └── tests/             # Provider verification
├── src/data_lake/              # provider-agnostic shared kernel
├── tests/                      # shared kernel / module boundary verification
└── datasets/
    └── <dataset-id>/
        ├── <Dataset authority documents>
        ├── src/                # Dataset implementation and composition
        ├── tests/              # Dataset verification
        └── data/<owned sqlite> # Dataset persistent runtime state
```

Shared Kernel、Provider 与 Dataset 分别拥有自己的 authority、implementation 与 tests；Provider co-locate 于 `providers/<provider-id>/`，Dataset co-locate 于 `datasets/<dataset-id>/`，顶层只拥有 DataLake-wide authority、shared kernel 与模块边界验证。Provider 是 provider-specific infrastructure ownership unit，不因此成为 Dataset 或拥有 persistent source-fact state。真实 SQLite/runtime state 默认不进入 Git；具体 filename 与目录 materialization 属于 implementation concern。SQLite lifecycle 与旧目录 state 隔离见 [PERSISTENCE.md](PERSISTENCE.md)。

不同 DataSet 的 owned state 必须能够独立存在、独立删除或重建；cache rebuild 的最小 ownership boundary 是 owning Dataset，兼容性与显式失败要求见 [PERSISTENCE.md](PERSISTENCE.md)；public service 的必要事实依赖不合并 storage lifecycle，也不保证 prerequisite 缺失时 operation 仍可执行。这不定义 refresh policy。同一 instrument 可以分别存在于多个 DataSet 自己的 instrument catalog 中；不得据此合并 persistence ownership。Storage resolution 的公共调用约束见 [APPLICATION.md](APPLICATION.md)。

这里的 `DataSet` 是 DataLake ownership 概念，不改写 Snapshot 中可能作为产品名称使用的 `Dataset`，也不授权读取或迁移产品私有 Raw。

## 2. 领域关系与 public boundary

核心领域主轴为 `Dataset → Scope + Window → FetchUnits → Records`。Dataset 定义业务维度与事实全集，Kernel 不强制按日。公共原语与不变量由 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 拥有；FetchUnitPlanner 等四个领域策略、两个 Outbound Ports 和可选 Dataset-owned Prerequisite Resolver 的接入责任由 [COMPOSITION.md](COMPOSITION.md) 拥有，不增加核心角色或 Port 数量。

每个 DataSet 自己拥有并发布 transport-neutral Public Application Service，作为该 Dataset 的唯一 canonical consumer boundary；Python consumer 直接通过 semantic request/result/view 使用 `coverage`、`ensure`、`export`，CLI / HTTP 只是 adapter，不拥有 Dataset 业务语义。直接消费具体 Dataset public API 是合法依赖，不是穿透 DataLake boundary；DataLake 不创建 DataLakeService、DatasetManager、registry、gateway 或 generic client，也不允许通过这些新 facade 替代具体 Dataset boundary。详细公共 operation contract 由 [APPLICATION.md](APPLICATION.md) 拥有。稳定依赖方向为：

```text
Consumers (lab CLI / future HTTP API / Research / Snapshot-Preparation / Python consumers)
    ↓
Dataset public Application Service
    ↓
DataLake shared kernel
```

Dataset Composition Root 将领域策略、Dataset Source Adapter、Kernel SQLite Repository Adapter 及已授权 prerequisites 绑定到 Kernel Application；Public Service 是这一 Composition 的产物。Consumer 禁止直接依赖 Dataset Repository internals、Source adapter internals、SQLite schema / connection、Dataset `data/` 文件或内部 FetchUnit / Record persistence identity。

允许 `Dataset → DataLake shared kernel`；禁止 `DataLake shared kernel → specific Dataset`。Dataset 间默认禁止依赖；已声明的单向 public service dependencies 为下列三个 consumer → `tushare_trade_calendar public Application Service`，只用于目标交易日展开：

| Consumer Dataset | Prerequisite authority |
| --- | --- |
| tushare_index_daily | [Index 交易日契约](datasets/tushare_index_daily/TRADING_DAYS.md) |
| tushare_equity_index_futures | [Futures 交易日契约](datasets/tushare_equity_index_futures/TRADING_DAYS.md) |
| tushare_equity_index_options | [Options 交易日契约](datasets/tushare_equity_index_options/TRADING_DAYS.md) |

Calendar 不反向依赖这些 consumers；Futures / Options 的 underlying index relationship 只表达稳定 semantic identity，不授予 Index runtime dependency，Futures 与 Options 也不互相依赖。禁止 cycles、跨 Dataset internal import、共享 SQLite 或跨库事务。公共 dependency 调用与 failure invariant 见 [APPLICATION.md](APPLICATION.md)。Catalog 不构成 runtime registry。

## 3. Shared Kernel Hexagonal Architecture

目标职责结构位于 `data-lake/src/data_lake/`：

```text
data_lake/
├── domain/                     # 通用领域原语与不变量
├── application/                # coverage / ensure / export Use Cases
├── ports/                      # Source / Repository Outbound contracts
├── adapters/outbound/sqlite/    # 标准 Repository Adapter
└── results.py                  # 兼容的公共 result / error contracts
```

这是代码组织的职责边界，不要求创建空目录、逐概念 Protocol 或机械拆文件。通用 runtime/storage resolution 与 serialization/hash helpers 按实际职责组织，不因此新增架构层。

| Boundary | Canonical responsibility |
| --- | --- |
| Domain | Scope / Window 公共语义、FetchUnit identity / ownership / status、Record / Instrument / UnitRecords、Dataset-independent completeness invariants；见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Application | 目标确定后的通用生命周期、状态协调、Source 编排、验证调用、提交与一致性读取；公共 operations 与 failure 见 [APPLICATION.md](APPLICATION.md)，内部执行见 [EXECUTION.md](EXECUTION.md) |
| Ports | Kernel 定义 Source 与 Repository 的 provider/storage-neutral 能力；见 [PORTS.md](PORTS.md) |
| Outbound Adapters | 实现相应 Port；标准 SQLite Adapter 由 Kernel 维护，lifecycle / transaction / snapshot / frozen basis 见 [PERSISTENCE.md](PERSISTENCE.md)；Dataset Source Adapter 留在 owning Dataset |

依赖方向固定为 Application → Domain / Ports，Ports → Domain / 中立 result/error types，Outbound Adapter → 对应 Port / Domain。Domain 不依赖 Application、Ports、具体 Adapter 或外部基础设施；Application 不依赖 SQLite、Tushare 或具体 Dataset / Provider。Adapter 不反向拥有领域规则、Use Case 或 public operation semantics。

Dataset Composition Root 可以选择具体 Adapter 并依赖 Kernel Application / Domain / Ports；Kernel 各层均不依赖具体 Dataset / Provider。交易日、合约生命周期、行情完整性及业务 Export 由 Dataset 提供。Kernel 不创建无实际职责的 Inbound Adapter；Dataset Public Service 是业务入口，CLI / HTTP 等传输 Adapter 归实际 owning module。

## 4. Canonical Python boundary

Canonical Python namespace 仍为 `data_lake`。模块内部区分 provider-agnostic shared kernel、provider-specific shared infrastructure 与 Dataset bounded contexts。顶层 `data-lake/src/` 只拥有 shared kernel：公共 domain primitives / invariants、Scope / Window / FetchUnit / Record 机制、coverage / ensure / export 通用 machinery、共享 persistence machinery、公共 result / error contracts、通用 serialization / hash 及 generic runtime / storage resolution infrastructure；provider infrastructure 只拥有跨 Dataset 的 provider execution，归对应 Provider 的 source root；Provider-specific tests 同样归该 Provider。顶层 `tests/` 验证公共能力与模块边界，kernel tests 使用 test-local fake Dataset / Source。

Kernel 不得知道具体 Dataset、provider endpoint、token、request frequency、provider-specific exception、instrument family、Dataset-specific Scope、completeness rule 或 export payload。只因一个具体 Dataset 存在的代码默认归 owning Dataset；其 service composition、Source adapter、领域 specialization 与相关 tests 归 `datasets/<dataset-id>/src/` 和 `tests/`。

Tushare provider infrastructure 的 namespace 为 `data_lake.providers.tushare`，implementation 归 `data-lake/providers/tushare/src/data_lake/providers/tushare/`，canonical execution authority 为 [providers/tushare/ARCHITECTURE.md](providers/tushare/ARCHITECTURE.md)。稳定依赖方向为 Dataset Source adapter → provider infrastructure → external provider client/API；provider 只可复用 kernel 的 provider-neutral error contracts，不依赖具体 Dataset、Service、Repository 或 FetchUnit semantics；kernel 不依赖 provider infrastructure。Provider 不拥有 Dataset endpoint selection、partition、Domain normalization / completeness 或 persistence，也不构成 consumer-facing service；Research / Modeling / Snapshot / HTTP / CLI consumers 不直接调用 Executor。详细 execution contract 只在 provider authority 定义。

Provider-local 与 Dataset-local source roots 不创建独立 Python project、Poetry environment 或 dependency graph；所有 source roots 遵守 repository root 唯一 Python project 与 worktree-local 根 `.venv` invariant。Filesystem ownership 不决定 Python import path，已有 Provider namespace、internal execution imports 与 Dataset public import surface 保持兼容。Multiple source roots registration 与 import/package wiring 复用已有工程机制，属于 implementation concern，不为此建立 plugin system 或 custom package loader。

## 5. Authority 导航

| 当前任务 | 下一份 authority |
| --- | --- |
| Scope / Window / FetchUnit / Records / logical persistence / completeness invariants | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Application Service / coverage / ensure / export / public result / runtime 调用约束 | [APPLICATION.md](APPLICATION.md) |
| Source / Repository Outbound Ports、Adapter 输入输出及失败责任 | [PORTS.md](PORTS.md) |
| FetchUnitPlanner、可选 Prerequisite Resolver、六角色接入与 Composition Root | [COMPOSITION.md](COMPOSITION.md) → owning Dataset ARCHITECTURE.md → 必要 TRADING_DAYS.md |
| Tushare-backed Dataset 的 Source execution / credential / client / shared limiter / provider failure | [providers/tushare/ARCHITECTURE.md](providers/tushare/ARCHITECTURE.md) |
| Operational progress / safe request and validation diagnostics | [DIAGNOSTICS.md](DIAGNOSTICS.md) |
| Bounded batching / validation reuse / Source-write overlap | [EXECUTION.md](EXECUTION.md) |
| SQLite lifecycle / transactions / read snapshots / frozen basis / rebuild-only compatibility | [PERSISTENCE.md](PERSISTENCE.md) |
| 具体 Dataset 的 Source、identity、fields、completeness | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md |
| Dataset-specific consumer request/result/view、public Python surface | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md → SERVICE.md |
| CLI topology / delegation / serialization / file delivery | [lab authority](../lab/ARCHITECTURE.md) |
| Authority 到当前代码的映射与尚未处理的实现差异 | [IMPLEMENTATION.md](IMPLEMENTATION.md)（状态与后续任务，不拥有新语义） |

Dataset 与 provider authority 只能在模块边界及相关公共 domain/application invariant 内 specialize 或 constrain；catalog 只提供导航，不拥有 schema。具体 Dataset 任务读取与任务有关的公共 authority 和 owning Dataset authority，不默认加载 sibling Dataset；普通 Dataset domain task 不默认加载 provider execution authority。

## 6. Non-goals 与 deferred semantics

DataLake 不引入 DataLakeService、DatasetManager、runtime registry、generic plugin / workflow framework 或 cross-Dataset query layer。Dataset 的直接 public service boundary 与明确 dependency permissions 已由上文固定。

HTTP / Research / Snapshot 等 consumer 的具体 integration implementation 仍须按已冻结 public boundary 完成；rebuild-only compatibility 由 PERSISTENCE.md 拥有，不维护 migration framework 或旧目录 compatibility import。Refresh / force / invalidation、TTL / stale、Source correction、多维 Window、通用 Dataset dependency graph 与 Source request audit table 继续 deferred，不从内部 serialization、hash、batching 或存储优化推导新的 public semantics。
