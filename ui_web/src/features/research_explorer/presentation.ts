export { ResearchExplorerPresentation } from './page/ResearchExplorerPresentation'
export { AnalysisDetails } from './components/AnalysisDetails'
export { useStaticExplorer } from './static/useStaticExplorer'
export {
  matchesAnalysis,
  matchesManifest,
  matchesPublicationList,
  matchesResponse,
  validateAnalysis,
  validateChartViewData,
  validateChartViewResponse,
  validateManifest,
  validatePublicationList,
} from './api/validateResearch'
export type { Analysis, Manifest, PublicationList } from './api/validateResearch'
export {
  validateEmbeddedPublicationSet,
} from './api/validateEmbeddedPublication'
export type {
  EmbeddedChartViewRecord,
  EmbeddedPublicationSetPayload,
  ValidatedPublicationSet,
} from './api/validateEmbeddedPublication'
export type {
  ExplorerLoad,
  ResearchExplorerController,
  ResearchExplorerMode,
} from './model/explorerPresentation'
export { STATIC_EXPLORER_DISCLOSURE, STATIC_SOURCE_NOTE } from './model/explorerPresentation'
export { ResearchError } from './model/failures'
export type { FailureKind } from './model/failures'
