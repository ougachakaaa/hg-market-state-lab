# Expiry DTE Collection implementation handoff

本文件把 [Study entry](ARCHITECTURE.md)、[INPUTS](INPUTS.md)、[METHOD](METHOD.md) 与 [RESULTS](RESULTS.md) 映射为 runnable Python / CLI implementation architecture，继承 [Study Package Contract](../IMPLEMENTATION.md) 与 [Research UI](../../ui/ARCHITECTURE.md)。Business semantics 继续由四份 authority 唯一拥有；本文不创建 runtime 或重新设计 Observation。

## Package 与 typed runtime boundary

Source 为 `market-research/src/market_research/studies/cffex_option_expiry_dte_collection/`，mandatory __init__.py / cli.py / study.py。Init docstring 指向本 Study ARCHITECTURE；intentional public re-exports 用 explicit redundant aliases，不使用 __all__。没有 observations.py、analyses.py、evidence.py 或 artifacts.py 占位；只有真实内聚需求才增加 private helper。

Study-local execution 接收 typed canonical request 与显式 concrete Observation collaborators，返回 typed immutable non-persistent outcome。Python carrier / helper names 是 implementation mechanics，不新增 generic Study service / registry；普通 CLI 用户只需四个 semantic flags，不提供 factories / paths / connections。

| Value / path | Python mapping |
| --- | --- |
| Request product_code / expiry_start_date / expiry_end_date / target_dte | str / datetime.date / datetime.date / int，全部必填，domain 继承 INPUTS；拒绝 datetime timestamp / bool / defaults 等非法值。 |
| Outcome request context | 保留相同四 fields / semantic values，不含 path、service、SQLite 或 upstream object。 |
| status | str，success 或 failure；依 RESULTS。 |
| discovered_expiry_count / planned_observation_count | int 或 None，None 仅表达尚不可用，不制造 0。 |
| completed_observation_count / failed_observation_count | non-negative int，包含所有实际完成的 chain attempts 结果。 |
| failures | immutable ordered sequence of Study-owned values，field paths 为 stage: str、expiry_date: date 或 None、reason: str；含义 / ordering 继承 RESULTS。 |

Request 与 outcome values 不要求 JSON / serialization / persistence，也不将 Observation Artifacts 的 market rows 嵌入 outcome。只处理已发布 Observation-owned public types / common errors，不 import DataLake / Snapshot 或 Observation private package。

## Composition 与 execution mapping

CLI 负责四 flags parsing / admission validation、引用两个 concrete public factories 的 explicit composition、调用 Study orchestration及 presentation。study.py 唯一驱动 METHOD steps，public bindings 固定为：

| Dependency package | Request / operation / consumed result |
| --- | --- |
| market_research.observations.cffex_option_expiry_universe | ExpiryUniverseRequest(product_code=request.product_code, expiry_start_date=request.expiry_start_date, expiry_end_date=request.expiry_end_date) → create_service / service.ensure → ExpiryUniverseArtifact。 |
| market_research.observations.cffex_option_expiry_dte_chain | 每个 runtime plan expiry 构造 ExpiryDteChainRequest(product_code=request.product_code, expiry_date=expiry, target_dte=request.target_dte) → create_service / service.ensure → ExpiryDteChainArtifact。 |

Composition 使用 explicit concrete factory / service collaborators，不引入 gateway / adapter / container。先完整验证 Study request，再进入 Universe dependency；chain factory / service 使用延迟到非空 plan 的实际 chain invocation，不能因不需要的 eager chain construction 阻止 complete empty Universe success。可在同一 invocation 内复用已构造 service，不要求 single service per Study 或跨 invocation service cache。

Universe construction / operation failure 进入 ensure_expiry_universe failure outcome。Chain construction / operation failure 对应当前 planned request，记录后继续下一 entry；若 service construction 尚未成功，后续不同 business request 可再次尝试必要 construction，不重试同一个 request。正常每项 ensure 只尝试一次；没有 Study retry loop / upstream call / 日期修复。Controlled doubles 可按同一 concrete public boundary 显式注入，test-only construction 不成为普通 CLI API。

每个 Artifact return 只按 public contract核对 complete、对应 business request / semantic identity，不重新推导其 facts。ObservationError family 从 market_research.observations public boundary处理；预期 dependency failure 或 invalid / mismatched return 形成 RESULTS operation failure，不导入 upstream exception classes。Publication failure 已由 ObservationOperationError 表达；successful return 依赖其 durable-before-return contract，不再由 Study写第二份数据库。系统 interruption 不吞为成功，也不发布 partial result。

## CLI delivery

Stable command / flags 唯一继承 INPUTS，采用 root lab research forwarding / discovery convention，CLI --help 不运行 workflow / factories。Invalid argument / request 在 dependency access 前退出 2；合法请求的 operation failure 输出 stage / counts / failure details，退出 1；成功输出 request / counts，退出 0。不要 traceback-only expected failure presentation。

Orchestration-only runner 不调用 load_config、canonical_run_directory 或 execute_run，不访问 research.toml / output.root，不创建任何 Study run output。不提供 output / database / sqlite-path / resume / overwrite flags，不为此修改 lab dispatch / registration。Observation factories 自己拥有 persistence composition 与内部 root-relative路径；CLI 不构造 Artifact、SQLite、upstream request 或 provider client。

## Acceptance 与 readiness

Implementation 必须验证：

- Canonical package / init authority pointer、mandatory modules、public-only Observation imports；无 DataLake / Snapshot / private persistence / provider imports、空 modules 或第二 empirical cache。
- 四必填 inputs / strict parsing / domains / no defaults / no extra flags，invalid request 与 --help 零 dependency operations；无 output config / directory dependency。
- Exact Universe bindings、完整 sorted plan 与各 exact chain bindings，Observation-owned dates / DTE 原样消费，无 Study 日期推导或市场 row copy。
- Universe failure 停止且 unknown counts 正确；complete empty Universe success、全部 counts=0，零 chain factory / ensure calls。
- 多个 chain failures 仍按升序尝试全部 planned requests，各尝试一次，无删项 / retry，ordered reasons 与 completed+failed=planned；success / failure exit codes 对应。
- 构造失败 / invalid Artifact return / operation failure 不假报成功；Study failure 不删除已成功 Observation Artifacts。
- Producers 实施后用 temporary owned persistence + fake public upstream services 验证 whole vertical slice：初次 invocation durable publication；丢弃全部 service state 后同 request 再运行，同 logical Artifacts，零上游 factory / service calls，不产生 Study retained files。无真实 provider调用。

Study semantics、Observation dependency contracts 与本 mapping 无 gap，为 **Study Authority Complete / Observation dependency contracts complete / Study implementation architecture complete / Implementation Ready**。Runtime **Not Implemented**，Study runtime Dependency Reconciled 尚未完成。按 [Authoring handoff](../AUTHORING.md#publication-与-dependency-handoff) 先完成 minimal Observation shared mechanics、两个 producers / durable acceptance，再核对实际 bindings，随后实施 Study 与 end-to-end tests；本轮仅写 authority，停止于 handoff。
