# DataLake bounded execution authority

本文件拥有内部批执行、验证复用与生命周期契约，继承 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 和 [APPLICATION.md](APPLICATION.md)。具体 endpoint、分组大小与完整性仍由 Dataset 拥有；provider 限流与错误转换由 [Tushare authority](providers/TUSHARE.md) 拥有。

一次 ensure 只选择 missing / non-success units。Source batch 必须精确 partition 这些 units；请求覆盖的日期区间可以包含已缓存日期，但只能提交 selected units。每个 unit 在其请求开始前提交 pending，完整性通过后独立原子提交；网络请求期间不得持有写事务。分页必须取得空终页，短页不能证明结束；重复页或重复自然 identity 属于 completeness failure。

批响应按日期及产品 partition；单 unit 数据异常只影响该 unit，无法证明整个请求完整的错误影响该批。Source 只保留当前小窗口的行情响应，释放后才处理下一窗口，不保留整段历史 daily cache。已知 catalog/metadata failure 时不启动无法提交的后续行情请求；产品隔离规则仍由 Dataset completeness 拥有。

ensure 可以启用一个 Source worker 和主线程单 SQLite writer，最多提前一个 batch。所有 provider calls 仍经过共享限流；worker 不访问 SQLite。前一批持久化与后一批 Source I/O 可以重叠。Operation failure / interruption 停止后续提交并取消尚未开始的工作，触发 Source 的 cancellation guard，等待已进入的请求收束，后续分页/metadata calls 不再启动；已提交 units 保留，已开始但未提交 units 留为可重试 pending。不得隐藏重试。

每次 operation/read snapshot 可复用同一冻结 basis 的解析、metadata 合法性验证和 contract indices；复用只限内部保持不变的同一对象，不跨 operation 信任曾通过验证的可变数据。每个 unit 仍验证 expected/observed 集合、每条 canonical Record、instrument association、record_count 和 content_hash。新 ensure 尝试使用新取得的 catalog，不以历史成功 basis 推断当前 contract universe。

存储连接与结构校验的边界见 [PERSISTENCE.md](PERSISTENCE.md)；复用与批执行不改变 public result、coverage、export ordering 或只读边界。
