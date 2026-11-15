import type { validateOptionChain } from '../../src/features/mo_option_chain/api/validateOptionChain'
import type { validatePremiumPlane } from '../../src/features/mo_option_premium/api/validatePremiumPlane'
import type { validateEmbeddedReport } from '../../src/features/futures_basis_research/api/validateResult'
import type { validateEmbeddedBacktestResult } from '../../src/features/backtesting/api/validateResult'
import type { validateEmbeddedCatalog } from '../../src/features/research_catalog/api/validateCatalog'
import type { validateEmbeddedPublicationSet } from '../../src/features/research_explorer/api/validateEmbeddedPublication'

export const exampleKeys = ['chain', 'premium', 'basis', 'catalog', 'publications', 'expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const
export type ExampleKey = typeof exampleKeys[number]
export interface ResultIdentity {
  id: ExampleKey
  preset_id: string
  result_contract: string
  source: { kind: 'formal_http'; description: string }
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
