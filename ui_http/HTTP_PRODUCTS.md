# ui_http HTTP Product Catalog

本文件是 `ui_http` 的 HTTP authority 导航 catalog，不定义 endpoint、DTO、业务语义或实现状态。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认 transport ownership，再进入当前任务需要的 specialized contract。

| HTTP product | Owning business module | Canonical HTTP contract |
| --- | --- | --- |
| MO Option Chain | `data_snapshot` | [HTTP contract](products/mo_option_chain/http-contract.md) |
| Descriptive Research | `market_research` | [HTTP contract](products/research/http-contract.md) |
| Research Publication | `market_research` | [HTTP contract](products/research_publication/http-contract.md) |
| MO Premium Plane | `data_snapshot` | [HTTP contract](products/mo_option_premium/http-contract.md) |

Owning business module 定义 query/result 与 classified semantic failures；本 catalog 只导航 HTTP transport authority，不创建 repository product catalog、shared DTO schema 或通用 API framework。

所有产品的 HTTP access 前置条件共同遵循 [Authentication MVP V1](AUTHENTICATION.md)。公共 Auth endpoints、认证错误与 Cookie 生命周期只由该专题契约定义；产品错误表继续只拥有通过 access gate 后的产品响应。
