# DataLake Outbound Ports authority

本文件拥有 Shared Kernel 的 Source / Repository Outbound capability contracts，继承 [模块架构](ARCHITECTURE.md)、[公共领域](DOMAIN_MODEL.md) 与 [Application operations](APPLICATION.md)。端口由 Kernel 定义，具体外部实现向端口依赖；端口不定义 Dataset 业务规则或 consumer API。六角色组合责任见 [COMPOSITION.md](COMPOSITION.md)。下列接口是能力与输入输出契约，不锁定 Python 方法名、Protocol 数量或内部类型拆分。

## 1. Source Port

Source Port 向 Application 提供：**对一批已选 FetchUnits 获取事实，并按这些 units 的 canonical identity 返回可供 Normalizer 处理的输入**。实现由 owning Dataset 的 Source Adapter 提供。Kernel 只传递通用 Unit，不解释 identity 的维度、endpoint、provider parameters 或响应类型。

| Responsibility | Contract |
| --- | --- |
| Input | 已合法展开、已选择执行的一批目标 units；batch 是执行分组，不改变 FetchUnit ownership |
| Output | 按目标 unit identity 对应的事实输入，或可定位到 unit 的安全失败；内部可使用 canonical unit key，不对 consumer 发布 persistence identity |
| Missing | 未提供目标 unit 的事实不是成功；必须进入该 unit 的 missing/completeness failure 路径，不能用空输入隐式证明零 Records 合法 |
| Request boundary | Adapter 决定 endpoint、parameters、metadata/catalog acquisition、pagination/exhaustion、response partition 与 provider representation 的交接；领域 normalization 规则由 Dataset 策略定义。一个请求可服务多个 units，一个 unit 也可需要多个请求 |
| Out-of-target facts | 请求范围可以包含已缓存或非目标 facts，但不授权提交 selected units 之外的状态或 Records；无法合法归属的响应按 owning Dataset failure isolation 处理 |
| Lifecycle | Application 仅在存在 selected units 时准备 Source；Adapter 的 provider initialization 遵守 APPLICATION.md 的 lazy I/O；worker 不访问 SQLite |

Source Adapter 将 provider-native representation 交给 Dataset 的 Normalizer；可调用 Dataset-owned 纯领域函数，不因此取得规则的 semantic ownership。Adapter 可以在内部提前 normalize 或分类，边界上仍须保持第 3 节的逐 unit 交接、验证与失败责任；不强制重复转换或拆成额外 transport DTO。

Source Port 与 Provider Executor 是不同边界：`Application → Source Port ← Dataset Source Adapter → Provider Infrastructure → external API`。Provider 返回 transport response、转换 provider execution failures；Dataset Adapter 负责请求与目标 unit 的对应。Provider 不实现 Kernel Source Port，也不接收 FetchUnits。Tushare 执行、凭据、共享限流与取消 guard 只由 [Provider authority](providers/tushare/ARCHITECTURE.md) 拥有。

可恢复请求/响应失败使用现有 provider-neutral `ExecutionFailure`：批请求失败由 Application 按该批实际尝试的 units 编码；可定位的 unit failure 只影响对应 unit。Normalizer / Validator 同样可报告可恢复逐 unit failure。Source 初始化或整个 operation 无法执行时为 `OperationError`，不伪装成正常缺行。已标 success 的缓存不合法时为 cache integrity / operation failure，不能悄悄转成一次新 fetch。公共分类唯一见 APPLICATION.md。

取消能力属于 Source 的执行生命周期，可按实际 Source 需要提供，不是第三个业务 Port；Application 触发取消与等待的契约见 [EXECUTION.md](EXECUTION.md)。端口不引入 retry、quota、credential 或 generic provider framework。

## 2. Repository Port

Repository Port 向 Application 与 Dataset 内部 composition 提供 **单个 owning Dataset 的通用缓存读写能力**。Kernel 定义能力并维护标准 SQLite Adapter；Dataset 只绑定自己的 identity、source identity 与 storage context，不重复实现 SQLite Repository，不向 consumer 暴露端口或连接。

| Capability | Input / output responsibility |
| --- | --- |
| Consistent read | 输入明确目标 units；返回同一 committed snapshot 的 statuses、成功 units 的 canonical Records、关联 Instrument facts 与 frozen basis。无 row 为 missing；不存在缓存时返回一致的空状态，不 materialize storage |
| Integrity | 验证 Dataset identity / generation、结构与引用、成功 metadata、record_count / content_hash 与 basis integrity；不认识交易日、合约类型或 Dataset completeness predicate |
| Internal metadata reuse | 可读取成功 identity，再对明确选定的代表 units 取一致 snapshot；解释 identity、选择代表、验证业务合法性及是否可复用由 Dataset 负责，不能仅凭 status 或裸 instrument row 信任 metadata |
| Write session | 仅供有权写入的 ensure 使用；可复用连接，但不跨 Source I/O 持有写事务 |
| Pending / failure | 对明确 selected unit 保存 pending 或其安全失败 metadata，状态语义继承 DOMAIN_MODEL.md；中断的未提交 attempts 保持可重试 |
| Atomic success | 输入 Unit 与已通过完整性验证的 UnitRecords；一致提交该 unit 的 Records、关联 instruments、frozen basis 与成功 metadata，返回本次成功写入 Record 数，失败不得留下 success |

Repository 不选择目标、不请求 Source、不决定何时重试/跳过、不推导 expected universe，也不生成 Dataset Export View。Coverage accounting 和 complete 的意义由 Application 拥有；Adapter 返回的内部 snapshot 即使携带公共统计，也只能实现该公共计数公式，不能另定业务含义。Application 在所有读路径对成功事实调用 Dataset Validator 后才发布 coverage / view；Repository integrity 检查不能代替这一验证。

SQLite connection、transaction、read snapshot、冻结 basis 存储、缺失/不兼容库与 rebuild-only 规则由 [PERSISTENCE.md](PERSISTENCE.md) specialize；端口不承诺跨库事务、SQL consumer contract、跨 Dataset 查询或新的存储后端。持久化错误映射为 `OperationError`。Source Adapter 不访问 Repository；需要本地合法 metadata 的 Dataset 由内部 composition 在 writer/调用线程取得并验证后交给 Source。

## 3. UnitRecords 数据交接与成功写入前置条件

唯一合法的成功事实写入主线为：

```text
Source Port → Normalizer → UnitRecords → Completeness Validator → Repository Port
```

| 交接责任 | 前置条件 / 输出 |
| --- | --- |
| Source Port | 获取 selected units 所需 Source facts，按 unit identity 分配原始事实与必要 metadata；不以 transport success 声明业务完整 |
| Normalizer | 将对应事实确定性转换为 Kernel 中立 UnitRecords；若 Adapter 已调用同一 Dataset Domain 转换，可接收其载体，不要求再次转换 |
| Completeness Validator | 对明确 Unit + UnitRecords 验证业务字段、identity、cardinality、Instrument association 和完整性依据；UnitRecords 本身不是证明，提前验证不能取代成功提交前的这一关口 |
| Repository Port | 仅接收已通过 Dataset 验证且内容未变化的 UnitRecords，执行通用 integrity 检查和逐 FetchUnit 原子成功提交；不推导或替代业务 completeness |

Application 协调上述交接及 pending/failure 状态写入；pending/failure metadata 不构成另一条成功事实写入路径。Normalizer/Validator 失败不调用 atomic success，不保存部分 Records 为 success；新的可恢复 unit failure 与成功缓存读校验失败分别遵循 APPLICATION.md 的 UnitFailure / OperationError 分类。

读取 cached success 时，Repository 从一个 committed snapshot 返回 facts/basis 并检查通用 integrity，Application 将其交给同一 Dataset completeness predicate 重新验证后才用于 skip、coverage、metadata reuse 或 export。Read-only 验证不重新 fetch、不重写 basis、不修改状态；Domain 不负责读取数据库。

Source Port 和 Repository Port 不直接调用彼此；不得引入 Source-to-Repository Port 或让 Source worker 持有写能力。Provider execution、Normalizer 和 Resolver 都不增加 Kernel Outbound Port 的数量，仍只有 Source 与 Repository 两个。
