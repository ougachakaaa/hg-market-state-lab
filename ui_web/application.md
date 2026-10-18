# ui_web application integration authority

本文档从属于 [ui_web architecture](ARCHITECTURE.md)，并遵循 [presentation architecture](presentation-architecture.md) 定义的内部 ownership boundary；它只拥有 Web application 的 entry、feature discovery/navigation、layout/shell 与 composition boundary。Ordinary UI、application-level theme 与 CSS policy 遵循 [UI system authority](ui-system.md)。正式 frontend surfaces 由 [feature catalog](FEATURES.md) 导航；各 surface 的产品与 visualization 语义仍由其 co-located feature authority 拥有。

## 1. Application Surfaces

当前 Web application 组合两个 sibling feature surfaces：

```text
ui_web application
        │
        ├── MO Option Chain
        │
        └── MO Premium Plane
```

MO Option Chain 是默认 application entry。用户必须能够通过显式 feature navigation 发现并在 MO Option Chain 与 MO Premium Plane 之间切换；加入 Premium Plane 不得替换、隐藏或破坏现有 Option Chain surface。

## 2. Application Ownership

Application shell 只拥有：

```text
application entry
feature discovery and navigation
application layout / shell
feature composition boundary
```

它不拥有或解释：

```text
market or product semantics
product query identity or request adaptation
option or premium calculations
expiry, strike or metric semantics
visual encoding and formatting
feature-local loading, failure or presentation state
```

Application navigation 只选择当前 feature surface，不成为 backend product contract 或 feature-local state 的 semantic owner。

## 3. Feature Independence

MO Option Chain 与 MO Premium Plane 保持独立 frontend bounded contexts。它们不共享产品 identity、backend DTO、query state、presentation state 或 visualization semantics，也不从 sibling feature 的 response 或 local state 派生自己的事实。

Application composition 不改变两者的 backend dependencies，也不表示两个 backend products 存在业务耦合。切换 surface 时 feature state 的 React lifecycle 或持久化机制属于实现细节；无论采用何种机制，一个 feature 都不得读取、覆盖或重新解释另一个 feature 的 local state。

## 4. Implementation Boundary

本 authority 不规定 React Router、navigation control 的精确 component/props、URL scheme、component tree、mounting strategy、CSS filename、state-management library 或 generic feature framework；这些实现选择仍须遵循 `ui-system.md` 规定的 Ant Design、theme 与 custom CSS boundary。实现只需满足默认 entry、显式 navigation、两个 surface 可访问及 bounded-context independence，不为假设中的未来 feature 引入 plugin 或 routing abstraction。
