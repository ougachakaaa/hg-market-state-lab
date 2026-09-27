# lab repository CLI authority

本文档定义 `hg-market-state-lab` 的 canonical repository-level CLI。仓库身份、唯一 Python runtime 与模块边界见 [repository architecture](../ARCHITECTURE.md)；当前可运行命令及环境准备见 [DEVELOPMENT.md](../DEVELOPMENT.md)。本文件描述目标 interface；console-script wiring 与 `dev.py` 迁移尚待 implementation reconciliation。

## Identity 与 ownership

`hg-market-state-lab` 是 repository / system identity；`lab` 是安装于 repository canonical Python project 的正式 console command，面向 human、operator 与 developer。`lab` 是 repository-level operator/orchestration interface，不是业务模块。

`lab` 只拥有 command parsing、hierarchical help、repository path/runtime resolution、local prerequisite/readiness checks、process invocation 与 foreground lifecycle、command forwarding、exit-code propagation、人类可读的 operational errors，以及明确需要的 repository-level discovery。它不拥有 Snapshot、Research method/dataset/result、Modeling、HTTP product 或 frontend 语义；共享根 `.venv` 与可 import 的下层 package 不授予跨模块 semantic access。

原则：`lab` orchestrates；owning modules define semantics and execute domain behavior。`lab` 不重新实现或复制下层业务逻辑。

## V1 command hierarchy

```text
lab
├── doctor
├── serve
│   ├── backend
│   └── frontend
└── research
    ├── list
    └── run <study-id> [study-specific args...]
```

顶层 namespace 按现有 repository-level capability 分组。`lab serve backend` 与 `lab serve frontend` 取代旧的平铺 `backend`、`frontend` 目标命令。只有出现真实的 repository-level orchestration requirement 时才扩展 hierarchy；V1 不预定义其他 command group。

## Delegation 与 failure boundary

- `lab doctor` 只读检查本地仓库结构、根 Python runtime、启动前提与服务 readiness，报告人类可读状态；必要前提缺失时非零退出。它不安装依赖、不修复环境，也不运行下层业务行为。
- `lab serve backend` 从 repository root 前台调用 `backend-api` 拥有的 launcher；`lab serve frontend` 在 `web-ui/` 前台调用其开发脚本。两者继承标准输入输出，传递子进程退出码，并保持正常的前台中断生命周期。Backend 的 HTTP composition/runtime 由 [backend-api authority](../backend-api/ARCHITECTURE.md) 拥有；Frontend 的 runtime/configuration 由 [web-ui authority](../web-ui/ARCHITECTURE.md) 拥有。
- `lab research list` 只按 [Research UI authority](../market-research/ui/ARCHITECTURE.md) 定义的 runnable Study convention 发现并列出 Study；不 import Research implementation、不维护中央 Study catalog、不执行 Study 或读取 Source。`lab research run <study-id>` 校验 ID 与 runner layout，再从 repository root 前台调用对应 study-local CLI，原样转发 Study ID 之后的参数，继承标准输入输出并传递子进程退出码。`--help` 及所有 study-specific arguments 由该 runner 解析。具体 Study 的 request、Snapshot public-boundary composition、method、dataset、artifact、result 与 failure presentation 仍由对应 retained Study authority 拥有。
- 缺少本地前提或遇到不可运行的 Study 时，`lab` 在调用子进程前给出人类可读的 operational error 并非零退出；下层进程启动后的 domain failure 由 owning module 呈现，`lab` 只传播其退出状态。

V1 不提供组合启动、后台进程管理、依赖安装、测试运行、部署、plugin、registry 或 workflow engine。
