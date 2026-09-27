# CLI and persisted output delivery authority

本文档拥有 `dms` CLI executable binding、dispatch 与共享 persisted-output convention。Product 是 semantic owner：从 [Capability Catalog](../../../CAPABILITIES.md) 进入其 request、result、orchestration、public entry 与 classified failure。Product 与 Application Service 的关系见 [module architecture](../../../ARCHITECTURE.md)；HTTP delivery 由 [backend-api](../../../../backend-api/ARCHITECTURE.md) 拥有。

## 1. CLI executable catalog

`services/catalog.py` 是显式、静态、仅服务于 `dms` 的 executable binding table，不是 repository Product catalog 或所有 Product Application Service 的 semantic inventory。当前只绑定返回 persisted artifact `Path` 的 `csi1000-5d-analysis`。其产品身份、query 和 canonical output 由 [CSI1000 5D Product](../products/csi1000_5d_analysis/ARCHITECTURE.md) 与其 specialized authority 拥有。

Index Daily History、CSI1000 IM Basis History、MO Option Chain 与 MO Premium Plane 是 request-scoped Products；其 public result 与 delivery surface 从各自 Product authority 进入，不需适配 `Path`-returning CLI binding。`index_daily` 和 `stock_daily` 是 Source Capture capability，不升级为 Product Application Service。CLI catalog 不扫描文件系统，也不引入 plugin、dynamic registry 或 service lifecycle framework。

## 2. `dms` CLI

V1 只支持 `dms list` 与 `dms get`。`dms list` 列出 CLI-addressable executable entries，至少输出 `service_id` 与 `description`；当前包含 `csi1000-5d-analysis`，不列出上述 request-scoped Products。完整 Product/capability discovery 见 [Capability Catalog](../../../CAPABILITIES.md)。

```text
dms get <service_id> --date YYYY-MM-DD
```

当前 `service_id` 为 `csi1000-5d-analysis`；`--date` 是调用方必填的 `target_trade_date`，不支持 `today`、`latest`、`yesterday`、自动寻找最近交易日或 fallback。CLI 只解析和校验 CLI 输入、resolve binding、调用 Product execution entry、报告结果或错误；Capture ordering、Preparation、结果和 semantic failure 由 Product authority 拥有。普通用户或 Agent 请求该 persisted result 时使用 `dms`，而不自行编排 Capture。

## 3. Persisted output convention

`output/` 是 persisted-artifact Product Application Service 的用户级输出根目录；不适用于 request-scoped results。共享目录约定是：

```text
output/<service_id>/<target_trade_date>/<service artifact>
```

当前 `csi1000-5d-analysis` 发布到 `output/csi1000-5d-analysis/<target_trade_date>/snapshot.json`。`service_id + target_trade_date` 确定该 Product 的 output partition；`snapshot.json` 的内容和发布时机由 [Product authority](../products/csi1000_5d_analysis/ARCHITECTURE.md) 拥有。日粒度只描述这个 Product 的 request/output partition，其内部 Raw 可以覆盖多个历史交易日；不推广为所有 Product 的 query shape。

`data/raw/` 存放选择持久化 Raw 的 Product 的内部 Source Facts artifact。[Daily Market Snapshot](../products/daily_market_snapshot/ARCHITECTURE.md) 继续使用自己的 `data/snapshots/YYYY-MM-DD/` Analysis-ready Artifact 契约；这个目录不是所有非 `dms` Product 的默认输出。`csi1000-5d-analysis` 只发布上述 `output/` canonical result，不维护第二份 `data/snapshots/csi1000-5d-analysis/...`。具体 Raw、artifact 名称及内容均由各 Product authority 拥有；request-scoped Product 不因本目录约定而必须写 Raw 或 final result。

## 4. HTTP and public Python boundaries

`dms`、HTTP 和 public Python execution entry 是不同 consumer surfaces，不是 Product semantic owners。HTTP adapter 投影完整 Product result 并映射 transport error/status，不调用 Source、不重新计算 Preparation，也不重新分类 Product failure。Index Daily History 与 CSI1000 IM Basis History 的 public Python contract 由各自 Product 拥有；MO Option Chain 与 MO Premium Plane 的 HTTP contract 由 `backend-api` 拥有。具体导航从 [Capability Catalog](../../../CAPABILITIES.md) 进入对应 Product。

不在本 context 设计 scheduler、database、通用 API platform、cache/retry framework、自动日期或研究分析。
