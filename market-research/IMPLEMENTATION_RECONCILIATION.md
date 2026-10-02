# Market Research implementation reconciliation

本文件记录 Observation-first authority 更新的基线、implementation / test drift 与交接状态，不拥有新的业务语义。入口见 [module architecture](ARCHITECTURE.md)；当前 contracts 分别见 [Observation authority](observations/ARCHITECTURE.md)、[Study Schema](studies/SCHEMA.md)、[Implementation Contract](studies/IMPLEMENTATION.md)、[Compatibility](studies/COMPATIBILITY.md) 与 [Research UI](ui/ARCHITECTURE.md)。

下文各轮记录保留历史基线与当时验证结果；首个 Observation 的落位见 [首轮 concrete 记录](#首个-concrete-observation-authority-落位)，workflow / 第二个 Observation / 首个 Study 见 [workflow reconciliation](#observation-driven-study-authority-reconciliation)，当前 upstream selection policy 与检查见 [本轮 upstream reconciliation](#observation-upstream-dependency-policy-reconciliation)。Observation runnable mapping 的当前状态见 [implementation architecture reconciliation](#observation-implementation-architecture-reconciliation)。历史测试结果不代表本 worktree 已验证。

## Baseline 与本次边界

基线 commit 为 `14dd806b2032672d22cc0e59d7140685aeef350c`。本次只更新 authority、navigation、authoring / review 和 reconciliation Markdown；Python、tests implementation、runtime data、SQLite schema、Snapshot / DataLake implementation、backend-api、web-ui、root runtime configuration 均未修改。

该基线 tracked Study authority 只有六份 framework documents，Study source 只有 namespace init，无 concrete retained Study；无 concrete Observation authority / implementation / public invocation delivery。既有 shared semantics / helpers 和 UI support 保留，不自动升级为新的 Observation capability。历史结构的有效性与显式迁移政策由 Compatibility 拥有。

## Remaining implementation / test drift

| 当前差异 | 后续处理边界 |
| --- | --- |
| Observation framework、两个 concrete Observation authorities 与首个 concrete Study authority 已存在，尚无 Observation producer / public invocation runtime 或该 Study implementation。 | 当前 semantics / readiness 见本轮 workflow reconciliation；下一步另行进行 implementation design，不从 authority readiness 推断 runtime readiness。 |
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

## Observation-driven Study authority reconciliation

本轮基线为 `c8814598a83b121705e03b7ba2e69ac6182cf5b2`，分支为 codex/observation，开始时工作区干净。本轮只更新 Research authority Markdown；未修改 Python、tests、runtime data、SQLite schema、DataLake / Snapshot、backend-api、web-ui 或 root configuration，未创建 commit / push，未开始 implementation。

### Canonical owners 与 human decisions

新增 [Study Workflow authority](studies/WORKFLOW.md)，将 steps、Study-local materialized Artifact identity 与 complete consumption 下沉为独立专题；Schema 只拥有对象模型 / cardinality，具体步骤与 retained Artifact shapes 仍由具体 Study METHOD / RESULTS 拥有。不引入 generic executable workflow / DAG / registry。

新增 [cffex_option_expiry_universe entry](observations/cffex_option_expiry_universe/ARCHITECTURE.md) 与其 [Artifact contract](observations/cffex_option_expiry_universe/ARTIFACT.md)。Human 已确认 historical trade-date window 与 inclusive expiry window 相同；完整 public rows 中实际出现且 expiry 位于该窗口的 sorted unique dates 是唯一 empirical definition，不宣称覆盖只在窗口外挂牌的合约。十三个 Observation Schema areas 均有 owner；合法完整空 universe 可发布 complete。

新增 [cffex_option_expiry_dte_collection entry](studies/cffex_option_expiry_dte_collection/ARCHITECTURE.md) 与 [Inputs](studies/cffex_option_expiry_dte_collection/INPUTS.md)、[Method](studies/cffex_option_expiry_dte_collection/METHOD.md)、[Results](studies/cffex_option_expiry_dte_collection/RESULTS.md)。Human 已确认 chain invocation failure 后继续按 expiry 顺序尝试所有计划项；任何失败都阻止 complete final collection，无 Study retry loop，不 rollback 已 complete Observation Artifacts。

Study INPUTS 拥有四个 normalized inputs / deterministic run identity；METHOD 拥有 Universe → materialized plan → chains → materialized collection 顺序与 bindings；RESULTS 拥有 expiry_plan / observation_collection semantic shapes、provenance、counts / human output 与 complete / empty / failure。Analysis=0、Evidence=0，collection 是 manifest，不复制 chain rows。DTE-chain entry 仅更正 discovery ownership 描述；其 DATE_RESOLUTION / ARTIFACT 未修改，DTE / population / completeness 不变。

### Framework / output reconciliation

五份 Study framework documents 同步 required Workflow、optional Analysis / Evidence、Question / Objective 与 optional hypothesis、prepared-input Analysis boundary、mandatory init / cli / study 与 conditional analyses / evidence，以及 observation-only Review Gate。Module architecture、AGENTS、Observation framework / authoring 最小更新职责与 navigation；Compatibility 不变，不自动迁移 legacy consumers。

UI canonical directory 泛化为 retained Study run output / workspace，保留 collision-before-execution、显式 overwrite、whole-directory staging / replacement 与发布失败恢复旧 output。同次 invocation 内 Artifact 先在 run staging workspace 物化再消费，成功后整体发布；失败不发布 complete final output，不新增 partial-output publication / resume protocol。Observation cache / SQLite 与 output.root / overwrite 独立。

### Capability 与 readiness

现有 OptionsDailyRange / ensure / export 的 full product-day coverage、同一 committed snapshot public rows / expiry 与 Calendar prerequisite 已足以证明锁定的 observed-window Universe，**未发现 DataLake capability gap**，不修改 DataLake authority、不穿透 opt_basic / persistence、不添加 API。

本 Study 六个 semantic areas 与 workflow / result relationships 已确定，状态为 **Study Authority Complete**；第二个 Observation 为 **Concrete Observation Authority Complete**。DataLake upstream semantic contracts 已核对，但两个 Observation 的 runtime producers / public invocation implementations 尚不存在。因此按 Authoring 定义，**Dependency Reconciled 尚未达到，Implementation Ready 尚未达到**。可以进入 Observation + Study implementation design；实际 Study implementation 必须先补齐 Observation dependencies 并复核实际 contracts / bindings。

Remaining semantic decisions 仅为已明确 deferred concerns：Observation refresh / invalidation / definition evolution，跨 invocation Workflow Artifact resume / reuse，serialization / filenames / run-key encoding，Observation schema / path / unique key / transaction / locking / retry，以及 invocation Python topology / CLI / HTTP delivery。本轮不以 deterministic identity 推导 cache、generation history 或 resume。

### 本轮 validation 与 test drift

Semantic review 沿 request → run identity → complete Universe → materialized plan → N chains → complete manifest 核对 ownership / bindings / provenance。核对 invalid inputs、inclusive filtering、重复 expiry 去重升序、complete empty universe / zero target、upstream incomplete failure、chain failure 后全部尝试、materialization / publication failure、complete reuse、unknown counts 与 Analysis / Evidence absence；具体 acceptance 仍由各 canonical owner 拥有。

旧 Study tests 的 REQUIRED_IMPLEMENTATION 固定 observations.py / analyses.py / evidence.py，fixtures 仍演示 Study-local Observations；尚不覆盖 Workflow Artifact completeness、optional Analysis / Evidence 或 Analysis invocation prohibition。Authority-only 本轮不修改 tests 或 runtime 迎合旧 invariant，需下一阶段 test reconciliation。历史 cache-only failure 只作历史记录，不视为当前 worktree 已复现。

本轮只读检查通过：19 份新增 / 修改 Research Markdown（7 new / 12 modified）的 205 个 local links / anchors 有效，七份新 owner 均可分别从 root ARCHITECTURE、Research ARCHITECTURE 与 Research AGENTS 到达；Study entry 直接链接 INPUTS / METHOD / RESULTS。`git diff --check` 及含 untracked 新文档的 trailing-whitespace 检查通过。完整 modified diff 与七份新文档已审阅，范围仅为 authority Markdown；DTE-chain DATE_RESOLUTION / ARTIFACT、Compatibility、Python 与 tests 均未改变。

根 `.venv` 仍不存在，`poetry env info --path` 无环境路径。未安装依赖、创建环境或通过 `poetry run` 隐式初始化。以下两项现有 suite 未执行，不能引用历史通过数，也不能据此宣称当前 baseline failures 已复现：

- `poetry run pytest market-snapshot/tests/test_authority_topology.py -q`
- `poetry run pytest market-research/tests/test_study_authority_topology.py -q`

## Observation Upstream Dependency policy reconciliation

本轮基线为 `754758a8633ecc6c5d8adc4c5ff16d5bd3dfea0b`，codex/observation 分支开始时工作区干净。只新增 [UPSTREAM.md](observations/UPSTREAM.md)，最小更新 Observation architecture / Authoring / Schema、两个 concrete entry、module architecture / AGENTS 与本记录，共九份 authority Markdown（1 new / 8 modified）。未改变 Study business semantics、两个 Observation inputs / key / population / grain / derivation / Artifact / completeness，未修改 implementation、tests、DataLake / Snapshot、SQLite、CLI / HTTP、root project / lock；未创建 commit / push。

### Canonical policy 与 concrete review

Detailed upstream policy 唯一归 UPSTREAM：DataLake-first 是 design-time semantic capability priority，不是 runtime try / fallback。Public facts / completeness 必须完整、确定、可验证，且不能实质重做已由 Snapshot Product 拥有的 canonical deterministic semantics；不能以 rows 恰含字段、cache missing、runtime implementation 未就绪或 execution failure 判断 semantic insufficiency。

DataLake sufficient 必须绑定 exact Dataset public service；insufficient 才记原因、检查 Snapshot catalog 并选明确 public Product request / result / failure contract。两侧没有足够 public capability 时记录 Upstream Capability Gap，按 source facts / prepared Product nature 交 DataLake / Snapshot owner，阻止 implementation readiness。Runtime failure 两侧均不换源，不 silent substitute / null-fill；multi-upstream 逐 fact 指定 canonical owner。Research / Observation absolute external-provider prohibition 与 public-only provenance 已落位，不创建 source / fallback abstraction。

两份 existing concrete entries 只增加 policy reference 与已有 public sufficiency proof：Universe 继续只依赖 tushare_equity_index_options public service；DTE-chain 继续依赖 tushare_trade_calendar 与 tushare_equity_index_options public services。两者均不需要 substantive business change，不选择 Snapshot，不改变 date fallback / observed-window definition；DATE_RESOLUTION 与两个 ARTIFACT files 均保持原样。

Observation upstream policy 已具备 **Authority Complete** 条件，可以进入 Observation implementation architecture design；实际 producer / public invocation / persistence design 仍未开始。既有 Study Dependency Reconciled / Implementation Ready 状态不因本轮 policy 更新而改变。

### Validation 与 completion audit

按附件编号审查 policy requirements：stable public boundaries、DataLake-first / sufficiency、Snapshot selection、双向 failure 禁止换源、multi-upstream、gap escalation、provider prohibition、authoring / schema、两侧 execution / provenance、specialized topology、concrete / module reconciliation 和 non-goals 均由上述 owners 表达。检查附件十项 reconciliation invariants 与完整 graph；全部 Research authority 的 28 份 Markdown 中 272 个 local links、42 个 anchors 有效，UPSTREAM 可分别从 root ARCHITECTURE、Research ARCHITECTURE 与 Research AGENTS 到达。Provider dependency 扫描未发现直接依赖授权；禁止示例、公开 Dataset identity 与 upstream failure 描述不构成 provider integration。

本轮找到可用 Python 3.13，并在 repository root 建立 canonical Poetry `.venv`、按现有 lock 安装依赖；root project / lock 未改变。现有 repository authority topology suite 为 13 passed，Research Study authority topology suite 为 12 passed。两套旧 tests 不完整覆盖新 policy，故另行核对 links / anchors、reachability、concrete inputs / key / population / grain 保持不变及完整差异。`git diff --check` 通过；范围仅为上述九份 authority Markdown。

## Observation implementation architecture reconciliation

本轮基线 `e86fbdb69fb4a3cd4e6a23cf1d9d9b9efade4a7c`，codex/observation；本次续轮开始时已有上一轮未提交 authority edits，按当前附件逐项复核并补齐，HEAD 未改变。已包含 Study 基线 754758a 与 UPSTREAM policy，prerequisite 满足。本轮只落位 authority / reconciliation，未开始 Python、SQLite、DataLake / Snapshot / Study implementation、CLI / HTTP；不 commit / push。

### Decisions 与 canonical owners

新增 [framework IMPLEMENTATION](observations/IMPLEMENTATION.md) 唯一拥有 namespace、ensure lifecycle、common errors、owned public object boundary、factory、placement / atomic complete publication、shared mechanics 与 tests handoff；新增 [Universe IMPLEMENTATION](observations/cffex_option_expiry_universe/IMPLEMENTATION.md) 和 [Chain IMPLEMENTATION](observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md) 拥有具体 exports、field / type projection、public dependency wiring 与 execution mapping。Framework architecture / Authoring / Schema、module / AGENTS 仅最小同步 navigation / handoff；两份 entry 替换已由本轮决定的 deferred path / topology 描述，两份 Artifact 仅澄清 Python mapping / coverage context，不改变 facts。首个 Study METHOD 仅补 public package binding links，不改变 workflow。

V1 consumer 直接 concrete import → typed immutable Request → 无参 create_service → ensure → owned complete Artifact。Framework root 发布 ObservationError / ObservationInvalidRequestError / ObservationOperationError，Study 不 import upstream classes / errors 或读取 SQLite。Invalid semantic request 在 upstream mutation 前识别；合法 request 的转换拒绝、proof / calculation / persistence / publication failure 为 OperationError，不返回 partial，不换源。

Runtime placement 为 `market-research/observations/<observation-id>/data/<observation-id>.sqlite3`，root-relative internal resolution、exactly one SQLite per Observation；没有上层 runtime-data convention conflict。Current ignore 不覆盖新路径，实施前必须补 ignore 并验证 WAL / journals；本轮不创建 DB 或改 ignore。Normalized business lookup → complete hit 零 upstream → miss 后 public upstream work / whole Artifact in memory → atomic publication。Concurrent misses 可重复计算，至多一个 complete logical Artifact；不承诺 single-flight，不建 job / pending / retry / history framework，不做 automatic migration / refresh / TTL / force。

两个 producer 继续 DataLake-backed：Universe 仅 Options public service，exact range ensure → complete export → sorted unique in-window expiries，Calendar prerequisite 留在 Options 内；chain Calendar public complete proof → 单 product-day public check / 必要 ensure / export → complete-but-absent 才回溯 → 首个非空 full matching chain。Public row / provenance 全部投影为 Observation-owned immutable values，市场字段 meaning / units / None 仍归 upstream，不泄漏 Export / Row / Coverage runtime object。Shared mechanics 不知道 expiry / DTE / Dataset / Product / concrete schema。没有 generic DataLake / Snapshot adapter 或 direct external-provider dependency。

### Dependency 与 readiness

已核对 Calendar / Options SERVICE、DataLake APPLICATION、实际 concrete public init exports 及现有 runtime request / ensure / export surface；已发布 contracts 足以支持本轮映射，无 DataLake / Snapshot public capability gap，无需 Snapshot selection。未调用 factory / ensure、provider 或读取 runtime DB；本轮仅静态核对及 import / topology verification，不宣称实盘网络 execution 已验证。

| Scope | Current state |
| --- | --- |
| 两个 Observation semantics | Authority Complete（保持既有 meaning） |
| Framework 与两个 concrete implementation architectures | Implementation Architecture Complete |
| 两个 concrete Observation | Authority Complete / Dependency Reconciled / Implementation Architecture Complete / Implementation Ready，依赖 public surface 可用且无 semantic conflict / capability gap；不是 runtime 已存在 |
| Observation runtime | Not Implemented |
| First Study | Study Authority Complete；本任务范围内 Observation dependency invocation contract fully specified；runtime Dependency Reconciled=false，Implementation Ready=false，等待两个 producers 实施与 bindings 复核 |

下一步按 minimal shared runtime primitives / common errors → Universe implementation / acceptance → chain implementation / acceptance → 两项 durable reuse / failure / public ownership reconciliation → first Study dependency reconciliation → Study implementation 的顺序。Shared primitives 只覆盖两项 producer 已真实需要的 mechanical concerns，不预建 generic framework。SQL DDL / indexes / serialization / transaction details 是下一阶段 mechanics，未授权 Artifact definition evolution、cross-Observation transaction、Observation CLI / HTTP 或 Study business redesign。

### Validation

本轮使用现有根 canonical `.venv` 执行 repository authority topology tests：13 passed；Research Study authority topology tests：12 passed。现有 tests 未覆盖新 Observation public namespace / owned types / publication implementation，旧 Study fixtures 仍固定 mandatory analyses / evidence topology，保持既有 reconciliation drift，不修改 tests 或 runtime 迎合。后续 producer implementation 必须补本轮 IMPLEMENTATION 要求的三层验证。

Supplemental 只读检查通过：31 份 Research Markdown、312 个 local links、46 个 anchors；三份新增 owners 均可从 root ARCHITECTURE、Research ARCHITECTURE 和 Research AGENTS 到达。Actual DataLake public imports / coverage / ensure / export surfaces 可用，未调用 factories / services。逐项审查当前附件第 30 节二十项 completion checks：public contract / owned type projection、zero-upstream hit、exactly-one SQLite、atomic complete publication、failure taxonomy / no failover、concrete mapping / Study bindings 与 readiness 均有明确 owner。

完整差异含三份新增文件已审阅，`git diff --check` 与 trailing-whitespace 检查通过。范围为 3 new / 11 modified Research authority Markdown；concrete inputs / key / population / grain 文段保持不变，DATE_RESOLUTION、UPSTREAM、DataLake / Snapshot、runtime source、tests、root project / lock 和 ignore 未修改。当前 Observation architecture 无 direct provider path / failover，DataLake public capability 无 gap。Research runtime source 扫描未发现 direct provider import / transport call；旧 `tests/test_im_basis.py` 引用 `market_snapshot.sources.tushare` 用于 fake-Source monkeypatch，是既有 private-boundary test drift，本轮仅记录、不修改 tests，也不授予新 Observation 依赖该路径的权限。`test_research_execution.py` 中 TUSHARE_TOKEN 为禁止依赖断言的字符串，不是 credential access。具体网络 / persistence 行为仍须下一阶段实现验证。


本次 completion audit 的二十项要求与实际 owners 对照如下（验证 authority，不冒充尚未实现的 runtime behavior）：

| 附件第 30 节 checks | Current-state evidence |
| --- | --- |
| 1–2：framework 唯一 owner / 两项 concrete handoff | 三份 IMPLEMENTATION 实际存在；module / AGENTS / entries 逐层导航，各自 intro 明确 responsibility。 |
| 3–5：ensure / factory / errors | Framework Public namespace、Factory、Public failures sections；concrete signature / exports tables，无参 factory，无重叠 verbs。 |
| 6–7：owned Python types / no upstream leakage | Framework object boundary；两项 concrete field / type / provenance mapping；chain row fields 与 actual public OptionsDailyRow fields 全部对应。 |
| 8–12：one DB / no global DB / zero-upstream hit / atomic publication / concurrency | Framework Owned SQLite 与 Complete publication sections；两个 explicit paths、normalized-input lookup、whole-Artifact validation、single atomic publication、same-key loser / failure handling。 |
| 13–16：两项 DataLake dependencies / no provider / no failover | Concrete execution mappings、未修改的 UPSTREAM；实际 public imports 可用；provider / private-source AST scan 仅既有 legacy test finding，runtime source 无 findings。 |
| 17：Study bindings | METHOD request fields 与两个 concrete Request fields 一一对应，owned Artifact resolution fields 支持现有 manifest；Study runtime readiness 未提前推进。 |
| 18–20：links / diff / tests | 31 Markdown 的 312 links / 46 anchors 与三入口 reachability、git diff --check、13 + 12 passing topology tests；旧 coverage 缺口已记录。 |

## Observation → DataLake invocation semantics reconciliation

本轮基线为 `334bd0fe838af9ef197ea9e45362f86c8e583152`，codex/observation，开始时 tracked 工作区干净。仅修改五份 Research authority / reconciliation Markdown：UPSTREAM、两个 concrete IMPLEMENTATION、Universe entry 的一处旧 deferred-order 描述，以及本记录。Framework IMPLEMENTATION 已覆盖 complete-hit / owned values / atomic publication，保持原文；没有新增 authority layer、Python / tests / DataLake 变更、runtime state、commit 或 push。

[UPSTREAM](observations/UPSTREAM.md) 唯一拥有本轮 framework-level reconciliation：Observation complete lookup 先于 DataLake、hit 零 upstream factory / service calls 与 recomputation、minimum legal Dataset invocation sequence、无通用 coverage → ensure → export protocol、ensure 与 export 的角色、one committed export 的 coverage + payload proof、missing / proven absence / failure 区分、owned public values 与 opaque execution。Concrete sequences 唯一进入 [Universe IMPLEMENTATION](observations/cffex_option_expiry_universe/IMPLEMENTATION.md) 与 [DTE-chain IMPLEMENTATION](observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md)；Universe entry 只链接已锁定 mapping，不再保留检查顺序未决表述。

只读核对 DataLake APPLICATION、Calendar / Options SERVICE 与 Options TRADING_DAYS：export read-only / committed snapshot、ensure 的 incomplete / failures、成功缓存跳过，以及 prerequisite ownership 均支持本轮映射，**未发现 DataLake contract conflict 或 capability gap**。Read-only Options prerequisite failure 属于 operation failure，不能冒充目标已知的 cache missing；初始 failed cache unit 与本次 ensure failure 不混淆。不修改 DataLake contract、不绕过 prerequisite、不添加 generic adapter / gateway、direct provider 或 alternative semantic path。

两项 Observation 继续保持 **Authority Complete / Dependency Reconciled / Implementation Architecture Complete / Implementation Ready**，runtime **Not Implemented**。首个 Study 继续 **Study Authority Complete**，runtime Dependency Reconciled=false / Implementation Ready=false。本轮只落实用户已确认的 invocation narrowing，没有新的 business semantic decision；inputs / keys / population / grain / Artifact / date-resolution / Study workflow、refresh / definition evolution 等 deferred concerns 均不改变。

### Validation 与既有 baseline failure

根 canonical Poetry environment 执行 `poetry run pytest market-snapshot/tests/test_authority_topology.py market-research/tests/test_study_authority_topology.py -q`：修改前与修改后均为 **24 passed / 1 failed**。失败均为 `test_new_runnable_studies_have_semantic_package_boundaries` 将 legacy source 目录的 ignored `__pycache__` 残留当作 runnable package，随后找不到 `__init__.py`；规划阶段首先报告 im_basis_baseline，本轮首先报告 price_to_lagged_ma_distribution，candidate set 遍历顺序不同。只读目录核对发现五个 legacy 残留目录均仅含 __pycache__，Git 没有其 tracked package files；本轮保持这些缓存与 tests 原样，无新增 test failure，不以历史 13 + 12 passed 记录冒充当前结果。

按本轮附件十九项检查审阅 framework / concrete ownership、calls / failure / projection / opacity 与 readiness；31 份 Research Markdown 的 329 个 local links / 58 个 anchors 有效，五份修改文档均可从 root ARCHITECTURE、Research ARCHITECTURE 与 Research AGENTS 到达，`git diff --check` 通过，完整 diff 范围已核对为上述五份 Markdown。验证 authority，不宣称 runtime invocation / publication 已实施或测试；本轮结束，不开始 implementation。
