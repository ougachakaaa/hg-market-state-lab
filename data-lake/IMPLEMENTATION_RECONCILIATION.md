# DataLake Implementation Reconciliation

## Purpose 与 baseline

本文件是 authority / implementation 的 live drift register 与下一轮 handoff，不拥有 semantic contract。稳定入口为 [module architecture](ARCHITECTURE.md)；rebuild-only decisions 唯一归 [PERSISTENCE.md](PERSISTENCE.md)，public boundary / failure mapping 归 [APPLICATION.md](APPLICATION.md)。

核对基准：`e25fd6c6a4e7dbaa3afc4ac488edbd201d8f86e8`。本次 authority-only encoding 不修改 implementation、tests、CLI、SQLite 或数据文件，不执行 rebuild。

## Open gap：rebuild-only persistence compliance

当前 `src/data_lake/_repository.py` 与新 contract 不一致：

- `_identity` 仍接受 generation 2 和 3，`_validate` / snapshot 路径按 generation 解释不同 basis representation，形成 legacy dual-read。
- 写 session 在 generation 2 上调用 `_upgrade`；该路径创建 backup、转换 frozen basis、更新 schema_version，并保留升级失败 rollback / backup recovery mechanics。
- `tests/test_core.py` 的 legacy read / cached ensure / upgrade-preserves-history、failed upgrade、backup failure、interrupted upgrade acceptance 仍要求这些 superseded 行为。
- 现有 incompatible storage diagnostics 未完整表达 owning Dataset cache rebuild 要求。

该 gap 属于 DataLake producer；[Research reconciliation](../market-research/IMPLEMENTATION_RECONCILIATION.md) 只引用，不重复维护。当前实现通过旧测试不能证明新 persistence contract compliance。

## 下一轮 implementation handoff

在单独授权的 implementation task 中，移除 generation 2 read/upgrade、migration backup 和相关 compatibility mechanics；仅接受当前 compatible generation/shape。不兼容 cache 经 public failure boundary 明确返回 OperationError 和 owning Dataset rebuild 诊断，不伪装 missing / incomplete，不自动修改、删除、升级或重建缓存。

后续 acceptance 必须覆盖 coverage / export、需要写入的 ensure、cached / zero-target ensure 对不兼容缓存明确失败；验证失败不改变旧 SQLite、不产生 migration backup，并保留 compatible generation 3 的 frozen basis、completeness、atomic successful unit 与 export snapshot。只用临时 fixtures，不操作真实缓存。届时再 reconciliation 旧 migration tests，不在本 authority-only task 修改它们。

Generation 3 内部 shape、Dataset public payload、operation family 与 Research-owned persistence 不由上述 handoff 重设计；不新增 rebuild CLI、gateway、migration / refresh engine。

## Boundary readiness

Authority 已冻结具体 Dataset public service 与 Research producer permissions，可作为 DataLake → Research 稳定并行开发 boundary。Internal persistence incompatibility 不改变 public request/result/view，Research 不依赖其 mechanics；runtime rebuild-only compliance 仍由上述 open gap 阻塞。设计完成不等于实现已符合契约。

## Verification boundary

当前检查只验证 authority links / anchors / reachability、semantic reconciliation、完整 Markdown diff 与 scope。Runtime compliance 的验收留给下一轮 implementation，不以 topology green 或历史 runtime test evidence 替代。
