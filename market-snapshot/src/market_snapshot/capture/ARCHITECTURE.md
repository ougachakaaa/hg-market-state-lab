# Shared Source Capture authority

本文件是共享 Source Capture bounded context 的入口。模块分层与依赖方向以 [market-snapshot 架构](../../../ARCHITECTURE.md) 为准；产品自己的 universe、窗口、Raw scope 与 completeness 必须由对应产品 authority 拥有。

## Ownership

本 context 拥有外部 Source endpoint 调用、Source query 参数、共享 Capture 身份、公共 Source 字段事实与 minimal normalization。它不拥有产品编排、analysis formula、read model、HTTP 或展示语义。

## Capture catalog

| Capture | Implementation | Specialized authority |
| --- | --- | --- |
| Common normalization | `common.py` | [Common contract](common-contract.md) |
| Index / stock daily | `index_daily.py` and product adapter | [Index and stock contract](index-stock-contract.md) |
| MO option basic / daily | `mo_option_basic.py`, `mo_option_daily.py` | [MO option contract](mo-option-contract.md) |
| IM futures basic / daily | `im_futures_basic.py`, `im_futures_daily.py` | [IM futures contract](im-futures-contract.md) |

Daily Market Snapshot 的六指数范围与 stock scope、CSI1000 history，以及各产品 completeness 均从 [Capability Catalog](../../../CAPABILITIES.md) 进入对应产品，不在本入口重复定义。
