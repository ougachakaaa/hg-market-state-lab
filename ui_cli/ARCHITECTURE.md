# lab repository CLI authority

本文档定义 `hg-market-state-lab` 的 canonical repository-level CLI。仓库身份、唯一 Python runtime 与模块边界见 [repository architecture](../ARCHITECTURE.md)；操作与示例见 [usage guide](README.md)（usage-only，不是 authority）；当前可运行状态及环境准备见 [DEVELOPMENT.md](../DEVELOPMENT.md)。

## Owning module versus executable identity

The owning directory and Python namespace are `ui_cli`. The executable stays `lab`. The sole installation mechanism is root `[project.scripts] lab = "ui_cli.cli:main"`. Business behavior remains with its owning module. Research execution commands are retired by the Research reset; other commands retain their arguments, exit codes, delegation, delivery and failure semantics.

## Identity 与 ownership

`hg-market-state-lab` 是 repository / system identity；`lab` 是安装于 repository canonical Python project 的正式 console command，面向 human、operator 与 developer。`lab` 是 repository-level operator/orchestration interface，不是业务模块。

`lab` 只拥有 command parsing、hierarchical help、repository path/runtime resolution、local prerequisite/readiness checks、process invocation 与 foreground lifecycle、command forwarding、exit-code propagation、人类可读的 operational errors、明确需要的 repository-level discovery，以及 DataLake / Auth public service delegation、summary、exit-code mapping 与已声明的 file delivery。它不拥有 DataSet、Snapshot、Research method/dataset/result、Modeling、Auth identity/state/storage、HTTP product 或 frontend 语义；共享根 `.venv` 与可 import 的下层 package 不授予跨模块 semantic access。

原则：`lab` orchestrates；owning modules define semantics and execute domain behavior。`lab` 不重新实现或复制下层业务逻辑。

Console entry 只组合 command topology、help 与 dispatch；readiness diagnostics、service delegation、DataLake delivery 与共享 process mechanics 在 `ui_cli` 内按职责分离。这是内部实现边界，不改变 `lab` 的唯一 public interface 或 owning module semantics。

## Supported platforms 与 installation

V1 使用同一 `lab` namespace 支持 Windows native 与 Linux；WSL 按 Linux execution environment 处理。macOS 不被实现主动排除，但本阶段未声明为 verified platform。根 canonical Python project 的 `[project.scripts] lab = "ui_cli.cli:main"` 是唯一正式 CLI installation mechanism；操作系统生成的 launcher 文件名与后缀不是 repository semantic contract。OS-specific bootstrap 只准备环境，不定义平行 CLI interface。

CLI 使用 `pathlib` 与当前 Python runtime 的路径语义。属于 canonical Python runtime 的子进程使用当前 interpreter；外部工具由平台可感知的 executable resolution 查找。实现不假设 `/bin/`、`Scripts/`、`bin/` 或任何固定 executable 后缀，也不以具体 launcher 文件名判断安装成功。所有平台共用同一 command parsing、delegation 与 failure semantics。

## Current command hierarchy

```text
lab
├── doctor
├── serve
│   ├── backend
│   └── frontend
├── datalake
│   ├── list
│   ├── coverage <dataset-id> [dataset-specific args]
│   ├── ensure   <dataset-id> [dataset-specific args]
│   └── export   <dataset-id> [dataset-specific args] --output <path>
└── auth
    ├── pending
    ├── approve <user-id>
    ├── reject <user-id>
    └── disable <user-id>
```

顶层 namespace 按正式 repository-level capability 分组。`lab serve backend` 与 `lab serve frontend` 取代旧的平铺 `backend`、`frontend` 目标命令。`datalake` 通过下方明确支持的 Dataset public services 实现 delivery contract；操作示例见 [usage guide](README.md)。只有出现真实的 repository-level orchestration requirement 时才扩展 hierarchy；V1 不预定义其他 command group。

## Delegation 与 failure boundary

- `lab doctor` 只读检查本地仓库结构、根 Python runtime、启动前提与服务 readiness，报告人类可读状态；必要前提缺失时非零退出。它不安装依赖、不修复环境，也不运行下层业务行为。
- `lab serve backend` 从 repository root 前台调用 `ui_http` 拥有的 launcher；`lab serve frontend` 在 `ui_web/` 前台调用其开发脚本。两者继承标准输入输出，传递子进程退出码，并保持正常的前台中断生命周期。Backend 的 HTTP composition/runtime 由 [ui_http authority](../ui_http/ARCHITECTURE.md) 拥有；Frontend 的 runtime/configuration 由 [ui_web authority](../ui_web/ARCHITECTURE.md) 拥有。
- `lab datalake` 直接调用具体 Dataset public Application Service，遵循 [公共 Application contract](../data_lake/APPLICATION.md)，将 CLI arguments 转换为 owning Dataset semantic request，再呈现结果；不通过子进程运行 Dataset CLI，不直接进入 SQLite、Repository 或 Source adapter。
- 对上述子进程 delegation，缺少本地前提时，`lab` 在调用前给出人类可读的 operational error 并非零退出；下层进程启动后的 domain failure 由 owning module 呈现，`lab` 只传播其退出状态。DataLake 的 in-process semantic result/application failure 按下文映射，不由 lab 重新计算语义。

## DataLake delivery contract

`lab datalake` 只负责 command topology、Dataset selection、CLI parsing、semantic request construction、public service invocation、human-readable summary、exit-code mapping 与 export JSON file delivery。Window semantics、FetchUnit generation、coverage calculation、Source batching、completeness、export view fields、SQLite persistence 与 Tushare semantics 均由 DataLake / owning Dataset 拥有。

`list` 只列目标 contract 正式支持的 canonical Dataset IDs，当前支持 `tushare_trade_calendar`、`tushare_index_daily`、`tushare_equity_index_futures` 与 `tushare_equity_index_options`；不访问 Source 或缓存，不通过 filesystem scanning 推导支持范围。使用 explicit wiring，不引入 generic plugin / dynamic registry framework。Dataset navigation 见 [DataLake catalog](../data_lake/DATASETS.md)；public semantic request/view 见 [calendar SERVICE.md](../data_lake/datasets/tushare_trade_calendar/SERVICE.md)，CLI arguments 与 parsing 由本文件拥有，不复制 Dataset 字段模型。

### Calendar CLI parsing

`lab datalake coverage/ensure/export tushare_trade_calendar` 共享以下 CLI arguments：

| CLI argument | Parsing / request construction |
| --- | --- |
| --exchange | 必填，传入 TradeCalendarRange.exchange |
| --start-date | 必填，严格 YYYY-MM-DD 字符串，解析为 date |
| --end-date | 必填，严格 YYYY-MM-DD 字符串，解析为 date |

CLI 从 `data_lake.datasets.tushare_trade_calendar` 创建 service 并构造 `TradeCalendarRange`，不传 raw date strings 或 argparse namespace；service 仍负责 semantic validation。CLI 不构造 Scope / FetchUnits、不重算 completeness。Export 必填 `--output` 只属于 delivery，不进入 range；V1 不增加 view selector 或 is_open filter。

可复制的 Bash / PowerShell lifecycle 示例见 [usage guide](README.md)；这些命令直接调用 calendar public service。

### Index / Futures / Options CLI parsing

三个 Dataset 共享必填 `--start-date` / `--end-date`，严格解析 YYYY-MM-DD 为 date。Index 必填 `--index-codes`，使用一个或多个完整 codes；Futures / Options 必填 `--product-codes`，使用一个或多个 canonical products。CLI 分别构造 IndexDailyRange / FuturesDailyRange / OptionsDailyRange，并调用对应 public create_service()；集合规范化、合法性与 prerequisite 由 service 拥有。各命令只接受对应 Dataset 的 selection 参数；export 仍必填 --output，仅用于 UTF-8 JSON file delivery，terminal 只报告 summary。

### Operation behavior 与 exit codes

| 情况 | Exit code | Delivery |
| --- | --- | --- |
| list 正常执行 | 0 | Canonical Dataset IDs |
| coverage 正常查询，包括 complete = false | 0 | Human-readable CoverageResult summary |
| ensure complete = true | 0 | Human-readable EnsureResult summary |
| ensure 执行完成但 complete = false | 1 | EnsureResult summary 与逐 unit failure summary，明确目标未完成 |
| export view 成功生成并写入，包括 incomplete coverage | 0 | Output path、exported record count、coverage summary |
| CLI parsing / 无效参数 / 未知 Dataset ID / InvalidRequestError | 2 | Human-readable error |
| OperationError 或 output file 无法写入 | 1 | Human-readable execution / delivery error |

Summary 展示 service 返回的计数与 complete，不根据 records 数量重算 coverage。ensure failures 使用 service 返回的 FetchUnit semantic identity 与 reason，不泄露内部 IDs 或 provider transport response。可恢复的 unit failure 由 service 编码为 EnsureResult，不因一批 Source request 成功而显示目标完成。

### Export file delivery

`lab datalake --log-level {DEBUG,INFO,WARNING,ERROR} --log-file <path> <operation> ...` 的日志选项在 operation 之前，均可省略。默认 INFO stderr；可选文件为 UTF-8 timestamped logs。lab 仅配置 data_lake logger，调用结束后恢复原 handler/level/propagation 并关闭自身 handler；不修改 caller root logging。文件无法打开时返回 exit 1，且不开始 Dataset operation。事件内容与脱敏由 [DataLake diagnostics](../data_lake/DIAGNOSTICS.md) 拥有。

JSON file 是 operator delivery，不是内部 Python consumer 的数据接口；Python consumer 直接调用具体 Dataset public service，不经 CLI 或 JSON file round-trip。

`--output <path>` 必填且仅属于 lab delivery，不传入 Dataset service request。CLI 构造请求、调用 `service.export()`、将 Dataset-owned envelope 序列化为 UTF-8 JSON，以增量 JSON 编码写入 output 同目录的临时文件，flush/fsync 成功后原子替换 output path；公开日期与 null 按 Dataset contract 序列化，不从 SQL row layout 推导 view。

Terminal 只报告 output path、exported record count 与 coverage summary，不 dump 完整 records。Coverage incomplete 不触发 ensure 或 Source I/O；只要 view 正常生成并成功写入，incomplete 本身不属于 export execution failure，完整性由 envelope 明确表达。写文件失败按 delivery failure 返回，不将其报告为成功导出。

Source credential 与 SQLite location 由 owning Dataset 内部 composition 使用 DataLake shared runtime/storage machinery 解析；Dataset-local state ownership 由 [DataLake architecture](../data_lake/ARCHITECTURE.md) 定义，lab 不解析缓存路径，也不要求 DataLake runtime facade。不接受 `--token`、`--db`，也不要求 coverage/export 配置 Source credential。普通 caller 只能指定 semantic range 和 lab 的 export output path。

V1 DataLake 不提供 describe、read、query、fetch-unit、db、refresh 或 repair，不添加 force、TTL、generic query language、多 view selection 或 terminal record dump。

V1 不提供组合启动、后台进程管理、依赖安装、测试运行、部署、plugin、registry 或 workflow engine。

DataLake export delivery 不复制整个 dataclass tree 或构造完整 JSON string。编码/写入/替换失败清理临时文件并保留已有 output；wire 字段、日期、null 与 ordering 保持 Dataset contract。

增量编码的小片段可先合并为有界字符缓冲，再写入同目录临时文件；缓冲不得随整个 export 增长，不改变编码、换行或 ordering。flush/fsync 与原子替换的既有交付契约保持不变，编码中途、写入、flush 或替换失败均保留原 output 并清理临时文件。

## Authentication Operator contract

本节是 [Authentication MVP V1](../ui_http/AUTHENTICATION.md) 的 CLI specialization；G1 在同一个 canonical `lab` 下实现：

```text
lab auth pending
lab auth approve <user-id>
lab auth reject <user-id>
lab auth disable <user-id>
```

此能力扩展上文的 public service delegation 范围，CLI 不拥有 Auth identity/state/storage。Operator 由服务器 OS/操作权限定义；CLI 不要求 Web 登录、JWT secret 或 HTTP server，也不建立管理员角色。它直接调用 `ui_http.auth` 公开 service，不能调用 HTTP endpoint、打开 SQLite、导入 persistence internals、实现哈希或重新定义状态转换。HTTP 与 CLI 使用相同 Auth-owned storage composition；不接受 `--db`、`--password` 或 `--token`，也不提供 CLI register/login、密码管理或用户批量操作。

`pending` 无参数，展示 service 返回的 ID、规范化 username、status、UTC created_at，保持其排序；空列表显示无待审批申请并成功。三个状态命令各接受一个 UUID user ID，先作 CLI parsing，再委托 owning service；成功展示 ID、username、结果 status，不输出 hash 或凭据。State matrix、幂等与 failure classification 仅由 Auth authority 拥有。

| Result | Exit code | Delivery |
| --- | --- | --- |
| pending 或状态操作成功（包括目标状态幂等） | 0 | 人类可读结果 |
| parsing、invalid input、unknown user ID 或 invalid transition | 2 | 安全的输入/目标错误 |
| storage/configuration/operational failure | 1 | 安全的执行错误，无 SQL、hash、secret |

G2 同时按 Auth authority 调整 `doctor`：受保护 `/openapi.json` 的预期 401 报告 `running / authentication required`，不使 readiness 失败，不获取凭据、不登录、不添加匿名健康路由。其他 prerequisite 检查、端口诊断与退出码保持原边界。G0/G1 的无认证 runtime 仍按现有 200 OpenAPI 检测；正式 Auth 生效后不保留匿名 schema exemption。

## Research retirement

`lab research` and its Study discovery/forwarding interface are removed as a breaking change.
Research currently publishes no execution capability or replacement CLI. Its semantic
foundation is owned by [Research authority](../market_research/ARCHITECTURE.md).
