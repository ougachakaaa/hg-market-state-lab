# backend-api HTTP Product Catalog

本文件是 `backend-api` 的导航 catalog，不定义 endpoint、DTO、error/status 或业务语义。先阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 确认 transport boundary，再选择当前任务需要的最小 authority 路径。

| HTTP product | HTTP contract | Owning application/product authority |
| --- | --- | --- |
| MO Option Chain | [HTTP contract](products/mo_option_chain/http-contract.md) | [market-snapshot product](../market-snapshot/src/daily_market_snapshot/products/mo_option_chain/ARCHITECTURE.md) |
| MO Premium Plane | [HTTP contract](products/mo_option_premium/http-contract.md) | [market-snapshot product](../market-snapshot/src/daily_market_snapshot/products/mo_option_premium/ARCHITECTURE.md) |

本 catalog 只发现 repository HTTP products。Query/Command identity、application result 与 semantic failure classification 由右侧 owning module authority 定义；wire projection 由中间的 HTTP contract 定义。
