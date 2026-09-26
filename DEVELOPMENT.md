# Repository Development CLI

本文档只描述本地开发编排与操作方式，不是架构、产品或 HTTP 语义 authority。Repository-level Python runtime invariant 与仓库级路由见 [ARCHITECTURE.md](ARCHITECTURE.md)，产品语义从 [market-snapshot/CAPABILITIES.md](market-snapshot/CAPABILITIES.md) 进入，HTTP transport contract 从 [backend-api HTTP catalog](backend-api/HTTP_PRODUCTS.md) 进入。

仓库根目录的 `dev.py` 是统一的 repository-level human/developer CLI surface。它只负责 command parsing、分层 help、repository path resolution、developer orchestration、command forwarding、process execution、exit-code propagation 和人类可读的 operational error。它不是 Data Service、Research framework、部署工具或新的业务模块。

## Codex managed worktree 环境

Codex 使用仓库内的 Local Environment 创建 managed worktree 时，会自动运行：

```bash
bash .codex/scripts/setup.sh
```

运行该脚本的 Bash 环境必须已经提供 `python3.13`、`poetry`、`node` 和 `npm`；脚本不安装或升级这些 machine-level tools。初始化流程必须从仓库根目录使用唯一的 `pyproject.toml` 与 `poetry.lock` 执行 `poetry install`，安装 frontend 依赖，然后运行 `poetry run python dev.py doctor` 检查 readiness；不会启动服务、运行完整测试或调用 Tushare。

每个 worktree 分别使用自己的根 `.venv` 与 `web-ui/node_modules`，不与其他 worktree 共享依赖目录。所有 repository Python packages 与 Python tools 共用该根 `.venv`；module directory 不拥有独立 Poetry environment。Codex managed worktree 会按根目录 `.worktreeinclude` 复制 source checkout 中已忽略的 `market-snapshot/.env`；如果 source checkout 没有该文件，setup 从 `.env.example` 复制一份空模板，不会生成或猜测 secret。

手工执行 `git worktree add` 不会触发 Codex Local Environment，可以在新 worktree 根目录手工运行同一命令完成初始化。

```bash
poetry run python dev.py doctor
poetry run python dev.py backend
poetry run python dev.py frontend
poetry run python dev.py data csi1000-5d-analysis
poetry run python dev.py data csi1000-5d-analysis --date 2026-09-18
poetry run python dev.py research list
poetry run python dev.py research run <study-id> --help
```

## 命令与状态

`doctor` 检查仓库结构、backend launcher、根 Poetry 虚拟环境中的 Python 3.13，以及 Node 和 npm。它报告默认本地地址 `127.0.0.1:8011` 的 backend 状态：未监听为 `stopped`，监听且 `/openapi.json` 有效为 `running / healthy`，否则为 `port occupied / unhealthy`。服务未启动是正常状态。若 `web-ui/package.json` 不存在，frontend 报告 `not initialized`；存在后检查默认 `127.0.0.1:5173` 是否监听，不要求专用 health endpoint。

`doctor` 在必要的仓库结构、backend launcher、Poetry 或 Python 3.13 条件不满足时非零退出；frontend 已初始化但 Node/npm 不可用时也非零退出。frontend 尚未初始化和服务停止本身不使 `doctor` 失败。检查只读，不创建虚拟环境、不安装依赖，也不调用 Tushare 或运行 pytest、Ruff、mypy。

`backend` 从 repository root 前台执行 `poetry run python backend-api/scripts/api.py`。`frontend` 在 `web-ui/` 前台执行 `npm run dev`；首次启动前需在 `web-ui/` 自行执行 `npm install`。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。

`data` 是 repository-level Data Service convenience command：

```text
poetry run python dev.py data <service_id> [--date YYYY-MM-DD]
```

`service_id` 必须显式提供，当前只接受 CLI-supported persisted-artifact Data Service `csi1000-5d-analysis`；`mo-option-chain` 的 canonical delivery surface 是 HTTP，不由此命令暴露。显式提供 `--date` 时，值原样作为 `target_trade_date` 转发。未提供时，使用 UTC+8 / `Asia/Shanghai` 的当天自然日，格式为 `YYYY-MM-DD`。

该默认值只属于 repository convenience CLI，并且 `today != latest trading day`：`dev.py` 不查询交易日历、不寻找最近交易日，也不在周末、节假日或数据未就绪时 fallback。上述情况保持底层 Data Service 的失败语义。

`data` 从 repository root 前台执行：

```text
poetry run python market-snapshot/scripts/dms.py get <service_id> --date <resolved-date>
```

它继承标准输入输出并传递子进程退出码。`dms get <service_id> --date YYYY-MM-DD` 仍是 canonical Data Service interface，其 `--date` 仍必须显式提供；`dev.py` 只在调用前解析 convenience default，不成为 Data Service semantic owner。

`research` 是 retained Study 的 repository-level discovery 与 forwarding command group：

```text
research
    ├── list
    └── run <study-id> [study-specific args...]
```

Runnable Study 是 `market-research/src/market_research/studies/` 下具有普通 `cli.py` 的直接 Python package。Package 名中的 `_` 确定性映射为 public Study ID 中的 `-`；例如 `im_basis_baseline` 对应 `im-basis-baseline`。`research list` 按 Study ID 排序输出可运行 Study，不读取 Source 或执行 Study。

`research run` 校验 Study identity 与 runner layout 后，使用当前 Python interpreter 从 repository root 前台执行 study-local module，原样转发 Study ID 之后的参数、继承标准输入输出并传递子进程退出码。因此 `research run <study-id> --help` 展示该 Study 自己的帮助；参数、输入选择、Method、dataset/statistical semantics、artifact 与 result semantics 均由对应 Study 拥有。

Root CLI 不 import Research implementation，不保持 Study catalog/registry，不解析 study-specific arguments。不存在、不可运行或 malformed 的 Study layout 在执行子进程前以明确错误失败。新增 runnable Study 只需遵循 study-local package/CLI convention 并在其自身 authority 记录用法，不修改 root CLI 的业务语义。

`web-ui/` 是独立 npm project，使用 Vite + React + TypeScript。Node.js 需满足当前 Vite 要求（20.19+ 或 22.12+）。`npm run dev` 在 `http://127.0.0.1:5173/` 提供可选择日期的 MO Option Chain 页面，与 `doctor` 的本地诊断地址一致；`npm run build` 执行 TypeScript 检查及 production build，`npm run lint` 运行 Oxlint，`npm run test` 运行前端测试。Vite dev proxy 将 frontend origin 的 `/mo-option-chain` 原路径和 query 转发到 `http://127.0.0.1:8011`，不需要 backend CORS policy。默认 provider 已接入真实读取链路；具体响应取决于目标日期与 Source 数据。

## Ownership

`dev.py` 只拥有 CLI parsing、命令分发、仓库路径解析、开发前提检查、Data Service `service_id` 转发、convenience default date resolution、Research runner discovery/forwarding、进程调用、exit-code propagation 和人类可读状态。HTTP bind/runtime composition 与 contract 的 owner 是 `backend-api`；Data Service CLI 仍由 `market-snapshot` 拥有。Retained Study 的请求、输入、方法、输出与结果语义仍由 `market-research` 中的具体 Study 拥有。Frontend 的 React/Vite 配置与开发脚本由 `web-ui` 拥有。`dev.py` 不导入模块内部代码，不拥有 Source Capture orchestration、Analysis Preparation、Data Service/Research business semantics、dataset schema 或 trading-calendar resolution；端口仅用于本地开发诊断，不构成业务契约。

V1 不提供组合启动、后台进程、PID、日志、停止或重启、端口分配、配置框架、环境变量管理、依赖安装、测试运行或部署功能。`dev.py` 的 frontend 诊断地址与 Vite 显式绑定的 `127.0.0.1:5173` 一致。
