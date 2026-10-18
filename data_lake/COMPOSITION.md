# DataLake Dataset Composition authority

本文件拥有自治 Dataset 接入 Shared Kernel 的公共 Composition Contract，继承 [模块架构](ARCHITECTURE.md)。Domain primitives 见 [DOMAIN_MODEL.md](DOMAIN_MODEL.md)，三个 Use Cases / public result / failures 见 [APPLICATION.md](APPLICATION.md)，两个 Outbound capability contracts 见 [PORTS.md](PORTS.md)。具体 Dataset 的领域特化与角色绑定从 [DATASETS.md](DATASETS.md) 进入其 ARCHITECTURE.md；不要求阅读 sibling internals。

## 1. 六个核心接入角色

Dataset 是自治领域边界，不是一个 Use Case。它定义事实全集、自然身份、标准化、完整性与 Export 语义；Composition Root 将下列 **四个领域策略 + 两个 Outbound Ports** 接入 Kernel Application。

| 接入角色 | Semantic owner | 输入 → 输出 / 责任 |
| --- | --- | --- |
| FetchUnitPlanner | Dataset Domain | Dataset Request + Planning Context → 完整目标 FetchUnits；纯领域展开，契约见第 3 节 |
| Source Port / Adapter | Kernel 定义 Port；Dataset 拥有 Adapter | selected unit batch → 逐 unit 事实输入 / 安全失败；Dataset 决定 Source mapping，Provider 执行外部请求，详见 PORTS.md |
| Normalizer | Dataset Domain | 一个目标 Unit + 对应 Source facts / 合法 metadata basis → canonical UnitRecords（Records、关联 Instruments、必要 basis）；确定性转换，不补造事实或生成分析派生值 |
| Completeness Validator | Dataset Domain | 一个 Unit + UnitRecords → 通过或明确失败；定义 cardinality、自然 identity、required facts、instrument association 与 expected/observed predicate，纯验证、不补取 Source、不写库 |
| Export Projector | Dataset Domain / public view semantics | 本次 request context + 已验证 coverage + 同一 snapshot 的成功 cached facts / basis → SERVICE.md 定义的业务 Export View、ordering 与空 payload；不再次读库或访问 Source |
| Repository Port / Adapter | Kernel 定义 Port 并维护标准 SQLite Adapter；Dataset 绑定存储实例 | 明确 units / 状态操作 / 已验证 UnitRecords ↔ Dataset-local consistent snapshot / 原子提交结果；持久化机制见 PORTS.md 与 PERSISTENCE.md |

这些是责任角色，不要求每个策略各自建立 Protocol、抽象基类、类或文件，也不要求六个构造器参数。`UnitRecords` 是 Kernel 的通用事实组载体，不能内置某个 Dataset 的字段或 expected-set 解释；其载体不变量由 DOMAIN_MODEL.md 拥有，数据交接与写入前置条件由 PORTS.md 拥有。业务 Scope / Window 可以保留 Dataset typed objects，Kernel 仅拥有公共语义，不建立通用维度 schema。

## 2. Composition Root 与 Public Service

Composition Root 由 owning Dataset 维护，选择并绑定领域策略、Dataset Source Adapter、标准 Repository Adapter、自己的 storage context 与已授权的 Dataset Public Service dependencies。它可依赖这些具体实现；Application 本身只依赖 Domain / Ports。Root 不能通过共享实例合并两个 Dataset 的 persistence ownership。

Dataset Public Application Service 是 Composition 的产物和唯一 consumer boundary，拥有 semantic request validation、按 operation permission 调用可选 Prerequisite Resolver、调用 FetchUnitPlanner 与 Kernel delegation。它不是第七个接入角色，也不是 Kernel Inbound Adapter。`create_service()`、public class / request / result / view 与 errors 保持原 SERVICE.md 契约；Source、Repository、token、prefetch、Planning Context 和内部策略不进入 public request。

普通 factory 仅组合依赖，不能读取 credential、初始化 provider client、发起 Source I/O 或 materialize SQLite。Coverage/export 的全部调用链只读。Ensure 只有实际需要 Source I/O 才初始化相关 provider；无 selected units 时不准备自己的 Source。Prerequisite 是否需要 ensure 由 Dataset 已声明权限决定，不由 Kernel 推导。

## 3. FetchUnitPlanner

唯一角色名称为 **FetchUnitPlanner**，由 Dataset Domain 拥有：

```text
Dataset Request + Planning Context → FetchUnits
```

Request 已通过 Dataset semantic validation，表达 Scope + Window；Planning Context 只携带本次展开必需且已验证、已固定的合法前置事实，无 prerequisite 的 Dataset 使用空 context。Context 的业务内容由 owning Dataset 声明，Kernel 不定义 Calendar schema 或通用 context registry，也不要求独立 context 类。

Planner 根据 Scope、Window 与必要前置事实确定事实所有权的最小单元及完整目标集合；同一合法 request/context 的展开确定且不因执行方式改变。它不读取数据库状态、不调用 Source 或其他 Dataset service、不创建持久 rows、不决定 Batch 划分、不根据已有 success 缓存、metadata 缺口或行情缺失缩小目标。哪些目标需要执行，随后由 Kernel Application 检查和验证缓存后选择；执行顺序由 [APPLICATION.md](APPLICATION.md) 拥有。

Planning Context 不等于 UnitRecords 的 completeness basis：前者证明目标全集可确定，后者解释一个 unit 的成功事实。当前三个行情 Dataset 的 Calendar context 用于展开交易日；其本地 instrument metadata / contract catalog 在 selected units 的 Source 执行与完整性验证阶段取得，不被移动到 Planner，也不用于裁剪目标。

## 4. 可选 Prerequisite Resolver

**Prerequisite Resolver** 是 Dataset-owned 的可选 Composition 能力，一个 Dataset 可以拥有零个、一个或多个；不是 Dataset Domain 的纯 Planner，不是第七个必需 Kernel 接入角色，也不是第三个 Outbound Port。

```text
Request + Operation Permission → Validated Planning Context
```

Resolver 接收已验证的 owning Dataset request 及本次 operation 允许的能力，通过模块架构已授权的 producer Public Application Service 获取 Planner 所需事实，校验 producer semantic view 与 request 的匹配、完整性和合法性，再交出固定的 context。Operation Permission 由 owning Composition 根据 operation 和已声明 dependency 权限提供，不由 caller 输入，也不因 Resolver 复用扩大。

| Operation | Resolver 权限 |
| --- | --- |
| coverage | Read-only；只使用已授权 prerequisite read-only public operations |
| export | Read-only；只使用已授权 prerequisite read-only public operations |
| ensure | 必要时允许调用已授权 prerequisite ensure；不得顺带确保无关范围或其他 Dataset |

Resolver 不直接访问 producer Source、Repository、SQLite 或 internal modules，不写 consumer units；没有授权 edge 就不能使用该 producer。前置事实不可用且无法确定目标全集时必须抛明确 OperationError，不能交出不完整 context、未知日期子集或伪造零目标。公共失败分类与执行顺序由 APPLICATION.md 拥有；具体 request、exchange、ensure 条件、view validation 与失败特化留在 owning TRADING_DAYS.md。

多个 Resolver 可组合、复用已有实现，但所需依赖、顺序和 context 合并由 owning Dataset Composition 明确决定，不由 Kernel 推导。只有匹配本次 request、producer 契约和 operation permission 的已验证事实可以在同一 operation 内复用；共享 consumer/producer service 或无状态 Resolver 实例不授权跨 operation 信任旧 context。可变中间结果不得泄漏至后续 operation；本次 context 在 planning、Use Case 与 projection 期间固定，结束即释放。Factory 只绑定 Resolver，不执行它；共享 Provider 生命周期仍按 Provider authority。

当前 Calendar 使用零 Resolver；Index / Futures / Options 各拥有一个 Calendar Resolver，规则从各自 ARCHITECTURE.md 进入 TRADING_DAYS.md。其他 Dataset 是否依赖 Calendar 由自己的目标全集要求和明确 dependency permission 决定，不作为所有 Dataset 的强制能力。不得引入 Kernel-wide Dependency Graph Engine、全局 Resolver Registry 或跨 Dataset 内部依赖。

## 5. 可选执行策略与生命周期

Dataset 可提供 **BatchPlanner**，与 FetchUnitPlanner 独立；它只将 Kernel 已选择的 FetchUnits 组合为 Source Requests 的执行 batches，不改变 unit identity、状态 ownership 或逐 unit 原子写入粒度。可选性、partition 契约、验证与调度由 [EXECUTION.md](EXECUTION.md) 拥有；具体 grouping / endpoint limits 归 Dataset。BatchPlanner 不属于四个领域策略，也不是第三个 Outbound Port。

Prefetch 是 Kernel 执行配置，不是业务 Port 或 public semantic input。Source/catalog、Completeness Validator 的 memo 与 typed projection cache 按 operation/read snapshot 限定生命周期；Composition Root 负责建立正确实例，不能复用可变的旧 operation basis。Shared Provider execution state 遵守 Provider 自己的 process/credential lifecycle，不随 Dataset operation 销毁或重置。

## 6. 目标代码职责组织

Kernel 的目标目录由模块架构锁定。Dataset 保持 `datasets/<dataset-id>/src/data_lake/datasets/<dataset-id>/` 的 co-location 与 public namespace，按实际职责组织：

- Dataset Domain：业务 Scope / Window interpretation、FetchUnitPlanner、facts / metadata normalization、Completeness Validator、Export Projector；只依赖 Kernel 中立领域/结果类型与本 Dataset 语义。
- Dataset Source Adapter：provider-native requests、分页、partition、调用本 Dataset 纯领域映射；依赖 Kernel Source Port 与 Provider Infrastructure，不依赖 SQLite 或 sibling internals。
- Composition Root / Public Service：request validation、可选 Resolver 的绑定与权限/顺序/context 管理、Planner 调用，绑定领域策略与具体 Adapters，委托三个 Kernel Use Cases；允许导入已授权 producer 的 public facade。
- Public models / facade：保留现有 public types、import surface、wire meaning 与 errors；对外不发布内部策略或 persistence types。

不锁定 Dataset 的机械文件模板；当前 `_models.py`、`_source.py`、`_service.py` 的名字不授予 semantic ownership。纯业务规则不能因调用 provider 或当前 colocate 于 adapter 文件而被定义为 Provider / Kernel 规则。只因一个 Dataset 存在的逻辑仍归该 Dataset；重复的 representation helper 不自动证明应抽进 Kernel。

新增或修改 Dataset 时，先在 owning authority 确认事实、六角色绑定和必要依赖权限，再实现；不得新增 DataLakeService、DatasetManager、Registry、Plugin Framework、通用依赖图或无实际职责的 Inbound Adapter。

当前实现映射与待处理差异见 [IMPLEMENTATION.md](IMPLEMENTATION.md)；该文档不定义第二套语义，也不授权额外的 implementation 重构。
