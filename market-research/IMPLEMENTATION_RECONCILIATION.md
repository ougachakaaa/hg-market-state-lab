# Market Research implementation reconciliation

本文件记录 Observation-first authority 更新的基线、implementation / test drift 与交接状态，不拥有新的业务语义。入口见 [module architecture](ARCHITECTURE.md)；当前 contracts 分别见 [Observation authority](observations/ARCHITECTURE.md)、[Study Schema](studies/SCHEMA.md)、[Implementation Contract](studies/IMPLEMENTATION.md)、[Compatibility](studies/COMPATIBILITY.md) 与 [Research UI](ui/ARCHITECTURE.md)。

下文第一、二轮记录保留历史基线与当时验证结果；当前首个 concrete authority 的状态见 [本轮落位记录](#首个-concrete-observation-authority-落位)，历史测试结果不代表本 worktree 已验证。

## Baseline 与本次边界

基线 commit 为 `14dd806b2032672d22cc0e59d7140685aeef350c`。本次只更新 authority、navigation、authoring / review 和 reconciliation Markdown；Python、tests implementation、runtime data、SQLite schema、Snapshot / DataLake implementation、backend-api、web-ui、root runtime configuration 均未修改。

该基线 tracked Study authority 只有六份 framework documents，Study source 只有 namespace init，无 concrete retained Study；无 concrete Observation authority / implementation / public invocation delivery。既有 shared semantics / helpers 和 UI support 保留，不自动升级为新的 Observation capability。历史结构的有效性与显式迁移政策由 Compatibility 拥有。

## Remaining implementation / test drift

| 当前差异 | 后续处理边界 |
| --- | --- |
| Observation framework 与首个 concrete authority 已存在，尚无 producer、public invocation implementation、owned SQLite 或 Artifact implementation。 | 首个 concrete semantics 见本轮落位记录；下一步另行进行 implementation reconciliation / design，不从 authority readiness 推断 runtime readiness。 |
| `test_study_authority_topology.py` 的 REQUIRED_IMPLEMENTATION 仍强制 observations.py，fixtures 仍以 Study-local method/observations 为例。 | 与未来 Package Contract / Schema 不一致；单独 test reconciliation，本次不修改测试，不保留旧规范来迎合它。 |
| 既有 Study topology helpers 不检查独立 Observation owner、Artifact bindings / completeness 或 Observation 分支可达性。 | 现有 tests 不能单独证明新 semantic graph；本次补充非持久化 link / reachability 检查与逐条 semantic review，后续自动化检查另行设计。 |
| 本地 src/market_research/studies 下残留已删除 Study 的 cache-only directories。 | 旧 discovery test 把目录当作 package，产生 baseline failure；不等于 tracked concrete Study，本次不清理目录、不重建 package。 |

## Validation 与交接

实施前检查：repository authority tests 为 13 passed；Research Study topology tests 为 11 passed / 1 failed。失败项为 `test_new_runnable_studies_have_semantic_package_boundaries`：cache-only 旧目录缺少 `__init__.py`，与本次文档变更无关。首次报告的目录为 `mo_option_risk_premium_baseline`；目录枚举顺序可能改变首次报告的名称。

实施后验证结果：

- `poetry run pytest market-snapshot/tests/test_authority_topology.py -q`：13 passed，包含 repository Markdown links 与 root-entry reachability。
- `poetry run pytest market-research/tests/test_study_authority_topology.py -q`：11 passed / 1 failed，同一个 baseline package-discovery failure；此次首次报告 `price_to_lagged_ma_distribution` cache-only directory 缺少 init，未出现新增失败。
- 非持久化检查：新增 / 修改文件的 relative links（含 anchors）有效；17 份 tracked / newly authored Research authority documents 均可从 root architecture / agent entry 到达，无 orphan owner；ignored runtime reports 不属于 authority graph。
- `git diff --check` 通过；完整 tracked diff 与四份新文档已审阅，变更仅为 14 份 Markdown（10 modified / 4 new），未修改 implementation、tests、runtime state 或 configuration。

不得把旧测试通过视为新 Observation semantics 已实现，也不得把 baseline failure 解释为 authority 迁移失败。

Observation refresh / invalidation、definition evolution 由 [Observation deferred decisions](observations/ARCHITECTURE.md#explicitly-deferred-decisions) 记录；Analysis reuse / Artifact / persistence / graph 由 [Study Schema](studies/SCHEMA.md#dependency-direction-与-deferred-analysis-model) 记录；这些问题本轮不锁定，也不阻塞 framework reconciliation。

## Acceptance review record

下表是对本次附件 17 条 acceptance criteria 的核对记录，不是新增 semantic owner；规则以表中对应的、上文链接的 canonical authority 为准。

| # | 核对结果 | Canonical owner |
| --- | --- | --- |
| 1 | Scratch / Observation / Study 三者分工与生命周期明确。 | Module architecture |
| 2 | Observation 不属于 Study。 | Observation architecture |
| 3 | Observation 职责终点为 retained Artifact。 | Observation architecture |
| 4 | Study 消费 Observation Artifact。 | Study Schema |
| 5 | Study 不重定义 Observation semantics。 | Study Schema |
| 6 | 同一有效 definition 下重复 invocation 业务幂等。 | Observation architecture |
| 7 | 每个 concrete Observation exactly owns 一个 SQLite。 | Observation architecture |
| 8 | 不建立 global Observation DB。 | Observation architecture |
| 9 | Study / Analysis 不读取 Observation SQLite。 | Observation architecture |
| 10 | Artifact 可被多个 Study 复用。 | Observation architecture |
| 11 | Artifact 与 Study Evidence 是不同语义产品。 | Observation architecture |
| 12 | Analysis 仍 Study-local。 | Study Schema |
| 13 | 未建立 reusable Analysis framework。 | Study Schema |
| 14 | 旧 Study 不自动迁移。 | Compatibility |
| 15 | 新 Study 不在内部发明 Observation。 | Study Authoring / Schema |
| 16 | Refresh / definition evolution 仍 explicitly deferred。 | Observation architecture |
| 17 | 未引入 generic registry / DAG / research platform。 | Observation architecture / Study Schema |

Authority readiness 与 runtime readiness 分开：本次 graph 已完成一致性、17 条 acceptance review 与拓扑验证，**足够进入下一步“设计第一个 concrete Observation authority”**。这不表示其 implementation、SQLite、invocation delivery 或 Study dependency capability 已就绪；remaining drift 保持显式，不阻塞独立 authority design。

## 第二份设计附件审核与最小补齐

本节对应后续《authority-only semantic refactor》附件的 16 条 acceptance criteria，保留上文第一轮 17 条验收和验证历史。审核时核心 Observation-first model、Study 六份 framework authority、Compatibility、UI 与 root navigation 已落在工作区，尚未提交；此轮只补齐以下三份已有工作区文档，不创建实现或新的 authority branch。

| 补充项 | 落位 / canonical owner |
| --- | --- |
| 未来 canonical Python namespace ownership | Observation architecture 的 Purpose；只预留归属，不创建 package 或 source registration。 |
| Complete Artifact 命中不重复 upstream access / computation | Observation architecture 的 invocation lifecycle。 |
| Arbitrary global Artifact ID 与 hash technique 的边界 | Observation architecture 的 business identity。 |
| Runtime SQLite 不进入 Git | Observation architecture 的 persistence ownership。 |
| Complete / unfinished business key 的原子可见性 | Observation architecture 的 completeness；不设计事务算法、锁、retry 或 state machine。 |
| Version / source digest / code hash / timestamp 不自行进入 key | Observation architecture 的 deferred decisions；不锁定 evolution policy。 |

Observation Schema 在 Business Key、Artifact Contract、Acceptance 中链接上述 framework invariants，使 concrete authority 可核对它们；不重复拥有规则，也不规定 hash algorithm。Study / UI / root authority 本轮无需进一步变更。

下表记录第二份附件逐项复核结果；语义仍由上文链接的 canonical owners 定义。

| # | 附件验收项 / 复核结果 | Canonical owner |
| --- | --- | --- |
| 1 | Observation 是 independent retained empirical fact producer。 | Observation architecture |
| 2 | Observation 终点为 Artifact；Study 的解释终点为 Evidence / Findings。 | Observation / module architecture |
| 3 | Observation 不属于 Study。 | Observation architecture |
| 4 | Successful invocation 返回 retained Artifact。 | Observation architecture |
| 5 | 同一有效 definition 下 complete hit 直接复用，不重复 upstream access 或计算。 | Observation architecture |
| 6 | Business key 为该 Observation 的 normalized business inputs。 | Observation architecture / Schema |
| 7 | 每个 concrete Observation exactly owns 一个 SQLite。 | Observation architecture |
| 8 | 不共享 global Observation DB。 | Observation architecture |
| 9 | Study / Analysis 不直接读取 SQLite。 | Observation architecture |
| 10 | Study 消费 Observation Artifact contract。 | Study Schema |
| 11 | Study 不重定义 population / grain / derivation 等 Observation semantics。 | Study Schema |
| 12 | Artifact 可被多个 Study 重复消费。 | Observation architecture |
| 13 | 未建立 generic reusable Analysis framework。 | Study Schema |
| 14 | Refresh / version semantics 仍明确 deferred。 | Observation architecture |
| 15 | Legacy Study 不强制迁移，只按 human-triggered reconciliation 处理。 | Compatibility |
| 16 | 未引入 implementation、registry、DAG 或 global cache 等机制。 | Observation architecture / Study Schema；本轮文件范围审查 |

Remaining implementation / test gaps 仍为上文所列；namespace reservation 与 completion visibility contract 不表示相应实现已存在。

此轮补充后的验证结果：repository authority tests 为 13 passed；Study topology tests 为 11 passed / 1 failed，仍为 baseline cache-only directory discovery failure，此次首次报告 `cffex_basis_forward_return_association` 缺少 init。非持久化检查确认 126 个相对链接 / anchors 有效，17 份 Research authority documents 从稳定入口可达；六项补充约束及本附件 16 条验收均已逐项复核。`git diff --check` 与新增文档 whitespace inspection 通过，逐文件内容 hash 对比和完整 incremental diff review 确认本轮只修改 Observation ARCHITECTURE、Observation SCHEMA 与本 reconciliation 三份 Markdown，其余已有工作区改动保持原样。

本附件要求已明确落入 authority，足够进入第一个 concrete Observation authority 的独立设计；refresh / version evolution 仍未决定，尚未开始 Observation implementation。本轮不创建 Git commit。

## 首个 Concrete Observation authority 落位

本轮基于 `codex/observation` 分支的 `8d770c5e33bff5f30266c9defe043c60d7d1e329`。附件所指 `1e5ea2bb7ba28d76e5cac4e6d4b9846686f83ed8` 是该提交祖先，期间 Research 文件无变化；消费当前 DataLake public contract，包括 Options export V2 的上市首日 pre_close 合法缺席规则。

Canonical entry 为 [cffex_option_expiry_dte_chain](observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md)，date derivation / resolution 与 Artifact contract 分别归 [DATE_RESOLUTION.md](observations/cffex_option_expiry_dte_chain/DATE_RESOLUTION.md)、[ARTIFACT.md](observations/cffex_option_expiry_dte_chain/ARTIFACT.md)。十三个 Schema areas 的 owner mapping 在 concrete entry；module / framework entry 仅增加发现链接，不上提 DTE 或 product-specific semantics。AGENTS、AUTHORING、SCHEMA 现有 contracts 足够，无需修改；不新增 Observation catalog。

本轮仅新增这三份 authority，并更新 module architecture、Observation framework architecture 与本 reconciliation，共六份 Research Markdown。未修改 Python implementation、tests、runtime data、SQLite schema、DataLake / Snapshot、CLI / UI 或 root configuration；未开始 Observation implementation，未创建 commit。

### Dependency 与 remaining gaps

Calendar public coverage / ensure / export 能提供完整显式 CFFEX 开市事实；Options public coverage / ensure / export 能提供单 product-day 强 completeness 与全部合法 OptionsDailyRow。当前未发现 DataLake capability gap，不扩展 upstream authority 或绕过 public boundary。

Human 已确认不设人为历史下界或最大回溯次数：只在完整 product-day 证明 requested expiry 缺席时继续回溯；upstream 不能提供完整证明或日期无法继续表示时失败。该决定由 concrete DATE_RESOLUTION 唯一拥有，不新增第四个 business input。

本 concrete Observation 没有剩余未决业务语义。Refresh / invalidation / definition evolution 仍沿用 framework deferred status；它们不阻塞同一有效 definition 下的 authority readiness。Public invocation Python types / package topology、SQLite schema / path / unique key / transaction / locking / retry 与测试 implementation 需下一阶段 design，不能由文档的 complete 状态推导已实现。

### 本轮验证与交接

根 `.venv` 不存在，`poetry env info --path` 无环境路径且非零退出。按 repository 唯一 runtime policy，本轮不安装依赖、不创建环境、不调用 `poetry run pytest` 隐式创建环境。以下现有检查未执行，不能引用上文历史结果为本轮通过：

- `poetry run pytest market-snapshot/tests/test_authority_topology.py -q`
- `poetry run pytest market-research/tests/test_study_authority_topology.py -q`

旧 Study topology tests 固定 observations.py，且尚未验证 independent Observation graph / completeness；本轮不修改 tests。历史 cache-only directory failure 是上文基线记录，未将其认定为当前 worktree 已复现的 failure。

Supplemental 只读检查通过：六份新增 / 修改 Markdown 中 72 个 local links / anchors 有效；三份 concrete authority 均可分别从 root ARCHITECTURE、Research ARCHITECTURE 与 Research AGENTS 进入。`git diff --check` 与含三份 untracked 新文档的 trailing-whitespace 检查通过。完整 modified diff 与新增 authority 已审阅，改动范围仅为上述六份 Research Markdown；没有通过更改 tests 或 upstream contract 掩盖 drift。

Semantic review 覆盖 inputs / key、DTE 算术、精确命中、周末 / 假日、complete-but-absent、cache-missing 后 ensure、upstream failure 停止、合法 None、完整 population、complete reuse、失败不可见及 persistence boundary；acceptance scenarios 由 Artifact contract 拥有，不复制为新的规则。

本轮 concrete authority 已满足十三个 semantic areas，状态为 **Concrete Observation Authority Complete**，可以进入该 Observation 的 implementation reconciliation / design；现有 pytest suite 仍待根 canonical environment 就绪后运行。Authority complete 不代表 implementation、runtime SQLite、CLI / HTTP delivery 或 runnable Study dependency 已就绪。
