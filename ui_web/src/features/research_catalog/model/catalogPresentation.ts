import type { Capability } from '../api/validateCatalog'

// Local presentation state explicitly distinguishes online discovery, a local Python /
// offline case, and the validated list/detail records currently available to render.
export type CatalogSelection =
  | { kind: 'online'; id: string }
  | { kind: 'local'; id: string }
  | null

export type CatalogListState =
  | { status: 'loading' }
  | { status: 'success'; data: Capability[] }
  | { status: 'error'; error: unknown }
  | { status: 'invalid'; error: unknown }

export type CatalogDetailState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: Capability }
  | { status: 'error'; error: unknown }
  | { status: 'missing'; id: string }

export interface ResearchOverviewController {
  list: CatalogListState
  detail: CatalogDetailState
  selection: CatalogSelection
  selectOnline: (id: string) => void
  selectLocal: (id: string) => void
  // Static composition has no online request lifecycle to retry.
  retryList?: () => void
  retryDetail?: () => void
}

export type ResearchOverviewMode = 'production' | 'static'

export interface ResearchOverviewNavigation {
  openExplorer: () => void
  openFuturesBasis: () => void
}

export const STATIC_CATALOG_DISCLOSURE =
  'Embedded Capability Example · 静态能力描述，不代表当前服务状态；浏览器未执行认证 GET，也未探测 Provider、Token 或缓存。'

export const STATIC_LOCAL_CASE_NOTE =
  '以上为正式产品的 Case 说明与访问方式；静态演示不执行 Python、在线 Run 或报告生成。'
