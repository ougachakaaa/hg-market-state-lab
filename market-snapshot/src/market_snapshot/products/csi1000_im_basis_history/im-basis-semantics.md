# CSI1000 IM Basis History basis compatibility authority

本文档从属于 [CSI1000 IM Basis History Product](ARCHITECTURE.md)，只说明本产品对 [共享 CFFEX 股指期货期限结构与基差语义](../../cffex_equity_index_basis/ARCHITECTURE.md) 的 IM-only 使用和兼容边界。共享文件是 family/underlying/listing、active lifecycle、M0/M1/Q1/Q2、calendar distance、annualization、basis formulas、validation 与 canonical ordering 的唯一 owner；本文不再定义平行版本。

本产品仍仅查询 `IM` 与其 CSI1000 标的，使用原有显式起止日期、实际 CSI1000 日线观测日、完整 IM panel 和原有 Source scope / completeness。其 [data authority](data.md) 与 [read/application contract](read-contract.md) 继续拥有这些产品专属选择。旧 public `CSI1000IMBasisHistoryRequest`、`CSI1000IMBasisHistoryResult`、`IMBasisObservation`、`CSI1000IMBasisHistoryError` 和 `run_csi1000_im_basis_history` 的名称、字段及可见行为保持兼容；尤其保留 `ts_code`、`future_close` 与原有 result 形状。共享语义的提升不要求旧 Research consumer 改请求、CLI 或 retained evidence。

当前 Python 实现仍位于本产品目录；这是本轮 authority-only reconciliation 的实施状态，不构成第二 canonical semantic owner。后续代码迁移须保持上述 public compatibility，并以共享 authority 为准。
