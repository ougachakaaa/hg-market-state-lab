# Shared Data Service Agent Rules

本文件细化 [market-snapshot rules](../../../AGENTS.md)，适用于本目录。

- 先读 [ARCHITECTURE.md](ARCHITECTURE.md)；只有修改 CLI、catalog 或 persisted delivery 时读取 [delivery.md](delivery.md)。
- Catalog 不发现文件系统、不拥有产品编排，也不得导入产品的 Source/Preparation internals。
- 修改后至少运行 Data Service CLI、catalog 与 orchestration boundary tests。
