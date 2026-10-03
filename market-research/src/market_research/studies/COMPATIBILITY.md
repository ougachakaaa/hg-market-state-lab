# Research Study Compatibility

本文件拥有既有 retained Study 的非追溯 schema evolution、reconciliation、migration 与 consolidation policy。新 Study 从 [Authoring](AUTHORING.md) 进入并遵守 [Observation-first Schema](SCHEMA.md)，不以历史 authority / shared helpers 作为默认语义来源。

## Legacy retained structure

**Schema evolution is non-retroactive by default.** 既有 Study-local Observation、conditional component Artifact identity、既定 shared semantic dependencies 与 package topology 是合法 legacy retained structure，继续依照其成立时的 canonical authority 可读、可复核。新版 framework 不自动使历史 Study、authority、implementation 或 evidence invalid。

Observation-first 更新不自动迁移既有 Study、不重写旧 authority / evidence、不要求旧 implementation 立即移除 observations.py、不重跑研究，也不把历史 Observation 自动提升为独立 capability。只有 human 明确触发针对某个 concrete Study 的 Observation-first reconciliation，才迁入新模型。

```text
old retained Study remains readable
new Study follows Observation-first model
migration is explicit and human-triggered
```

当前 retained Study / implementation 状态见 [implementation reconciliation](../../../IMPLEMENTATION_RECONCILIATION.md)；本政策保护历史 retained structure 与显式迁移，不依赖当前是否存在 concrete consumer。

## Existing Study reconciliation 与 implementation maintenance

Human 明确要求升级 / reconciliation、substantial semantic modification、真实 authority contradiction / ownership conflict、必须新增未定义语义的 implementation change，或 human-triggered migration / consolidation 可以触发相关范围的核对。触发核对不等于授权自动迁入 Observation-first；该 architecture migration 须 human 明确指定。

仅处理触发事项与真实冲突，保留已有研究含义，不为新版文件风格机械重排旧 authority。局部 bug 修复、CLI / evidence 维护不要求整包迁移。缺失研究决定走 Authoring human loop，不从 implementation 或 sibling Study 猜测。

[Implementation Package Contract](IMPLEMENTATION.md) 对新 runnable Study 首次实现有效；已有 implementation 不因更新自动拆分。Human 要求重构或改动实质重做某些 responsibilities 时，按 [Review](REVIEW.md) 审查该次涉及的边界，同时尊重尚未迁移的 legacy contract，不由新版 topology check 强制重做整包。

显式 Observation-first migration 必须核对 independent Observation owner、invocation / Artifact contracts、Analysis consumption 与 Evidence traceability；历史 evidence、provenance 和执行 behavior 的变更范围需单独明确，不能从迁移请求推导自动 overwrite 或重算。

## Method 与 consolidation

当前 Study authority 描述其唯一有效 Method，不维护 method_v1 / method_v2 lineage 或 version registry。历史 evidence 兼容性按其既定 provenance、适用 identity 与 explicit reconciliation 判断；需长期保留不同研究含义时，先判断是否是不同 Study / hypothesis。这不决定 Observation definition evolution 或 Artifact refresh，后者见 [Observation deferred decisions](../observations/ARCHITECTURE.md#explicitly-deferred-decisions)。

`CONSOLIDATE` 仅由 human 明确发起，不是新 Study 创建或 schema evolution 的默认步骤。只有此时才比较多个成熟 Study，决定是否提升稳定 shared Research semantics，并按需 reconciliation consumers。当前保留的 historical shared canonical owners：

- [Empirical Distribution Research Semantics](../shared/distribution/ARCHITECTURE.md)
- [IM Basis Research Semantics](../shared/im_basis/ARCHITECTURE.md)
- [Price-to-Lagged-Reference Research Semantics](../shared/price_to_lagged_reference/ARCHITECTURE.md)

这些窄 authority 和 helpers 继续有效，不自动成为 Observation、reusable Analysis 或新 Study 默认依赖。新的小领域 Component 分类 / 提升见 [Component authority](../shared/ARCHITECTURE.md)，不要求为明确的机制复用先启动历史 CONSOLIDATE；后者仍只处理已有 Study research-semantic consolidation。Consolidation 不能替代 Observation-first migration、定义 refresh / versioning，或建立 generic research framework。拆分历史 authority 仅在有真实阅读收益、能保持既定语义且在授权范围内时进行；不自动修改公式、参数、Artifact contract、evidence 或 runner。
