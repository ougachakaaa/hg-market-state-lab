# ui_http HTTP Product Catalog

本文件是 `ui_http` 的 HTTP authority 导航 catalog，不定义 endpoint、DTO、业务语义或实现状态。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认 transport ownership，再进入当前任务需要的 specialized contract。

| HTTP product | Owning business module | Canonical HTTP contract |
| --- | --- | --- |
| MO Option Chain | `data_snapshot` | [HTTP contract](products/mo_option_chain/http-contract.md) |
| Descriptive Research | `market_research` | [HTTP contract](products/research/http-contract.md) |
| MO Premium Plane | `data_snapshot` | [HTTP contract](products/mo_option_premium/http-contract.md) |

Owning business module 定义 query/result 与 classified semantic failures；本 catalog 只导航 HTTP transport authority，不创建 repository product catalog、shared DTO schema 或通用 API framework。
