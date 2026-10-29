# lab 使用指南

`lab` 是 repository canonical operator CLI。本文件是面向 human 与 AI agent 的 canonical usage guide，只提供操作、示例和导航，不是 semantic authority。

先按 [DEVELOPMENT.md](../DEVELOPMENT.md) 准备环境，再从 **repository root** 运行 `poetry run lab <command>`；根 Poetry environment 已激活时，也可直接运行 `lab <command>`。

## 先看 help

优先通过 help 发现当前支持的命令和参数。以下命令在 Bash 和 PowerShell 中均可使用；`lab <command> --help` 用于继续查看对应命令。

```bash
poetry run lab --help
poetry run lab serve --help
poetry run lab datalake --help
poetry run lab datalake export --help
poetry run lab auth --help
```

## 命令速览

```text
lab
├── doctor                         检查本地环境与服务 readiness
├── serve                          前台启动开发服务
│   ├── backend                    启动 backend
│   └── frontend                   启动 frontend
├── datalake                       使用 Dataset public services
│   ├── list                       发现支持的 Dataset IDs
│   ├── coverage <dataset-id>      查看当前缓存覆盖
│   ├── ensure <dataset-id>        补齐缺失或未成功的覆盖
│   └── export <dataset-id>        读取当前 semantic view 并交付 JSON
└── auth                           本机 Operator 用户审批
    ├── pending                    查看待审批用户
    ├── approve <user-id>          批准 Pending 用户
    ├── reject <user-id>           拒绝 Pending 用户
    └── disable <user-id>          禁用 Active 用户
```

## 常用 workflow

### 环境检查与服务启动

```bash
poetry run lab doctor
poetry run lab serve backend
poetry run lab serve frontend
```

服务在前台运行，backend 与 frontend 分别在独立终端启动，Ctrl+C 结束。环境与安装前提见 [DEVELOPMENT.md](../DEVELOPMENT.md)。

### Authentication：注册申请与 Operator 审批

G1 发布 Python 注册 service 和本机审批 CLI；G2 已提供 HTTP 注册/登录与统一访问保护。Backend 启动须先配置 Auth，见 [开发环境](../DEVELOPMENT.md)。Python caller 使用同一公开入口：

```python
from getpass import getpass
from ui_http.auth import create_service

result = create_service().register(input("Username: "), getpass("Password: "))
print(result.message)
```

Operator 从 pending 输出复制 UUID，按需执行对应命令：

```bash
poetry run lab auth pending
poetry run lab auth approve <user-id>
poetry run lab auth reject <user-id>
poetry run lab auth disable <user-id>
```

`approve` / `reject` 用于 Pending；`disable` 用于 Active。重复目标状态操作成功，其他转换明确失败。空 pending 列表成功退出。CLI 不需要启动 server 或配置 JWT secret；数据库默认位于 `ui_http/data/auth.sqlite3`，可用服务器环境变量 `LAB_AUTH_DB_PATH` 指定绝对路径。用户名规则、密码要求与 service failure 分类见 [Auth authority](../ui_http/AUTHENTICATION.md#2-user-identity-and-persistence)。

### DataLake：发现、补齐、导出

```bash
poetry run lab datalake list
```

`list` 发现 Dataset；`coverage` 查看缓存；`ensure` 补齐未成功覆盖；`export` 将当前 view 写为 JSON。coverage / export 不访问 Source、不创建缓存，export 不隐式 ensure（仍会写入指定的导出文件）。ensure 只有实际需要 fetch 时才访问 Source；首次 fetch 前按 [DEVELOPMENT.md](../DEVELOPMENT.md) 配置 `TUSHARE_TOKEN`。

以下示例使用 `tushare_trade_calendar`，依次检查、补齐、复查、导出，再次 ensure。目标已全部成功时，最后一步跳过 fetch；未成功目标仍可能重试。日期范围与 Dataset-specific semantics 见 [Dataset catalog](../data_lake/DATASETS.md)。`calendar.json` 写入当前目录。

**Bash**（逐行运行）：

```bash
poetry run lab datalake coverage tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
poetry run lab datalake ensure tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
poetry run lab datalake coverage tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
poetry run lab datalake export tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31 --output calendar.json
poetry run lab datalake ensure tushare_trade_calendar --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
```

**PowerShell**（backtick 必须是该行最后一个字符）：

```powershell
poetry run lab datalake coverage tushare_trade_calendar `
    --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
poetry run lab datalake ensure tushare_trade_calendar `
    --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
poetry run lab datalake coverage tushare_trade_calendar `
    --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
poetry run lab datalake export tushare_trade_calendar `
    --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31 `
    --output calendar.json
poetry run lab datalake ensure tushare_trade_calendar `
    --exchange SSE --start-date 2024-01-01 --end-date 2024-01-31
```

### Index、Futures 与 Options

需要调试时，日志选项放在 operation 前：

```bash
poetry run lab datalake --log-level DEBUG --log-file datalake.log ensure tushare_equity_index_futures --product-codes IF IH IC IM --start-date 2026-01-01 --end-date 2026-10-02
```

默认 INFO 在 stderr 显示 ensure 进度与失败，DEBUG 增加脱敏的请求 endpoint、日期、分页、等待和耗时；--log-file 可选，文件为 UTF-8。文件父目录须已存在。Token、原始异常与 response 不写入日志。日志位置由 caller 选择，runtime 文件可放 Dataset data/ 下以保持 Git 忽略。

Tushare 默认按 180 次/分钟运行，适合 2000 积分账号的 200/min 额度；`TUSHARE_CALLS_PER_MINUTE` 可设为 1..500 的整数，按自己的实际权限调整。Windows PowerShell 例如 `$env:TUSHARE_CALLS_PER_MINUTE = "180"`；Bash 例如 `export TUSHARE_CALLS_PER_MINUTE=180`。额度在单一 process 内共享，不协调其他程序的账户用量。失败请求有安全分类；可用相同 ensure 继续补齐 non-success units，已 success facts 默认跳过。

以下 ensure 命令分别使用指数、期货产品与期权产品 selection；相同参数也适用于 coverage，export 再加必填 --output。

```bash
poetry run lab datalake ensure tushare_index_daily --index-codes 000300.SH 000905.SH --start-date 2026-09-30 --end-date 2026-09-30
poetry run lab datalake ensure tushare_equity_index_futures --product-codes IF IH IC IM --start-date 2026-09-30 --end-date 2026-09-30
poetry run lab datalake ensure tushare_equity_index_options --product-codes IO HO MO --start-date 2026-09-30 --end-date 2026-09-30
poetry run lab datalake export tushare_equity_index_options --product-codes IO HO MO --start-date 2026-09-30 --end-date 2026-09-30 --output options.json
```

上述命令可直接在 Bash 或 PowerShell 运行。首次 ensure 可补齐所需 Calendar；coverage/export 只读，Calendar prerequisite 未完整时明确失败。查看各 Dataset 参数可使用 `lab datalake ensure <dataset-id> --help`。

### Research status

Research execution and Study discovery are retired. No replacement Research CLI
is published; see the [Research authority](../market_research/ARCHITECTURE.md).

## 错误与自动化

正常结果与 incomplete result 的退出行为因 operation 而异。shell / automation caller 应使用 process exit code，不解析人类可读消息；完整映射见 [CLI exit-code contract](ARCHITECTURE.md#operation-behavior-与-exit-codes)。

## 下一步读什么

| 需要 | 阅读入口 |
| --- | --- |
| 使用 lab / 查常见示例 | 本 usage guide |
| 本地 setup、bootstrap、当前 runtime 状态 | [DEVELOPMENT.md](../DEVELOPMENT.md) |
| 修改或审阅 CLI semantics、delegation、delivery | [lab authority](ARCHITECTURE.md) |
| Dataset-specific semantics | [DataLake catalog](../data_lake/DATASETS.md) → owning Dataset authority |

Usage guide 不替代上述 authority；业务语义由 owning module 定义。
