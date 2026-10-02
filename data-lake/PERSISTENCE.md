# DataLake SQLite execution and generation authority

本文件拥有内部 SQLite 生命周期和明确的 generation 2 → 3 升级契约，继承 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 的单位 ownership 与原子性；不是 consumer SQL contract，也不是通用 migration framework。

Generation 3 在每个 Dataset 自己的 SQLite 内保存内容寻址的 frozen basis；多个 units 可以引用完全相同的 immutable basis。不得跨 Dataset 共享 basis。Unit 的历史 basis、records、content_hash、record_count、status 与取得时间仍一一对应；新 catalog 不修改旧 success basis。内容 hash 与存储原文必须一致；冲突、缺失引用及损坏必须报 OperationError。

coverage/export 支持合法 generation 2 和 3，保持真正只读，包括不升级、不备份、不建索引。全部已成功或零目标 ensure 同样不升级。只有确实尝试写入的 ensure 可升级 generation 2：先校验原库、创建不可覆盖的完整 SQLite backup，然后在一个事务内去重 basis、建立引用并更新 schema_version。保留原有 facts、hash、计数与所有历史 metadata；失败回滚至 generation 2，backup 可恢复。未知 generation 拒绝执行。旧目录 legacy cache 仍不迁移、不 fallback。

一个 ensure 可以复用一个写连接；pending / failure / success 各自提交短事务。每个 success 事务同时更新 instruments、替换其 records、引用 frozen basis 并更新成功 metadata；使用批量 SQL 不放宽逐 unit 原子性。外键约束始终开启。完整结构、identity 和全库引用校验在写 session 入口、出口及每次 read snapshot 执行，不逐条记录或逐个短事务重复扫描全库；每个短事务仍核对 Dataset identity/generation。

读操作使用一个 committed snapshot，在此 snapshot 内复用相同 basis 的 JSON 解析；所有目标 success records 仍逐条校验 content hash 和 Dataset completeness。不得通过跳过旧数据验证、读写共用事务、WAL 或 consumer 直读 SQL 来加速。

升级释放的 SQLite pages 可供后续写入复用；去重不承诺原有文件立刻缩小，不在 ensure 内隐式 VACUUM。Backup 仅在完整复制成功后作为恢复依据保留，复制失败清理未完成 backup。

Snapshot 可以在同一 read transaction 内有界批量取得目标 units、records 和关联 instruments，并复用 join 得到的 instrument facts；在内存还原原目标及记录顺序、关联去重，不另开 snapshot。SQL 批次限制参数和临时行缓冲；最终 public view 的 materialization 契约不变。批量读取仍对每个成功 unit 执行原有 hash/count、错误 metadata、basis 与 Dataset completeness 验证，不把 status='success' 当作完整性证明。
