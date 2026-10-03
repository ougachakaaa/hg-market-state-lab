# DataLake Implementation Reconciliation

## Purpose 与 baseline

本文件是 authority / implementation 的 live drift register，不拥有 semantic contract。稳定入口为 [module architecture](ARCHITECTURE.md)；rebuild-only decisions 唯一归 [PERSISTENCE.md](PERSISTENCE.md)，public boundary / failure mapping 归 [APPLICATION.md](APPLICATION.md)。

本轮 implementation reconciliation 基于 `be5bc0130108c8bdd14274fff9116dc9dab9fed7`，只对齐已冻结 persistence contract，不改变 Dataset public semantic contracts，不操作真实 cache 或执行 rebuild。

## Current reconciliation status

Rebuild-only persistence compliance gap 已关闭。共享 Repository 只接受当前 generation 3 及其 required persistence shape；generation 2、未知 generation、不兼容结构或旧 inline basis 不再通过 compatibility path 读取或写入。失败经现有 `OperationError` boundary 暴露，诊断明确 owning Dataset cache incompatible / rebuild required，不作为 missing / incomplete 返回。

Generation 2 dual-read、2 → 3 automatic upgrade、migration backup 与 transactional upgrade / backup recovery mechanics 已移除。检测不自动修改、删除、覆盖或重建 incompatible cache；原 generation 3 schema、frozen basis 与逐 unit transaction / committed read snapshot 保持不变。现有 factory、Dataset public request/result/view、CLI adapter 与 Research consumer API 无需调整。

本轮受影响 persistence concerns 未发现剩余 authority / implementation drift，也未发现需要新 semantic decision 的 ambiguity。未实现 rebuild service / CLI、force、migration framework 或 refresh semantics。

## Verification boundary

隔离临时 fixture 验证 generation 2、未知 generation、identity / shape 不兼容、旧 basis representation 与非法 SQLite 在以下路径明确失败：

- `coverage` / `export`（包含 zero-target）。
- 需要写入的 `ensure`、全部目标已缓存的 `ensure` 与 zero-target `ensure`。
- Repository writer session 入口。

失败检查同时验证 owning Dataset / rebuild diagnostic、SQLite 字节与修改时间不变、无 backup 或其他新增文件、无 Source initialization / fetch。旧 migration acceptance tests 已由 incompatible rejection 和 current-generation history preservation tests 取代。

Compatible generation 3 的 read-only 查询、cached / zero-target ensure accounting、frozen basis 去重 / 历史不变、Dataset completeness、逐 unit atomic success 与 export committed-snapshot consistency 继续由 core / Dataset tests 验证。Module / CLI tests、installed imports、Ruff / mypy、repository architecture / authority topology 及 Research consumer regression checks 覆盖相关 boundary；执行结果与通过数属于本轮报告，不长期作为 contract。

## Boundary readiness

DataLake → Research public boundary 可以继续作为并行开发的稳定基础。本轮关闭 producer persistence compliance gap，未改变 public request/result/view、population、grain 或 completeness；Research 仍直接消费已声明 Dataset public semantic objects，不依赖 internal persistence mechanics，也无需 downstream API 适配。现存 incompatible cache 仍须显式由 owning Dataset 处理；本轮不发布 rebuild execution mechanics。
