# Research UI authority

本文档定义 retained Study 的 human-facing execution convention 与窄义共享 Research UI 支撑。模块 identity、Research result 与 Snapshot 消费原则见 [market_research architecture](../ARCHITECTURE.md)；配置 schema 与 resolution 见 [configuration authority](CONFIGURATION.md)；具体命令与参数由对应的 canonical Study authority 拥有，从 `../studies/<study_package>/ARCHITECTURE.md` 进入。新建 Study 的详细输入与 CLI 映射位于该 entry 链接的 `INPUTS.md`，见 [Study authoring topology](../studies/AUTHORING.md#mandatory-top-level-topology)。

本 UI owner 的 authority、configuration contract 与 Python support colocate 于 `market_research/ui/`，module-root `research.toml` placement 不变。

当前已定义的 human-facing runnable surface 仍以 Study CLI 为主，不是 Research 永久唯一执行模型。[Observation authority](../observations/ARCHITECTURE.md) 已定义 public invocation semantics，但 Observation CLI delivery 尚未决定；本 UI contract 不创建该 delivery。

## 1. Interaction boundary

Canonical human namespace 是 repository CLI：

```text
lab research list
lab research run <study-id> [study-specific args...]
```

Repository CLI 只拥有 runnable Study discovery、layout 校验、进程执行、参数透明转发、operational error 与 exit-code propagation。它不 import `market_research`，不解析 study-specific arguments，不组合 Snapshot dependency，不拥有 Study method、artifact 或 result semantics。

每个 runnable Study 拥有自己的 CLI module，负责 parsing、input validation、runtime collaborator composition、Study invocation 与 success / failure presentation。Study orchestration 调用声明的 Component / Observation public boundary 准备 complete inputs，CLI 不代替 workflow 驱动 empirical invocations 或实现 Observation；Analysis 只计算已准备 inputs。Legacy Snapshot composition 的范围唯一见 [Compatibility](../studies/COMPATIBILITY.md#legacy-retained-structure)。`research run <study-id> --help` 由 study-local parser 生成，不由 root CLI 复制参数。

## 2. Runnable Study convention

Runnable Study 是 `studies/` 下的直接 owner，其 Python package 位于 owner-local source root：

```text
market_research/studies/
    <study_package>/src/market_research/studies/<study_package>/
        __init__.py
        cli.py
        ... Study implementation
```

`study_package` 必须是小写 snake_case Python identifier。Stable public Study ID 只允许小写 ASCII 字母、数字与单个连字符分隔的 segment，并通过 `_` 到 `-` 的一对一映射从 package 名确定性得到。例如：

```text
example_study
    ↔ example-study
```

`research list` 只发现具有 owner-local source root、普通非 symlink `__init__.py` 和 `cli.py` 的直接 Study owner，按 public Study ID 排序输出。它不 import package、不读取 Source、不执行 Study，也不从中央文件读取 catalog。非法命名、symlink、非普通文件或无法安全映射的 runner layout 必须以人类可读的 malformed-study 错误失败，不得静默加载。

`research run` 只允许上述 public ID format，确定性映射回直接 package，并使用当前 Python interpreter 执行：

```text
python -m market_research.studies.<study_package>.cli [study-specific args...]
```

请求的 package 不存在是 unknown Study；package 存在但没有有效 `cli.py` 是 non-executable Study；路径逃逸、symlink 或非法命名是 malformed Study。Root CLI 不拥有 short description、argument schema 或 execution adapter。

新增 runnable retained Study 需在根 pyproject 注册 owner-local source root，并增加符合本 convention 的 study package/CLI、同一 `market_research/studies/<study_package>/` owner 内的 canonical Study authority 和对应 tests；不修改 root CLI。该 convention 不是 Study Registry、Experiment Engine、plugin system、Research Repository 或通用 lifecycle framework。

## 3. Shared configuration and output placement

Runnable Study 的 execution shape 由 specific Study authority 决定，不增加 generic mode flag / registry：

| Shape | CLI / output contract |
| --- | --- |
| Orchestration-only Study | Parse request → invoke Study orchestration → present human / runtime success or failure；无需 retained Study directory，不加载 output config、不要求 filesystem run key / collision / overwrite / staging。 |
| Retained-output Study | 仅 specific Study 明确声明 retained outputs 时使用下列 configuration / placement / publication rules；保持已有 retention contract。 |

Retained Study authority 的保留不意味着每次 execution 必须保留 output。首个 [cffex_option_expiry_dte_collection](../studies/cffex_option_expiry_dte_collection/ARCHITECTURE.md) 属于 orchestration-only shape，retained empirical Artifacts 由 Observations 持久化。

Research UI configuration 只提供 `output.root`，仅 retained-output runner 需要加载。以下本节 run-key / directory / collision / overwrite / staging 规则只适用于已声明 retained outputs 的 Study：从完整 semantic request 确定 deterministic run key，相同请求得到相同 key，改变 retained workflow results / evidence 含义的参数变化必须区分。当前时间、随机 UUID、进程身份、临时路径或运行顺序不成为 semantic identity。Key 表示形式留给 Study design，共享 UI 不定义统一 request schema、参数列表或算法。

该 run key 标识整次 Study 请求，用于 retained Study run output / workspace placement。Run workspace 可以包含 Study-local Workflow Artifacts、实际 Analysis outputs 与 Evidence。Observation identity / internal SQLite 由 [Observation authority](../observations/ARCHITECTURE.md) 拥有，不由 run key、output.root 或 UI 管理。[Schema](../studies/SCHEMA.md) / [Workflow](../studies/WORKFLOW.md) 拥有 bindings、materialized artifacts 与 complete consumption；共享 UI 不解释 Artifact identity，不提供分段执行或 Observation publication。Legacy component identity 按 Compatibility 保留。

Study-local CLI 将 Study-owned run key 交给共享 Research UI，canonical placement 为：

```text
<output-root>/
└── <study-id>/
    └── <study-owned-run-key>/
```

共享 Research UI 只将 key 作为不透明的单个目录名使用，并负责校验其 filesystem safety，防止绝对路径、路径逃逸或其他不安全的目录映射；它不解释 key 的 Study 语义。同一 `study-id + study-owned-run-key` 始终映射到同一 canonical run directory。共享 UI support 可以提供 configuration loading、canonical placement、collision detection 与事务性的整目录 staging/replacement，但不得定义 Study arguments、Snapshot request、artifact filenames/contents、statistics 或 result semantics。

若 canonical run directory 已存在，默认在调用 Study workflow / Observation 前失败，legacy 则在 Snapshot / Study 前失败，保留原 run output。只有 Study 显式提供并接收 `--overwrite` 才允许替换；以整个 run directory 为单位，先在同级 staging directory 完成，发布失败恢复原 output。

同次 retained-output invocation 内，已声明 workflow Artifacts 可在所属 staging workspace 先物化并以 complete state 供下游步骤消费；成功后随整目录发布，失败不发布 complete final run output。保留 Workflow Artifacts 的 Study 与 Evidence-producing Study 使用同一 collision / replacement invariant；不因多个 named artifacts 引入独立目录发布或 segmented UI。Orchestration-only runtime plan / references / counts 不需要 materialization 或 publication。

`--overwrite` 仅授权 Study run directory replacement，不授权 Observation refresh / overwrite / invalidation，也不管理 Observation-owned database。跨独立 invocation 的 workflow resume / reuse、generic partial-output publication 与 failure-output protocol 继续 deferred，不从确定性 run key 或 staging 推导 cache / resume engine。

Configuration 是 runner 内部支撑，repository CLI 不公开 `research config` command。

## 4. Snapshot boundary and failure presentation

新 Study-local CLI 只组合声明的 Component / Observation public collaborators，由 Study orchestration 准备 complete inputs；其 DataLake / Snapshot upstream permissions 见 [UPSTREAM](../UPSTREAM.md)。Legacy Snapshot CLI composition 仅适用 [Compatibility](../studies/COMPATIBILITY.md#legacy-retained-structure) 已保留的范围。所有 Study CLI 均不得导入 Source/Capture internals、构造 Source client、读取 credential 或依赖 upstream / Observation persistence layout。

正常用户错误必须由 study-local CLI 转换为简洁消息与 non-zero exit code，且不得要求用户阅读 Python traceback 才能识别 command/input、configuration、Snapshot/data、Study/sample 或 output filesystem failure。V1 不锁定跨 Study 的具体 exit-code number。

## 5. Strict non-goals

```text
central Study catalog / registry / dispatch table
entry-point plugin or dynamic registration
generic Study argument or data interface
Web Research Viewer / TUI / interactive wizard
HTTP Research API or generic UI framework
database / queue / background execution / scheduler
run registry / artifact registry / result browser
```
