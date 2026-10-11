# DataLake 模块架构 authority

本文件是 DataLake 的稳定模块入口，只定义职责、ownership、关键模块 invariant、public boundary、依赖方向与 authority 导航。仓库级职责与 Python runtime invariant 见 [repository architecture](../ARCHITECTURE.md)；专题语义按任务从下方导航选择，不要求加载全部公共或 Dataset authority。

## 1. Ownership 与 persistence boundary

DataLake 是多个自治 DataSet 的宿主 bounded context，拥有 DataLake-wide invariants 与 shared kernel；具体 DataSet 持久缓存并管理来自外部 Source 的 reusable source facts；persistence 是可重建 cache，不维护 schema migration。DataLake 不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI，也不接管 Snapshot 产品已声明的 Raw Artifact。Public service 的发布不自动建立 Research/Snapshot runtime integration；这些 consumer 的实际接入 implementation 须遵循已发布 boundary，Research 选择与调用权限由 [Research UPSTREAM](../market-research/UPSTREAM.md) 拥有。

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
│   └── TUSHARE.md              # provider execution authority
├── src/data_lake/              # shared kernel + separate provider infrastructure
│   └── providers/tushare/      # Tushare runtime implementation
├── tests/                      # shared kernel / provider / module boundary verification
└── datasets/
    └── <dataset-id>/
        ├── <Dataset authority documents>
        ├── src/                # Dataset implementation and composition
        ├── tests/              # Dataset verification
        └── data/<owned sqlite> # Dataset persistent runtime state
```

Colocation 让同一 Dataset 的语义、代码、验证与持久化 state 由同一 bounded context 拥有。真实 SQLite/runtime state 默认不进入 Git；具体 filename 与目录 materialization 属于 implementation concern。SQLite lifecycle 与旧目录 state 隔离见 [PERSISTENCE.md](PERSISTENCE.md)。

不同 DataSet 的 owned state 必须能够独立存在、独立删除或重建；cache rebuild 的最小 ownership boundary 是 owning Dataset，兼容性与显式失败要求见 [PERSISTENCE.md](PERSISTENCE.md)；public service 的必要事实依赖不合并 storage lifecycle，也不保证 prerequisite 缺失时 operation 仍可执行。这不定义 refresh policy。同一 instrument 可以分别存在于多个 DataSet 自己的 instrument catalog 中；不得据此合并 persistence ownership。Storage resolution 的公共调用约束见 [APPLICATION.md](APPLICATION.md)。

这里的 `DataSet` 是 DataLake ownership 概念，不改写 Snapshot 中可能作为产品名称使用的 `Dataset`，也不授权读取或迁移产品私有 Raw。

## 2. 领域关系与 public boundary

DataSet 内部以 Scope + transient Window 确定希望覆盖的 FetchUnits；FetchUnit 拥有 Records 与 coverage state，Source adapter 获取外部事实，Repository 管理 owned SQLite。公共领域与 persistence 细节由 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 拥有。

每个 DataSet 自己拥有并发布 transport-neutral Public Application Service，作为该 Dataset 的唯一 canonical consumer boundary；Python consumer 直接通过 semantic request/result/view 使用 `coverage`、`ensure`、`export`，CLI / HTTP 只是 adapter，不拥有 Dataset 业务语义。直接消费具体 Dataset public API 是合法依赖，不是穿透 DataLake boundary；DataLake 不创建 DataLakeService、DatasetManager、registry、gateway 或 generic client，也不允许通过这些新 facade 替代具体 Dataset boundary。详细公共 operation contract 由 [APPLICATION.md](APPLICATION.md) 拥有。稳定依赖方向为：

```text
Consumers (lab CLI / future HTTP API / Research / Snapshot-Preparation / Python consumers)
    ↓
Dataset public Application Service
    ↓
DataLake shared kernel
```

Dataset 内部组合 Source adapter 与 Repository 来访问 external API 和 owned SQLite。Consumer 禁止直接依赖 Dataset Repository internals、Source adapter internals、SQLite schema / connection、Dataset `data/` 文件或内部 FetchUnit / Record persistence identity。

允许 `Dataset → DataLake shared kernel`；禁止 `DataLake shared kernel → specific Dataset`。Dataset 间默认禁止依赖；已声明的单向 public service dependencies 为下列三个 consumer → `tushare_trade_calendar public Application Service`，只用于目标交易日展开：

| Consumer Dataset | Prerequisite authority |
| --- | --- |
| tushare_index_daily | [Index 交易日契约](datasets/tushare_index_daily/TRADING_DAYS.md) |
| tushare_equity_index_futures | [Futures 交易日契约](datasets/tushare_equity_index_futures/TRADING_DAYS.md) |
| tushare_equity_index_options | [Options 交易日契约](datasets/tushare_equity_index_options/TRADING_DAYS.md) |

Calendar 不反向依赖这些 consumers；Futures / Options 的 underlying index relationship 只表达稳定 semantic identity，不授予 Index runtime dependency，Futures 与 Options 也不互相依赖。禁止 cycles、跨 Dataset internal import、共享 SQLite 或跨库事务。公共 dependency 调用与 failure invariant 见 [APPLICATION.md](APPLICATION.md)。Catalog 不构成 runtime registry。

## 3. Canonical Python boundary

Canonical Python namespace 仍为 `data_lake`。模块内部区分 provider-agnostic shared kernel、provider-specific shared infrastructure 与 Dataset bounded contexts。顶层 `data-lake/src/` 拥有前两者，但它们是独立 ownership：shared kernel 包含公共 domain primitives / invariants、Scope / Window / FetchUnit / Record 机制、coverage / ensure / export 通用 machinery、共享 persistence machinery、公共 result / error contracts、通用 serialization / hash 及 generic runtime / storage resolution infrastructure；provider infrastructure 只拥有跨 Dataset 的 provider execution。顶层 `tests/` 验证公共能力、provider execution 与模块边界，kernel tests 使用 test-local fake Dataset / Source。

Kernel 不得知道具体 Dataset、provider endpoint、token、request frequency、provider-specific exception、instrument family、Dataset-specific Scope、completeness rule 或 export payload。只因一个具体 Dataset 存在的代码默认归 owning Dataset；其 service composition、Source adapter、领域 specialization 与相关 tests 归 `datasets/<dataset-id>/src/` 和 `tests/`。

Tushare provider infrastructure 的 namespace 为 `data_lake.providers.tushare`，implementation 归 `data-lake/src/data_lake/providers/tushare/`，canonical execution authority 为 [providers/TUSHARE.md](providers/TUSHARE.md)。稳定依赖方向为 Dataset Source adapter → provider infrastructure → external provider client/API；provider 只可复用 kernel 的 provider-neutral error contracts，不依赖具体 Dataset、Service、Repository 或 FetchUnit semantics；kernel 不依赖 provider infrastructure。Provider 不拥有 Dataset endpoint selection、partition / normalization / completeness 或 persistence，也不构成 consumer-facing service；Research / Modeling / Snapshot / HTTP / CLI consumers 不直接调用 Executor。详细 execution contract 只在 provider authority 定义。

Dataset-local source root 不创建独立 Python project、Poetry environment 或 dependency graph；所有 source roots 遵守 repository root 唯一 Python project 与 worktree-local 根 `.venv` invariant。Filesystem ownership 不决定 public import path，已有 Dataset public import surface 保持兼容。Multiple source roots registration 与 import/package wiring 属于 implementation concern，不为此建立 plugin system 或 custom package loader。

## 4. Authority 导航

| 当前任务 | 下一份 authority |
| --- | --- |
| Scope / Window / FetchUnit / Records / logical persistence / mutation flow | [DOMAIN_MODEL.md](DOMAIN_MODEL.md) |
| Application Service / coverage / ensure / export / public result / runtime 调用约束 | [APPLICATION.md](APPLICATION.md) |
| Tushare-backed Dataset 的 Source execution / credential / client / shared limiter / provider failure | [providers/TUSHARE.md](providers/TUSHARE.md) |
| Operational progress / safe request and validation diagnostics | [DIAGNOSTICS.md](DIAGNOSTICS.md) |
| Bounded batching / validation reuse / Source-write overlap | [EXECUTION.md](EXECUTION.md) |
| SQLite lifecycle / transactions / read snapshots / frozen basis / rebuild-only compatibility | [PERSISTENCE.md](PERSISTENCE.md) |
| 具体 Dataset 的 Source、identity、fields、completeness | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md |
| Dataset-specific consumer request/result/view、public Python surface | [DATASETS.md](DATASETS.md) → owning Dataset ARCHITECTURE.md → SERVICE.md |
| CLI topology / delegation / serialization / file delivery | [lab authority](../lab/ARCHITECTURE.md) |

Dataset 与 provider authority 只能在模块边界及相关公共 domain/application invariant 内 specialize 或 constrain；catalog 只提供导航，不拥有 schema。具体 Dataset 任务读取与任务有关的公共 authority 和 owning Dataset authority，不默认加载 sibling Dataset；普通 Dataset domain task 不默认加载 provider execution authority。

## 5. Non-goals 与 deferred semantics

DataLake 不引入 DataLakeService、DatasetManager、runtime registry、generic plugin / workflow framework 或 cross-Dataset query layer。Dataset 的直接 public service boundary 与明确 dependency permissions 已由上文固定。

HTTP / Research / Snapshot 等 consumer 的具体 integration implementation 仍须按已冻结 public boundary 完成；rebuild-only compatibility 由 PERSISTENCE.md 拥有，不维护 migration framework 或旧目录 compatibility import。Refresh / force / invalidation、TTL / stale、Source correction、多维 Window、通用 Dataset dependency graph 与 Source request audit table 继续 deferred，不从内部 serialization、hash、batching 或存储优化推导新的 public semantics。
