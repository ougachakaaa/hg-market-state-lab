# Daily Market Snapshot bounded-context authority

本 context 是验证 Source → Raw → deterministic preparation 路径的独立场景。它不定义共享 Tushare Source facts，也不拥有其他产品语义。

## Ownership

本 context 拥有固定六指数 observation universe、A 股 target-date scope、场景 Raw artifact 组织与场景 preparation contract。共享 `index_daily` endpoint 与 normalization 由 [Capture authority](../../capture/ARCHITECTURE.md) 拥有。

## Navigation

- 场景输入、Capture scope 与 Raw contract：[data.md](data.md)
- Raw → analysis-ready structure、formula 与 failure：[preparation.md](preparation.md)
- 共享 Capture facts：[Capture authority](../../capture/ARCHITECTURE.md)

该场景目前保留 development Capture adapters；它不是 `dms` catalog 中的 persisted Data Service。
