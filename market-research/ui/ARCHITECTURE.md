# Research UI authority

本文档定义 retained Study 的 human-facing execution convention 与窄义共享 Research UI 支撑。模块 identity、Research result 与 Snapshot 消费原则见 [market-research architecture](../ARCHITECTURE.md)；配置 schema 与 resolution 见 [configuration authority](CONFIGURATION.md)；具体命令与参数由 `../studies/<study_package>/ARCHITECTURE.md` 中对应的 canonical Study authority 记录。

## 1. Interaction boundary

Canonical human namespace 是 repository CLI：

```text
lab research list
lab research run <study-id> [study-specific args...]
```

Repository CLI 只拥有 runnable Study discovery、layout 校验、进程执行、参数透明转发、operational error 与 exit-code propagation。它不 import `market_research`，不解析 study-specific arguments，不组合 Snapshot dependency，不拥有 Study method、artifact 或 result semantics。

每个 runnable Study 拥有自己的 CLI module。该 module 拥有其 command parsing、input validation、Snapshot public application composition、Study invocation、failure presentation 和 success presentation。`research run <study-id> --help` 必须由该 study-local parser 生成，不由 root CLI 复制参数说明。

## 2. Runnable Study convention

Runnable Study 是以下 source root 下的直接 Python package：

```text
market-research/src/market_research/studies/
    <study_package>/
        __init__.py
        cli.py
        ... Study implementation
```

`study_package` 必须是小写 snake_case Python identifier。Stable public Study ID 只允许小写 ASCII 字母、数字与单个连字符分隔的 segment，并通过 `_` 到 `-` 的一对一映射从 package 名确定性得到。例如：

```text
im_basis_baseline
    ↔ im-basis-baseline
```

`research list` 只发现具有普通、非 symlink `__init__.py` 和 `cli.py` 的直接 package，按 public Study ID 排序输出。它不 import package、不读取 Source、不执行 Study，也不从中央文件读取 catalog。非法命名、symlink、非普通文件或无法安全映射的 runner layout 必须以人类可读的 malformed-study 错误失败，不得静默加载。

`research run` 只允许上述 public ID format，确定性映射回直接 package，并使用当前 Python interpreter 执行：

```text
python -m market_research.studies.<study_package>.cli [study-specific args...]
```

请求的 package 不存在是 unknown Study；package 存在但没有有效 `cli.py` 是 non-executable Study；路径逃逸、symlink 或非法命名是 malformed Study。Root CLI 不拥有 short description、argument schema 或 execution adapter。

新增 runnable retained Study 只需增加符合本 convention 的 study package/CLI、`market-research/studies/<study_package>/` 下的 canonical Study authority 和对应 tests；不修改 root CLI。该 convention 不是 Study Registry、Experiment Engine、plugin system、Research Repository 或通用 lifecycle framework。

## 3. Shared configuration and output placement

Research UI configuration 只提供 `output.root`。每个 Study 从自身完整的 semantic request 确定 deterministic run key：语义相同的请求必须得到相同的 key，任何会改变 retained evidence 含义的 Study 参数变化都必须得到不同的 key。当前时间、随机 UUID、进程身份、临时路径或运行顺序不得成为 canonical semantic identity。key 的表示形式（包括是否使用 hash 或编码）由 Study 决定；共享 Research UI 不定义统一 request schema、参数列表或 key 算法。

Study-local CLI 将 Study-owned run key 交给共享 Research UI，canonical placement 为：

```text
<output-root>/
└── <study-id>/
    └── <study-owned-run-key>/
```

共享 Research UI 只将 key 作为不透明的单个目录名使用，并负责校验其 filesystem safety，防止绝对路径、路径逃逸或其他不安全的目录映射；它不解释 key 的 Study 语义。同一 `study-id + study-owned-run-key` 始终映射到同一 canonical run directory。共享 UI support 可以提供 configuration loading、canonical placement、collision detection 与事务性的整目录 staging/replacement，但不得定义 Study arguments、Snapshot request、artifact filenames/contents、statistics 或 result semantics。

现有 `im-basis-baseline` 与 `im-basis-forward-return-association` 的 run identity 由各自显式日期区间决定，可以继续使用 `<start_trade_date>__<end_trade_date>` 作为各自的 deterministic run key；该泛化不要求迁移既有 output directory 或改变这两个 Study 的语义。

若 canonical run directory 已存在，默认在调用 Snapshot 或 Study 前失败并保留原 evidence。只有 Study 显式提供并接收 `--overwrite` 时才允许替换；replacement 以整个 run directory 为单位，先在同级 staging directory 完成，发布失败恢复原 evidence。

Configuration 是 runner 内部支撑，repository CLI 不公开 `research config` command。

## 4. Snapshot boundary and failure presentation

Study-local CLI 只能调用对应 Snapshot product 拥有的 production-ready public application entry，不得导入 Source/Capture internals、构造 Source client、读取 credential 或依赖 persistence layout。

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
