# Expiry DTE Collection request 与 semantic identity

本文件拥有 [Study](ARCHITECTURE.md) 的 canonical request、parameter relationships、canonicalization、CLI 映射与 semantic request identity。Invocation bindings / execution 见 [METHOD.md](METHOD.md)，runtime presentation 见 [RESULTS.md](RESULTS.md)，Python mapping / CLI handoff 见 [IMPLEMENTATION.md](IMPLEMENTATION.md)。本 Study 没有 retained run output。

## Required semantic request

| Parameter | Semantic owner / canonical contract | Consumers / identity role | CLI expression |
| --- | --- | --- | --- |
| product_code | Study 选择值；domain / canonicalization 引用 [Universe inputs](../../shared/cffex_option_expiry_universe/CONTRACT.md#inputs) 与 [chain inputs](../../observations/cffex_option_expiry_dte_chain/ARCHITECTURE.md#inputs-与-canonicalization)，两者一致。 | Universe、所有 planned chains、runtime request context；identity-changing。 | --product-code，例如 MO |
| expiry_start_date | Study 选择 inclusive expiry window 起点，date domain 引用 Universe。 | Universe、runtime plan / outcome context；identity-changing。 | --expiry-start-date，YYYY-MM-DD |
| expiry_end_date | Study 选择 inclusive expiry window 终点，date domain / start<=end 引用 Universe。 | Universe、runtime plan / outcome context；identity-changing。 | --expiry-end-date，YYYY-MM-DD |
| target_dte | Study 选择值，正整数自然日 domain 唯一引用 chain inputs，拒绝 bool。 | 全部 chain invocations、runtime outcome；identity-changing。 | --target-dte，正整数文本 |

四项均必填、无默认值，canonical field 仍为 product_code。CLI 解析显式日期 / integer expression 为 canonical semantic types；所有 inputs 先验证再进入 workflow / dependency factories。非法输入不 trim / 改大小写、不倒置交换 window、不猜名称，不使用 today / timestamp / hidden date defaults。

两端选择的是 expiry_date window，不是 observation_date window。Study 将 window 原样交给 Universe，再将每个 discovered expiry 与 target_dte 交给 chain；实际 observation_date / actual_dte 由 chain 决定，Study 不执行 expiry-DTE 日期算术。

## Semantic request identity

```text
normalized semantic request
    = (product_code, expiry_start_date, expiry_end_date, target_dte)
Study request identity
    = Study identity + normalized semantic request
```

合法 canonical values 按原值比较，等价 CLI 表达解析为相同 values 后是同一个请求；任一值变化区分请求。Discovered list、derived dates、execution time / UUID、Source / code hash、path、attempt 顺序或 counts 不进入 identity。

该 identity 只表达请求等价关系，不是 persistent Study run Artifact identity，不映射为 filesystem run key / hash / directory，也不建立 Study cache / resume。METHOD 分别绑定 resolver inputs 与 chain business key；只有 chain 由 Observation persistence durable reuse，Universe inputs 无 artifact identity / research cache。

## Invocation surface

Canonical user command 为：

```bash
lab research run cffex-option-expiry-dte-collection \
  --product-code MO \
  --expiry-start-date 2025-01-01 \
  --expiry-end-date 2026-10-01 \
  --target-dte 30
```

Invocation 使用 shared resolver + chain Observation 的声明 bindings。实际数据可用性依已选 upstream completeness proof 决定。本 Study 属 [orchestration-only UI shape](../../ui/ARCHITECTURE.md#3-shared-configuration-and-output-placement)，不加载 output.root 配置、不创建 retained Study run directory，不提供 --output、--database、--sqlite-path、--resume、--overwrite 或 config override。CLI parse request → invoke Study orchestration → present outcome；Component construction / I/O 与 Observation persistence 分别归其 owner。
