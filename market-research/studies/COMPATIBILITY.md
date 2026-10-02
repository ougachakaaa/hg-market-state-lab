# Research Study Compatibility

本文件拥有既有 retained Study 的 schema evolution、reconciliation、migration 与 consolidation policy。新 Study 的默认路径从 [Authoring](AUTHORING.md) 进入，不以本文件或历史 shared Research semantics 作为语义来源。

## Existing Study reconciliation

**Schema evolution is non-retroactive by default.** 已有 retained Study 继续依照其成立时的 canonical authority 工作；新版 creation isolation 或 Completeness Gate 不自动使其失效。现有对 `market-research/shared/*` 的合法 Research semantic dependency 保持有效，不能因新版 schema 更新而强制拆除、重新物化 Observation / Analysis、修改 artifact、重跑研究或改变研究含义。

[Implementation Package Contract](IMPLEMENTATION.md) 的默认 package topology 也不追溯触发既有 implementation 的拆分或迁移。新 runnable Study 在首次实现时必须遵守它；已有 Study 仅在 human 明确要求重构该实现，或某项 implementation change 实质性重做相关 semantic responsibilities 时，按 [Review](REVIEW.md) 的 implementation topology check 审查该次改动涉及的责任边界。仅修复局部 bug、维护现有 CLI 或 evidence 输出，不自动要求整包迁移；已有 Study 的现行 evidence 与执行行为继续保持其既定 contract。

仅在 human 明确要求升级该 Study、发生 substantial semantic modification、authority 存在真实内部矛盾或 ownership conflict、implementation change 必须新增尚未定义的 Study semantic，或专门执行 Research Semantic Consolidation / migration 时，才对相关旧 Study 考虑 reconciliation。只处理触发事项所涉及的语义与真实冲突，默认保留原有研究含义；旧 Study 已有 shared dependency 不因创建规则而迁移。进入 reconciliation 后，真正缺失的研究决定依 [Authoring](AUTHORING.md) 的 human semantic-decision loop 处理，不能从现有实现或 sibling Study 猜测，也不为新版 schema 风格机械重排整份旧 authority。

当前没有 retained Study；下述 compatibility 与 consolidation policy 继续保留，供后续实际需要时使用。

## Method 与 consolidation

当前 Study canonical authority 描述该 Study 唯一有效的 Method，不维护 `method_v1` / `method_v2` lineage 或 method version registry。历史 evidence 的兼容性通过 provenance、适用时的 artifact identity 与 execution reconciliation 判断；若两种方法需长期代表不同研究语义，先重新判断是否属于不同 Study / hypothesis。

`CONSOLIDATE` 是 human 明确发起的独立工作，不是新 Study 创建或 schema/topology 演进的默认步骤。只有此时才比较多个成熟 Study，决定是否提升真正稳定的 shared Research semantics，并按需 reconciliation consumers 或抽取 shared code。已有合法 shared semantic owners：

- [Empirical Distribution Research Semantics](../shared/distribution/ARCHITECTURE.md)
- [IM Basis Research Semantics](../shared/im_basis/ARCHITECTURE.md)
- [Price-to-Lagged-Reference Research Semantics](../shared/price_to_lagged_reference/ARCHITECTURE.md)

拆分既有 Study authority 仅在确有阅读收益且可保持所有既定语义时进行；不因为文档较长或新版 topology 自动拆分，不机械重排历史 authority，不修改公式、参数、artifact contract、retained evidence 或 runner。
