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

DataLake-backed Observation 先声明 required semantic fact slice，只通过选定的 Dataset public service 要求完整性证明、消费 committed public export，并派生自己的 retained Artifact；不读取 DataLake storage。沿用 [framework reuse](ARCHITECTURE.md#business-identity-与-invocation-lifecycle) 与 [publication lifecycle](IMPLEMENTATION.md#complete-publication-与-concurrency)，**complete Observation Artifact lookup MUST happen before DataLake access**：

```text
Observation.ensure(request)
    → validate / canonicalize
    → lookup Observation-owned persistence
        ├── complete hit → return retained Artifact
        │                  zero DataLake calls
        │                  zero upstream factory / service calls
        │                  zero recomputation
        └── miss → invoke selected public upstream service
                 → establish required completeness
                 → consume public export / semantic result
                 → deterministic Observation derivation
                 → atomic Observation publication → return
```

Observation retained Artifact lookup 先于 DataLake Dataset cache access。Complete hit 不因 DataLake 当前缺失、credential 不可用或 provider offline 而访问上游；corrupt / unreadable retained state 的处理仍按 framework IMPLEMENTATION，不能伪装为 miss。只有没有 complete Artifact 时才按选定 public contract 获取 facts：

| Canonical upstream | Allowed invocation semantics |
| --- | --- |
| DataLake Dataset | Concrete Observation 根据 required fact slice 与具体 Dataset public contract，选择能够满足 completeness proof 的 minimum legal invocation sequence，再消费合法 public export 并 deterministic derive。不统一强制 coverage → ensure → export。 |
| Snapshot Product | 直接引用该 Product public request、result 与 failure contract，不强加 Dataset-style coverage / ensure / export。 |

Coverage / ensure / export 的 ownership 继续属于 Dataset Application Service。Concrete authority 只声明需要证明什么、哪个 Dataset contract 拥有这些 facts、采用何种 public invocation pattern、什么状态允许消费以及什么状态必须失败。两项已选 DataLake-backed Observation 的具体序列唯一见 [Universe IMPLEMENTATION](cffex_option_expiry_universe/IMPLEMENTATION.md#composition-与-canonical-execution) 与 [DTE-chain IMPLEMENTATION](cffex_option_expiry_dte_chain/IMPLEMENTATION.md#canonical-execution-mapping)，不在 framework 统一 concrete calls。

只使用 public semantic objects。DataLake 自己拥有 coverage、ensure、export、cache completeness、Source execution 与 credentials；Observation 不读取 DataLake persistence、不重新实现 DataLake cache、不接管 provider execution。Snapshot 自己拥有 canonical Product preparation 与结果有效性；Observation 不穿透 Capture、Raw 或 private Preparation。共享 runtime 不授予内部 import 权限。

### Ensure 与 committed export proof

以下角色唯一继承 [DataLake APPLICATION](../../data-lake/APPLICATION.md#1-application-service-与公共-operation-family)，不改变 Dataset API：

| Operation | Observation 如何使用 public contract |
| --- | --- |
| coverage | Read-only 当前 completeness check，可用于选择后续调用；独立 coverage 不是最终 records 的 snapshot proof。 |
| ensure | 按需 mutate Dataset state，尝试使 requested semantic slice complete；可能报告 incomplete / unit failures 或抛 application error，Observation 必须检查结果。 |
| export | Read-only 一份 committed Dataset cache snapshot，同时含该 request 的 coverage 与 semantic payload；incomplete export 也是合法 Dataset result，但不能作为 complete empirical derivation input。 |

Canonical derivation input 是 **one public export = coverage proof + payload**。消费前按具体 Dataset / Observation contract 验证 identity、view / schema、scope / window、coverage 与 public records；不解释 Dataset completeness internals。不得拼接 operation A 的 coverage 与 operation B 的 rows，然后宣称它们为同一完整事实视图。

若 concrete 先调用 `ensure(request)`，必须检查 EnsureResult，再 `export(same semantic request)`。EnsureResult.complete=true 证明 mutation operation 在结束时完成目标，不能代替后续 export 的最终 completeness / records proof；后续 export 不完整或非法时仍须失败。Independent coverage 可以指导 read-first / ensure-if-needed，不要求每次 preliminary coverage，也不改变最后消费合法完整 export 的要求。每份 export 保持自己的 snapshot invariant，不宣称不同 calls / Datasets 共享 snapshot 或 provider-current freshness。

### Missing、proven absence 与 operation failure

| Public state | Consumer interpretation |
| --- | --- |
| 合法 public check / export 表明 missing、pending、failed 或 coverage incomplete | 尚不能证明 required slice complete；按 concrete invocation pattern ensure 后重新 export / 判断，不以当前 empty / partial payload 证明 absence。初始 failed cache unit 不等于本次 ensure 已失败。 |
| 合法 complete export 中 concrete 所需 matching population 为空 | Proven absence；是否允许 complete empty Artifact 或日期回溯，唯一由 concrete 已锁定的业务规则决定。 |
| 本次 ensure incomplete / unit failures、operation / prerequisite / integrity failure 或非法 export | ObservationOperationError；不当作 absence、不消费 partial、不跳过 candidate、不换 Snapshot。 |

```text
cache missing != proven absence
runtime failure != proven absence
DataLake failure != permission to change candidate date
```

Read-only prerequisite failure 也属于 operation failure，不能绕过 public contract 将目标未知解释为普通 cache missing。日期回溯是 complete-but-absent 的 concrete business rule，不是 infrastructure fallback；完整性失败的 default 行为保持下方 runtime failure policy。

### Public object lifetime 与 opaque execution

DataLake public semantic objects 仅在 Observation 内消费，经 deterministic projection 成为 Observation-owned immutable public values，再交给 Study。Study 不消费 CoverageResult、EnsureResult、OptionsDailyExport、OptionsDailyRow、TradeCalendarExport 或 TradeCalendarRecord；对当前两项 producer，只消费 ExpiryUniverseArtifact、ExpiryDteChainArtifact / ExpiryDteChainRow。即使 upstream object 已 typed，也不能直接嵌入 Artifact；public owned-value mapping 见 [framework IMPLEMENTATION](IMPLEMENTATION.md#python-semantic-object-boundary) 与实际 concrete contract。

Observation 只依赖 public request、result、completeness 与 semantic rows，不解释或依赖 FetchUnit generation / internal selected unit set、Repository layout、SQLite schema、pending transitions、Source batches / pagination、Tushare endpoint / provider request grouping、rate limiting / retry、worker concurrency 或 generation schema。Dataset ensure 内部如何 skip successful units、fetch missing / non-success units、调用 Source / provider，均不能成为 Research dependency；public counters / failures 仍按 Dataset contract 消费，不以此重建内部执行逻辑。

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

本专题只编码 semantic dependency rules，不创建 Python package / adapters、SQLite / persistence design、public ensure types、retry / fallback engine、provider wrapper、generic DataSource / Repository、DataLake / Snapshot facade、DI framework、plugin / registry、workflow engine、Study / Analysis implementation、CLI 或 HTTP API。不创建 DataLakeObservationAdapter、DatasetGateway、ensure_and_export()、DataLakeClient、CoverageCoordinator、MarketDataProvider、UpstreamProvider、SourceResolver、FallbackProvider、DataSourceRegistry、SnapshotRepository、SnapshotGateway、SnapshotProvider 或 GenericSnapshotService。
