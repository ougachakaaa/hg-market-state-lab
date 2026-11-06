# Repository Development

本文档只描述当前本地开发环境与操作方式，不是架构、CLI、产品或 HTTP 语义 authority。Repository-level Python runtime invariant 与仓库级路由见 [ARCHITECTURE.md](ARCHITECTURE.md)，canonical CLI interface 与 delegation 见 [lab authority](ui_cli/ARCHITECTURE.md)，产品语义从 [data_snapshot/CAPABILITIES.md](data_snapshot/CAPABILITIES.md) 进入，HTTP transport contract 从 [ui_http HTTP catalog](ui_http/HTTP_PRODUCTS.md) 进入。

正式 console command 是 `lab`，由根 canonical Python project 安装。以下命令在 repository root 的 Poetry environment 中运行；help discovery 与完整 workflow 见 [lab usage guide](ui_cli/README.md)（usage-only，不是 authority）。

## Canonical runtime paths

Canonical paths and disposable runtime state follow [repository authority](ARCHITECTURE.md#naming-and-transition-authority). Start directly with canonical paths; historical local directories can remain and do not affect execution. Configure credentials and runtime settings through the current environment or the repository-root `.env` (bootstrap can create an empty template from `.env.example`); no historical token is copied. The executable remains `lab`.

## Repository configuration

Repository 本地配置统一位于 **repository root `.env`**，tracked template 为根 `.env.example`；Python consumer 只通过 `config/src/lab_config` 读取。不要在 `data_snapshot/`、`ui_http/` 或其他 module 目录建立独立 `.env`。

来源优先级固定为：

```text
process environment > repository-root .env > built-in defaults
```

环境变量存在但为空白时不回退到 `.env`。`.env` 不进入 Git；production 应使用显式 server environment。当前支持的 key：

| Key | 语义 |
| --- | --- |
| `TUSHARE_TOKEN` | Tushare Source I/O 所需 credential；缺失/空白时 Source operation 失败 |
| `TUSHARE_CALLS_PER_MINUTE` | 可选，整数 1..500，默认 180；只在需要 Source I/O 时读取 |
| `LAB_AUTH_JWT_SECRET` | Auth serving 必填，base64url 编码的至少 32 random bytes |
| `LAB_AUTH_MODE` | `production`（默认）或 `loopback-http` |
| `LAB_AUTH_ORIGIN` | Auth serving 必填的 browser-facing origin |
| `LAB_AUTH_DB_PATH` | 可选，Auth SQLite 绝对路径；默认 `ui_http/data/auth.sqlite3` |
| `LAB_RESEARCH_PUBLICATION_ROOT` | 可选，Publication storage 绝对路径 |

首次准备：

```powershell
Copy-Item .env.example .env
# 编辑 .env，填入 TUSHARE_TOKEN 与需要的 Auth 配置
```

`data_snapshot/.env` 是退休位置，不再被读取；旧 worktree 可把 token 手工迁移到根 `.env`。

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

每个 worktree 分别使用自己的根 `.venv` 与 `ui_web/node_modules`，不与其他 worktree 共享依赖目录。所有 repository Python packages 与 Python tools 共用该根 `.venv`；module directory 不拥有独立 Poetry environment 或 `.venv`。Codex managed worktree 会按根目录 `.worktreeinclude` 复制 source checkout 中已忽略的根 `.env`；如果 source checkout 没有该文件，setup 从根 `.env.example` 复制一份空模板，不会生成或猜测 secret。若旧 worktree 只有 `data_snapshot/.env`，setup 只提示手工迁移到根 `.env`，不自动复制历史 token。

手工执行 `git worktree add` 不会触发 Codex Local Environment，可以在新 worktree 根目录运行对应平台的 bootstrap 命令。

## Windows One-Click Development Startup

在 Windows 上双击仓库根目录的 `market-lab.cmd`（无参数等价于 `start`）。需要预先安装 Python 3.13、Poetry、Node.js（20.19+ 或 22.12+）和 npm，并使其可从 PATH 使用；首次启动或依赖不完整时会运行现有 Windows bootstrap，安装需要网络连接。启动前会检查 backend import；启动成功后会自动打开 `http://127.0.0.1:5173/`。

根目录 `market-lab.cmd` 是统一入口，实际逻辑集中在 `scripts/market-lab.ps1`：

```powershell
.\market-lab.cmd start    # 启动（推荐写法；双击 .cmd 不带参数也等价）
.\market-lab.cmd status   # 查看 8011/5173 是否由本仓库服务占用
.\market-lab.cmd stop     # 停止本仓库的 backend/frontend
```

`start` 会保持前台运行并等待按键；`stop` 和 `status` 可在另一个终端执行。

原生 Windows 缺少 Publication V1 存储所需的 POSIX `dir_fd`、`O_DIRECTORY` 与 `O_NOFOLLOW` 能力。backend 与其他产品可正常启动，但 Publication 读操作及 `retain_source`/`publish` 返回 503 `unavailable`，Research Explorer 显示 Publication 存储不可用。完整 Publication 仍需 Linux 或满足相同文件系统能力的 WSL，并显式配置 `LAB_RESEARCH_PUBLICATION_ROOT`；详见 [Publication 平台限制](market_research/descriptive/ACCEPTANCE.md#native-windows-publication-limitation)。当前集成验证以 Linux 为准，WSL 仍需满足相同文件系统能力要求。

首次使用时在网页注册，然后在仓库根目录的另一个终端运行 `poetry run lab auth pending`，取得用户 ID 后运行 `poetry run lab auth approve <user-id>`，再返回网页登录。若在 process environment 或根 `.env` 设置了 `LAB_AUTH_DB_PATH`，审批终端也必须使用相同的值。

保持启动窗口打开，按任意键停止两个服务。若启动窗口已关闭而服务仍在运行，在另一个终端运行 `.\market-lab.cmd stop`；它按默认端口 8011/5173 查找本仓库的 backend/frontend 并停止，不会终止使用这些端口的其他程序。启动失败时查看窗口提示和 `ui_http/data/one-click/` 中的日志；检查工具是否在 PATH、依赖安装是否成功、默认端口 8011 和 5173 是否被占用，以及显式 Auth 配置是否与本地 loopback 模式匹配。可在仓库根运行 `poetry run lab doctor` 进一步诊断。启动器在该已忽略目录中保存本机 JWT 密钥以便重启复用，不会清空用户库或行情缓存；根 `.env` 已提供 `LAB_AUTH_MODE` / `LAB_AUTH_ORIGIN` / `LAB_AUTH_JWT_SECRET` 时，启动器不会覆盖，process environment 仍优先。

## 当前可运行命令

```bash
poetry run lab doctor
poetry run lab serve backend
poetry run lab serve frontend
poetry run lab datalake list
poetry run lab auth pending
```

安装环境已激活时可直接使用 `lab`；`poetry run lab` 会从根环境调用相同的 console script。

## 当前命令与状态

Auth 已提供持久化注册 Python service 与 `lab auth pending/approve/reject/disable`，使用方式见 [CLI usage guide](ui_cli/README.md#authentication注册申请与-operator-审批)。默认独立数据库为 `ui_http/data/auth.sqlite3`；`LAB_AUTH_DB_PATH` 只接受绝对路径，CLI 与 HTTP Auth 使用相同 composition，不依赖当前目录。整个 `ui_http/data/`（含 journal/WAL）已忽略。首次操作创建数据库；既有不兼容或损坏 schema 明确失败，不自动恢复。Auth CLI 不需要 JWT 配置；HTTP runtime 已强制认证，包括 docs/schema 与独立 product app。注册、登录、身份查询、退出见 [Auth HTTP contract](ui_http/AUTHENTICATION.md#4-http-contract-and-access-order)。Web 已提供登录/注册、启动 Cookie 身份检查、退出及 `/auth` Vite proxy。

`doctor` 检查仓库结构、backend launcher、当前 Python 3.13 runtime 是否位于根 `.venv`、根 `.env` 与 `TUSHARE_TOKEN` presence、是否存在 module-local `.venv`，以及 Node 和 npm。它报告默认本地地址 `127.0.0.1:8011` 的 backend 状态：未监听为 `stopped`，监听且 `/openapi.json` 返回预期认证 401 为 `running / authentication required`，旧版有效 schema 200 为 `running / healthy`，否则为 `port occupied / unhealthy`。服务未启动是正常状态。若 `ui_web/package.json` 不存在，frontend 报告 `not initialized`；存在后检查默认 `127.0.0.1:5173` 是否监听，不要求专用 health endpoint。

`doctor` 在必要的仓库结构、backend launcher、Poetry 或 Python 3.13 条件不满足时非零退出；frontend 已初始化但 Node/npm 不可用时也非零退出。frontend 尚未初始化和服务停止本身不使 `doctor` 失败。检查只读，不创建虚拟环境、不安装依赖，也不调用 Tushare 或运行 pytest、Ruff、mypy。

启动 backend 前必须配置 Auth；没有有效配置会拒绝启动。本机 HTTP 示例（仓库根目录）：

```dotenv
# .env（repository root）
LAB_AUTH_MODE=loopback-http
LAB_AUTH_ORIGIN=http://127.0.0.1:5173
LAB_AUTH_JWT_SECRET=<generated base64url secret>
```

生成 secret（把输出粘贴到 `.env`；不要把真实 secret 写入命令历史或 Git）：

```bash
poetry run python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

也可以继续使用 shell/process environment 变量；process environment 优先于根 `.env`。`poetry run lab serve backend` 从 `.env` 读取其余配置。

密钥从进程继承或从根 `.env` 读取，应通过安全配置保存以便重启复用；根 `.env` 已被 Git 忽略。重新生成会使旧 JWT 失效，不在仓库保存或打印真实密钥。Production（默认模式）要求 HTTPS browser origin，Cookie 固定 Secure；本机模式只接受 loopback listener/origin。Launcher 禁用隐式 proxy-header trust。无浏览器的 unsafe HTTP caller 同样须携带匹配 Origin；登录只通过 HttpOnly Cookie，没有 Bearer 入口。首次浏览器注册为 Pending，再用 `lab auth approve` 审批；具体步骤见下文。

`lab serve backend` 从 repository root 使用当前 Python interpreter 前台执行 `ui_http/scripts/api.py`。`lab serve frontend` 在 `ui_web/` 前台执行系统解析到的 npm `run dev`；首次启动前需在 `ui_web/` 自行执行 `npm install`。两个命令继承标准输入输出、传递子进程退出码，Ctrl+C 结束前台进程。缺少启动前提时明确报错，不自动修复环境。


`ui_web/` 是独立 npm project，使用 Vite + React + TypeScript。Node.js 需满足当前 Vite 要求（20.19+ 或 22.12+）。`npm run dev` 在 `http://127.0.0.1:5173/` 提供认证入口和三个业务 surface（MO Option Chain、MO Premium Plane、Research Explorer），与 `doctor` 的本地诊断地址一致；`npm run build` 执行 TypeScript 检查及 production build，`npm run lint` 运行 Oxlint，`npm run test` 运行前端测试。Vite dev proxy 将 frontend origin 的 `/research`、`/auth`、`/mo-option-chain`、`/mo-option-premium-plane` 原路径和 query 转发到 `http://127.0.0.1:8011`，不需要 backend CORS policy。默认 provider 已接入真实读取链路；具体响应取决于目标日期与 Source 数据。

### 浏览器注册、审批与登录

1. 在仓库根目录按上例配置 Auth 并启动 backend。可先在 process environment 或根 `.env` 设置 `LAB_AUTH_DB_PATH` 为隔离测试库的绝对路径；审批终端必须使用相同路径。测试数据库与正式用户数据库必须严格隔离；不要意外删除正式数据库，也不要把密钥、数据库或账号密码提交到 Git。
2. 另一个终端从仓库根执行 `poetry run lab serve frontend`，打开 `http://127.0.0.1:5173/`。始终使用 `127.0.0.1`，不与 `localhost` 混用。
3. 点击 Register，输入 username/password 并提交；202 只表示等待审批，不会登录。输入规则见 [Auth authority](ui_http/AUTHENTICATION.md#2-user-identity-and-persistence)。
4. Operator 从仓库根执行 `poetry run lab auth pending`，读取申请 ID，再执行 `poetry run lab auth approve <user-id>`。
5. 返回 Login，使用已审批账号登录。默认进入 MO Option Chain，可切换 MO Premium Plane 或 Research Explorer；MO 页面选择日期才发起行情请求。行情仍依赖其 Source 配置和数据可用性。
6. 刷新时由 `/auth/me` 检查 HttpOnly Cookie 恢复身份。Logout 期间卸载业务页面；成功返回登录，失败显示重试退出。登录过期的业务 401 同样返回登录。

所有浏览器请求走相对 URL 和 Vite 同源代理，不直接调用 `:8011`，无需 CORS 或本地认证绕过。

### Authentication 验证与部署准备

在 `ui_web/` 执行 `npm run contract:generate`、`npm run contract:check`、`npm run test`、`npm run build`、`npm run lint`；从仓库根执行 `poetry run pytest ui_http/tests ui_web/scripts/test_export_contracts.py`、`poetry run ruff check ui_http ui_web/scripts` 与 `poetry run mypy ui_http`。离线 contract export 不需要配置 Auth 或创建用户数据库。

真实浏览器 smoke（不是 Mock UI 测试）：在 `ui_web/` 执行 `npx playwright install chromium`，然后 `npm run test:auth-browser`。Linux 还需 Chromium 系统运行库；可用 `npx playwright install-deps chromium` 安装。已有兼容 Chromium 可通过 `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` 指定。端口 5173/8011 必须空闲；脚本拒绝连接已有开发服务。

脚本创建临时 Auth 库和随机密钥，通过真实 Chromium → Vite → FastAPI → SQLite 完成注册、CLI pending/approve、登录、两个 MO 结果、刷新与退出，结束后删除临时库并停止进程。Auth/Cookie/CLI 不作 Mock；只有行情 public provider 使用 `ui_http/tests` 的确定性 fixtures，不访问外部 Source 或默认市场缓存。`poetry run pytest ui_http/tests/test_auth_tls.py` 使用 OpenSSL 生成临时自签名证书，通过本机真实 TLS 检查 production Cookie；它不验证正式证书或部署。浏览器测试依赖只用于开发验证。

开放公网前必须完成 HTTPS、Nginx、可信代理链与入口限流配置并验证部署拓扑和 Research 路由暴露；这些属于 Deployment Gate。应用内限流仅在单进程内生效，重启清空，多个 worker 不共享，反向代理后的用户可能共享同一 IP bucket。无状态 JWT 的 logout 不撤销已复制的 token；禁用用户或轮换密钥可阻止其后续访问。正式 JWT secret 必须安全保存并在重启间保持稳定。

`lab doctor` 的 frontend 诊断地址与 Vite 显式绑定的 `127.0.0.1:5173` 一致。CLI ownership 以 [lab authority](ui_cli/ARCHITECTURE.md) 为准。

`lab datalake` 支持 list、coverage、ensure 与 export；参数与退出码见 lab authority。coverage / export 不访问 Source、不创建缓存；ensure 在确实需要 fetch 时解析 `TUSHARE_TOKEN`（process environment 优先，repository root `.env` fallback）。四个 Dataset 的默认 owned cache 分别位于 `data_lake/datasets/<dataset-id>/data/<dataset-id>.sqlite3`，service 内部解析路径。Canonical storage 与 rebuild-only cache compatibility 见 [DataLake persistence authority](data_lake/PERSISTENCE.md)；当前 runtime 仅接受 compatible generation 3，不兼容 cache 以 OperationError 明确提示 owning Dataset 需要 rebuild；不自动升级或重建。export 用必填 --output 交付 UTF-8 JSON，coverage 不完整也可导出当前成功 facts。

## DataLake V1 运行与恢复

操作示例沿用 [lab usage guide](ui_cli/README.md)。Tushare 限流只在单一 Python process / credential 内共享，不能协调其他 processes、worktrees 或机器；按账号权限在 process environment 或根 `.env` 配置 `TUSHARE_CALLS_PER_MINUTE`。Provider 不自动 retry；可恢复失败或中断后由 operator 再次执行相同 ensure，已提交 success 跳过，non-success 重新尝试。缺 credential、权限或网络时先解决运行条件，不通过换源或修改成功缓存规避失败。限制与错误分类以 [Provider authority](data_lake/providers/tushare/ARCHITECTURE.md) 为准。

遇到 incompatible generation 或损坏缓存时先停止使用该 Dataset 的 writers，保留原文件供诊断；coverage/export 不负责修复。确需 rebuild 时，由 operator 显式将该 Dataset 的完整 `data/` 目录移至仓库外的备份位置，再使用原 semantic request 执行 ensure，由 service 重新创建 owned cache。不要复制旧 SQLite 内容进入新库，不自动迁移、删除原缓存或重建 sibling Dataset。Calendar 与三个行情库分别拥有生命周期；重建 Calendar 后须先恢复所需日期范围，才能为行情 operations 提供完整 prerequisite。具体 compatibility / integrity 规则见 [PERSISTENCE.md](data_lake/PERSISTENCE.md)。

日常 ensure 不刷新已有 success，不保证 provider-current freshness；无需通过重建缓存例行更新历史事实。运行验收使用系统临时存储并重定向内部 Composition 路径，不把 token 或 storage path 加入 public request，不对默认用户缓存做试验。历史 V1 验收证据见 [Historical Acceptance](data_lake/RELEASE_ACCEPTANCE.md)（仅历史基线，非当前验收或操作指令）；当前验证按受影响模块的 Agent rules 执行。

Research publishes an independent [Python Observation API](market_research/README.md)
for index Trailing Return, a reusable scalar Sample Converter and independent Result
Association, Single Job and Batch execution, using this same root environment. Deterministic
public API acceptance runs with `poetry run python market_research/tests/job_execution_example.py`
and `poetry run python market_research/tests/batch_execution_example.py`.
There is no Research execution CLI command. The previous Study CLI is retired.

### Research Explorer

登录后选择 Research Explorer，浏览 Publication 列表并按需翻页；选择 Publication 查看声明 scope 和 Jobs，再选择 Analysis 检查原始结果、Coverage 与 provenance。点击 quantile、count 或 frequency 才读取对应 View。浏览不会执行 Research；服务端验证容量不足时可手动重试。

真实浏览器合成数据验收：在 `ui_web/` 执行 `npm run test:research-browser`，需要 Playwright Chromium 及系统运行库、空闲的 5173 和 8011 端口。脚本建立临时 Auth 数据库和合成 Publication Store，不访问真实行情。
