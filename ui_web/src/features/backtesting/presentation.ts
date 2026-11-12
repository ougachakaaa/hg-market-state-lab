export { BacktestingPresentation } from './page/BacktestingPresentation'
export type { BacktestingPresentationProps } from './page/BacktestingPresentation'
export { useStaticBacktesting } from './static/useStaticBacktesting'
export type { StaticBacktestingState } from './static/useStaticBacktesting'
export {
  CASE_ID,
  DEFINITION_VERSION,
  matchesResponse,
  RESULT_PROFILE,
  sameRequest,
  validateEmbeddedBacktestResult,
  validateImmutableRequest,
  validateResult,
  validateResultResponse,
  validateRunState,
} from './api/validateResult'
export type {
  Accepted,
  BacktestResult,
  EmbeddedBacktestResultPayload,
  ImmutableRequest,
  Preflight,
  ResultResponse,
  Run,
  RunRequest,
  ValidatedEmbeddedBacktestResult,
} from './api/validateResult'
export { STATIC_BACKTESTING_DISCLOSURE, STATIC_BACKTESTING_SOURCE_NOTE } from './model/staticPresentation'
export { Result } from './components/Result'
