# data_snapshot 模块架构 authority

本文件定义 `data_snapshot` 的稳定 ownership、执行角色与依赖边界。仓库级定位见 [repository architecture](../ARCHITECTURE.md)；产品与共享能力从 [CAPABILITIES.md](CAPABILITIES.md) 进入。字段、公式、产品结果和失败契约由对应 bounded context 拥有。

## Module identity and DataLake boundary

The owning directory and canonical Python namespace are `data_snapshot`, directly succeeding Market Snapshot as an independent bounded module. Inherit the [repository naming rules](../ARCHITECTURE.md#naming-and-transition-authority). Product identity and public contracts remain unchanged.

All existing Products, Capture, Preparation, Raw Artifacts, public application contracts and shared capabilities remain here. DataLake owns reusable source facts and Dataset-owned caches. Sharing the `data_*` family does not move Snapshot semantics or Raw into DataLake, delete shared capabilities, or force replacement of Snapshot Capture. Dataset integration uses only explicitly authorized Dataset Public Application Services, never private persistence or Source adapters. [DataLake Experiments](../data_lake/EXPERIMENTS.md) cannot be stable runtime dependencies.

## 1. Product 是主要语义所有权边界

Product 是一个具有明确数据需求、query identity、invariants 和 analysis-ready result 的 bounded ownership unit。一个 Product 可以拥有完整 vertical slice：Source scope 与 completeness、产品专属 Source Facts / Raw、Analysis Preparation、Application Service、public Python application contract、semantic failure，以及需要时的 persisted output contract。

Product 不是横向 Source → Capture → Preparation → Service pipeline 中的一层。产品专属 `preparation.py` 或 `service.py` 留在 `products/<product>/` 是正常的 ownership；外层同名目录不要求迁移产品代码。具体产品从 [catalog](CAPABILITIES.md) 进入，其 specialized authority 是产品契约的 canonical owner。

Product 外的能力须由多个活跃 Product 的实际需求证明，而非为未来可能复用建立通用 framework。Product-local semantic 归 Product；经真实跨 Product 需求证明的 semantic 或 mechanic 才可共享。当前共享能力包括 Source adapter / Capture facts、通用 artifact filesystem/JSON mechanics，以及由 CSI1000 IM Basis History 与 CFFEX Equity Index Futures Basis History 共同消费的窄 CFFEX 股指期货期限结构与基差语义。两个 Product 各自拥有 Source scope、完整性、request/result/failure/execution contract；共享代码和单一 Python runtime 不授予跨 Product 读取私有 Raw 或 result 的权限。

## 2. Product execution 的角色

```text
semantic request
    → Product Application Service
    → Capture
    → Source Facts / Raw Data
    → Preparation
    → analysis-ready result
    → supported public application boundary / delivery
```

上图描述一次 Product execution 的职责，不规定 repository 必须按这些角色划分横向 package。Application Service 是 Product 内部执行一次 semantic request 的 orchestrator：按产品契约组织 Capture 与 Preparation，分类失败并发布结果；它不重定义 Source facts 或公式。既有 “Data Service” 仅表示可被请求的 Product application-service capability，不是与 Product 平级或凌驾于 Product 之上的业务实体，也不是独立 framework。

Public Application Boundary 是 Product 发布给 consumer 的 semantic request、result、classified failure 与 execution entry。Product authority 决定所支持的 public Python boundary 与结果是否持久化；HTTP parsing、DTO 与 status mapping 由 [ui_http](../ui_http/ARCHITECTURE.md) 拥有。Delivery 不能拥有或重新计算 Product semantics。

Source 是项目外的数据提供方。Capture 获取 Source facts，处理 Source endpoint/query 与 minimal normalization；产品选择自己的 Source scope、universe、窗口及 completeness。Capture 可以理解 Source-domain facts，但不能因下游分析偏好筛选事实或生成市场判断。Preparation 对已取得的 Source facts 做确定性的 selection、join、projection、rename、restructure 和已定义公式计算，不自行采集或产生市场判断。Analysis-ready result 可以是持久化 artifact，也可以是 request-scoped read model，由 Product authority 决定。`Dataset`、`Snapshot`、`Snapshot Assembly` 与 `Snapshot Definition` 可以是产品名称，不是额外的通用架构层。

## 3. Source Facts 与 persisted Raw Artifact

Capture 的逻辑输出是 Source Facts / Raw Data。Product 可以在内存中把这些事实交给 Preparation，也可以按自己的 authority 持久化为 Raw Artifact。persisted Raw Artifact 是采用它的 Product 在 Capture 与 Preparation 之间的可复现性契约；它不是所有 Product 的强制 runtime stage。不得为了满足目录或流程图而做无价值的 write-then-read。

无论是否持久化，Raw 都保留 Source 字段、单位、合法 null 与事实缺席的区别；required input 缺失、数值零和合法 null 不得静默合并。Minimal normalization 只为稳定表达 Source fact，必须确定且可逆或语义等价，不创造分析语义。日期格式、表格行到 record 与 Source scalar 的稳定表示可以属于 Raw；join、窗口、分析命名、派生公式、分组和排序属于 Preparation。不得自动换日期、猜测事实、补零或静默删除必需记录。

同一 Product 的相同 Source facts、query 与 Preparation Definition 必须产生语义一致的结果；对于已声明 persisted Raw 的 Product，相同 Raw Artifact 与 Definition 也必须如此。Preparation 不依赖当前时间、网络、随机性或本地缓存残留。具体 Raw 文件、身份、命名空间、按目标组织的路径、字段、输出结构和失败条件由 Product authority 定义，不能由本模块的通用描述覆盖。共享 artifact 能力可以提供通用 Raw root、文件系统与 JSON 读写 helper；调用这些 helper 不转移 Product Raw 路径的语义所有权。

## 4. 依赖与发布边界

- Product 可以依赖真正共享的 Source/Capture、Preparation semantics 和 infrastructure；共享能力不依赖 Product。Product 不读取 sibling Product 的私有 Raw 或最终产物，除非其 authority 明确声明该依赖。
- Capture 不依赖 Preparation result；Preparation 不调用 Source 或发起 Capture；Application Service 不改写二者的事实与公式。
- `data_snapshot` 只发布确定性、可分析的数据，不拥有市场状态解释、概率判断、交易建议或 Research finding。
- `data_snapshot` 拥有自己发布的 Product public contract；`market_research` 拥有所需的数据要求。Research 只通过受支持的 Product request/result/failure/execution surface 消费 Snapshot，不复制其 DTO/result authority，也不依赖 Source client、Capture、私有 Preparation、Raw 或 persistence layout。Snapshot 不依赖 Research。
- `ui_http` 依赖 Product public application boundary 并拥有 HTTP delivery；HTTP DTO 不反向定义 Product semantics。

## 5. Authority 导航与 implementation layout

```text
ARCHITECTURE.md
    → CAPABILITIES.md
        → Product ARCHITECTURE.md → product-local specialized authority
        → shared capability ARCHITECTURE.md → shared specialized authority
```

上层只定义稳定边界与导航，不复制产品字段、公式或失败契约。Implementation layout 遵循上述 semantic topology；活跃 Product 的 Python 实现保留在各自 context：

| 当前区域 | ownership |
| --- | --- |
| `products/<product>/` | 保留活跃 Product-local Source scope、Preparation、Application Service 与 public contract |
| `sources/`、`capture/` | 保留共享 provider adapter、Source facts、normalization 与 Capture mechanics；产品专属 scope 下沉 Product |
| `cffex_equity_index_basis/` | 两个真实 Product 共用的 CFFEX family、slot、calendar distance、formula 与 ordering 语义 owner；实现迁移属于后续 implementation |
| `products/csi1000_im_basis_history/` | 保留旧 IM Product public contract、scope 与当前实现；共用语义以共享 authority 为准 |
| `artifacts.py` | 仅保留通用 Raw root、filesystem/JSON mechanics；Product-specific Raw 路径由各 Product 构造 |

不因本 authority 重命名为 `shared/` 或引入 pipeline、plugin、registry、workflow engine。实施时先按 owning authority reconcile，发现上下层或同级冲突须显式解决。

## 6. Canonical Python namespace

The canonical Python namespace is `data_snapshot`, implemented at `data_snapshot/src/data_snapshot/` (repository-relative). The [repository authority](../ARCHITECTURE.md) owns the single Python runtime and dependency graph; a shared environment grants no additional imports. Daily cadence remains Product-local.
