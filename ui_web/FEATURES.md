# ui_web frontend feature catalog

本文件是 `ui_web` 正式 vertical slices 的 navigation-only catalog。Application entry、feature navigation 与 composition boundary 见 [application authority](application.md)；具体展示与交互语义由各 feature 的 co-located authority 拥有。

| Frontend slice | 状态与用途 | Canonical authority entry |
| --- | --- | --- |
| MO Option Chain | 已实现；展示指定交易日的完整 MO 期权链价格分布 | [mo_option_chain/ARCHITECTURE.md](src/features/mo_option_chain/ARCHITECTURE.md) |
| MO Premium Plane | 已实现；检视指定 observation 与取价口径下的 MO 稀疏年化权利金数值平面 | [mo_option_premium/ARCHITECTURE.md](src/features/mo_option_premium/ARCHITECTURE.md) |
| Research Explorer | 已实现；浏览已发布的 Research scope、结果与可视化，不执行研究 | [research_explorer/ARCHITECTURE.md](src/features/research_explorer/ARCHITECTURE.md) |
| Research Catalog & Workspace | WP3 已实现；只读发现在线 Capability、本地 Case 与离线报告流程 | [research_catalog/ARCHITECTURE.md](src/features/research_catalog/ARCHITECTURE.md) |
| Futures Basis Research | 已实现 Web Consumer、在线执行与共享报告 Reader；Provider / Cache readiness 独立验证 | [futures_basis_research/ARCHITECTURE.md](src/features/futures_basis_research/ARCHITECTURE.md) |

本 catalog 不拥有 input、table/chart、metric、formatting、interaction、empty/error 或其他 visualization semantics。新增、删除或重命名正式 frontend slice 时更新本文件；slice 内部语义变化只更新其 canonical authority。
