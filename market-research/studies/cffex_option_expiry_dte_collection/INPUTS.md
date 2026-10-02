# Expiry DTE Collection inputs 与 run identity

本文件拥有 [Study](ARCHITECTURE.md) 的 request、parameter relationships、canonicalization、future CLI 映射、execution-only options 与 deterministic run identity。Invocation consumer / workflow 见 [METHOD.md](METHOD.md)，retention 见 [RESULTS.md](RESULTS.md)。

## Required semantic request

| Parameter | Semantic owner / canonical contract | Consumers / identity role | Future CLI expression |
| --- | --- | --- | --- |
| product_code | Study 选择值；domain / canonicalization 引用 [ExpiryUniverse inputs](../../observations/cffex_option_expiry_universe/ARCHITECTURE.md#inputs-与-business-identity) 与 [chain inputs](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md#inputs-与-canonicalization)，两者一致。 | Universe、全部 planned chains、两个 workflow Artifacts；identity-changing。 | --product-code，例如 MO |
| expiry_start_date | Study 选择 inclusive expiry window 起点；date domain 引用 Universe。 | Universe、plan / collection context；identity-changing。 | --expiry-start-date，YYYY-MM-DD |
| expiry_end_date | Study 选择 inclusive expiry window 终点；date domain / start<=end 引用 Universe。 | Universe、plan / collection context；identity-changing。 | --expiry-end-date，YYYY-MM-DD |
| target_dte | Study 选择值；正整数自然日 domain 唯一引用 chain inputs，拒绝 bool。 | 全部 planned chain invocations、plan / collection；identity-changing。 | --target-dte，正整数文本 |

四项均必填、无默认值。CLI 只解析显式日期 / integer expression 为 canonical semantic types，非法输入不 trim / 改大小写、不倒置交换 window、不使用 today 或 timestamp 默认值。Study 不扩展 Observation domains；所有参数先验证再执行 workflow / upstream invocation。

两端选择的是 expiry_date，不是 observation_date。Study 将 window 原样交给 Universe；每个 discovered expiry 与 target_dte 交给 chain。Observation 自己解析实际日期，Study 不执行 expiry-DTE 日期算术。

## Deterministic run identity 与 Artifact identities

```text
normalized semantic request
    = (product_code, expiry_start_date, expiry_end_date, target_dte)
Study run identity
    = normalized semantic request within cffex_option_expiry_dte_collection
Workflow Artifact identity
    = Study identity + Study run identity + expiry_plan / observation_collection
```

合法 canonical values 按原值比较；等价 CLI 表达解析为相同 semantic values 后是相同请求，任一值变化均区分 run。Inputs 覆盖实际 dependency bindings，不把 discovered expiry list、derived dates、execution timestamp、UUID、Source / code hash、path、输出位置、attempt 顺序、reuse counts 或 overwrite 加入 run identity。

Run-key filesystem encoding / hash、具体 filenames / serialization 留给后续 implementation design；必须保持上述等价 / 区分规则与 [UI filesystem safety / placement](../../ui/ARCHITECTURE.md#3-shared-configuration-and-output-placement)。Semantic identity 不由目录字符串替代，也不定义 cache / resume。

## Execution-only options 与 invocation surface

Future Study CLI 通过 `lab research run cffex-option-expiry-dte-collection` 接收上述四个 flags；本轮只有 authority，不表示命令已可运行。`--overwrite` 为 Study-owned optional boolean flag，默认 false，CLI / run-output handling 消费，仅授权整个 Study run directory replacement，不进入 identity，不授权 Observation refresh。

Shared configuration 仅使用 [output.root](../../ui/CONFIGURATION.md)，不增加 Study 参数、token、SQLite path、config override 或 resume flags。Canonical output collision 在调用 workflow / Observations 前处理。
