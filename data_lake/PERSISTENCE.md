# DataLake SQLite lifecycle and compatibility authority

本文件是 Kernel Outbound SQLite Repository Adapter 的 canonical authority，拥有内部 SQLite lifecycle、transaction / read snapshot、frozen basis 与 rebuild-only cache compatibility，继承 [ARCHITECTURE.md](ARCHITECTURE.md) 的 owned SQLite boundary、[DOMAIN_MODEL.md](DOMAIN_MODEL.md) 的单位 ownership / 原子性及 [APPLICATION.md](APPLICATION.md) 的 read-only / export consistency invariant；实现 [Repository Port](PORTS.md)；不反向拥有 Application lifecycle 或 Dataset completeness，不发布 consumer SQL contract 或通用 migration framework。

## 1. Owned SQLite lifecycle

Dataset composition 显式提供本 Dataset 的 storage context，shared path machinery 不提供全局默认 root，也不创建目录或 SQLite。当前默认 owned filename 为 `<dataset-id>.sqlite3`，位于模块架构声明的 Dataset-local `data/`；目录仅在有权写入的 operation 需要时 materialize。缓存缺失及非法缓存的 public 行为继承 APPLICATION.md。

旧 `data_lake/data/*.sqlite3` 是隔离的 legacy runtime state：不自动移动、复制、删除、覆盖，不作为 factory、coverage/export 或 ensure 的 fallback，不双写，也不建立旧目录 compatibility layer。不通过迁移或 import 使旧缓存兼容当前 runtime；不兼容缓存的处理遵循下方 rebuild-only contract。本契约不授权自动处理旧目录 state。

## 2. Frozen basis invariant

Generation 3 在每个 Dataset 自己的 SQLite 内保存内容寻址的 frozen basis；多个 units 可以引用完全相同的 immutable basis。不得跨 Dataset 共享 basis。Unit 的历史 basis、records、content_hash、record_count、status 与取得时间仍一一对应；新 catalog 不修改旧 success basis。内容 hash 与存储原文必须一致；冲突、缺失引用及损坏必须报 OperationError。

## 3. Rebuild-only cache compatibility

DataLake persistence 是可重建的 reusable source-fact cache，不是需要长期 schema migration 的业务数据库。一个 Dataset exactly owns 一个 SQLite，因此 incompatible cache 的最小 rebuild ownership boundary 是 owning Dataset；不要求 repository-wide DataLake rebuild，不合并 prerequisite 或 sibling Dataset 的 storage lifecycle。

当前 canonical internal persistence generation 为 3。`schema_version` / generation 只检测 persisted shape 与当前 runtime 的兼容性，不驱动 migration。Generation 2、未知 generation 或其他不兼容 persisted schema 必须明确失败，要求重建 owning Dataset cache；即使目标 units 已 success 或目标为空，也不允许通过旧格式 compatibility path 消费不兼容缓存。Public failure mapping 见 [APPLICATION.md](APPLICATION.md)。

不做 in-place migration、automatic upgrade、fallback、dual-read、dual-write 或 migration backup / transactional upgrade；不为未来建立 migration framework。

Cache rebuild 是显式 owning Dataset 操作，不由 coverage、ensure、export 或 factory 自动删除、覆盖或转换旧库。本文件锁定 ownership 与失败要求，不定义 rebuild CLI、删除流程或其他执行 mechanics。

Internal persistence shape 与 public semantic contract 是正交 concern：内部不兼容要求 Dataset cache rebuild；public request/result/view、population、grain 或 completeness 改变则需按 owning authority 对 downstream 做正常 reconciliation。内部 generation 变化不自动改变 public export schema version 或 payload。

Frozen basis 去重释放的 SQLite pages 可供后续写入复用，不承诺已有文件立刻缩小，不在 ensure 内隐式 VACUUM；兼容 cache 内的逐 unit atomic transactions 仍遵守下一节。

## 4. Transactions、read snapshots 与 validation

一个 ensure 可以复用一个写连接；pending / failure / success 各自提交短事务。每个 success 事务同时更新 instruments、替换其 records、引用 frozen basis 并更新成功 metadata；使用批量 SQL 不放宽逐 unit 原子性。外键约束始终开启。完整结构、identity 和全库引用校验在写 session 入口、出口及每次 read snapshot 执行，不逐条记录或逐个短事务重复扫描全库；每个短事务仍核对 Dataset identity/generation。

读操作使用一个 committed snapshot，在此 snapshot 内复用相同 basis 的 JSON 解析；所有目标 success records 仍逐条校验 content hash 和 Dataset completeness。不得通过跳过旧数据验证、读写共用事务、WAL 或 consumer 直读 SQL 来加速。

Snapshot 可以在同一 read transaction 内有界批量取得目标 units、records 和关联 instruments，并复用 join 得到的 instrument facts；在内存还原原目标及记录顺序、关联去重，不另开 snapshot。SQL 批次限制参数和临时行缓冲；最终 public view 的 materialization 契约不变。批量读取仍对每个成功 unit 执行原有 hash/count、错误 metadata、basis 与 Dataset completeness 验证，不把 status='success' 当作完整性证明。
