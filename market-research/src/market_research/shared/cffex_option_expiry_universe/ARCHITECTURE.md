# cffex_option_expiry_universe Shared Research Component authority

本文件是 reusable expiry / universe resolver 的 canonical entry，拥有 identity、purpose、分类、职责与导航。继承 [Shared Research Component authority](../ARCHITECTURE.md) 与 [Research boundaries](../../../../ARCHITECTURE.md)。具体 inputs、observed-window derivation、public dependency、complete result / failure 与 acceptance 唯一归 [CONTRACT.md](CONTRACT.md)。

## Identity、purpose 与定位

Canonical component identity 为 `cffex_option_expiry_universe`。给定 CFFEX 股指期权产品和 inclusive expiry window，resolve 完整 historical daily facts 中实际出现且 expiry 落在该窗口的 distinct dates，供研究选择输入、展开计划或构造 Observation。

它是跨研究可复用的小领域 resolver，复用理由是同一 observed-window expiry selection 可为不同研究目标准备 expiry inputs，不依赖 target DTE、Study question、Analysis 或 conclusion。当前 [DTE collection Study](../../studies/cffex_option_expiry_dte_collection/ARCHITECTURE.md) 是明确 consumer；无需预建额外 Study 或框架证明复用。

Universe selection 是 reusable mechanism，不是需要独立持久化和解释的最小 empirical research artifact。日期列表值得作为研究输入使用，不因此获得 Observation 身份；原有 ensure、Artifact 类型、SQLite 与 business key 不构成该身份的语义理由。**Reuse does not imply Observation**。

## Ownership 与边界

本 component 拥有 observed-window extraction / resolver I/O，不拥有 market-data facts、官方上市计划、窗口外历史 catalog、DTE / chain construction、Study window choice / plan / orchestration、Analysis、Evidence 或统计解释。DataLake 继续拥有 facts、completeness、public export 与 persistent cache。

Result 只在调用后作为 complete component result 消费；无 Observation identity、retained artifact identity、幂等业务键、research cache、SQLite、complete-hit lookup、atomic research publication 或跨 invocation durable reuse。可以使用 DataLake 已有 ensure / export，不把 Dataset cache 变成 component cache。

Study orchestration 或 Observation 可以调用本 resolver；Analysis 不自行调用它获取 facts，只消费已准备的 result。Chain Observation 直接接受一个 expiry，不依赖 Universe，不被强制先做 discovery。

## Reconciliation 与导航

本 entry 与 CONTRACT 取代基线 `observations/cffex_option_expiry_universe/` 三份 authority 的当前语义；旧 Observation / Artifact / implementation handoff 已撤销，不作为第二 canonical owner。该分类已落实为 shared resolver Python boundary；本轮不迁移、读取或删除旧 Universe Research SQLite。

Canonical runtime 为 `market_research.shared.cffex_option_expiry_universe`；旧 Observation public package / lifecycle 已撤销，Study 使用 resolver。当前验证与历史证据的适用限制见 [implementation reconciliation](../../../../IMPLEMENTATION_RECONCILIATION.md#shared-component-runtime-reconciliation)。这里只拥有 component semantics；Python mapping 见 [IMPLEMENTATION.md](IMPLEMENTATION.md)。
