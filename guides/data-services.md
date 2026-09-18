# guides/data-services.md — Data Service / CLI / output contract authority

> 状态：authority（design-only）。本文档定义项目最上层的用户调用语义单位 Data Service、用户级 CLI（`dms`）的语义，以及 Data Service 的 canonical user-facing output。只落 authority，不实现 CLI，不修改 Collector，不修改 `build_snapshot.py`。
>
> 层级：本文档位于 `ARCHITECTURE.md` 之下。架构层面的稳定边界以 `ARCHITECTURE.md` 为准（尤其第 0 节术语、第 2 节核心架构、第 3 节 Raw/Snapshot 边界、第 8 节 Guide 职责、第 9 节项目结构）。本文档定义 Data Service 的清单、调用契约与输出契约；具体 Dataset / Raw / Snapshot 语义继续由对应 Guide 负责，不在本文档重复。

## 1. 什么是 Data Service

Data Service 是用户可直接请求的一组稳定业务语义的数据产品。一个 Data Service 可以由多个 Dataset、Raw artifact 和 deterministic transformations（Snapshot Assembly）共同生成。

关系：

```text
Data Service
    ↓
existing Dataset / Collector / Snapshot Definition
    ↓
final dated output
```

Data Service 不是：

```text
Dataset
Source
Pipeline framework
Workflow engine
Plugin
```

它只是最上层的**用户调用语义单位**。用户和 Agent 不需要知道底层有哪些 Collector，只需要指定：

```text
我要什么数据服务（service_id）
+
我要哪个交易日（target_trade_date）
```

## 2. Data Service Catalog

第一版只定义一项 Data Service，不为了丰富 catalog 创造其他服务。

| service_id | description | input | output |
| --- | --- | --- | --- |
| `csi1000-5d-analysis` | 为外部 analyzer 分析中证1000未来约 5 个交易日市场状态准备的 analysis-ready 数据产品 | `target_trade_date`（CLI 的 `--date`） | `snapshot.json` |

Catalog 是显式、静态、authority-driven 的，不通过扫描文件系统动态发现。不做：

```text
dynamic registry
plugin discovery
schema registry
service lifecycle framework
```

`index_daily`、`stock_daily` 仍属于 Dataset / Raw capability，**不**升级为 Data Service。

## 3. service: csi1000-5d-analysis

语义：

> 为外部 analyzer 分析中证1000未来约 5 个交易日市场状态准备的 analysis-ready 数据产品。

它复用当前已经存在的：

```text
CSI1000 history（Dataset index_daily，000852.SH）
MO option chain（Dataset mo_option_basic + mo_option_daily）
IM futures（Dataset im_futures_basic + im_futures_daily）
deterministic Snapshot Assembly（guides/csi1000-5d-analysis-snapshot.md）
```

最终 artifact：`snapshot.json`。

相关 authority：

* Dataset / Raw artifact 契约：`guides/csi1000-5d-analysis-data.md`
* Snapshot Definition（Raw → `snapshot.json`）：`guides/csi1000-5d-analysis-snapshot.md`

Data Service 不重新定义 Source semantics / Dataset semantics / window semantics / derived formula / Snapshot schema；这些继续由上述 Guide 负责。

## 4. CLI: dms

用户级 CLI 语义名称为 `dms`。第一版只支持两个命令：`list`、`get`。

### 4.1 dms list

canonical semantic：

```text
dms list
```

作用：

> 列出当前仓库支持的 Data Service。

第一版至少输出每项 Data Service 的：

```text
service_id
description
```

结果中应包含：

```text
csi1000-5d-analysis
```

Catalog 不通过扫描文件系统动态发现。

### 4.2 dms get

canonical semantic：

```text
dms get <service_id> --date YYYY-MM-DD
```

当前示例：

```text
dms get csi1000-5d-analysis --date 2026-09-18
```

其中：

```text
--date
```

明确表示：

```text
target_trade_date
```

调用者必须显式提供。当前不支持：

```text
today
latest
yesterday
自动寻找最近交易日
自动 fallback
```

## 5. get 的职责（orchestration）

对于：

```text
dms get csi1000-5d-analysis --date D
```

CLI 负责 orchestration：

```text
D
↓
collect CSI1000 history
↓
collect MO option basic
↓
collect MO option daily
↓
collect IM futures basic
↓
collect IM futures daily
↓
build analysis-ready Snapshot
↓
publish final Data Service output
```

CLI 不重新定义：

```text
Source semantics
Dataset semantics
window semantics
derived formula
Snapshot schema
```

这些继续由已有 authority 负责。

## 6. canonical output

Data Service 的用户级输出根目录为 `output/`：

```text
output/
└── <service_id>/
    └── <target_trade_date>/
        └── <service artifact>
```

当前：

```text
output/
└── csi1000-5d-analysis/
    └── 2026-09-18/
        └── snapshot.json
```

因此：

```text
service_id + target_trade_date
```

唯一确定一次 Data Service 的最终用户输出位置。

## 7. Raw / Snapshot / Output 边界与 reconciliation

* `data/raw/`：Source Facts / internal runtime artifacts。继续不变，见 `ARCHITECTURE.md` 第 3、9 节。
* `data/snapshots/`：非 Data Service 的 Snapshot 输出目录。第一版 Daily Snapshot（`data/snapshots/YYYY-MM-DD/snapshot.json`）不是 Data Service，继续使用 `data/snapshots/`。
* `output/<service_id>/<target_trade_date>/`：Data Service 的 canonical user-facing output。

reconciliation（当前 CSI1000 Data Service）：

> `output/<service>/<date>/` 是 Data Service 的 canonical user-facing output。

`build_snapshot.py` 直接写该位置；`data/snapshots/csi1000-5d-analysis/<date>/snapshot.json` 不再产生，不维护两份相同 artifact。

本 Goal 不重构无关的 Daily Snapshot；`data/snapshots/YYYY-MM-DD/` 语义保持不变。

## 8. 日粒度语义

每次：

```text
get <service> --date D
```

代表一个按日的数据服务请求。

运行单元：

```text
service_id
+
target_trade_date
```

对应：

```text
output/<service_id>/<target_trade_date>/
```

需要明确：

> “按日”描述的是 Data Service request / output partition，不表示所有内部 Raw artifact 只能包含一天数据。

例如：

```text
index_daily_history.json
im_futures_daily.json
```

可以包含多个历史交易日。但它们都属于 `target_trade_date = D` 这一次数据准备。

## 9. Git boundary

锁定以下均为 runtime artifacts：

```text
.env
data/raw/**
output/**
```

它们不得进入 Git history。（`data/snapshots/**` 也继续作为运行产物，不进入版本控制。）

仓库只版本化：

```text
code
authority / guides
tests
configuration templates
```

不记录每日市场数据产品。

## 10. Agent execution surface

锁定：

> Data Service CLI 是普通用户和 Agent 执行数据任务的 canonical interface。

以后用户要求：

```text
生成 2026-09-18 的 csi1000-5d-analysis
```

Agent 应优先执行语义等价于：

```text
dms get csi1000-5d-analysis --date 2026-09-18
```

而不是自行逐个寻找 Collector。

底层 Collector / Builder 可以继续存在，用于：

```text
development
debugging
testing
reconciliation
```

但不是普通用户主入口。

## 11. CLI implementation surface

当前仓库仍使用 Poetry `package-mode = false`。本文档只锁定 CLI **语义名称** `dms`，不要求 package 化，不提前要求生成系统级 executable。

第一版 implementation 可以自然落成：

```text
poetry run python scripts/dms.py list
```

```text
poetry run python scripts/dms.py get csi1000-5d-analysis --date 2026-09-18
```

它们在语义上分别是：

```text
dms list
dms get ...
```

是否增加真正的 `dms` console entry point 保持 deferred。

## 12. Non-goals

不要设计：

```text
scheduler / cron / database / API server

plugin system / dynamic registry / workflow engine / dependency graph framework

retry framework / cache framework

automatic latest trading date / automatic scheduling

GPT analyzer / trading analysis
```

保持第一版极小。

## 13. Deferred

```text
真正 dms console entry point
```

## 14. 完成自检

仅阅读相关 authority（`ARCHITECTURE.md`、本文档及本文档引用的 Guide）应能明确回答：

1. 什么是 Data Service？
2. 当前有哪些 Data Service？
3. `csi1000-5d-analysis` 表示什么？
4. 如何列出 service？
5. 如何请求 service？
6. `--date` 的语义是什么？
7. 一次调用最终写到哪里？
8. `data/raw` 与 `output` 有什么区别？
9. 哪些文件不进入 Git？
10. 为什么普通用户/Agent 不需要知道底层 Collector？
11. 现有 `data/snapshots` 与新的 canonical output 如何 reconciliation？

若这些问题仍需 implementation agent 自行发明，则本 authority 未完成。
