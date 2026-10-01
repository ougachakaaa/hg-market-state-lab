# DataLake 模块架构 authority

本文件定义 DataLake 的稳定 ownership、公共逻辑 persistence model 与操作边界。仓库级职责见 [repository architecture](../ARCHITECTURE.md)；具体 DataSet 从 [DATASETS.md](DATASETS.md) 进入。本文不定义 SQL DDL、Python API 或 runtime integration。

## 1. Ownership 与 persistence boundary

DataLake 持久缓存并管理来自外部 Source 的 reusable source facts。它不拥有 Snapshot Product semantics、Preparation、analysis-ready computation、Research、Modeling、HTTP 或 UI，也不接管 Snapshot 产品已声明的 Raw Artifact。本轮不建立 consumer runtime dependency。

```text
DataLake
    └── DataSet 1..n
            └── exactly one owned SQLite
```

DataSet 是独立的数据与 persistence ownership boundary；canonical Dataset identity 由其 authority 声明。一个 DataSet exactly owns 一个 SQLite database，固定 cardinality 为 `1 DataSet : 1 SQLite`。禁止多个 DataSet 共用 SQLite、一个 DataSet 跨多个 SQLite、cross-Dataset foreign key、DataLake global database 与 global instrument master。

不同 DataSet 必须能够独立存在、独立 refresh、独立删除或重建。这不定义 refresh policy。同一 instrument 可以分别存在于多个 DataSet 自己的 instrument catalog 中；不得据此合并 persistence ownership。具体 filesystem root / filename resolution 留给 implementation design。

这里的 `DataSet` 是 DataLake ownership 概念，不改写 Snapshot 中可能作为产品名称使用的 `Dataset`，也不授权读取或迁移产品私有 Raw。

## 2. 公共逻辑 persistence model

每个 DataSet 的标准模型包含 `dataset_meta`、`fetch_unit`、`instrument` 与 `records` 四个核心实体。以下是逻辑字段与 invariants，不是具体 SQL schema。

### dataset_meta

`dataset_meta` 描述当前 SQLite 自身，至少表达：

```text
dataset_name
schema_version
source_name
created_at
updated_at
```

单独拿到一个 DataSet SQLite 时，必须能够识别其 Dataset identity 与 schema generation。这里不设计 migration framework。

### fetch_unit

FetchUnit 是 DataSet 的 minimum synchronization unit、minimum reconciliation unit、minimum write ownership boundary 与 coverage state owner。逻辑字段至少包括：

```text
unit_id
unit_key
status
content_hash
record_count
created_at
last_attempt_at
succeeded_at
error_code
error_message
```

具体 DataSet 可以拥有额外 typed identity fields。`unit_key` 必须稳定、确定且唯一表达该 DataSet 内的 FetchUnit identity；不同 DataSet 可以采用不同 identity shape，具体字符串 serialization 留给 implementation design。

第一版持久状态只有 `pending`、`success`、`failed`。`missing` 不是持久状态：`no fetch_unit row = missing`。默认需要执行的条件是：

```text
unit does not exist OR unit.status != success
```

已有 `success` unit 默认不重新 fetch。不引入 stale、dirty、TTL 或其他 refresh state。

`content_hash` 描述当前 FetchUnit 所拥有的 canonical Record set 的内容 hash，属于 FetchUnit metadata，不属于单条 Record；`record_count` 表达该 unit 所拥有的 Record 数量。Hash 算法与 canonical serialization 留给 implementation design。

FetchUnit 只有在其 Records 成功提交后才能进入 `success`。成功写入必须原子地替换该 unit 拥有的 Records 并更新成功 metadata，使 Records、`content_hash`、`record_count` 与成功状态语义一致；不得在 Records 未成功提交时留下 `success`。事务机制与失败恢复的实现细节留给后续设计。

### records

Records 保存该 DataSet 的 Source Facts：

```text
FetchUnit 1
    owns
Records 0..n
```

每条 Record 必须属于且只属于一个 FetchUnit。逻辑公共字段至少为 `record_id`、`fetch_unit_id`，其余字段与自然 Record identity 由 Dataset authority 定义；下层可以对公共 `0..n` cardinality 作更严格的 completeness 约束。

FetchUnit 不要求只拥有一条 Record，例如未来某个 Dataset 的 FetchUnit 可以是一日，而 Records 为当日数千个 instruments 的 Source facts。

普通 consumer 对 Records 默认只读。只有 owning DataSet 的 FetchUnit execution 可以创建、删除或替换其所拥有的 Records；不得把 arbitrary record-level mutation 发布为公开能力。

### instrument

`instrument` 是 Dataset-local instrument catalog，不是 repository-wide master instrument table。标准逻辑字段可以表达：

```text
instrument_id
source_code
instrument_type
symbol
exchange
name
valid_from
valid_to
```

具体 required fields 由 Dataset authority 定义。Instrument-addressed Dataset 的 Records 可以通过 `records.instrument_id → instrument.instrument_id` 引用同一 SQLite 内的本地 instrument。

不是所有 Dataset 都具有自然的 tradable instrument。标准模型保留 instrument entity，但 Dataset 必须能够声明 `instrument usage: none`，此时不要求 instrument entries 或 Records 引用，不得人为制造 Instrument 语义。

## 3. Scope、Window 与 Source Request

Scope 由具体 Dataset authority 定义，用于确定该次 operation 所针对的 Source fact 范围。Window 是 transient operation input，描述希望 Dataset 覆盖的范围，第一版只设计一维 Window。

Window 不持久化，因为它表达一次操作的目标范围，而非数据库当前 coverage；coverage state 由各 FetchUnit 拥有。Window 负责在 Dataset 与 Scope 下确定目标 FetchUnit 集合：

```text
Window
    ↓
generate desired FetchUnits
    ↓
materialize / inspect fetch_unit
```

Window 不直接创建 Records，也不定义 Source API request batching。

`FetchUnit != Source Request`：FetchUnit 是 DataLake ownership unit；Source Request 是 provider adapter 的传输/调用单位。一个 Source Request 可以返回 `1..n` FetchUnits，返回事实必须按 FetchUnit identity 重新 partition，然后写入各 unit 自己拥有的 Records。不得因为 provider endpoint 支持 date range query，就把整个 range 变成一个 FetchUnit。

## 4. Mutation flow 与 read boundary

稳定概念 flow 为：

```text
Dataset + Scope + Window
          ↓
      expand Window
          ↓
  desired FetchUnits
          ↓
 materialize / inspect
      fetch_unit
          ↓
select units not success
          ↓
     Source request(s)
          ↓
      Source facts
          ↓
partition by FetchUnit
          ↓
normalize source representation
          ↓
canonical Record set
          ↓
compute content_hash
          ↓
atomic persistence
    ├─ replace records owned by unit
    └─ mark unit success
```

Normalization 只稳定表达 Source facts，必须确定且保持 Source 语义；不得生成 analysis-ready 派生结果、补造缺失事实或把缺失当作数值零。每个 unit 的成功必须满足 Dataset-specific completeness，不能用一次请求的成功代替所有目标 units 的成功。

显式行为边界固定为：

| operation | Source I/O | DataSet SQLite |
| --- | --- | --- |
| ensure / sync | 可以访问 Source | 可以 mutation |
| read | 禁止访问 Source | SQLite only、read only |

普通读取不得因缓存缺失而静默访问 Source，包括 Tushare。具体 Python API 与 read 缺失结果的表达留给 implementation design。

## 5. Authority 导航与 deferred design

```text
repository ARCHITECTURE.md
    ↓
data-lake/ARCHITECTURE.md
    ↓
DATASETS.md
    ↓
datasets/<dataset>/ARCHITECTURE.md
```

模块 authority 只拥有稳定公共边界和 persistence invariants；[catalog](DATASETS.md) 只提供 Dataset navigation，不复制 schema。Dataset authority 在这些边界内拥有 Source、Scope、Window shape、FetchUnit / Record identity、Record fields、instrument usage 与 completeness。

本轮不实现 Python、SQLite DDL、migration framework、Tushare client、CLI、HTTP 或任何 runtime integration。具体路径、字段类型/null 表达、key serialization、canonicalization/hash、事务机制、失败恢复、adapter batching、Python API 与未来 consumer integration 留给后续 implementation design。

Refresh / force / invalidation policy、TTL、stale state、多维 Window、Dataset dependency graph、cross-Dataset query engine、Source request audit table、plugin framework 与 generic workflow engine 均不在本轮设计范围内。
