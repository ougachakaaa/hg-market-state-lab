# Observation Authority Authoring

本文件拥有独立 Observation 的创建与设计交接流程。先读 [Observation architecture](ARCHITECTURE.md) 确认边界，再按 [Schema](SCHEMA.md) 锁定 concrete semantics；Research identity 与导航见 [module architecture](../ARCHITECTURE.md)。本流程不在 Study Method 内定义 Observation。

## Semantic decision workflow

```text
clarify what is observed
    → lock business inputs
    → lock business key / canonicalization
    → lock population / grain
    → lock upstream public facts
    → lock deterministic derivation
    → lock validity / missingness
    → lock Artifact contract / completeness
    → dependency reconciliation
    → only then implementation
```

Agent 先整理 human 已给出的观察意图、事实来源、限制和未决问题，区分 human decision、canonical fact 与 unresolved decision。可以组织措辞、命名与布局；不得自行补全会改变 business inputs、key、population、grain、derivation、validity、Artifact 含义或解释边界的未决 semantic decision。

每个实质未决项须说明缺失决定、为何影响观察含义、推荐 resolution 及有实际差异的 alternatives；建议不构成默认授权。取得 human 明确决定后更新草稿并重新核对 schema。既有 Study、shared helper 或 implementation 不能替代缺失决定。

## Authority placement 与 review

Concrete Observation 从 `observations/<observation-id>/ARCHITECTURE.md` 进入；本 framework 不规定 ID token format 或 implementation package mapping。Entry 只保留 purpose / identity、边界、关键 invariants、依赖概览与导航。按独立 semantic concern 下沉详细契约；不机械复制 Study 的四文件布局，也不因省文件把独立 concern 全塞入 entry。

Authority 完成前逐项核对 Schema 的十三个 areas、跨 area 一致性、canonical ownership、entry reachability 与相对链接。消费者无需了解 SQLite、Study question 或 Analysis conclusion 才能理解 Artifact contract。未解决的业务语义不能发布为 complete authority。

## Dependency reconciliation 与 implementation handoff

Concrete authority 可以明确记录尚未就绪的 public upstream capability，但必须完整表达需要哪些事实、谁拥有它们及缺口是什么。随后只读取实际需要的 upstream authority，与对应 owner reconciliation；不得读取所有 sibling products 或穿透 Source / persistence internals。

只有 concrete semantics 已完整且依赖能力已就绪、边界无冲突，才交接 implementation。Implementation 不由本流程自动触发，不预建统一 schema、executor、registry 或 retry engine。Observation public invocation 的 delivery 与 implementation topology 需后续单独明确，不能从现有 Study CLI 推导 Observation CLI。

若任务来自 Study capability gap，独立 Observation design / implementation 完成后返回 [Study Authoring](../studies/AUTHORING.md)，核对 Artifact bindings、workflow / retained results，以及实际需要的 optional Analysis / Evidence；不强制 observation-only Study 创建它们。Refresh / definition evolution 等 [deferred semantics](ARCHITECTURE.md#explicitly-deferred-decisions) 不因本流程自动锁定。
