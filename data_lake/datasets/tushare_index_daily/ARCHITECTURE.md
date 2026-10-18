# tushare_index_daily Dataset architecture authority

本文件是指数日线自治 bounded-context 入口，拥有 identity、Source ownership、Scope / Window、FetchUnit / Record identity 与 completeness。继承 [DataLake architecture](../../ARCHITECTURE.md) 和公共 [DOMAIN_MODEL.md](../../DOMAIN_MODEL.md)；稳定入口为 [DATASETS.md](../../DATASETS.md)。Instrument 与字段 normalization 进入 [FACTS.md](FACTS.md)，目标交易日与 dependency 进入 [TRADING_DAYS.md](TRADING_DAYS.md)，consumer contract 进入 [SERVICE.md](SERVICE.md)。

## 1. Identity 与 ownership

Canonical identity 为 `tushare_index_daily`，沿用现有 `tushare_trade_calendar` 的 lowercase snake_case convention。Dataset 表达 Tushare 指数日线 Source facts 与 Dataset-local index catalog，不限制为四个股指期货 underlying indices。

本 bounded context 位于 `datasets/tushare_index_daily/`；authority、`src/`、`tests/` 与 `data/` 的 ownership、colocation 和 Python boundary 继承 [模块架构](../../ARCHITECTURE.md)。

Primary Source 为 Tushare `index_daily`；instrument metadata Source 为 `index_basic`。两个 endpoint 属于本 Dataset 的 Source composition，不因 endpoint 数量拆分 Dataset，也不通过 Snapshot 私有 adapter 读取。Provider-native representation 与 canonical semantic facts 的映射由 FACTS.md 拥有。

Source provider 为 Tushare，execution 继承 [providers/tushare/ARCHITECTURE.md](../../providers/tushare/ARCHITECTURE.md)。本 Dataset Source Adapter 拥有 endpoint / parameters、batching / pagination 与 partition；identity / normalization 的领域规则由 [FACTS.md](FACTS.md) 拥有。

本 Dataset 不拥有 moving average、return window、volatility、technical indicators、relative strength、basis 或 research features；这些属于下游 Research / Modeling。与 Futures / Options 的组合只能通过各自 public service；不建立 shared market database、global instrument master 或跨库 foreign key。

## 2. Scope、Window 与目标集合

第一版唯一 Scope shape 为 `IndexDailyScope(index_codes)`：明确选择的一组完整 provider-native index codes。Window 为 transient `start_date..end_date`，两端 inclusive。选择集合不持久化为 Window，也不以常用指数列表封闭 Dataset fact space；规范化、合法 Source instrument 与 metadata 规则见 FACTS.md，public input types 见 SERVICE.md。

Expected FetchUnits 由所选指数与 [TRADING_DAYS.md](TRADING_DAYS.md) 确定的目标交易日展开，不逐自然日强求日线 Record。V1 不按指数发布日期自动裁剪 Window；Source 可有发布前回溯历史，metadata list_date 不等于行情首日。Consumer 明确选择自己的历史范围，目标交易日缺失行情必须如实报告失败，不能收缩目标集合掩盖缺口。

## 3. FetchUnit / Record identity 与 completeness

Canonical FetchUnit identity 为 `(index_code, trade_date)`，是一只指数一个目标交易日的 minimum synchronization / reconciliation / write ownership / completeness unit。Natural Record identity 同为 `(index_code, trade_date)`，独立于内部 unit_id / record_id。

```text
1 successful FetchUnit (index_code, trade_date)
    → exactly owns 1 canonical IndexDailyRecord
```

成功要求目标 identity 唯一匹配、FACTS.md 中全部 required daily facts 合法，以及本地 instrument identity/metadata 合法可解释；Record、instrument 所需状态与成功 metadata 必须一致提交。空响应、缺失目标日、任何重复 identity（即使内容相同）、identity conflict、非法数值或 required fact 缺失均不得 success。不能补造日线、零成交、前值或用其他指数替代。

`FetchUnit != Source Request`：adapter 可按 `ts_code + start_date + end_date` 批量获取历史，并处理 provider truncation / pagination；返回行必须 partition 回逐指数逐日 units。只验证、写入本次 selected units；response 中其他日期、已 success unit 或其他指数不授权新写入。无法确定目标归属的响应不能用来宣告所尝试 units 成功。

Selected units 独立验证并原子保存；可定位的重复 daily identity 只失败对应 `(index_code, trade_date)`，其他能完整验证的 units 继续。分页穷尽与整批失败边界继承 [EXECUTION.md](../../EXECUTION.md)。Status 与已有 success 的跳过规则继承公共 domain authority。Metadata 只服务本地 instrument ownership，不发布独立 record-level mutation 或新的 catalog operation。

## 4. Dependency 与下一份 authority

唯一 Dataset service dependency 为 `tushare_index_daily → tushare_trade_calendar`，仅通过 Calendar public Application Service 取得交易日语义；Calendar 不反向依赖 Index。交易日 selection、read-only 操作、ensure 编排、prerequisite failure 与 snapshot 边界由 TRADING_DAYS.md 拥有；不直接调用另一套 trade_cal、不访问 Calendar SQLite / Repository / internal source。

Index 与 Futures / Options 的 storage ownership 保持分离；underlying relationship 不构成 persistence relationship。Public `coverage / ensure / export`、business Index Daily View、runtime configuration 见 SERVICE.md。

## 5. Dataset Composition 与职责组织

本 Dataset 按公共 [COMPOSITION.md](../../COMPOSITION.md) 接入 Kernel；六角色绑定如下：

| Role | 本 Dataset 绑定 / canonical owner |
| --- | --- |
| FetchUnitPlanner | 本文件第 2–3 节：canonical index set × 固定交易日 D → `(index_code, trade_date)`；D 的取得与权限只由 [TRADING_DAYS.md](TRADING_DAYS.md) 拥有 |
| Source Port / Adapter | 本 Dataset 的 index_basic/index_daily Adapter；Source identity / metadata acquisition / bounded requests 见 [FACTS.md](FACTS.md)，Provider 只执行请求 |
| Normalizer | Index Domain；[FACTS.md](FACTS.md) 的 Source → Instrument / canonical daily facts mapping |
| Completeness Validator | Index Domain；本文件第 3 节的 exactly-one predicate 结合 FACTS.md 的 required facts、metadata / Instrument association；读缓存仍验证成功时 basis |
| Export Projector | Index Domain 的业务 view projection；[SERVICE.md](SERVICE.md) 唯一拥有 `index_daily` view、字段、ordering 与 wire meaning |
| Repository Port / Adapter | Kernel 标准 SQLite Adapter；Index Composition Root 绑定自己的 identity/source/storage context，存储机制见 [PERSISTENCE.md](../../PERSISTENCE.md) |

本 Dataset 有一个 Dataset-owned Calendar Prerequisite Resolver，按 [TRADING_DAYS.md](TRADING_DAYS.md) 将合法 Index request + operation permission 转为已验证 SSE Calendar context（由匹配 Window 的完整 view 验证得到的固定 D）。Composition Root 绑定该 Resolver、Calendar public service、上述六角色与 Adapters，发布 IndexDailyService / create_service()。Public Service 先验证 request，再调用 Resolver；纯 FetchUnitPlanner 消费 request/context 展开 canonical index set × D，不读库、不调用 Calendar/Source、不按缓存或缺行缩小目标；Kernel 随后检查缓存并选择待执行 units。

Normalizer 按 FACTS.md 将 daily facts 与合法本地 index metadata 转为 UnitRecords（恰一条 Record、关联 Instrument 和成功 metadata basis）；Completeness Validator 通过后才经 Repository Port 原子提交。Metadata acquisition/reuse 位于 selected units 的 Source 执行准备与完整性流程，不是额外 Calendar Resolver 或 Planning Context，不改变目标全集。交接与读 success 重验证继承 [PORTS.md](../../PORTS.md)；通用 ensure、coverage、snapshot 与 failure accounting 委托 Kernel。

Index Domain 拥有本地 metadata 可复用的业务条件与成功代表 unit 选择（FACTS.md）；composition 通过 Repository Port 读取并验证代表 snapshot 后向 Source 提供合法 metadata。Source Adapter 不直连 SQLite，也不以裸 instrument row 或当前 provider metadata 替换旧 success basis。BatchPlanner 属于 Dataset 执行策略，具体 bounds / endpoints 归 FACTS.md，prefetch 与 writer lifecycle 归 EXECUTION.md。

目标职责区分 Dataset Domain（目标展开、metadata/fact normalization、validation、projection）、Source Adapter（请求、分页、partition）、Composition Root / Public Service（request / Calendar 编排、实例绑定、Kernel delegation）。不强制独立策略文件；纯领域逻辑不依赖 Provider、SQLite 或 Calendar internal modules。Public namespace 与 request/result/view 不变。
