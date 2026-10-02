# Expiry DTE Collection implementation handoff

本文件把 [Study entry](ARCHITECTURE.md)、[INPUTS](INPUTS.md)、[METHOD](METHOD.md) 与 [RESULTS](RESULTS.md) 映射为 Python / CLI responsibilities，继承 [Study Package Contract](../IMPLEMENTATION.md) 与 [Research UI](../../ui/ARCHITECTURE.md)。四份 authority 唯一拥有业务语义；resolver I/O / failure 归 [Universe CONTRACT](../../shared/cffex_option_expiry_universe/CONTRACT.md)。当前代码仍有 [implementation gaps](../../IMPLEMENTATION_RECONCILIATION.md#shared-component-semantic-reconciliation)。

## Package 与 typed runtime boundary

Study source 仍为 `market-research/src/market_research/studies/cffex_option_expiry_dte_collection/`，mandatory __init__.py / cli.py / study.py。Init docstring 指向 Study entry，intentional re-exports 使用 explicit redundant aliases，不用 __all__。无 observations.py / analyses.py / evidence.py / artifacts.py 占位。

Study 接收 typed request 与显式 resolver / chain collaborators，返回 typed immutable non-persistent outcome。Resolver public Python carrier / operation spelling 和 source layout 留给下一轮实现选择，不沿用旧 Observation namespace / ensure / Artifact / error family 作为新 canonical contract，不为本轮创建目录或框架。该选择是 mechanics，无待决研究含义。

| Value / path | Python mapping |
| --- | --- |
| Request product_code / expiry_start_date / expiry_end_date / target_dte | str / datetime.date / datetime.date / int，全部必填；domains 继承 INPUTS。 |
| Outcome request context | 相同四 fields / values，无 path、service、SQLite 或 upstream object。 |
| status | str，success / failure；依 RESULTS。 |
| discovered_expiry_count / planned_observation_count | int 或 None；None 表达 unavailable。 |
| completed_observation_count / failed_observation_count | non-negative int，统计 chain attempts。 |
| failures | immutable ordered Study-owned values，stage: str、expiry_date: date 或 None、reason: str；ordering 依 RESULTS。 |

不将 result / market rows 嵌入 outcome，不要求 JSON / file / persistence。Study 只消费 Research-owned public values / failures，不 import DataLake / Snapshot 或 private implementation。

## Composition 与 execution mapping

CLI 负责 parsing / admission、explicit public composition、调用 Study 与 presentation；study.py 唯一驱动 METHOD steps。

| Dependency | Required binding / public behavior |
| --- | --- |
| Universe shared resolver | product_code=request.product_code、expiry_start_date=request.expiry_start_date、expiry_end_date=request.expiry_end_date → public resolve I/O → owned complete result；核对同 request context、expiries 与 public completeness context，无 Observation semantic_identity / retained-hit。 |
| market_research.observations.cffex_option_expiry_dte_chain | ExpiryDteChainRequest(product_code=request.product_code, expiry_date=expiry, target_dte=request.target_dte) → create_service / service.ensure → ExpiryDteChainArtifact；核对 complete / business identity，durable-before-return 由 producer 保证。 |

先完整验证 request，再进入 resolver；chain factory / service 延迟到非空 plan 的 invocation。使用具体 public collaborators，不引入 gateway / container / registry。Controlled doubles 沿同一 public contract 注入，不成为普通 CLI 参数。

Resolver construction / operation / invalid result failure 进入 resolve_expiry_universe outcome；chain construction / operation / invalid Artifact failure 对应当前 request，继续下一项。Construction 尚未成功时后续不同 request 可再次尝试 construction，不重试同一个 request。Interruption 不吞成成功。

Resolver errors 使用其 own public failure boundary；chain errors 仍从 market_research.observations 消费。Readable context 投影至 Failure.reason，不 import upstream exception classes。Study 不构造 upstream request、读 persistence、derivation 或写第二 cache。

## CLI delivery

Stable flags 继承 INPUTS，lab discovery / forwarding 无变化。--help 零 workflow / factory access；invalid request exit=2，execution failure exit=1，success exit=0。Expected failure 提供 stage / actual counts / ordered reasons，不采用 traceback-only presentation。Universe stage 改为 resolve_expiry_universe。

Runner 不调用 load_config、canonical_run_directory 或 execute_run，不读 output.root、不创建 run output；无 output / database / sqlite-path / resume / overwrite flags。Resolver 经 DataLake public ensure 使用 Dataset cache；只有 chain research SQLite 由 Observation factory 管理。

## Acceptance、readiness 与下一轮

- Mandatory package / pointer、Component + Observation public-only imports；无 direct DataLake / Snapshot / provider / persistence 或第二 empirical cache。
- 四必填 flags / strict parsing，invalid request / --help 零 operations，无 output config / directory。
- Exact resolver inputs、complete result、sorted whole plan、exact chain bindings；无 Study 日期推导、market-row copy 或 Universe Artifact identity。
- Resolver failure 停止、unknown counts 正确；empty result success、counts=0、零 chain factory / ensure。
- Chain failure 后全部 requests 升序尝试一次，ordered reasons / counts / exits 一致；成功 chain 不 rollback。
- Controlled E2E：相同 request 再运行仍调用 resolver，Dataset ensure 自己复用 cache；已有 chain complete-hit 零上游、跨 service / process recreation reuse。只产生 chain Observation research SQLite，无 Universe research SQLite / Study retained files。不能以第二次禁用全部 upstream factories 的旧 E2E 验收新流程。
- Component boundary / Study wiring / stage / tests 与 source pointers 同步 reconciliation；保留 chain durable / completeness acceptance。

Study Authority Complete / Research dependency contracts complete / Study implementation architecture complete，设计 **Implementation Ready**。Runtime 新语义 **Not Reconciled**；现有 CLI 是旧 wiring，历史通过不能证明新 resolver 已实施。本轮不改 Python / tests / state。下一轮可按已锁定 contract 独立实施 resolver → Study wiring / focused acceptance；状态处置限制进入 reconciliation。
