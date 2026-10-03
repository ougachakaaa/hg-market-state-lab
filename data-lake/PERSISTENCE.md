# DataLake SQLite lifecycle and compatibility authority

本文件拥有内部 SQLite lifecycle、transaction / read snapshot、frozen basis 与当前支持的 persistence generation compatibility，继承 [ARCHITECTURE.md](ARCHITECTURE.md) 的 owned SQLite boundary、[DOMAIN_MODEL.md](DOMAIN_MODEL.md) 的单位 ownership / 原子性及 [APPLICATION.md](APPLICATION.md) 的 read-only / export consistency invariant；不发布 consumer SQL contract 或通用 migration framework。

## 1. Owned SQLite lifecycle

Dataset composition 显式提供本 Dataset 的 storage context，shared path machinery 不提供全局默认 root，也不创建目录或 SQLite。当前默认 owned filename 为 `<dataset-id>.sqlite3`，位于模块架构声明的 Dataset-local `data/`；目录仅在有权写入的 operation 需要时 materialize。缓存缺失及非法缓存的 public 行为继承 APPLICATION.md。

旧 `data-lake/data/*.sqlite3` 是隔离的 legacy runtime state：不自动移动、复制、删除、覆盖，不作为 factory、coverage/export 或 ensure 的 fallback，不双写，也不建立旧目录 compatibility layer。此规则与同一 owned SQLite 内的 generation compatibility 不同；显式旧目录 migration / import 须独立设计。

## 2. Frozen basis invariant

Generation 3 在每个 Dataset 自己的 SQLite 内保存内容寻址的 frozen basis；多个 units 可以引用完全相同的 immutable basis。不得跨 Dataset 共享 basis。Unit 的历史 basis、records、content_hash、record_count、status 与取得时间仍一一对应；新 catalog 不修改旧 success basis。内容 hash 与存储原文必须一致；冲突、缺失引用及损坏必须报 OperationError。

## 3. Current supported persistence generations

新建 owned SQLite 使用 generation 3；当前支持合法 generation 2 与 3。Coverage/export 对两者均保持只读，包括不升级、不备份、不建索引；全部已成功或零目标 ensure 同样不升级。未知 generation 拒绝执行。

只有确实尝试写入的 ensure 可将 owned SQLite 从 generation 2 升至 3：先校验原库、创建不可覆盖的完整 SQLite backup，然后在一个事务内去重 basis、建立引用并更新 schema_version。保留原有 facts、hash、计数与所有历史 metadata；失败回滚至 generation 2，完整 backup 可恢复。Backup 仅在完整复制成功后保留，复制失败清理未完成 backup。此契约不授权处理旧目录 cache。

去重释放的 SQLite pages 可供后续写入复用，不承诺已有文件立刻缩小，不在 ensure 内隐式 VACUUM。

## 4. Transactions、read snapshots 与 validation

一个 ensure 可以复用一个写连接；pending / failure / success 各自提交短事务。每个 success 事务同时更新 instruments、替换其 records、引用 frozen basis 并更新成功 metadata；使用批量 SQL 不放宽逐 unit 原子性。外键约束始终开启。完整结构、identity 和全库引用校验在写 session 入口、出口及每次 read snapshot 执行，不逐条记录或逐个短事务重复扫描全库；每个短事务仍核对 Dataset identity/generation。

读操作使用一个 committed snapshot，在此 snapshot 内复用相同 basis 的 JSON 解析；所有目标 success records 仍逐条校验 content hash 和 Dataset completeness。不得通过跳过旧数据验证、读写共用事务、WAL 或 consumer 直读 SQL 来加速。

Snapshot 可以在同一 read transaction 内有界批量取得目标 units、records 和关联 instruments，并复用 join 得到的 instrument facts；在内存还原原目标及记录顺序、关联去重，不另开 snapshot。SQL 批次限制参数和临时行缓冲；最终 public view 的 materialization 契约不变。批量读取仍对每个成功 unit 执行原有 hash/count、错误 metadata、basis 与 Dataset completeness 验证，不把 status='success' 当作完整性证明。
