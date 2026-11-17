import type { validateResult as validateDaily } from '../../src/features/futures_calendar_spread/presentation'
import type { validateResult as validateHistorical } from '../../src/features/calendar_spread_relative_value/presentation'
import type { validateOptionChain } from '../../src/features/mo_option_chain/presentation'
import type { validatePremiumPlane } from '../../src/features/mo_option_premium/presentation'
import type { validateEmbeddedReport } from '../../src/features/futures_basis_research/presentation'
import type { validateEmbeddedBacktestResult } from '../../src/features/backtesting/presentation'
import type { EmbeddedCatalogPayload } from '../../src/features/research_catalog/presentation'
import type { EmbeddedPublicationSetPayload } from '../../src/features/research_explorer/presentation'
import type { RegistryEntry } from '../build/registry'

export type ExampleKey = RegistryEntry['bundle_id']
export interface ResultIdentity {
  id: ExampleKey
  preset_id: string
  result_contract: string
  source: { kind: 'formal_http'; description: string }
}
export interface BundleData {
  calendar_spread_daily: ReturnType<typeof validateDaily>
  calendar_spread_relative_value: ReturnType<typeof validateHistorical>
  chain: ReturnType<typeof validateOptionChain>
  premium: ReturnType<typeof validatePremiumPlane>
  basis: ReturnType<typeof validateEmbeddedReport>
  expiry_to_M1_v1: ReturnType<typeof validateEmbeddedBacktestResult>
  expiry_to_Q1_v1: ReturnType<typeof validateEmbeddedBacktestResult>
  catalog: EmbeddedCatalogPayload
  publications: EmbeddedPublicationSetPayload
}
export type BundleLoaders = Record<ExampleKey, () => Promise<{ default: unknown }>>
