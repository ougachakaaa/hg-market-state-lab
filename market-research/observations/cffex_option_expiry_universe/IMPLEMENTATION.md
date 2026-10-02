# ExpiryUniverse Implementation Contract

本文件把 [semantic entry](ARCHITECTURE.md) 与 [Artifact authority](ARTIFACT.md) 映射到 runnable Python package，继承 [framework IMPLEMENTATION](../IMPLEMENTATION.md) / [UPSTREAM](../UPSTREAM.md)。不改变 observed-window definition、inputs、key 或 completeness。

## Public package 与 values

Canonical package 为 `market_research.observations.cffex_option_expiry_universe`，source 在 `market-research/src/market_research/observations/cffex_option_expiry_universe/`。Public `__init__.py` 发布 ExpiryUniverseRequest、ExpiryUniverseArtifact、ExpiryUniverseService、create_service；public contract / orchestration / derivation / persistence 按内聚性分开，private filenames 不锁定。

```python
from datetime import date
from market_research.observations.cffex_option_expiry_universe import (
    ExpiryUniverseRequest, create_service,
)

request = ExpiryUniverseRequest(
    product_code="IO", expiry_start_date=date(2026, 10, 1),
    expiry_end_date=date(2026, 10, 31),
)
artifact = create_service().ensure(request)
```

这是未来 consumer contract 示例，不宣称 runtime 或示例市场数据已存在。`ExpiryUniverseService.ensure(request: ExpiryUniverseRequest) -> ExpiryUniverseArtifact` 是唯一 public semantic operation。

| Value | Required public fields / Python semantic types |
| --- | --- |
| ExpiryUniverseRequest | product_code: str；expiry_start_date / expiry_end_date: datetime.date；全部必填，domains / canonicalization 仅引用 entry。 |
| ExpiryUniverseArtifact | observation_identity: str 固定 cffex_option_expiry_universe；product_code: str；expiry_start_date / expiry_end_date: date；expiries: immutable ordered sequence[date]；complete: bool 固定 True；provenance: Observation-owned value，如下。 |

Artifact 提供 read-only `semantic_identity`，值为 `(observation_identity, product_code, expiry_start_date, expiry_end_date)`，不引入新的 ID。Request / Artifact / nested values 按 framework immutable / deterministic equality contract；expiries sorted unique、inclusive in-range，完整空序列合法。无 chain rows / target_dte / observation_date。

Provenance 的 field paths 固定为 `dataset: str`、`view: str`、`export_schema_version: int`、`scope.product_codes: immutable sequence[str]`、`window.start_date / end_date: date`、`coverage.requested_units / successful_units / missing_units / pending_units / failed_units: int`、`coverage.complete: bool`。它们是本 Observation 拥有的 immutable typed values，不是 DataLake classes 或 dict / JSON consumer protocol；具体 carrier names 留给实现。值从实际 Options export 无损投影，含完整 coverage counters；scope 只有 requested product，window 等于 request 两端。Coverage meaning 继续引用 [DataLake APPLICATION](../../../data-lake/APPLICATION.md)，complete=True 不保证 freshness，不纳入 identity。

## Composition 与 canonical execution

Factory 无参、无 network / credential access；内部 owned SQLite 固定为 `market-research/observations/cffex_option_expiry_universe/data/cffex_option_expiry_universe.sqlite3`。Public dependency 只组合 `data_lake.datasets.tushare_equity_index_options` 的 OptionsDailyRange / create_service / service operations。Options 自己拥有 [Calendar prerequisite](../../../data-lake/datasets/tushare_equity_index_options/TRADING_DAYS.md)；本 service 不直接调用 Calendar、不创建 Calendar request、不判断开市日、不读取 Calendar export、不重复 prerequisite logic，只要求完整 Options facts。不创建 Snapshot adapter，也不读取 upstream internals / provider。

1. 验证 Request 类型及 entry 三个 domains；按 normalized tuple lookup owned persistence。Complete hit 立即返回，零 upstream factory / service calls 与 recomputation。
2. Miss 后 create / use Options public service，构造 `OptionsDailyRange(product_codes=(request.product_code,), start_date=request.expiry_start_date, end_date=request.expiry_end_date)`。
3. 调用 `OptionsDailyService.ensure(exact range)`，要求合法 EnsureResult.complete=true、无 unit failures。Incomplete / failure 即 ObservationOperationError，不从成功子集派生。随后 `OptionsDailyService.export(exact same range)`，验证 dataset=tushare_equity_index_options、view=options_daily、export_schema_version=2、scope 仅含 requested product、window 恰等于请求，以及 coverage.complete=true、coverage counters consistency 与合法 public records（继承 [Options SERVICE](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md#3-options-daily-export-v2)）。只以这份 committed export snapshot 的 coverage / records 作为最终 proof，不能拼接先前 coverage / EnsureResult 与另一份 rows。
4. 按 entry 筛选 expiry 在 inclusive request window 内的 rows，提取 sorted unique dates；不保留 chain rows，不扩大 trade-date window，不查询 catalog。完整零目标或完整无 matching rows 均形成 complete empty Artifact。
5. 无损投影 required provenance，构造整份 Artifact，核对 inputs / scope / window / coverage / sorted unique in-range completeness，再原子发布，最后 return。失败不发布 partial；publication / persistence / upstream errors 按 framework taxonomy。

Canonical miss strategy 是 **ensure-first**：`ensure(exact range) → require complete → export(exact same range) → validate complete snapshot → derive`，无需 preliminary `coverage()`。本 Observation 的要求就是先确保整个 requested semantic range 完整，再消费它；[Dataset ensure](../../../data-lake/datasets/tushare_equity_index_options/SERVICE.md#2-coverageensure-与-accounting) 已拥有 skip successful units、仅补 missing / non-success units 的职责。即使 Dataset cache 已 complete，仍使用此 public sequence，由 ensure 自己避免重复 Source fetch；Observation 不先执行 `coverage → if incomplete ensure → export` 来实现自己的 completeness / cache optimization。未来 public contract semantic change 须先 reconciliation，不能静默换调用模式。

Readable public prerequisite / dependency context 可进入 OperationError message；合法 Observation request 转成 upstream request 后被拒绝也是 operation failure，不误判 caller。Ensure complete 后 export incomplete / invalid 同样失败，不以 EnsureResult 替代 final export proof。

## Verification 与 handoff

除 framework 三层 checks，具体验证 miss 为 exact same range ensure → export、无 preliminary coverage / direct Calendar calls、ensure complete 后 export incomplete / invalid 仍失败，以及重复 expiry 去重升序、边界 inclusive、窗口外排除、complete empty / zero targets、incomplete / unit failures 不发布、provenance 值与 export 一致，repeat / reopened service reuse 零 upstream。Fake dependencies 通过合法 public results 控制，不调用 Tushare；tests 不让 Study import Options types。

现有 Options public service 已有对应 request / ensure / export runtime surface，无 public capability gap；本 package **Authority Complete / Dependency Reconciled / Implementation Architecture Complete / Implementation Ready**，runtime **Not Implemented**。先实施本 producer 并通过 acceptance，再与 chain producer 一起复核 Study bindings；不在本轮创建 source、database、CLI 或 Study code。
