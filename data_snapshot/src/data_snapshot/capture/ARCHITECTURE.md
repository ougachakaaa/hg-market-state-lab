# Shared Source Capture authority

本文件是跨 Product 复用的 Source adapter、Source fact 与 Capture mechanics 入口。Product ownership 与执行角色以 [data_snapshot 架构](../../../ARCHITECTURE.md) 为准；产品自己的 universe、窗口、Raw scope 与 completeness 必须由对应产品 authority 拥有。

## Ownership

本 context 拥有外部 Source endpoint 调用、Source query 参数、共享 Capture 身份、公共 Source 字段事实与 minimal normalization。Capture 产出逻辑 Source Facts；产品决定是否持久化为自己的 Raw Artifact。本 context 不拥有产品编排、产品专属 Capture scope、analysis formula、read model、HTTP 或展示语义。外层 `capture/` 不是所有 Product Capture 实现的强制归属目录。

有效的产品请求若自然展开为多个 Source endpoint 调用，Source/Capture execution 必须遵守 provider 的请求频率限制。Provider library 抛出的调用异常须在 Source 边界归一化为项目 Source error，不得以原始异常穿透到 Capture 或 Product。

## Capture catalog

| Capture | Implementation | Specialized authority |
| --- | --- | --- |
| Common normalization | `common.py` | [Common contract](common-contract.md) |
| Index daily | `index_daily.py` | [Index daily contract](index-daily-contract.md) |
| MO option basic / daily | `mo_option_basic.py`, `mo_option_daily.py` | [MO option contract](mo-option-contract.md) |
| CFFEX equity-index futures basic / daily | `im_futures_basic.py`, `im_futures_daily.py` 的 IF/IH/IC/IM family 参数化 Capture；保留 IM caller | [CFFEX futures Source contract](im-futures-contract.md) |

各产品的 Source scope、窗口与 completeness（例如 CSI1000 history）均从 [Capability Catalog](../../../CAPABILITIES.md) 进入对应产品，不在本入口重复定义。

## Historical session Source execution

MO historical acquisition uses a shared process-local budget of 450 request
starts/minute (60/450 seconds between starts), including attempts and retries,
across all session endpoints/clients. Reservation locks do not cover HTTP calls.
Explicit provider throttling pauses the entire session budget for 60 seconds
and retries once. Connection errors/timeouts retry once after one second;
permission, input and contract failures are not retried. Legacy futures pacing
is unchanged for other callers; session bulk futures calls use session pacing
only. Metrics aggregate endpoint attempts, response seconds, pacing seconds,
retry counts and safe failure categories. They never include secrets or raw
provider error text. Separate processes are not coordinated by this budget.
