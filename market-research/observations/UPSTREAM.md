# Observation Upstream Dependency authority

本文件是 Observation upstream dependency policy 的唯一专题 owner：priority、semantic sufficiency、design-time selection、public execution、failure / fallback、multi-upstream ownership、capability-gap escalation、provider prohibition 与 provenance boundary。稳定 invariants 由 [Observation architecture](ARCHITECTURE.md) 进入；[Schema](SCHEMA.md) 要求 concrete authority 回答实际依赖，[Authoring](AUTHORING.md) 拥有决策流程。本文不改变 Observation inputs / key / empirical semantics 或 Study workflow。

## DataLake-first capability selection

```text
Observation required empirical facts
    → inspect existing DataLake public Dataset contracts FIRST
        ├── semantically sufficient → bind exact Dataset public service
        └── semantically insufficient → record reason
             → inspect Snapshot Capability Catalog
                 ├── suitable public Product → bind exact Product contract
                 └── no suitable public Product → Upstream Capability Gap
```

DataLake-first 是 **authority / design-time capability selection priority**，不是 runtime try / fallback strategy。每个 concrete Observation 先判断所需 facts 能否从已发布 DataLake public semantic contracts 完整、确定、可验证地取得；足够时 DataLake 是 canonical upstream fact owner，必须使用对应 Dataset public Application Service。不因 Snapshot API 更方便、结果已经整理或少写代码而跳过 DataLake。

DataLake contract 的 runtime implementation 暂未就绪、缺少本地缓存或 operation 失败，均不等于 public semantic capability insufficient；readiness / failure 与选择何种语义来源分别核对。

## Semantic sufficiency 与 Snapshot selection

DataLake sufficient 要同时满足：所需 facts 在已发布 public service / view 中合法可消费；scope / window / population 与 completeness 能按契约完整、确定、可验证地满足需求；Observation 的 derivation 不需要实质重新实现已经属于 Snapshot Product 的 canonical deterministic product semantics。某些 rows 恰有相似字段、私有 catalog 有事实或 transport 返回过字段，不能证明 public capability sufficient。

Calendar、option / futures / index daily facts、公开 contract metadata 与 complete product-day facts 等，可在相应 existing Dataset contract 足够时直接消费；这不是对所有未来需求的预先 sufficiency 保证。Observation-owned deterministic derivation 继续由具体 Observation 拥有，不因多 Dataset facts composition 自动成为 Snapshot 产品，也不得借 composition 复制既有 Snapshot canonical semantics。

只有 DataLake **semantic capability insufficient** 才检查 [Market Snapshot Capability Catalog](../../market-snapshot/CAPABILITIES.md)。典型理由包括未公开所需 fact、public contract 不能证明所需 completeness、目标已经是 Snapshot-owned deterministic prepared / analysis-ready Product，或自行从 DataLake join / transform 会实质重做已有 Snapshot Product semantics。

此时选择一个明确 Product，只消费其 public Product / Application request、result 与 failure contract。Concrete authority 必须记录 required capability、已审查的 DataLake public contracts / insufficiency reason、selected Product identity、exact public request / result contract、failure semantics 与 remaining gaps。Snapshot 产品边界由 [Snapshot architecture](../../market-snapshot/ARCHITECTURE.md) 及该 Product authority 拥有；不为 Research 创建统一 facade / manager / gateway。

## Public execution 与 responsibility

已存在 complete retained Artifact 时，沿用 [framework reuse](ARCHITECTURE.md#business-identity-与-invocation-lifecycle)，不重复 upstream access / computation。没有 complete Artifact 时才按选定 public contract 获取 facts：

| Canonical upstream | Allowed invocation semantics |
| --- | --- |
| DataLake Dataset | 按需使用 public coverage / ensure，满足 concrete authority 声明的 completeness，再消费合法 export / semantic result 并 deterministic derive。具体 Dataset contract 决定最小合法调用方式，不统一强制 coverage → ensure → export。 |
| Snapshot Product | 直接引用该 Product public request、result 与 failure contract，不强加 Dataset-style coverage / ensure / export。 |

只使用 public semantic objects。DataLake 自己拥有 coverage、ensure、export、cache completeness、Source execution 与 credentials；Observation 不读取 persistence、不重新实现 DataLake cache、不接管 provider execution。Snapshot 自己拥有 canonical Product preparation 与结果有效性；Observation 不穿透 Capture、Raw 或 private Preparation。共享 runtime 不授予内部 import 权限。

## Runtime failure 不授权换源

```text
DataLake runtime failure != permission to fallback to Snapshot
Snapshot execution failure != permission to reconstruct from DataLake
```

Canonical upstream 是 concrete authority 的 design-time 决定。同一 Observation business key 不得因一次失败、missing / null 或缓存状况切换到另一套 semantic source。DataLake-backed Observation 遇到 OperationError、credential missing、provider timeout / temporary network failure、ensure incomplete、FetchUnit failure、persistence / integrity failure、Calendar prerequisite failure，或其他不能满足 declared completeness 的情况，invocation 失败；不执行 try DataLake / except Snapshot。

已选择 Snapshot Product 的 Observation 遇该 Product execution / validity failure，同样 invocation 失败；不手工从 DataLake reconstruction。已 complete retained Artifact 的正常 reuse 不要求重新执行 upstream，也不是 failover。

Concrete authority 可以拥有自己的 proven absence / date resolution 规则，例如 DTE-chain 在同一已选 DataLake boundary 内回溯已证明无 requested expiry 的日期；这不是换源 permission，也不能把 upstream failure 当 absence。Future multi-source reconciliation 只能在明确 semantic decision 和 concrete canonical contract 中另行定义；当前没有默认重建、补洞或 fallback 行为。

## Multi-upstream canonical ownership

Observation 可以同时依赖多个 DataLake public services 与明确 Snapshot public Products，前提是 **one semantic fact → one canonical upstream owner**，每种 facts 的契约与 owner 都明确，分别按 DataLake-first 审查。例如 Calendar facts 归 DataLake、已有 prepared basis history 归明确 Snapshot Product，不能因组合而合并 ownership。

禁止同一 fact 正常用 DataLake、missing 时用 Snapshot；也禁止正常用 Snapshot、null 时用 DataLake 填补。没有 explicit concrete reconciliation semantics 时不得 silent substitution；默认各声明依赖必须满足自己的 public contract，任一 required dependency failure 使 invocation 失败。不自行引入跨来源 freshness、优先级覆盖、合并或冲突裁决策略。

## Upstream Capability Gap 与 escalation

DataLake semantically insufficient 且 Snapshot 无适合的 public Product 时，concrete authority 必须记录 **Upstream Capability Gap**：缺哪些 facts / completeness / prepared result、已核对哪些 public contracts、正确 owner 与对 readiness 的影响。Observation 不进入 implementation-ready 状态，不用 private access 或 provider SDK 绕过。

Reusable source / market facts 或其 public completeness 缺口交给 [DataLake owner](../../data-lake/ARCHITECTURE.md) reconciliation；deterministic prepared / analysis-ready Product 缺口交给 Snapshot owning module / Product design。该 escalation 不授权本任务自动扩展 upstream API、实现新 Product 或修改消费者业务语义。

## Absolute external-provider prohibition

**market-research, including every Observation, MUST NOT depend directly on Tushare or any other external market-data provider.** Research 只依赖 Dataset / Product identity 与发布的 public semantic service，不获取 token、不拥有 provider transport semantics。

明确禁止 Observation / Research 直接使用：`import tushare`、`pro_api`、`TUSHARE_TOKEN` / provider credential、provider client、provider transport DTO、requests / HTTP calls to provider、DataLake provider package、Source Adapter / Repository、DataLake SQLite 或 internal FetchUnit / Record storage、Snapshot Capture provider adapter / Raw / private Preparation / persistence、backend-api / FastAPI DTO / frontend types，以及 CLI / serialized JSON round-trip。

Provider-native facts 只有在 upstream public contract 已合法发布时，才按其公开 semantic meaning 消费；这不是 import provider runtime、调用 endpoint、读取 credential 或穿透 internal provenance 的授权。研究代码不能以 Scratch、legacy helper 或新 Observation 的名义直接集成 provider。

## Provenance boundary

Observation Artifact provenance 描述选定的 **upstream semantic dependency**：DataLake Dataset identity、view / export schema version、scope / window / coverage context；或 Snapshot Product identity、canonical query identity、public result contract / product version（该 Product 已定义时）。具体必需 provenance 仍由 concrete Artifact contract 拥有，不统一发明 envelope、versioning 或 query identity。

Tushare endpoint、token、HTTP response、provider request parameters、internal Source Adapter、SQLite path、Repository object、Raw file path 都不是 Research dependency 或主动获取的 provenance。Provider provenance 若由 upstream public contract 合法暴露，可以作为公开事实继承，不主动穿透获取，不据此引入 credential / transport dependency。Provenance 不自动进入 business key，不改变 [deferred evolution](ARCHITECTURE.md#explicitly-deferred-decisions)。

## Review 与 implementation non-goals

审查 concrete authority 的 required facts、DataLake capability review / sufficiency、selected exact public boundary、failure semantics、gap 与 public provenance；Snapshot 选择必须有 DataLake semantic insufficiency 理由。默认 provider path、runtime failover 与 silent substitution 均不合法。

本专题只编码 semantic dependency rules，不创建 Python package / adapters、SQLite / persistence design、public ensure types、retry / fallback engine、provider wrapper、generic DataSource / Repository、DataLake / Snapshot facade、DI framework、plugin / registry、workflow engine、Study / Analysis implementation、CLI 或 HTTP API。不创建 MarketDataProvider、UpstreamProvider、SourceResolver、FallbackProvider、DataSourceRegistry、SnapshotRepository、SnapshotGateway、SnapshotProvider 或 GenericSnapshotService。
