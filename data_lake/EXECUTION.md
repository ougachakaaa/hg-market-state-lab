# DataLake bounded execution authority

本文件拥有 Kernel Application 的内部批调度、验证复用与生命周期契约，继承 [DOMAIN_MODEL.md](DOMAIN_MODEL.md) 和 [APPLICATION.md](APPLICATION.md)。角色绑定见 [COMPOSITION.md](COMPOSITION.md)，外部能力边界见 [PORTS.md](PORTS.md)；具体 endpoint、分页实现、分组大小与完整性仍由 Dataset 拥有；provider 限流与错误转换由 [Tushare authority](providers/tushare/ARCHITECTURE.md) 拥有。

## 1. BatchPlanner 与目标规划的边界

Prerequisite resolution 与 FetchUnitPlanner 在进入批执行前已经固定完整目标，调用顺序见 APPLICATION.md。FetchUnitPlanner 拥有最小事实所有权单元与目标全集；**BatchPlanner** 是独立的可选执行策略，只决定如何把 Kernel Application 选中的 FetchUnits 组合为 Source Requests 的执行 batches，不访问 prerequisite 来重规划目标。

```text
complete desired FetchUnits → Kernel cache validation / selection
    → selected FetchUnits → BatchPlanner → Source batches
```

BatchPlanner 输入 selected units，输出有限、非空 batches 的精确 partition：全部 selected units 恰出现一次，没有遗漏、重复或额外 units；selected 为空时不启动批执行。没有具体 batching 需要时使用 Kernel 默认分组。Dataset 拥有分组与 endpoint limits，Kernel 验证 partition、调度并协调 writer；一个 execution batch 可由 Adapter 映射为一个或多个请求。Planner 不参与分组，BatchPlanner 不改变 FetchUnit identity、status ownership、completeness predicate 或逐 FetchUnit 原子写入粒度。

Calendar 的 FetchUnit 始终是 `(exchange, cal_date)`，包含自然日与休市日；Calendar-owned BatchPlanner 可以按自然年组合同 exchange 的 selected 日期，范围请求仍 partition 回逐日 facts。自然年是 Source Batch 边界，不是年度 FetchUnit，也不意味着只生成开市日 unit；具体绑定见 [Calendar architecture](datasets/tushare_trade_calendar/ARCHITECTURE.md)。

## 2. Batch、worker、writer 与取消

一次 ensure 只选择 missing / non-success units。Source batch 必须精确 partition 这些 units；请求覆盖的日期区间可以包含已缓存日期，但只能提交 selected units。每个 unit 在其请求开始前提交 pending，完整性通过后独立原子提交；网络请求期间不得持有写事务。

采用 offset/limit 分页的 Dataset Source Adapter 必须取得空终页，短页不能证明结束。Offset 按原始响应行数推进，完整分页保留重复自然 identity，不能静默去重。可定位的重复 identity 按 owning Dataset completeness 隔离失败；重复整页或其他无法证明穷尽的响应使整批失败，不作为合法分页结束。

Source Adapter 按 Dataset identity 将响应 partition；单 unit 数据异常只影响该 unit，无法证明整个请求完整的错误影响该批。Source 只保留当前有界 batch 的批量事实响应，释放后才处理下一 batch，不保留整段 operation 的批量事实响应 cache；可跨 batch 复用的合法 metadata / basis 仍由 Dataset authority 决定。已知前置事实取得失败时不启动无法提交的后续请求；业务归属与失败隔离规则仍由 Dataset authority 拥有。

ensure 可以启用一个 Source worker 和主线程单 Repository writer（标准实现为 SQLite Adapter），最多提前一个 batch。所有 provider calls 仍经过共享限流；worker 不访问 SQLite。前一批持久化与后一批 Source I/O 可以重叠。Operation failure / interruption 停止后续提交并取消尚未开始的工作，触发 Source 的 cancellation guard，等待已进入的请求收束，后续分页/metadata calls 不再启动；已提交 units 保留，已开始但未提交 units 留为可重试 pending。不得隐藏重试。

每次 operation/read snapshot 可复用同一冻结 basis 的解析、metadata 合法性验证和 Dataset-provided indices；复用只限内部保持不变的同一对象，不跨 operation 信任曾通过验证的可变数据。每个 unit 仍由 Dataset 策略验证其业务 completeness（包含适用的 expected/observed 集合）和每条 canonical Record、instrument association、record_count 和 content_hash。前置事实取得与合法 metadata 复用遵循 owning Dataset authority；Kernel 不决定何时需要重新取得或哪份 basis 可用于新的业务 expected set。

存储连接与结构校验的边界见 [PERSISTENCE.md](PERSISTENCE.md)；复用与批执行不改变 public result、coverage、export ordering 或只读边界。Planning Context 的 Resolver 复用由 COMPOSITION.md 拥有，不与此处 Source metadata / completeness basis 复用混为一谈。

同一 export 可复用其 committed snapshot 内已完整验证的 canonical Record 所投影的 typed row；缓存由 owning Dataset 拥有，保留 Record 对象身份且内部 facts 在验证与 projection 之间不变，操作结束即释放。不得跨 operation 复用、在 coverage/ensure 保留整窗 typed rows，或让 kernel 认识具体行情行类型。每条 Record 仍至少完整验证一次，unit hash/count、metadata 对照、expected/observed 与 instrument association 均不省略。固定 typed schema 的字段集合可预先计算。
