# ui_web frontend feature catalog

本文件是 `ui_web` 正式 vertical slices 的 navigation-only catalog。Application entry、feature navigation 与 composition boundary 见 [application authority](application.md)；具体展示与交互语义由各 feature 的 co-located authority 拥有。

| Frontend slice | 用途 | Canonical authority entry |
| --- | --- | --- |
| MO Option Chain | 展示指定交易日的完整 MO 期权链价格分布 | [mo_option_chain/ARCHITECTURE.md](src/features/mo_option_chain/ARCHITECTURE.md) |
| MO Premium Plane | 检视指定 observation 与取价口径下的 MO 稀疏年化权利金数值平面 | [mo_option_premium/ARCHITECTURE.md](src/features/mo_option_premium/ARCHITECTURE.md) |
| Research Explorer | 浏览已发布的 Research scope、结果与可视化 | [research_explorer/ARCHITECTURE.md](src/features/research_explorer/ARCHITECTURE.md) |
| Futures Basis Research | 选择产品与 inclusive 日期窗口，运行 R01-A 在线基差研究并检视既有六段交互报告 | [futures_basis_research/ARCHITECTURE.md](src/features/futures_basis_research/ARCHITECTURE.md) |

本 catalog 不拥有 input、table/chart、metric、formatting、interaction、empty/error 或其他 visualization semantics。新增、删除或重命名正式 frontend slice 时更新本文件；slice 内部语义变化只更新其 canonical authority。
