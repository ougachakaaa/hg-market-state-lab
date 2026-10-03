# Observation Upstream Dependency specialization

本文件仅拥有 Observation retained lifecycle 与公共 upstream policy 的衔接，继承 [Observation architecture](ARCHITECTURE.md) 与 [Research public upstream authority](../../../UPSTREAM.md)。DataLake-first selection、sufficiency / Snapshot selection、minimum legal Dataset calls、one committed export proof、missing / proven absence / failure、provider prohibition、multi-upstream ownership 与 public provenance 唯一由公共专题定义，不在此复制。

## Retained lookup 先于 upstream access

Observation 根据 declared business request ensure complete retained Artifact。沿用 [framework reuse](ARCHITECTURE.md#business-identity-与-invocation-lifecycle) 与 [publication lifecycle](IMPLEMENTATION.md#complete-publication-与-concurrency)，complete lookup 必须先于 DataLake / component / upstream dependency factories 或 operations：

    Observation.ensure(request)
        → validate / canonicalize → lookup Observation-owned persistence
            ├── complete hit → return retained Artifact
            │                  zero dependency factories / operations / recomputation
            └── miss → declared public upstream / component invocation
                     → establish required complete inputs
                     → deterministic derivation / whole-Artifact validation
                     → atomic durable publication → return

Complete hit 不因 Dataset cache / credential / provider 当前不可用而重访上游。Corrupt / unreadable retained state 依 IMPLEMENTATION 失败，不伪装 miss。Component result 无此 lookup / publication lifecycle；component 使用 DataLake cache 不等同于 Observation Artifact reuse。

## Public output、failure 与 provenance

Miss 只通过已选 public contract 消费完整 facts / component results；具体 invocation sequence 归 actual concrete owner，当前为 [DTE-chain implementation](cffex_option_expiry_dte_chain/IMPLEMENTATION.md#canonical-execution-mapping)。Component-mediated facts 必须保持原 canonical upstream owner / public snapshot proof，不把 helper 变成新的市场事实 owner。

Observation 将 public inputs 投影为自己拥有的 immutable Artifact values，见 [owned-value mapping](IMPLEMENTATION.md#python-semantic-object-boundary)。Study / Analysis 不需 import upstream objects。Failed ensure、invalid / incomplete export、dependency / prerequisite / integrity failure 属 ObservationOperationError；不消费 partial、不当作 proven absence、不换源。合法 empty / date fallback 仍由 concrete owner 决定。

Artifact provenance 描述实际 selected Dataset / Product / component contract 与 concrete 要求的 public context，不穿透 provider / Repository / SQLite。Provenance 不自动进入 business key，沿 [deferred evolution](ARCHITECTURE.md#explicitly-deferred-decisions) 保留现有未决项；不自行加入 timestamp / digest / version 绕过幂等。

## Navigation 与维护边界

Design 从本文件进入 [公共 policy](../../../UPSTREAM.md)，再按 [Schema](SCHEMA.md) / [Authoring](AUTHORING.md) 锁定 actual Observation；runtime handoff 进入 [IMPLEMENTATION](IMPLEMENTATION.md)。[Universe resolver](../shared/cffex_option_expiry_universe/ARCHITECTURE.md) 已是 component，仅继承公共 policy，不继承本 lifecycle。

本文件不定义新的 operation family、producer schema、cache / refresh engine、provider adapter、registry 或 execution framework。当前差异见 [reconciliation](../../../IMPLEMENTATION_RECONCILIATION.md#shared-component-semantic-reconciliation)。
