# Market Research implementation reconciliation evidence

本文件只记录 implementation / topology reconciliation evidence，不拥有 Research semantics、contract 或 canonical owner navigation。语义从 [module architecture](ARCHITECTURE.md) 进入各 colocated framework / capability；本记录不取代其 authority。

## Authority 与 implementation colocation

2026-10-03，基于 `09eb31335bb3bde549a41d43c7c6f8e96a9316f0` 完成 topology / ownership reconciliation。Python project、dependency graph、package root 与 runtime model 保持原样。

| Scope | Current physical owner / change |
| --- | --- |
| Module policy | `market-research/AGENTS.md`、`ARCHITECTURE.md`、`UPSTREAM.md` 留在 module root。 |
| Shared | Framework 与四个 component 的 authority 共置于 `src/market_research/shared/` 及各 component package。distribution / im_basis / price_to_lagged_reference 从单文件改为同名 package，原 import paths、public names 与计算保持。Universe resolver 原 package 不变。 |
| Observation | Framework / concrete chain authority、ARTIFACT / DATE_RESOLUTION / IMPLEMENTATION 与代码共置于 `src/market_research/observations/` / chain package。 |
| Study | Framework documents 与 concrete collection 的四文件 authority / implementation handoff 共置于 `src/market_research/studies/` / collection package。 |
| UI | ARCHITECTURE / CONFIGURATION 与 configuration / execution support 共置于 `src/market_research/ui/`。`research.toml` 不搬迁。 |
| Tests / navigation | Tests 留在 `market-research/tests`；topology checks 验证同目录 owner、可达性、links / anchors、source pointers、public imports；repository links / test path expectations 随迁移更新。 |
| Durable state | Chain SQLite 仍在 `market-research/observations/cffex_option_expiry_dte_chain/data/`；该树仅存 runtime state，不再含 authority / source。保留原 factory resolution / ignore / durable reuse，不自动迁移或清理已有 SQLite。旧 Universe state 同样不读取、删除或迁移。 |

30 份下层 authority relocation；无 authority-only Shared / Observation / Study / UI mirror tree。Semantic entry 与 specialized details 仍各有唯一 owner，无 centralized documentation registry。

### Semantic drift review

本次只改变 physical ownership / package shape / navigation。Universe 是 shared resolver（resolve / owned complete result，无 Observation lifecycle），chain 是 retained Observation（ensure / durable Artifact），collection 是 resolver + chain 的 orchestration-only Study。Observation persistence、Analysis prepared-input boundary、upstream public-only dependencies、Study failure continuation / counts / CLI exits 均保持基线语义。

### Verification

修改前：`poetry run pytest market-research/tests market-snapshot/tests/test_authority_topology.py lab/tests -q` → **336 passed / 2 skipped**。

最终检查从 repository root 唯一 Poetry environment 执行：

| Check | Result |
| --- | --- |
| `poetry run pytest market-research/tests market-snapshot/tests lab/tests -q -rs` | **638 passed / 2 skipped**；覆盖全 Research runtime / fresh-process controlled E2E、完整 Snapshot regression、lab forwarding 与 repository links / reachability。两项 skip 是 Windows 无 symlink creation privilege 的既有检查。 |
| `poetry run ruff check market-research/src market-research/tests lab market-snapshot` | Passed。 |
| `poetry run mypy market-research/src market-research/tests` | Passed，42 source files。 |
| `poetry run mypy market-snapshot` | Passed，64 source files。 |
| CLI smoke | `poetry run lab research list` 仍只发现 cffex-option-expiry-dte-collection；`poetry run lab research run cffex-option-expiry-dte-collection --help` 的四个必填 flags / discovery / forwarding 正常。 |
| Packaging | `poetry build --format wheel` passed；wheel 包含全部 30 份 colocated documents 与三个同名 helper packages，不含 retired helper .py files；展开至 isolated installed directory 后，7 个 capability / UI modules 从该 wheel 内容在 fresh process 中成功 import。根 pyproject / lock / source registration 未改。 |
| Source equivalence | 基线与当前全部 29 个 Research source files 的 executable AST 完全一致，只忽略 module docstring，按三个 helper relocation 映射比较。 |
| Canonical links / topology | 116 份 Markdown（排除 _temp_docs 与被整理的 ledger）的原始 canonical targets 按 relocation 映射保持；全部 Research contracts 从 repository / module / AGENTS stable entries 可达；Research local links / fragments、同目录 source pointers、shared public names / module identity 与 shadow-owner rejection tests 通过。 |
| Full diff | 完整 relocated / added / modified diff 已审阅；`git diff --check` 与新文件 whitespace checks 通过。 |

没有调用真实 external provider；controlled E2E 验证既有 public services / isolated persistence / repeat-call behavior，不宣称 provider-current freshness。

### Remaining reconciliation gaps

当前无新增 semantic decision 或 upstream capability gap。Observation refresh / definition evolution、future Analysis / Evidence persistence 与旧 state 处置仍依原 authority deferred；它们不是 colocation 所需的实现。本轮 topology、source、tests、tooling 与 navigation 无 remaining reconciliation gap。

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
