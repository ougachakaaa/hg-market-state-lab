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
poetry run lab research --help
```

## 命令速览

```text
lab
├── doctor                         检查本地环境与服务 readiness
├── serve                          前台启动开发服务
│   ├── backend                    启动 backend
│   └── frontend                   启动 frontend
├── research                       发现并运行 retained Studies
│   ├── list                       列出当前可运行的 Study IDs
│   └── run <study-id>              转发到对应 Study 的 CLI
└── datalake                       使用 Dataset public services
    ├── list                       发现支持的 Dataset IDs
    ├── coverage <dataset-id>      查看当前缓存覆盖
    ├── ensure <dataset-id>        补齐缺失或未成功的覆盖
    └── export <dataset-id>        读取当前 semantic view 并交付 JSON
```

## 常用 workflow

### 环境检查与服务启动

```bash
poetry run lab doctor
poetry run lab serve backend
poetry run lab serve frontend
```

服务在前台运行，backend 与 frontend 分别在独立终端启动，Ctrl+C 结束。环境与安装前提见 [DEVELOPMENT.md](../DEVELOPMENT.md)。

### DataLake：发现、补齐、导出

```bash
poetry run lab datalake list
```

`list` 发现 Dataset；`coverage` 查看缓存；`ensure` 补齐未成功覆盖；`export` 将当前 view 写为 JSON。coverage / export 不访问 Source、不创建缓存，export 不隐式 ensure（仍会写入指定的导出文件）。ensure 只有实际需要 fetch 时才访问 Source；首次 fetch 前按 [DEVELOPMENT.md](../DEVELOPMENT.md) 配置 `TUSHARE_TOKEN`。

以下示例使用 `tushare_trade_calendar`，依次检查、补齐、复查、导出，再次 ensure。目标已全部成功时，最后一步跳过 fetch；未成功目标仍可能重试。日期范围与 Dataset-specific semantics 见 [Dataset catalog](../data-lake/DATASETS.md)。`calendar.json` 写入当前目录。

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

以下 ensure 命令分别使用指数、期货产品与期权产品 selection；相同参数也适用于 coverage，export 再加必填 --output。

```bash
poetry run lab datalake ensure tushare_index_daily --index-codes 000300.SH 000905.SH --start-date 2026-09-30 --end-date 2026-09-30
poetry run lab datalake ensure tushare_equity_index_futures --product-codes IF IH IC IM --start-date 2026-09-30 --end-date 2026-09-30
poetry run lab datalake ensure tushare_equity_index_options --product-codes IO HO MO --start-date 2026-09-30 --end-date 2026-09-30
poetry run lab datalake export tushare_equity_index_options --product-codes IO HO MO --start-date 2026-09-30 --end-date 2026-09-30 --output options.json
```

上述命令可直接在 Bash 或 PowerShell 运行。首次 ensure 可补齐所需 Calendar；coverage/export 只读，Calendar prerequisite 未完整时明确失败。查看各 Dataset 参数可使用 `lab datalake ensure <dataset-id> --help`。

### Research：发现 Study 与查看接口

```bash
poetry run lab research list
poetry run lab research run <study-id> --help
```

`research list` 发现当前可运行的 retained Studies；`research run <study-id> --help` 查看对应 Study 的接口。当前没有可运行的 retained Study，`research list` 输出为空。新增 Study 后，实际参数、方法与结果语义继续读取该 Study authority。

## 错误与自动化

正常结果与 incomplete result 的退出行为因 operation 而异。shell / automation caller 应使用 process exit code，不解析人类可读消息；完整映射见 [CLI exit-code contract](ARCHITECTURE.md#operation-behavior-与-exit-codes)。

## 下一步读什么

| 需要 | 阅读入口 |
| --- | --- |
| 使用 lab / 查常见示例 | 本 usage guide |
| 本地 setup、bootstrap、当前 runtime 状态 | [DEVELOPMENT.md](../DEVELOPMENT.md) |
| 修改或审阅 CLI semantics、delegation、delivery | [lab authority](ARCHITECTURE.md) |
| Dataset-specific semantics | [DataLake catalog](../data-lake/DATASETS.md) → owning Dataset authority |
| Research execution convention / Study-specific semantics | [Research UI entry](../market-research/ui/ARCHITECTURE.md) → 对应 retained Study authority |

Usage guide 不替代上述 authority；业务语义由 owning module 定义。
