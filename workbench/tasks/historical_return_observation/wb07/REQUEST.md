# Goal: WB-07 — 2026 四大指数真实研究矩阵与 DataLake Cache E2E

Repository: `ougachakaaa/hg-market-state-lab`
Baseline: `develop`，必须包含 `3edb363160a79e5c832c7da58bda6b4e28b19e54`

执行模式：Codex Goal Mode

## Objective

使用现有 Workbench `historical_return_observation` Task，完成一次真实市场数据研究，验证：

1. 自然语言研究需求能够转换为完整 ResearchPlan。
2. Research 能够通过正式 DataLake Public Services 获取真实市场数据。
3. DataLake 能正确缓存、读取和复用 Calendar / Index Daily 数据。
4. Research / Statistics 能够正确计算 16 组收益分布。
5. 所有结果、缓存调用证据、问题和结论均可以被独立审查。

这是 Real Market E2E Acceptance，不是新增研究功能。

优先复用现有 Authority 和实现，不要开发新的框架。

## 研究目标

统计 2026 年四个主要指数的历史累计涨跌幅分布。

### Subjects

按以下顺序：

- 中证1000：`000852.SH`
- 中证500：`000905.SH`
- 沪深300：`000300.SH`
- 上证50：`000016.SH`

上述代码是本次明确指定的候选输入，必须通过 DataLake 的实际 Provider Metadata 验证，不得仅凭代码格式或名称认定身份正确。

### Windows and Horizons

- Inclusive sample window：`2026-01-01` 至 `2026-10-29`
- Horizons：`[1, 3, 5, 10]` 个交易时段
- Metric：`trailing_cumulative_return_v1`
- Metric parameters：`{}`
- Failure policy：`continue`

对于每个交易日 T：

`R(T,H) = close(T) / close(T-H) - 1`

只使用正式 SSE Calendar 确定交易时段，不能根据自然日、工作日或者已有行情行号推断。

样本窗口从 2026 年开始，但应按最大 H=10 正确获取 2025 年末的必要预热数据。

如果 2026-10-29 的行情尚未发布，保留真实 Unavailable 或失败证据，不得静默将窗口改为 10 月 28 日。变更截止日需要明确决策。

### Statistics

本轮使用两种现有方法。

Quantile：

`[0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]`

Interval Count：

`[-0.15, -0.10, -0.05, -0.03, -0.02, -0.01, 0, 0.01, 0.02, 0.03, 0.05, 0.10, 0.15]`

Unit：`decimal_ratio`

必须保留低于最小边界和高于最大边界的样本数量与频率。

这些是本轮验收明确指定的统计规格，不是以后所有 Research 的默认参数。

预期：

- 4 subjects × 4 horizons × 1 window = 16 Research Jobs。
- 每个 Job 进行两项统计，合计 32 个 Analysis Outcomes。

使用一个完整的 Python ResearchPlan。不要使用 HTTP 分段后合并结果。

## Stage 0 — Authority and Readiness

首先读取：

- Root AGENTS.md / ARCHITECTURE.md
- Workbench Task、G1/G3/G4/G5 contracts
- WB-06 ACCEPTANCE / PROBLEMS / LIVE_READINESS
- Research Batch、Trailing Return Input contracts
- DataLake Calendar / Index Daily SERVICE
- DataLake APPLICATION / PERSISTENCE
- Tushare Provider execution contract
- 已有 LIVE-E2E-01 隔离执行机制

确认当前 Task v1 是否已经支持四个 subjects、四个 horizons 的完整执行。

原则上不得改变 Task Version、Research 业务模型或 Statistics 实现。

检查当前数据环境：

1. DataLake Calendar / Index 服务是否可用。
2. 现有默认缓存是否兼容当前 Generation 3。
3. Provider Credential 是否能够解析。
4. 指数 Metadata 能否在合法、受控的真实调用中验证。
5. 是否存在已知的旧缓存不兼容问题。

检查默认缓存时优先只读，不允许自动修复、删除、迁移或覆盖。

## Stage 1 — Build and Freeze Workflow

使用现有 Workbench 完成：

G1 Backend Ready → G3 Capability Discovery → G4 Workflow Planning and Persistence。

G2 Authentication 和 G6 Visualization 维持当前批准的 SKIPPED 语义。

由 Agent 根据本 Goal 的研究目标生成 ResearchPlan，不得复制 WB-06 的旧 Candidate 作为本次研究结果。

必须通过正式 public Preview 验证：

- 16 个 Job 全部展开。
- 32 个预期 Analysis Outcomes。
- Subject / Horizon / Window 顺序正确。
- Python execution surface 合法。
- 日期和统计参数没有变化。

冻结 Workflow，保存 ID、SHA-256、Preview Evidence。

## Stage 2 — Establish a bounded real-data environment

本次要真实使用 DataLake，但必须保护已有用户数据。

优先复用 `market_research/tests/live_e2e_acceptance.py` 已验证的隔离方式，建立可在本次冷缓存与热缓存验收期间持续使用的独立 Generation 3 Calendar / Index Daily 存储。

必须实际验证 Research 内部创建的 Dataset Services 都指向预期存储，包括 Index 对 Calendar 的隐式依赖。

不要以两段非空的 resource_budget / data_isolation 字符串代替技术检查。

执行前建立并报告：

- Provider 最大调用次数和实际强制计数方式。
- Tushare rate limit。
- 最大运行时间及中断后的不确定状态处理。
- 数据库与 Workbench Evidence 的存储预算。
- 实际 SQLite 连接路径隔离检查。
- 默认缓存执行前后的不变性检查。

优先使用现有 DataLake / Provider 机制及已有受控 E2E Harness。

如果仅缺少一层很窄的验收工具，可以在本 Goal 内新增 Task-local opt-in 验收脚本，但不得改变 DataLake 的业务语义或新增通用执行框架。

若有限预算、隔离或授权不能得到确认，必须停止真实执行并报告 BLOCKED。

## Stage 3 — Cold Cache Real Execution

在新的隔离缓存上执行第一次真实研究。

执行前使用 Public Dataset API 记录初始 Calendar / Index 缓存 Coverage。

取得用户针对本次 Frozen Workflow ID、SHA-256 和数据获取副作用的明确授权之后，才允许启动 G5。

不得由 Agent 伪造批准。

通过正式 Workbench G5 执行完整 ResearchPlan，实际 Research 仍然通过公开 DataLake Service 消费缓存。

保留：

- G5 Run / Workflow / authorization / execution intent。
- 真实 Research BatchResult。
- 所有 16 个 Job 的原始结果。
- Calendar / Index 的 Export 和 Ensure 证据。
- 每个 Dataset 的 requested / already_successful / attempted / succeeded / failed units。
- Records written 和最终 Coverage。
- 实际 Provider 调用次数、endpoint 分类与资源使用量。
- Input fingerprints / provenance。
- 数据库实际写入及隔离检查结果。

必须证明首次真实执行能够将缺失数据补齐到隔离 DataLake Cache，并正确用于 Research。

不能以一次成功的 Python 调用取代 Cache Evidence。

对于未获取到的数据，保留其真实失败或缺失状态，不允许生成假数据。

## Stage 4 — Warm Cache Reuse Verification

这是本 Goal 的独立核心验收。

在 Cold Run 完成后，保留同一份隔离 DataLake 缓存，不要重新建立空数据库。

首先使用 Public Dataset coverage / export 做只读复查，验证已成功缓存的 Calendar 和 Index Units 可以重新取得，且与首次执行结果一致。

然后验证已成功缓存的 Units 不会因相同请求再次触发 Provider 获取或重复写入。

重点检查：

- Cache already_successful_units。
- New attempted_units。
- New records_written。
- Provider invocation count。
- Export payload and coverage。
- Index metadata reuse。
- Research Input fingerprints。

当完整研究所需数据均已成功缓存且资源与授权条件满足时，创建**新的 Workbench Run**，使用相同研究计划执行一次 Warm Cache Research。

第二个 G5 Run 需要独立的 Frozen Workflow 和真实用户授权。

不能重复使用 Cold Run 的执行 Intent，也不能以旧授权自动执行第二次。

对于完全缓存的相同请求，预期：

- 新 Provider calls = 0。
- 新 Index / Calendar records_written = 0。
- Research 16 Jobs 正常完成。
- 与 Cold Run 相同的合法输入产生相同观察值、统计结果和 Input fingerprints。

如果 Cold Run 存在 missing / failed / pending Units，DataLake 可以依照现有契约再次选择这些非成功 Units；不得把这种合法重试误判为成功缓存被重新获取。

此时应分开报告：

1. 已成功 Units 是否正确复用。
2. 非成功 Units 是否仍然缺失。
3. 整体 Warm Cache 是否具备零 Provider 调用条件。

不要为了制造零调用结果而修改 Source 或填补行情。

如果完整 Warm Research 无法安全执行，可先完成 Public Service 级缓存复用举证，明确标记 Research-level Warm Run 未通过或未执行。

## Stage 5 — Independent Research Verification

对 16 个 Job 分别验证：

- 真实指数 Metadata 和代码。
- SSE Calendar 与样本日期。
- H 个交易时段前的正确 Lookback。
- close(T) / close(T-H) - 1。
- Eligible / Unavailable / Excluded 数量。
- Market Fact Coverage 和 Observation Coverage。
- Quantile 的 Type 7 计算。
- Interval Count 各区间和溢出区间。
- Frequency 分母、数量守恒。
- Input fingerprints 与结果关联。

尽可能基于保存的 Public Export 数据独立重算，而不是直接相信 Research 或 Statistics 返回的数字。

不允许使用私有 Provider API、直接读取 SQLite 行情或第二套隐藏数据源作为研究事实。

必须区分：

- 研究计算成功。
- 缓存复用成功。
- 市场数据完整。
- 整体 E2E 验收完成。

## Stage 6 — Research Matrix Report

最终生成一张 4 × 4 的实际研究结果矩阵。

每行至少包含：

Index、Horizon、Sample Count、Eligible、Unavailable、Excluded、Coverage、P5、P10、P25、Median、P75、P90、P95、Job Status。

另外输出每组 Interval Count 的完整分布及频率。

报告需要对四个指数和四个 Horizon 做简短的描述性对比，但不要推断可交易性、预测力或策略收益。

所有数值必须来自真实保存的 Research Results。

输出可追溯的 Run ID、Artifact ID、SHA-256 和本地结果路径。

## Stage 7 — Problem Reporting (Mandatory)

除了机器 Evidence，必须编写一份独立问题报告。

对执行过程中每个实际遇到的问题，记录：

- Problem ID / Stage。
- Expected vs Actual。
- Severity。
- Root cause（不确定时明确 Unknown）。
- Evidence Reference。
- Actions Taken。
- Status：RESOLVED / WORKAROUND / OPEN / BLOCKED。
- Impact on the research and cache acceptance。
- Recommended next action。

包括最终被修复的问题、Provider 权限问题、数据缺失、缓存不兼容、性能或资源问题、Agent 自身测试脚本错误，以及非致命警告。

预期的测试注入失败必须与生产缺陷区分。

发生执行中断、报错或报告阶段异常时，首先读取已有 Run Intent 和结果，禁止自动重试或删除历史证据。

## Acceptance Gates

本次 Goal 在 Workbench 原有 Gate 之外使用验收报告中的检查项目，不新增通用 Workbench Gate。

A. Full Matrix：16 Jobs、32 Analysis Outcomes，且结果身份与输入吻合。

B. Real Data：所有统计数据来自实际 DataLake Public Export，Provider Metadata 已验证。

C. Research Correctness：独立数值核验通过。

D. Cache Population：真实缺失数据能够按授权通过 Ensure 进入隔离缓存。

E. Cache Reuse：成功 Units 能被复用，不重复获取或重写；完整 Warm Cache 时零 Provider 调用。

F. Isolation：既有默认缓存未被修改，所有预期操作只在隔离存储发生。

G. Evidence：所有实际 Batch、Coverage、统计结果、授权与执行关联可重新读取。

H. Problem Reporting：已解决与未解决的问题均完整记录。

只有实际通过的项目才能标记 PASS。任何尚未执行或被环境阻断的项目必须独立标记 NOT RUN / BLOCKED。

## Delivery

遵循：

Authority Review → G1/G3/G4 → Live Readiness → Authorized Cold Run → Cache Verification → Authorized Warm Run → Independent Verification → Reconciliation。

提交：

1. 真实研究的 16 行结果矩阵。
2. 各指数各 Horizon 的分布统计。
3. Cold / Warm Cache 对比与 Provider Call Audit。
4. E2E Acceptance Report。
5. Problem Report。
6. 原始 Workbench Evidence 的完整引用。
7. Authority / Implementation Reconciliation。
8. 实际运行命令、测试结果与最终 Commit SHA。

研究结果和大体积 Run Evidence 依照既有 Workbench Storage Contract 保留，不要将凭据、私有路径或大量原始市场数据直接提交 Git。

尽量复用现有 API 和契约。只有发现真实阻断时才进行最小修复，不得临时发明新的 Research 或 DataLake 业务语义。

## Success Criterion

Codex 使用 Workbench 正式完成 2026 年四个主要指数、四种交易日 Horizon 的真实涨跌幅分布研究，并以原始市场数据、独立统计校验以及 DataLake Cold/Warm Cache Evidence 证明系统能力。

若无法完成真实授权或安全数据获取，交付所有已完成的验证和具体 Blocker，不得以合成数据结果替代本次真实市场验收。
