# ui_web UI system authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md) 与 [presentation architecture](presentation-architecture.md)，拥有 ordinary application UI、application-level theme、generic UI composition 与 custom CSS exception 的边界。Feature 的产品展示与 analytical visualization 语义仍由 [feature catalog](FEATURES.md) 导航到对应 co-located authority。

## 1. Stable UI-system Split

Frontend presentation 保持以下稳定分工：

```text
ordinary application UI
        ↓
Ant Design

analytical / financial visualization
        ↓
feature model and chart semantics
        ↓
shared chart infrastructure
        ↓
Plotly
```

Ant Design 是 `ui_web` 的标准 ordinary UI component system。Navigation、layout、form controls、buttons、selectors、checkbox/radio controls、cards、descriptions、alerts、loading/empty presentation、collapse/disclosure、ordinary tables、spacing、typography、border、radius 与 standard responsive layout 应优先由 Ant Design components、layout primitives 与 theme tokens 表达。

可用的 Ant Design primitives 包括 `Layout`、`Flex` / `Space`、`Typography`、`Button`、`DatePicker`、`Select`、`Radio`、`Checkbox`、`ColorPicker`、`Card`、`Descriptions`、`Alert`、`Empty`、`Spin`、`Collapse` 与 `Table` 等；该列表用于说明 ownership，不是逐组件迁移清单，也不锁定精确 component selection、props 或 package version。

Analytical visualization 的外观本身携带 feature semantics，包括 chart encoding、expiry opacity、Call / Put / Futures identity、Spot / Futures reference、strike-relative coloring、heatmap、probability plane、market-state coloring 与其他 analytical marks。这些语义仍由 owning feature 的 model、charts 或 visualization authority 拥有。Ant Design 可以提供 surrounding layout 和 controls，但不得成为 analytical encoding 的 semantic owner；Plotly 也不得成为 generic application UI system。

## 2. Theme and Composition Ownership

Application shell 必须通过一个 application-level UI provider 向所有 frontend surfaces 提供共享 theme/configuration。Conceptual ownership 为：

```text
app/
    AppUiProvider          application-wide provider boundary

shared/ui/
    theme                  domain-neutral UI policy
```

精确文件名与 component tree 属于实现细节。Shared theme 拥有深色优先的近黑背景、克制的黑白灰层级、primary accent、font、control sizing、spacing、border radius 与 component density；使用 Ant Design Dark Algorithm 和 theme tokens。

Shared theme 不得拥有 MO、expiry、Call / Put、premium、market-state、chart-series identity 或 analytical classification 语义。Feature semantic colors 与 visual encodings 必须留在 owning feature/model/chart/visualization boundary。

`features/<feature>/components/` 继续拥有 feature-specific React presentation。Feature components 可以直接组合 Ant Design primitives，同时拥有 `ExpirySelector`、`PremiumMetricControls`、`OptionChainSummary` 或 `RawResponseInspector` 等 feature meaning。不得仅因组件使用 Ant Design 或在多个 feature 中结构相似，就把 feature semantics 移入 `shared/ui`。

`shared/ui` 只在 repository 确实形成跨 feature、domain-neutral 的稳定 invariant 时拥有 abstraction，例如 application theme、common page frame、generic query panel 或 generic error/empty state。不得仅为隐藏 Ant Design 而建立 `OurButton`、`OurCheckbox`、`OurSelect` 或 `OurTable` 等 wrapper；只有 repository 自身增加了稳定行为或语义时，wrapper 才成立。

## 3. CSS Policy

Ordinary UI presentation 按以下优先级实现：

```text
1. Ant Design component
2. Ant Design component props / layout primitives
3. shared theme / design tokens
4. component-level token / configuration
5. custom CSS
```

Custom CSS 是 exception path，不是 ordinary UI 的默认机制。当前四层机制不能清晰表达 specialized layout、analytical visualization semantics、chart-specific geometry 或 feature-specific visual encoding 时，可以使用 custom CSS，并应靠近 owning feature 或 chart。

不得使用 feature-local CSS 重建 UI system 已拥有的 button/input/select/fieldset styling、card border、ordinary table chrome、generic spacing、generic typography 或 generic navigation styling。Custom CSS 仍可表达 expiry swatch、custom chart legend geometry、chart frame sizing、strike-relative cell coloring、analytical highlighting 与 visualization overlay 等 concern。

Domain-neutral chart defaults 可以位于 `shared/charts`，但 `below-reference` / `at-reference` / `above-reference`、Call / Put / Futures identity、expiry opacity 等 semantic encoding 不得进入 generic application theme 或由 shared infrastructure 重新定义。

## 4. CSS Exception Review

Custom CSS 必须按 ownership 而不是按当前 selector 或文件名审查：

- application-global CSS 只保留无法由 provider、theme 或 component configuration 表达的最小 browser reset；
- feature-local CSS 可以表达 analytical color、identity、highlighting、legend mark 与其他 visual encoding，但不得接管 ordinary control chrome；
- chart frame、legend geometry、overflow、sticky/scrolling analytical table 与 raw response code presentation 等 specialized presentation，可以在 Ant Design 不拥有该 concern 时保留；
- 一旦规则只是在复制 generic control、card、table、navigation、spacing 或 typography behavior，就属于 implementation drift，必须回到 Ant Design 或 shared theme。

审查结果只决定该 concern 应由 UI system、feature semantics 还是 specialized presentation 拥有；不得把 incidental selector、CSS filename 或当前 component tree 固化为 authority。

## 5. Implementation and Maintenance Boundary

以下属于 architecture authority：

```text
Ant Design owns ordinary UI
Plotly renders analytical charts under feature chart semantics
application-level provider and shared theme own global ordinary visual policy
feature components may consume Ant Design directly
shared UI remains domain-neutral
custom CSS is an exception path
analytical visual semantics remain feature-owned
```

Exact Ant Design version、component selection、prop choice、token value、provider filename、component tree、CSS filename 与 individual specialized-layout decision 属于 implementation choice，但不得违反上述 boundary。

UI-system changes 不改变 Page / Hooks / API / Model / Components / Charts ownership，不改变 MO Option Chain 或 MO Premium Plane semantics，也不改变 test ownership。
