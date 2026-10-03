# DataLake Implementation Reconciliation

## Purpose 与 baseline

本文件是 authority / implementation 的 live drift register，不拥有 semantic contract。稳定入口为 [module architecture](ARCHITECTURE.md)；rebuild-only decisions 唯一归 [PERSISTENCE.md](PERSISTENCE.md)，public boundary / failure mapping 归 [APPLICATION.md](APPLICATION.md)。

本轮 implementation reconciliation 基于 `a729ad3f31408b92db4d5c5b598108ba5c78face`，对齐已冻结 catalog classification、Index failure isolation 与 provider dispatch 限流契约，不改变 Dataset public semantic contracts，不操作真实 cache 或执行 rebuild。

## Current reconciliation status

Rebuild-only persistence compliance gap 已关闭。共享 Repository 只接受当前 generation 3 及其 required persistence shape；generation 2、未知 generation、不兼容结构或旧 inline basis 不再通过 compatibility path 读取或写入。失败经现有 `OperationError` boundary 暴露，诊断明确 owning Dataset cache incompatible / rebuild required，不作为 missing / incomplete 返回。

Generation 2 dual-read、2 → 3 automatic upgrade、migration backup 与 transactional upgrade / backup recovery mechanics 已移除。检测不自动修改、删除、覆盖或重建 incompatible cache；原 generation 3 schema、frozen basis 与逐 unit transaction / committed read snapshot 保持不变。现有 factory、Dataset public request/result/view、CLI adapter 与 Research consumer API 无需调整。

此前受影响 persistence concerns 未发现剩余 authority / implementation drift；该关闭结论保持有效。未实现 rebuild service / CLI、force、migration framework 或 refresh semantics。

本轮审查发现的 implementation gaps：

- **已关闭：Futures / Options catalog classification。** 排除 metadata 前核对完整 identity / product evidence；冲突按所有候选产品失败，无法归属且不能证明 unrelated 时按 catalog failure 处理。合法产品继续执行，不能通过排除可疑行缩小 expected universe。
- **已关闭：Index duplicate failure isolation。** 完整分页保留重复 rows；可定位的重复 daily / metadata identity 只失败对应 unit / code。重复整页或无法证明穷尽的响应仍失败整批，不静默去重。
- **开放：Provider dispatch 限流。** 放行时间与实际发送分离，日志或线程延迟可能使实际 request starts 小于 TUSHARE authority 的 minimum interval。

## Verification boundary

Catalog classification 使用隔离 fake Source 验证 code / symbol / product / underlying 冲突、无法归属行、合法 unrelated 行及多产品失败隔离；失败产品不发布 success facts，全批 catalog failure 不发起 daily requests。

Index 使用隔离 fake Source 验证同页及不同非重复页的 duplicate、混合合法日期与 metadata codes、原始 row-count offset、重复整页拒绝及失败 metadata 不重复请求。局部 failures 与合法 success 的 accounting / export 保持一致。

隔离临时 fixture 验证 generation 2、未知 generation、identity / shape 不兼容、旧 basis representation 与非法 SQLite 在以下路径明确失败：

- `coverage` / `export`（包含 zero-target）。
- 需要写入的 `ensure`、全部目标已缓存的 `ensure` 与 zero-target `ensure`。
- Repository writer session 入口。

失败检查同时验证 owning Dataset / rebuild diagnostic、SQLite 字节与修改时间不变、无 backup 或其他新增文件、无 Source initialization / fetch。旧 migration acceptance tests 已由 incompatible rejection 和 current-generation history preservation tests 取代。

Compatible generation 3 的 read-only 查询、cached / zero-target ensure accounting、frozen basis 去重 / 历史不变、Dataset completeness、逐 unit atomic success 与 export committed-snapshot consistency 继续由 core / Dataset tests 验证。Module / CLI tests、installed imports、Ruff / mypy、repository architecture / authority topology 及 Research consumer regression checks 覆盖相关 boundary；执行结果与通过数属于本轮报告，不长期作为 contract。

## Boundary readiness

DataLake → Research public boundary 可以继续作为并行开发的稳定基础。本轮关闭 producer persistence compliance gap，未改变 public request/result/view、population、grain 或 completeness；Research 仍直接消费已声明 Dataset public semantic objects，不依赖 internal persistence mechanics，也无需 downstream API 适配。现存 incompatible cache 仍须显式由 owning Dataset 处理；本轮不发布 rebuild execution mechanics。
