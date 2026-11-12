import type { ChartView as ChartViewContract } from '../../../shared/visualization/contract'
import type { Analysis, Manifest, PublicationList } from '../api/validateResearch'

// Four independent request results plus local view-selection state. The same contract is
// implemented by the Production HTTP controller and the Embedded Publication controller.
export type ExplorerLoad<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: unknown }
  | { status: 'missing'; id: string }
  | { status: 'invalid'; error: unknown }

export interface ResearchExplorerController {
  list: ExplorerLoad<PublicationList>
  manifest: ExplorerLoad<Manifest>
  result: ExplorerLoad<Analysis>
  chart: ExplorerLoad<ChartViewContract>
  publication: string | null
  analysis: string | null
  view: string | null
  page: number
  canPrevious: boolean
  canNext: boolean
  selectPublication: (id: string | null) => void
  selectAnalysis: (id: string | null) => void
  setView: (id: string) => void
  previous: () => void
  next: () => void
  /**
   * Static composition: the embedded page set is a prefix and its final page declares a
   * further online page that is not embedded. It never means the online list ended.
   */
  morePagesNotEmbedded?: boolean
  retryList?: () => void
  retryManifest?: () => void
  retryResult?: () => void
  retryChart?: () => void
}

export type ResearchExplorerMode = 'production' | 'static'

export const STATIC_EXPLORER_DISCLOSURE =
  'Embedded Publication Example · 静态 Publication 示例；未查询在线 Publication Store，未执行研究，不代表实时服务或 Provider 状态。示例 Provenance / Source Metadata 不证明真实市场来源。'

export const STATIC_SOURCE_NOTE =
  '以上为嵌入示例的 Provenance / Source Metadata；未执行 Research Producer，也不证明真实市场来源。'
