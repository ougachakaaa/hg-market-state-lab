# Repository Development

本文档只描述当前本地开发环境与操作方式，不是架构、CLI、产品或 HTTP 语义 authority。Repository-level Python runtime invariant 与仓库级路由见 [ARCHITECTURE.md](ARCHITECTURE.md)，canonical CLI interface 与 delegation 见 [lab authority](ui_cli/ARCHITECTURE.md)，产品语义从 [data_snapshot/CAPABILITIES.md](data_snapshot/CAPABILITIES.md) 进入，HTTP transport contract 从 [ui_http HTTP catalog](ui_http/HTTP_PRODUCTS.md) 进入。

正式 console command 是 `lab`，由根 canonical Python project 安装。以下命令在 repository root 的 Poetry environment 中运行；help discovery 与完整 workflow 见 [lab usage guide](ui_cli/README.md)（usage-only，不是 authority）。

## Canonical runtime paths

Canonical paths and disposable runtime state follow [repository authority](ARCHITECTURE.md#naming-and-transition-authority). Start directly with the new paths; historical local directories can remain and do not affect execution. Configure credentials through the current environment or `data_snapshot/.env` (bootstrap can create an empty template); no historical token is copied. The executable remains `lab`.

## Codex managed worktree 环境

Codex 使用仓库内的 Local Environment 创建 managed worktree 时，会自动运行：

```bash
bash .codex/scripts/setup.sh
```

运行该脚本的 Bash 环境必须已经提供 `python3.13`、`poetry`、`node` 和 `npm`；脚本不安装或升级这些 machine-level tools。初始化流程必须从仓库根目录使用唯一的 `pyproject.toml` 与 `poetry.lock` 执行 `poetry install`，安装 frontend 依赖，然后运行 `poetry run lab doctor` 检查 readiness；不会启动服务、运行完整测试或调用 Tushare。

Windows native 手工初始化从仓库根目录运行：

```powershell
.\.codex\scripts\setup.ps1
```

PowerShell 脚本使用 Python 3.13、Poetry、Node 与 npm 达到相同终态。Codex Local Environment 仍调用上面的 Bash 脚本；WSL 使用 Bash 入口。两个脚本只负责 bootstrap，正式操作均使用 `lab`。

每个 worktree 分别使用自己的根 `.venv` 与 `ui_web/node_modules`，不与其他 worktree 共享依赖目录。所有 repository Python packages 与 Python tools 共用该根 `.venv`；module directory 不拥有独立 Poetry environment。Codex managed worktree 会按根目录 `.worktreeinclude` 复制 source checkout 中已忽略的 `data_snapshot/.env`；如果 source checkout 没有该文件，setup 从 `.env.example` 复制一份空模板，不会生成或猜测 secret。

手工执行 `git worktree add` 不会触发 Codex Local Environment，可以在新 worktree 根目录运行对应平台的 bootstrap 命令。

## 当前可运行命令

```bash
poetry run lab doctor
poetry run lab serve backend
poetry run lab serve frontend
poetry run lab datalake list
poetry run lab research list
poetry run lab research run <study-id> --help
```

安装环境已激活时可直接使用 `lab`；`poetry run lab` 会从根环境调用相同的 console script。

## 当前命令与状态

`doctor` 检查仓库结构、backend launcher、当前 Python 3.13 runtime 是否位于根 `.venv`，以及 Node 和 npm。它报告默认本地地址 `127.0.0.1:8011` 的 backend 状态：未监听为 `stopped`，监听且 `/openapi.json` 有效为 `running / healthy`，否则为 `port occupied / unhealthy`。服务未启动是正常状态。若 `ui_web/package.json` 不存在，frontend 报告 `not initialized`；存在后检查默认 `127.0.0.1:5173` 是否监听，不要求专用 health endpoint。

`doctor` 在必要的仓库结构、backend launcher、Poetry 或 Python 3.13 条件不满足时非零退出；frontend 已初始化但 Node/npm 不可用时也非零退出。frontend 尚未初始化和服务停止本身不使 `doctor` 失败。检查只读，不创建虚拟环境、不安装依赖，也不调用 Tushare 或运行 pytest、Ruff、mypy。

`lab serve backend` 从 repository root 使用当前 Python interpreter 前台执行 `ui_http/scripts/api.py`。`lab serve frontend` 在 `ui_web/` 前台执行系统解析到的 npm `run dev`；首次启动前需在 `ui_web/` 自行执行 `npm install`。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。

`lab research list` 列出可运行的 retained Study；`lab research run <study-id> --help` 转发到对应 Study 的帮助。Study ID、runner layout 与转发规则见 [Research UI authority](market_research/ui/ARCHITECTURE.md)，具体参数见对应 retained Study authority。

`ui_web/` 是独立 npm project，使用 Vite + React + TypeScript。Node.js 需满足当前 Vite 要求（20.19+ 或 22.12+）。`npm run dev` 在 `http://127.0.0.1:5173/` 提供可选择日期的 MO Option Chain 页面，与 `doctor` 的本地诊断地址一致；`npm run build` 执行 TypeScript 检查及 production build，`npm run lint` 运行 Oxlint，`npm run test` 运行前端测试。Vite dev proxy 将 frontend origin 的 `/mo-option-chain` 原路径和 query 转发到 `http://127.0.0.1:8011`，不需要 backend CORS policy。默认 provider 已接入真实读取链路；具体响应取决于目标日期与 Source 数据。

`lab doctor` 的 frontend 诊断地址与 Vite 显式绑定的 `127.0.0.1:5173` 一致。CLI ownership 以 [lab authority](ui_cli/ARCHITECTURE.md) 为准。

`lab datalake` 支持 list、coverage、ensure 与 export；参数与退出码见 lab authority。coverage / export 不访问 Source、不创建缓存；ensure 在确实需要 fetch 时解析 TUSHARE_TOKEN（环境变量优先，data_snapshot/.env fallback）。四个 Dataset 的默认 owned cache 分别位于 `data_lake/datasets/<dataset-id>/data/<dataset-id>.sqlite3`，service 内部解析路径。Canonical storage 与 rebuild-only cache compatibility 见 [DataLake persistence authority](data_lake/PERSISTENCE.md)；当前 runtime 仅接受 compatible generation 3，不兼容 cache 以 OperationError 明确提示 owning Dataset 需要 rebuild；不自动升级或重建。export 用必填 --output 交付 UTF-8 JSON，coverage 不完整也可导出当前成功 facts。

## DataLake V1 运行与恢复

操作示例沿用 [lab usage guide](ui_cli/README.md)。Tushare 限流只在单一 Python process / credential 内共享，不能协调其他 processes、worktrees 或机器；按账号权限配置 `TUSHARE_CALLS_PER_MINUTE`。Provider 不自动 retry；可恢复失败或中断后由 operator 再次执行相同 ensure，已提交 success 跳过，non-success 重新尝试。缺 credential、权限或网络时先解决运行条件，不通过换源或修改成功缓存规避失败。限制与错误分类以 [Provider authority](data_lake/providers/tushare/ARCHITECTURE.md) 为准。

遇到 incompatible generation 或损坏缓存时先停止使用该 Dataset 的 writers，保留原文件供诊断；coverage/export 不负责修复。确需 rebuild 时，由 operator 显式将该 Dataset 的完整 `data/` 目录移至仓库外的备份位置，再使用原 semantic request 执行 ensure，由 service 重新创建 owned cache。不要复制旧 SQLite 内容进入新库，不自动迁移、删除原缓存或重建 sibling Dataset。Calendar 与三个行情库分别拥有生命周期；重建 Calendar 后须先恢复所需日期范围，才能为行情 operations 提供完整 prerequisite。具体 compatibility / integrity 规则见 [PERSISTENCE.md](data_lake/PERSISTENCE.md)。

日常 ensure 不刷新已有 success，不保证 provider-current freshness；无需通过重建缓存例行更新历史事实。运行验收使用系统临时存储并重定向内部 Composition 路径，不把 token 或 storage path 加入 public request，不对默认用户缓存做试验。V1 验收范围与已知限制见 [Release Acceptance](data_lake/RELEASE_ACCEPTANCE.md)（非 Authority）。
