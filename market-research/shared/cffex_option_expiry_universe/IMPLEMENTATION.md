# Expiry Universe resolver Python mapping

本文件将 [CONTRACT](CONTRACT.md) 映射为 public Python boundary；不改变 observed-window selection、完整性或失败语义。稳定入口见 [ARCHITECTURE](ARCHITECTURE.md)。

Canonical package 为 `market_research.shared.cffex_option_expiry_universe`，发布 `ExpiryUniverseRequest`、`ExpiryUniverseResult`、`ExpiryUniverseResolver`、`create_resolver`，以及独立的 `ExpiryUniverseError`、`ExpiryUniverseInvalidRequestError`、`ExpiryUniverseOperationError`。错误不继承 Observation errors。

`create_resolver()` 无参、无 I/O；`resolver.resolve(request: ExpiryUniverseRequest) -> ExpiryUniverseResult` 是唯一 public operation。Request 的三个必填 fields / types 引用 CONTRACT；operation 前重新验证，未来 window 按 Options public request validation 拒绝并映射为 resolver invalid request。

Result 为 immutable Research-owned value：product_code、expiry_start_date、expiry_end_date、expiries: tuple[date, ...]、complete: bool（成功固定 True）及 provenance。Provenance 和其 scope / window / coverage 均为本 component 自己的 frozen values，field paths / meaning 引用 CONTRACT 的 upstream public context；不包含 daily rows、Observation identity、semantic_identity、path 或 upstream runtime objects。

Result construction 验证请求绑定、sorted unique in-range dates、owned context types、exact Options dataset / view / schema / scope / window 与 complete coherent coverage。Study 可使用 public result constructor 重新校验 collaborator return，非法值归 resolve_expiry_universe stage。

Internal composition 只注入 Options public service factory；每次 resolve 调用 exact-range ensure → export → validate → derive / project。无 Research persistence、lookup、publication 或 durable hit，重复调用重新执行 public sequence；DataLake 自己复用其 cache。Interruption 传播，expected operation / completeness failure 映射为 resolver operation error，安全 ensure diagnostics 原顺序保留。普通 consumer 不传 SQLite path、provider、credential 或 output 配置。

Source 按 public models/errors、resolver orchestration、derivation、upstream validation 分拆；public init 使用 explicit redundant aliases 并指向本 mapping / canonical entry。Chain Observation 不依赖本 component；其 lifecycle 不变。验证与当前状态见 [reconciliation](../../IMPLEMENTATION_RECONCILIATION.md#shared-component-runtime-reconciliation)。
