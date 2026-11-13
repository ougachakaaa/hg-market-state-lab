# Windows 到 WSL Nginx 的静态部署

此工具在 Windows 构建当前 npm/Vite SPA，通过指定的 WSL 发行版将静态文件发布到已有 Nginx 站点目录。它不安装依赖、不构建镜像、不重启容器，也不配置后端或隧道。脚本需要 Windows PowerShell 5.1 或兼容版本，以及 WSL 内的 Python 3.9+ 和 `wslpath`。

## 新机器初始化

1. 安装项目兼容的 Node.js 和 npm，在 `ui_web` 执行 `npm ci`。项目的构建依赖在 Windows 使用，WSL 不需要 Node.js。
2. 安装 WSL 和 Linux 发行版，运行 `wsl --list --verbose` 确认发行版名称；以普通 Linux 用户启动一次并确认可以写入部署目录。
3. 安装 Docker Desktop，启用该发行版的 WSL Integration。预先准备并启动 Nginx Gateway、Compose、网络、端口和站点目录；确认站点目录以 bind mount 挂入 Nginx，且站点配置提供 health endpoint 和 SPA fallback。部署工具不会创建这些基础设施。
4. 在 `ui_web` 执行：

   ```powershell
   Copy-Item .\deploy\deploy.config.example.psd1 .\deploy\deploy.config.psd1
   ```

   编辑本机配置：填写发行版、已有 Linux 部署根目录、站点相对路径和对应 URL。不要将凭据写入配置；本地文件已被 Git 忽略。
5. 首次及后续发布均运行：

   ```powershell
   .\deploy\deploy.ps1
   ```

   也可用 `-ConfigPath 'D:\configs\deploy.config.psd1'` 指定其他配置。相对配置路径以当前 PowerShell 工作目录解析；默认配置和默认项目根目录以脚本位置解析。

## 配置

| 字段 | 模板默认值 | 含义 |
| --- | --- | --- |
| `ProjectRoot` | 空字符串 | 自动使用 `deploy` 的父目录；也可指定 Windows 项目路径。 |
| `PackageManager` | `npm` | 当前项目固定使用 npm 和 `package-lock.json`。 |
| `BuildArguments` | `@('run', 'build')` | 传给 npm 的参数数组，不经 shell 求值。 |
| `BuildOutput` | `.build/online` | 项目根目录下的构建目录，必须包含 `index.html`。 |
| `Distribution` | `Ubuntu-24.04` | `wsl --list --verbose` 显示的发行版名称。 |
| `DeployRoot` | `~/deployments/nginx-gateway` | 已存在的 Linux 部署根目录；`~` 指该发行版的默认用户。 |
| `SitePath` | `sites/example` | 根目录下的相对站点目录；应只包含该站点的静态文件。 |
| `BaseUrl` | `http://localhost:8080` | 实际指向该站点的 HTTP(S) 地址。 |
| `HealthPath` | `/healthz` | health endpoint 的绝对 URL 路径。 |
| `VerifyHttp` | `$true` | 发布后检查首页、health、资源及 SPA fallback。 |
| `CreateBackup` | `$true` | 成功时保留旧站点副本。 |
| `BackupRetention` | `3` | 该站点保留的备份数量；启用备份时至少为 1。 |
| `AllowOverwrite` | `$true` | 是否允许更新已存在的站点目录。 |

脚本检查配置、工具及 lockfile，在 Windows 构建；WSL 中复制到 staging 并逐文件校验 SHA-256，然后保存旧站点恢复副本，更新现有绑定目录并再次校验，最后执行配置的 HTTP 验证。每阶段以及成功或失败都有明确输出；失败返回非零退出码。API 占位路由可另行检查：`curl.exe -i http://localhost:8080/api/health`；其预期状态取决于网关配置。

## 恢复、限制与排查

- 目录本身保持不变以兼容直接 bind mount；文件原位替换**不是原子操作**，请求可能短暂看到混合版本。需要原子切换时，须另行设计父目录挂载及版本切换，并迁移容器配置。
- 发布或 HTTP 验证失败后尝试恢复旧文件；失败日志会给出保留的恢复目录。即使关闭长期备份，也会在发布期间建立临时恢复副本。首次发布失败时清空新文件，但保留已创建的站点目录。进程被强制终止或机器断电时无法保证自动恢复。
- 成功后的备份保存在部署根目录 `.web-deploy/` 下对应站点的目录中，输出会显示路径。手动回滚时先停止其他发布，确认目标和备份，再将备份**内容**复制回现有站点目录；不要替换该目录本身。保留副本直至确认站点恢复。
- 站点目录由部署工具管理，发布会删除其中不属于新构建的文件。不要把其他站点、Docker 配置或用户数据放在该目录；不要并发使用其他工具修改它。部署树中的符号链接不受支持。
- 若检查失败，依次检查发行版名称、Linux 目录权限、Node/npm 和依赖、build 输出、网关挂载及本机 URL。可检查 `docker compose ps`、容器日志和 `curl.exe -i http://localhost:8080/healthz`。HTTP 检查从 WSL 发起，因此 URL 也必须能从目标发行版访问。
- 脚本针对本项目的 npm 静态构建，不能证明任意其他框架不存在 SSR；使用其他构建工具或 Node 服务端渲染需要重新评估，不能直接套用。不要把秘密或本机配置注入前端构建产物，静态文件会公开提供。

## Workspace 路由前提

`/research/publications` 是浏览器页面路径，也是后端 Publication API 路径。站点网关需把 `/research`、`/research/publications`、`/data/*`、`/backtesting` 的 HTML navigation 回退到 `index.html`，并把同源 `/api/research/*` 去除 `/api` 后转发至原后端路径，保留 Cookie、query、状态码与响应体。此仓库不包含实际 Nginx 站点配置；发布前应在目标网关验证这两类请求，不能仅以普通 SPA fallback 检查代替。
