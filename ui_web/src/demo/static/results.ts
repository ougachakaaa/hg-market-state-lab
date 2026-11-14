import type { validateOptionChain } from '../../features/mo_option_chain/api/validateOptionChain'
import type { validatePremiumPlane } from '../../features/mo_option_premium/api/validatePremiumPlane'
import type { validateEmbeddedReport } from '../../features/futures_basis_research/api/validateResult'
import type { validateEmbeddedBacktestResult } from '../../features/backtesting/api/validateResult'
import type { validateEmbeddedCatalog } from '../../features/research_catalog/api/validateCatalog'
import type { validateEmbeddedPublicationSet } from '../../features/research_explorer/api/validateEmbeddedPublication'

export const exampleKeys = ['chain', 'premium', 'basis', 'catalog', 'publications', 'expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const
export type ExampleKey = typeof exampleKeys[number]
export interface ResultIdentity {
  id: ExampleKey
  revision: 1
  delivery: 'static'
  origin: 'real_market'
  execution: 'historical_embedded_result'
  provider: string
  producer: string
  sourceRevision: string
  inputFingerprint: string | null
  evidenceDigest: string
  resultDigest: string
}
// Composition types only: no legacy package admission or fixed dataset profile.
export interface StaticData {
  chain: ReturnType<typeof validateOptionChain>
  premium: ReturnType<typeof validatePremiumPlane>
  basis: ReturnType<typeof validateEmbeddedReport>
  m1: ReturnType<typeof validateEmbeddedBacktestResult>
  q1: ReturnType<typeof validateEmbeddedBacktestResult>
  catalogPayload: Parameters<typeof validateEmbeddedCatalog>[0]
  publicationPayload: Parameters<typeof validateEmbeddedPublicationSet>[0]
  identities: Record<ExampleKey, ResultIdentity>
}
