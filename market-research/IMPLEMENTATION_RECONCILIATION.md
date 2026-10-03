# Market Research implementation reconciliation evidence

本文件只记录 implementation / topology reconciliation evidence，不拥有 Research semantics、contract 或 canonical owner navigation。语义从 [module architecture](ARCHITECTURE.md) 进入各 colocated framework / capability；本记录不取代其 authority。

## Authority 与 implementation colocation

2026-10-03，基于 `003a686cfd58e1b1cd466b217b0b3ecb2e0141f7` 按已确认的 owner-first 原则重新整理。Repository 唯一 Python project / dependency graph / environment 保持；公开 Python namespaces、Study IDs 与业务计算保持。

| Owner | 当前 topology |
| --- | --- |
| Module | AGENTS / ARCHITECTURE / UPSTREAM、research.toml、tests 与本 evidence ledger 在 module root。无 module-level facade，故不保留 module src。 |
| Shared | shared 根目录拥有 framework authority；四个 component 各自拥有 authority 与 src/market_research/shared/<component>/，无空 shared/src。 |
| Observation | observations 根目录拥有 framework authority 与 src/market_research/observations/ mechanics；chain owner 拥有 specialized authority、自己的 src 与 output。 |
| Study | studies 根目录拥有 authoring contracts；collection owner 拥有四份 semantic documents、implementation handoff 与 src/market_research/studies/<study>/，无空 studies/src。 |
| UI | ui 根目录拥有 ARCHITECTURE / CONFIGURATION，support 在 ui/src/market_research/ui/。 |
| Runtime registration | 根 pyproject 显式注册八个 owner-local source roots，Observation framework 使用与 DataLake 相同的 extend_path；公开 imports 保持，无 registry 或新抽象。 |
| Persistence | 按用户授权清理了旧 chain 与 retired Universe 两份 Research SQLite；以后 chain SQLite / sidecars 归 chain/output，Git ignore 保护。Universe 仍是无 persistence 的 shared resolver。 |
| CLI / navigation | lab 按直接 Study owner 发现，再验证 owner-local Python runner；仍通过原 module path 启动。Markdown links / source pointers / topology tests 随物理布局 reconciliation。 |

### Verification

- 全仓库 pytest：1062 passed / 2 skipped；Windows symlink privilege 导致原有 skips，另有现存 FastAPI/Starlette deprecation warning。
- Research / lab / Snapshot mypy：118 source files 通过；Backend mypy：21 source files 通过。相关模块 Ruff 通过。
- 118 份正式 Markdown local links 无 broken target；Research contracts 从 stable entries 可达，source pointers、topology / public facade checks 通过。
- `lab research list` 与 collection `--help` 保持原 Study ID / 参数；root `poetry install --only-root`、wheel build 与 9 个 fresh-process isolated wheel imports 通过。
- 26 份搬迁 Python 文件去除 module docstrings 后 AST 比对：仅 Observation namespace extend_path、SQLite output/root resolution 与 UI config root resolution 有预期差异。
- 完整包含 renamed / added files 的 diff 与 whitespace 检查通过；未调用真实 external provider。

历史通过数仅解释对应 baseline，不替代当前验证。

### Remaining reconciliation gaps

本次不改变 Artifact / resolver / Study workflow semantics。Observation refresh / definition evolution 等既有 deferred decisions 继续由原 specialized authority 拥有。旧 module src 下仅有 ignored Python cache，清理该缓存目录的自动审批返回 blocked by policy；无 source / authority / runtime registration 留在旧 root。

## 首个 concrete Observation authority 落位

历史 concrete chain design 已由其当前 colocated authority 继续承载。本 heading 仅保留既有 evidence anchor；详细 ledger 见下方 Git baseline，不是第二 semantic owner。

## First Observation-driven vertical slice implementation

历史首个 slice 的两个 Observation / 两库 / 整个 Study 零上游验收已被 subsequent component reconciliation 取代；不能用于证明当前 Universe resolver behavior。Chain durable-before-return / restart reuse 仍适用并由当前测试验证。

## Shared component semantic reconciliation

Universe 从 Observation 改为 shared component 的已确认决定保持；当前 canonical semantics 在其 colocated ARCHITECTURE / CONTRACT，Python mapping 在同目录 IMPLEMENTATION。原 authority-only 的 Not Reconciled 与 blanket shared-link test gap 已在基线 `09eb313...` 闭合，不是 remaining work。

## Shared component runtime reconciliation

基线 `09eb31335bb3bde549a41d43c7c6f8e96a9316f0` 已实现 resolver、独立 errors、Research-owned immutable result / provenance、exact-range Options ensure → committed export proof → observed-window extraction，以及 Study resolve_expiry_universe stage / whole ascending chain plan。Chain one SQLite / durable reuse 保持，旧 Universe Observation package / Artifact / SQLite lifecycle 已撤销。

基线当前验收：Research + lab Research + repository authority focused suite **275 passed / 2 skipped**；upstream Options / Calendar + lab regression **131 passed / 1 skipped**；Research Ruff 与 mypy（41 files）通过。Fresh-process controlled E2E 用 actual DataLake public services / isolated caches：第二次仍执行 resolver public ensure / export，Dataset Source calls=0；chain hit 的 upstream factories / operations=0。只产生 DataLake-owned caches 与 chain Research SQLite，无 Universe Research SQLite / Study retained files。本轮重新运行这些 Research runtime tests，历史通过数不替代当前验证。

## Historical evidence retrieval

旧 400 多行 ledger 中仍有价值的 baseline、scope、acceptance 与 drift resolution 已在本文件保留简述；完整历史 evidence 保存在 Git：

```text
git show 09eb31335bb3bde549a41d43c7c6f8e96a9316f0:market-research/IMPLEMENTATION_RECONCILIATION.md
```

历史路径、未实施状态与后续已关闭 gaps 只在该原始 commit 的时间语境中解释，不作为当前 canonical path / contract。Ledger 留在 module root，不机械迁入任一 runtime package。
