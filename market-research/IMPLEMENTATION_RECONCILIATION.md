# Market Research implementation reconciliation

> 本文保留历次执行证据。当前 component / Observation 分类及 Universe / Study runtime gaps 唯一进入 [Shared component semantic reconciliation](#shared-component-semantic-reconciliation)；此前把 Universe 称为 Observation、两个 durable producers、零 upstream E2E 或整个 slice 无 drift 的结论只适用于当时基线，已被本轮新语义 supersede。旧链接导航到新 owner 或本轮 gap，不表示旧 contract 继续有效。

本文件记录 Observation-first authority 更新的基线、implementation / test drift 与交接状态，不拥有新的业务语义。入口见 [module architecture](ARCHITECTURE.md)；当前 contracts 分别见 [Component authority](shared/ARCHITECTURE.md)、[Research public upstream](UPSTREAM.md)、[Observation authority](observations/ARCHITECTURE.md)、[Study Schema](studies/SCHEMA.md)、[Implementation Contract](studies/IMPLEMENTATION.md)、[Compatibility](studies/COMPATIBILITY.md) 与 [Research UI](ui/ARCHITECTURE.md)。

下文各轮记录保留历史基线与当时验证结果；首个 Observation 的落位见 [首轮 concrete 记录](#首个-concrete-observation-authority-落位)，workflow / 第二个 Observation / 首个 Study 见 [workflow reconciliation](#observation-driven-study-authority-reconciliation)，当时 upstream selection policy 与检查见 [历史 upstream reconciliation](#observation-upstream-dependency-policy-reconciliation)。Observation runnable mapping 的历史设计见 [implementation architecture reconciliation](#observation-implementation-architecture-reconciliation)。历史测试结果不代表本 worktree 已验证。

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

新增 [cffex_option_expiry_universe entry](shared/cffex_option_expiry_universe/ARCHITECTURE.md) 与其 [旧 Artifact contract 的当前替代 owner](shared/cffex_option_expiry_universe/CONTRACT.md)。Human 已确认 historical trade-date window 与 inclusive expiry window 相同；完整 public rows 中实际出现且 expiry 位于该窗口的 sorted unique dates 是唯一 empirical definition，不宣称覆盖只在窗口外挂牌的合约。十三个 Observation Schema areas 均有 owner；合法完整空 universe 可发布 complete。

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

新增 [framework IMPLEMENTATION](observations/IMPLEMENTATION.md) 唯一拥有 namespace、ensure lifecycle、common errors、owned public object boundary、factory、placement / atomic complete publication、shared mechanics 与 tests handoff；新增 [旧 Universe handoff 撤销 / gaps](#shared-component-semantic-reconciliation) 和 [Chain IMPLEMENTATION](observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md) 拥有具体 exports、field / type projection、public dependency wiring 与 execution mapping。Framework architecture / Authoring / Schema、module / AGENTS 仅最小同步 navigation / handoff；两份 entry 替换已由本轮决定的 deferred path / topology 描述，两份 Artifact 仅澄清 Python mapping / coverage context，不改变 facts。首个 Study METHOD 仅补 public package binding links，不改变 workflow。

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

[UPSTREAM](observations/UPSTREAM.md) 唯一拥有本轮 framework-level reconciliation：Observation complete lookup 先于 DataLake、hit 零 upstream factory / service calls 与 recomputation、minimum legal Dataset invocation sequence、无通用 coverage → ensure → export protocol、ensure 与 export 的角色、one committed export 的 coverage + payload proof、missing / proven absence / failure 区分、owned public values 与 opaque execution。Concrete sequences 唯一进入 [旧 Universe handoff 撤销 / gaps](#shared-component-semantic-reconciliation) 与 [DTE-chain IMPLEMENTATION](observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md)；Universe entry 只链接已锁定 mapping，不再保留检查顺序未决表述。

只读核对 DataLake APPLICATION、Calendar / Options SERVICE 与 Options TRADING_DAYS：export read-only / committed snapshot、ensure 的 incomplete / failures、成功缓存跳过，以及 prerequisite ownership 均支持本轮映射，**未发现 DataLake contract conflict 或 capability gap**。Read-only Options prerequisite failure 属于 operation failure，不能冒充目标已知的 cache missing；初始 failed cache unit 与本次 ensure failure 不混淆。不修改 DataLake contract、不绕过 prerequisite、不添加 generic adapter / gateway、direct provider 或 alternative semantic path。

两项 Observation 继续保持 **Authority Complete / Dependency Reconciled / Implementation Architecture Complete / Implementation Ready**，runtime **Not Implemented**。首个 Study 继续 **Study Authority Complete**，runtime Dependency Reconciled=false / Implementation Ready=false。本轮只落实用户已确认的 invocation narrowing，没有新的 business semantic decision；inputs / keys / population / grain / Artifact / date-resolution / Study workflow、refresh / definition evolution 等 deferred concerns 均不改变。

### Validation 与既有 baseline failure

根 canonical Poetry environment 执行 `poetry run pytest market-snapshot/tests/test_authority_topology.py market-research/tests/test_study_authority_topology.py -q`：修改前与修改后均为 **24 passed / 1 failed**。失败均为 `test_new_runnable_studies_have_semantic_package_boundaries` 将 legacy source 目录的 ignored `__pycache__` 残留当作 runnable package，随后找不到 `__init__.py`；规划阶段首先报告 im_basis_baseline，本轮首先报告 price_to_lagged_ma_distribution，candidate set 遍历顺序不同。只读目录核对发现五个 legacy 残留目录均仅含 __pycache__，Git 没有其 tracked package files；本轮保持这些缓存与 tests 原样，无新增 test failure，不以历史 13 + 12 passed 记录冒充当前结果。

按本轮附件十九项检查审阅 framework / concrete ownership、calls / failure / projection / opacity 与 readiness；31 份 Research Markdown 的 329 个 local links / 58 个 anchors 有效，五份修改文档均可从 root ARCHITECTURE、Research ARCHITECTURE 与 Research AGENTS 到达，`git diff --check` 通过，完整 diff 范围已核对为上述五份 Markdown。验证 authority，不宣称 runtime invocation / publication 已实施或测试；本轮结束，不开始 implementation。

## Research persistence / orchestration authority reconciliation

本轮基线为 `0827378626602fa15683a51cfd0763076774e455`，codex/observation，开始时工作区干净。本轮仅修改 Research authority / reconciliation Markdown，并新增首个 Study 的 specialized implementation handoff；未修改 Python、tests、DataLake、配置、ignore、legacy Compatibility 或 sibling Study authority，未创建 SQLite、runtime、commit 或 push。历史记录保留；以下决定 supersede 旧记录中强制 retained plan / collection、所有 runner 必须有 output directory，以及 producer runtime 缺失即否定 design Implementation Ready 的表述。

### Human decisions 与 canonical owners

[Observation architecture](observations/ARCHITECTURE.md) 拥有唯一 reusable empirical persistence / exactly-one SQLite boundary；[framework IMPLEMENTATION](observations/IMPLEMENTATION.md#durable-reuse-acceptance) 拥有 successful ensure 的 whole-Artifact validation / atomic durable publication-before-return 与 service recreation 零 upstream acceptance。[旧 Universe handoff 撤销 / gaps](#shared-component-semantic-reconciliation) 与 [Chain IMPLEMENTATION](observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md) 引用该验收，不复制框架机制。每个 concrete 的同一 owned SQLite 容纳多个 requests / complete Artifacts；Study 不读取 SQLite、不复制 rows 建第二份 empirical cache。

[Study Schema](studies/SCHEMA.md) 与 [Workflow](studies/WORKFLOW.md) 分别拥有 runtime / retained object model 与 orchestration boundary。Human 确认 runtime plan、references、counts 不自动成为 Artifact，retained Workflow Artifacts=0 / Analysis=0 / Evidence=0 是完整合法 Study；明确声明 retained outputs 的其他 Study 继续使用现有 retention / publication 规则。Future Analysis 只消费 Study 已确保 complete 的 Artifacts，其 persistence 与 Evidence persistence 未决，本轮不设计。

首个 Study 的 [entry](studies/cffex_option_expiry_dte_collection/ARCHITECTURE.md)、[INPUTS](studies/cffex_option_expiry_dte_collection/INPUTS.md)、[METHOD](studies/cffex_option_expiry_dte_collection/METHOD.md)、[RESULTS](studies/cffex_option_expiry_dte_collection/RESULTS.md) 拥有 orchestration-only objective、四项必填 request / normalized tuple、执行与非持久化 outcome。Human 确认 chain failure 后继续剩余全部项、最终任一失败即 failure、已成功 Observation 不 rollback；complete empty Universe 成功。撤销 retained expiry_plan / observation_collection 的 Artifact identity、manifest、materialization、publication 与 run-directory contract，runtime references 不成为新的 reusable product。Success CLI 只呈现 request / counts，failure 呈现阶段、实际 counts 与有序 readable reasons，unknown counts 不伪报零；本 Study exit codes 0 / 1 / 2 仅由 RESULTS 拥有。

新增 [Study IMPLEMENTATION](studies/cffex_option_expiry_dte_collection/IMPLEMENTATION.md)，从 entry / METHOD 可达，继承通用 [Package Contract](studies/IMPLEMENTATION.md)，拥有 mandatory init / cli / study、typed request / outcome projection、explicit public Observation bindings、lazy composition / orchestration 分工与 future acceptance。没有空 analyses / evidence / observations modules。[Research UI](ui/ARCHITECTURE.md#3-shared-configuration-and-output-placement) 拥有 orchestration-only / retained-output 两种 shape；[Configuration](ui/CONFIGURATION.md) 的 output.root schema / loader failure semantics 不变，仅 retained-output runner 加载。首个 Study 不加载 output config、不调用 run-directory / publication helpers，不提供 output / database / sqlite-path / resume / overwrite flags。

[Authoring](studies/AUTHORING.md#publication-与-dependency-handoff) 唯一拥有 readiness 定义：authority、dependency contracts、bindings 与 implementation architecture complete 且无 semantic gap 即 design Implementation Ready；producer runtime 缺失单独记录，实际 runtime Dependency Reconciled 仍需 producer implementation / bindings 验证。Review / Skeleton、module entry / AGENTS 与 framework package contract 同步适用范围，不改变 legacy Compatibility。

### Contract preservation、capability 与 readiness

[UPSTREAM](observations/UPSTREAM.md) 保持原文；Universe ensure-first、DTE Calendar / Options read-first / ensure-if-needed、one committed export 的 proof + payload、missing / proven absence / operation failure 三态与 failure 禁止跳日 / 换源规则保持不变。两项 Observation inputs / business keys / population / grain / market facts / DTE formula / date fallback / ARTIFACT / DATE_RESOLUTION 不变。只读核对现有 DataLake public contracts，未发现 contract conflict 或 DataLake / Observation semantic capability gap；尚缺 producers runtime 是实施工作，不是新的 semantic decision。

| Scope | Current state |
| --- | --- |
| Observation framework / shared mechanics design | Authority Complete / Implementation Architecture Complete / Implementation Ready；runtime Not Implemented。 |
| Universe / DTE Chain | Authority Complete / upstream Dependency Reconciled / Implementation Architecture Complete / Implementation Ready；runtime Not Implemented。 |
| First Study | Study Authority Complete / Observation dependency contracts complete / Study implementation architecture complete / Implementation Ready；runtime Not Implemented，actual runtime Dependency Reconciled 未完成。 |

本轮 human decisions 已编码且无剩余 vertical-slice semantic gap。**Repository vertical slice is Authority Complete and ready for implementation.** 下一 goal 顺序为 minimal shared mechanics → Universe → DTE Chain → Observation runtime / Study bindings reconciliation → Study → end-to-end tests。Observation refresh / definition evolution、future Analysis persistence 等已有 deferred concerns 不阻止当前已锁定 slice，也不由本轮发明实现。

### Validation 与既有 test limitation

按附件十九项逐项审阅：1–4 的唯一 persistence / one SQLite / durable-before-return / restart reuse 由 Observation owners 承载；5–7 的 public-only consumer / no upstream / no second cache 由 Study Schema / Workflow / handoff 承载；8–11 的 runtime plan / no retained collection / zero Workflow Artifacts / zero Analysis-Evidence 由首个 Study 四份 authority 承载；12–13 的 CLI / UI shape 由 INPUTS / UI 承载；14 的调用规则保留由未改的 UPSTREAM 与 concrete mappings 证明；15–16 的 bindings / no direct provider 由 METHOD / handoff 承载；17–19 由 local links / anchors / stable-entry reachability、两套 tests 与完整 diff / whitespace review 验证。此处验证 authority acceptance contract，不宣称尚不存在的 runtime behavior 已通过。

根 canonical Poetry environment 执行 `poetry run pytest market-snapshot/tests/test_authority_topology.py market-research/tests/test_study_authority_topology.py -q`，修改前后均为 **24 passed / 1 failed**，无新增失败。既有 `test_new_runnable_studies_have_semantic_package_boundaries` 将 ignored legacy cache-only directories 当作 runnable package，找不到 __init__.py；修改前首先报告 price_to_lagged_ma_short_horizon_reversion，修改后首先报告 mo_option_risk_premium_baseline，set candidate order 不同但同一 limitation。五个 legacy 残留目录只有 ignored __pycache__，没有 tracked package source；缓存 / tests 保持原样。旧 REQUIRED_IMPLEMENTATION 仍固定 observations / analyses / evidence modules，下一 implementation 阶段需 reconciliation，不以本轮 authority-only edits 掩盖测试覆盖缺口。

全部受影响 Markdown local links / anchors 有效，semantic owners（包括新增 handoff）从 root / Research stable entry 可达；local AGENTS 按执行政策继承链发现。完整 diff 与新文件已审阅，`git diff --check` 通过；范围仅为 20 modified / 1 new Research Markdown。没有 SQLite、Python、test、DataLake、配置、ignore 或 runtime state 变更。本轮停止于 implementation handoff，不开始实施。

## First Observation-driven vertical slice implementation

本次 implementation 基于 `d6db0c5f1ec065a6b920829b93e53f0bc05c8c5e`，依当前 framework / concrete handoff 完成 producer-first vertical slice。此前各轮记录保留为历史基线；本节 supersedes 两项 producers / 首个 Study 的 Not Implemented 状态与旧 topology test limitation，不改变已锁定业务语义。

### Implemented components 与 reconciliation

| Owner / package | Runtime / verification |
| --- | --- |
| [Observation framework](src/market_research/observations/__init__.py) | Public common errors、private root-relative path / SQLite transaction / safe owned-value serialization primitives；无 registry、executor 或 shared business schema。 |
| [ExpiryUniverse](src/market_research/observations/cffex_option_expiry_universe/__init__.py) | Immutable request / Artifact / provenance；exact-range ensure-first Options integration、sorted unique inclusive extraction、owned durable SQLite。Implemented / Verified。 |
| [ExpiryDteChain](src/market_research/observations/cffex_option_expiry_dte_chain/__init__.py) | Immutable request / Artifact / rows / provenance；Calendar / Options read-first、incomplete-only ensure、complete-but-absent-only fallback、完整 matching population 原值保留、owned durable SQLite。Implemented / Verified。 |
| [First Study](src/market_research/studies/cffex_option_expiry_dte_collection/study.py) / [CLI](src/market_research/studies/cffex_option_expiry_dte_collection/cli.py) | 四输入 admission、exact public Observation bindings、ascending runtime plan、每项一次 invocation / failure 后继续、non-persistent counts / failure details、exit 0 / 1 / 2。Implemented / Verified / actual runtime Dependency Reconciled。 |

Public factory 为无参 `create_service()`，合法 request 在 persistence / dependency access 前验证，complete hit 在所有 upstream factories / operations 前返回。每个 concrete 唯一 owned SQLite 以三个 normalized business fields 作 primary key，多请求共存；整份合法 Artifact 先在 memory 形成，再以 SQLite FULL synchronous transaction 原子提交后返回。Concurrent losers 返回已发布 winner，无 overwrite / 第二 logical Artifact。Corrupt / unreadable / unsupported state 属 operation failure，不伪装 miss；未创建 pending / attempt / generation / migration / retry framework。

Canonical production placement 保持各 Observation `data/<identity>.sqlite3`；根 ignore 覆盖整个 owned data directory，包括 WAL / SHM / journal。测试只写 temporary persistence；没有创建真实 Observation state、访问真实 provider、改动 DataLake public semantics / package registration / lab dispatch。Research 没有 direct provider / credential / upstream-private imports；Study 没有 DataLake / Snapshot / SQLite access、market-row copy 或 retained output。

Authority / package surface / runtime / tests 已核对：Universe observed-window、所有 inputs / keys、chain DTE formula / Calendar proof / missing-absence-failure 三态、完整 population / nullable facts，以及 Study orchestration / zero retained artifacts 均保持原契约。没有 DataLake / Observation semantic conflict 或 capability gap，没有剩余 slice authority/runtime drift。Refresh、definition evolution、future Analysis / Evidence persistence 等原有 deferred concerns 保持 deferred。

### Acceptance evidence

- [Producer acceptance](tests/test_observation_runtime.py) / [public topology](tests/test_observation_boundaries.py)：domains、exact upstream sequences、empty / zero-target Universe、holiday / weekend / multi-window Calendar proof、target=1 / exact DTE / proven absence / incomplete ensure、非法 export / unit / prerequisite failures、完整 rows / None、durable-before-return、service recreation 零 upstream reuse、多请求共存、concurrent unique publication、corrupt / partial / incompatible state、real SQLite insert abort / interruption / factory failure。
- [Study / CLI acceptance](tests/test_expiry_dte_collection.py)：四 required flags / strict parsing、help / invalid inputs 零 execution、exact bindings、unknown counts、empty success 零 chain construction、factory / operation / invalid Artifact failures、ordered full-plan continuation、counts / presentation / exits、public-only imports / no persistence、installed lab discovery / help / parse exit propagation。
- [Fresh-process E2E](tests/test_observation_vertical_slice.py)：第一进程以 controlled public Dataset doubles 运行真实 Study CLI，发布 Universe 与两个 chains；第二独立进程禁用全部 upstream factories，same request 返回相同 summary / retained payloads，factory / Options / Calendar calls 全为零。只有两个 Observation-owned SQLite，无 Study retained files。
- [Study topology tests](tests/test_study_authority_topology.py) 已 reconciliation：mandatory init / cli / study，conditional helpers 按实际 concern 检查；cache-only legacy directories 不冒充 runnable packages。保留 authority pointer / single-script / missing helper 的拒绝测试，并新增每个 mandatory module 缺失的验收；没有删除、skip 或弱化仍有效的行为检查。

### Quality gates 与 baseline limitations

全部从 repository root 唯一 Poetry / Python 3.13 根 `.venv` 执行：

| Check | Result |
| --- | --- |
| Producer checkpoint + Calendar / Options / DataLake boundary regression | 195 passed，随后补充 publication / interruption / factory / exact-DTE tests。 |
| Final slice / Research topology / repository authority focused checks | 144 passed。 |
| `poetry run pytest -q -rs` | 997 passed / 2 existing skips；Windows 无 symlink creation privilege。一个 existing Starlette deprecation warning。 |
| `poetry run ruff check lab data-lake market-research market-snapshot backend-api` | Passed。 |
| `poetry run mypy market-research lab data-lake` | Passed，90 source files。 |
| Authority local links / anchors / root reachability，complete diff / whitespace review | Passed；最终检查见本次执行记录。 |

额外尝试 repository-wide `ruff check .` 与根配置 `mypy`，有两个确认属于未改基线的限制：`web-ui/scripts/export_contracts.py:19` 的 I001 import sorting（`git show HEAD:...` 同样失败），以及 `backend-api/tests/support` 与 `market-snapshot/tests/support` 同名造成 mypy Duplicate module（两个目录无 diff，独立指定二者亦复现）。这些不是本 slice 引入的问题；未修改 unrelated owners 来隐藏失败，受影响 Research / lab / DataLake scope 单独通过 lint / type checks。

**First Observation-driven Study vertical slice is implemented and reconciled with repository authority.**

## Shared component semantic reconciliation

本轮唯一基线为 `34f28e707545d28eb588b6af42168c7e2000d8eb`，隔离 worktree 为 `C:\Users\Benjamin\.codex\worktrees\research-component-authority\hg-market-state-lab`，分支 `codex/research-component-authority`。HEAD 从该 commit 建立，无 develop 合并。主 checkout 与另一任务 owned 的 bb43 worktree 未修改；本任务 attached worktree 已核对。前次中断后从同一隔离树续做，没有另建执行任务。

本轮只改 authority Markdown / navigation，撤销旧 Universe 三份 authority、建立 shared resolver entry / CONTRACT；无 Python、tests、配置、依赖声明、lock、ignore 或 DataLake contract 变更，无 runtime SQLite 创建 / 删除 / 迁移，无 push。验证环境按根 lock 安装到本 worktree 根唯一 Python 3.13 .venv，不使用主 checkout / module-local 环境。前述历次记录与链接保留为历史 evidence；其“两项 Observation / 两库 / 整个 Study 重启零上游 / 无 drift”结论不适用于新定位。

### Semantic decisions 与唯一 owners

| Concern | Canonical owner / decision |
| --- | --- |
| Stable mental model / navigation | [Module architecture](ARCHITECTURE.md)：Component 复用小领域机制，Observation 是最小独立 research artifact boundary，Study / Analysis 拥有研究目标、编排 / 解释。具体 I/O / operation / workflow 不上提。 |
| Classification / promotion / admission | [Component authority](shared/ARCHITECTURE.md)：local logic 可 colocate，只有明确跨研究机制复用才提升 component；Reuse does not imply Observation。独立 artifact 值得下游消费与解释才进入 Observation authoring。 |
| Public fact consumption | [Research UPSTREAM](UPSTREAM.md)：共用 DataLake-first、public services、one committed export proof、failure / absence、no failover / provider、fact ownership。由原 Observation policy 拆出，不为组件加载 retained lifecycle。 |
| Observation retained lifecycle | [Observation architecture](observations/ARCHITECTURE.md) / [specialization](observations/UPSTREAM.md) / [IMPLEMENTATION](observations/IMPLEMENTATION.md)：inputs / business key、complete hit、durable publication、one SQLite / 幂等保留，只适用于真正的 Observation。可调用 component / 包含 local logic。 |
| Universe resolver | [Entry](shared/cffex_option_expiry_universe/ARCHITECTURE.md) → [CONTRACT](shared/cffex_option_expiry_universe/CONTRACT.md)：observed-window expiry selection 与 ensure-first Options proof 保留；撤销 research Artifact、business key、SQLite / cache / durable-hit。原 observations authority 不再存在。 |
| Study / Analysis dependencies | [Study Schema](studies/SCHEMA.md) / [Workflow](studies/WORKFLOW.md)：orchestration 可调用 resolver / reader 准备输入；Analysis 只计算已准备的 complete inputs / 调用 pure component，无隐藏 fetch / persistence。Shared mechanism 不共享 question / interpretation / Evidence。 |
| Current Study | [Collection entry](studies/cffex_option_expiry_dte_collection/ARCHITECTURE.md) / [METHOD](studies/cffex_option_expiry_dte_collection/METHOD.md)：1 component + 1 Observation，resolve Universe → whole ascending plan → all chain ensures → summary。Empty / chain continuation、零 Study retained output、counts / CLI exits 保留；Universe stage 改为 resolve_expiry_universe。 |
| Future date-specific price reader | Component authority 允许消费已有 [Futures](../data-lake/datasets/tushare_equity_index_futures/SERVICE.md) / [Index](../data-lake/datasets/tushare_index_daily/SERVICE.md) authoritative contracts。DataLake 继续拥有行情事实、单位、nullable rules / cache / export；具体 price selection / missingness 等真实需求出现再锁定。本轮不定义新 reader contract / code / framework。 |

### Explicit conflicts 与 implementation gaps

| Baseline evidence / conflict | Current resolution / remaining work |
| --- | --- |
| Universe old authority 要求独立 Artifact / key / exactly-one SQLite；新语义是小领域 resolver | 新 owner 撤销旧 lifecycle；保持既定 inputs、observed-window derivation、完整 / empty / failure 与 public dependency，分类改变不篡改市场事实。 |
| [Universe source facade](src/market_research/observations/cffex_option_expiry_universe/__init__.py) / [_models](src/market_research/observations/cffex_option_expiry_universe/_models.py) 仍指旧 authority、发布 ExpiryUniverseArtifact / observation_identity / semantic_identity | 未修改代码；下轮迁到 component public boundary / owned result 与 own failure contract，更新 pointers / consumers，不继续把旧 API 当 canonical resolver。具体 Python names / layout 属实现 mechanics。 |
| [_service](src/market_research/observations/cffex_option_expiry_universe/_service.py) 先 _persistence.load，再 public Options calls，最后 publish；factory 指旧 Universe SQLite | 与 component 无 research persistence 冲突；下轮移除 Universe research lookup / publication，保留 exact-range ensure → export proof / extraction / diagnostics。不自动迁移或删除任何已存在旧 DB，不从旧 Artifact 读取新 resolver result。 |
| [Study orchestration](src/market_research/studies/cffex_option_expiry_dte_collection/study.py) / [CLI](src/market_research/studies/cffex_option_expiry_dte_collection/cli.py) 仍 import Universe Observation、调用 ensure、校验 Artifact identity、stage=ensure_expiry_universe | 下轮绑定 component public I/O、校验对应 complete result、使用 resolve_expiry_universe stage / own errors。保持四 flags、plan / chain continuation、counts / exits 与无 Study output。 |
| [Producer boundary tests](tests/test_observation_boundaries.py) / [runtime tests](tests/test_observation_runtime.py) 把 Universe 列为 Observation；[E2E](tests/test_observation_vertical_slice.py) 要求两个 research SQLite、第二次禁用全部 upstream factories | 旧验收仍能验证旧实现，不能证明新 contract。下轮重写相关分类 / component tests，验收没有 Universe research SQLite、repeat resolve 合法调用 Dataset，而 chain 继续 durable-hit 零上游。不为本轮检查改业务 / tests。 |
| [Study topology test](tests/test_study_authority_topology.py) 的 test_creation_entry_does_not_link_to_legacy_shared_semantics 用任何 ../shared/ 字符串拒绝新 authoring 导航 | 该断言把新 component authority 与 historical shared semantics 混为一谈。新语义仍禁止默认继承历史研究语义，但允许当前 component 分类入口；本轮保留旧 test，报告新增 failure。下轮更新此区分并补新 owner reachability / boundary acceptance。 |
| [Chain contract](observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md) 曾指 Universe Observation；旧 handoff 宣称整个 slice reconciled | 改指 shared resolver，明确 chain 不依赖 Universe；chain inputs / key / DTE / date resolution / population / Artifact / SQLite 保留。整条 Study 新 wiring 未 reconciliation，不能引用旧 whole-slice green status。 |

### Progressive disclosure 与下一轮 handoff

Stable root → Research module / local AGENTS → shared classification 或 Observation / Study owner；组件 facts 任务进入 Research UPSTREAM，不必读 Observation persistence。Universe entry 只拥有 purpose / classification / boundaries，I/O / invocation / proof / failure 下沉 CONTRACT；Study bindings / step order、outcome 与 Python responsibility 分属 INPUTS / METHOD / RESULTS / IMPLEMENTATION。Component / Observation facts 共用 policy 无第二副本，Observation specialization 仅约束 lifecycle，lower owner 不推翻 repository invariant。

新 helper 可以沿 shared classification 完成 local / shared / Observation 判断，无需扫描 sibling Studies。Historical shared owners 的导航只说明 existing Compatibility，不自动迁移公式 / evidence 或推广默认依赖。Concrete reader 无真实新需求，因此没有预建 implementation directory、registry / provider abstraction / shared utility framework。

当前 classification、Universe semantic contract、Study dependency / workflow / result handoff **Authority Complete**；已选 Options / Calendar public capability sufficient，无 DataLake contract gap。Study 设计 **Implementation Ready**，component carrier / operation spelling / source layout 是 mechanics，下一轮无需重新决定研究含义。新 resolver / Study runtime **Not Reconciled**；chain 保持有效 Observation contract 与已有 implementation。

下一轮明确范围：component public resolver / owned result / failures → 撤销旧 Universe research lifecycle / 更新 source pointers → Study / CLI public wiring / stage → 分类、component / Study topology、focused runtime / controlled E2E acceptance。按 producer-first 顺序，保留 chain 的 durable reuse / whole-publication checks；不扩大为 generic framework、reader、Analysis、DataLake API 或自动处理旧 state。旧 DB 是否显式清理 / 迁移、未来 reader price choice、Observation refresh / definition evolution 不因本轮自动决定；不处理这些也能实施当前 resolver / Study wiring。

### Validation 与限制

基线修改前，在隔离 worktree 根 canonical environment 运行 Research topology + repository authority suite：**28 passed**。修改后相同命令为 **27 passed / 1 failed**；唯一新增 failure 是上述旧 topology test 的 any-shared-link 禁止，不是 baseline failure。本轮范围禁止改 tests / production 迎合旧 topology，故如实保留并交接。Repository local Markdown file links / reachability tests 在该 suite 内通过。


补充检查覆盖全部 117 份 Git-managed Markdown（排除 _temp_docs / runtime dependencies），所有 local file links resolve；32 份 Research semantic authority（不含执行政策 AGENTS）均可从 repository / Research module / Research AGENTS 三入口到达，所有 Research local anchors 有效，无新 orphan / duplicate canonical owner。AGENTS 通过根 / module 路径继承发现，不要求把执行政策嵌入 semantic graph。Repository anchor 扫描发现两处已有 Snapshot gap：daily_market_snapshot/data.md 的 capture/#index_daily 与 #stock_daily；源 / 目标文件均与指定 HEAD 字节内容一致，已确认 baseline 未改，不在本轮扩大修复。

新旧 authority 对照与完整 diff / 新文件内容已审阅：Universe 原三份文档撤销；common upstream / Observation lifecycle concern 拆分可独立消费；只有明确 component promotion 改变默认 shared 入口限制，historical Compatibility 继续有效；Analysis prepared-input / chain retained lifecycle / DataLake boundary 无上层冲突。Git authority-only / exact baseline guard 与 git diff --check 通过，root / dependency / source / tests 没有 diff。没有运行实际市场采集、resolver / Study 新 runtime E2E、Ruff / mypy / 全仓业务 suite：本轮未改实现，现有 runtime 仍是已记录旧语义，这些检查不能证明尚未实施的新 contract；只执行所需 authority gates，不宣称实现验收通过。

Authority 变更清单（路径均相对 market-research）：

| Group | Paths |
| --- | --- |
| Module / navigation / current gaps | AGENTS.md、ARCHITECTURE.md、IMPLEMENTATION_RECONCILIATION.md |
| New shared / public facts owners | UPSTREAM.md、shared/ARCHITECTURE.md、shared/cffex_option_expiry_universe/ARCHITECTURE.md、shared/cffex_option_expiry_universe/CONTRACT.md |
| Observation policy / handoff | observations/ARCHITECTURE.md、observations/AUTHORING.md、observations/SCHEMA.md、observations/UPSTREAM.md、observations/IMPLEMENTATION.md |
| Chain navigation / historical slice status | observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md、observations/cffex_option_expiry_dte_chain/IMPLEMENTATION.md |
| Study framework reconciliation | studies/AUTHORING.md、studies/SCHEMA.md、studies/WORKFLOW.md、studies/SKELETON.md、studies/IMPLEMENTATION.md、studies/REVIEW.md、studies/COMPATIBILITY.md |
| Current Study contracts | studies/cffex_option_expiry_dte_collection/{ARCHITECTURE,INPUTS,METHOD,RESULTS,IMPLEMENTATION}.md |
| Retired Universe Observation authority | observations/cffex_option_expiry_universe/{ARCHITECTURE,ARTIFACT,IMPLEMENTATION}.md（删除） |
