export const registry = [
  {
    bundle_id: 'basis',
    path: 'basis.json',
    preset_id: 'basis',
    result_contract: 'futures_basis_research:FuturesBasisReportResponse.data',
    validator: 'validateEmbeddedReport',
  },
  {
    bundle_id: 'catalog',
    path: 'catalog.json',
    preset_id: 'catalog',
    result_contract: 'research:CapabilityDescription[]+CapabilityDescription',
    validator: 'validateEmbeddedCatalog',
  },
  {
    bundle_id: 'chain',
    path: 'chain.json',
    preset_id: 'chain',
    result_contract: 'mo_option_chain:OptionChainDTO',
    validator: 'validateOptionChain',
  },
  {
    bundle_id: 'expiry_to_M1_v1',
    path: 'expiry_to_M1_v1.json',
    preset_id: 'expiry_to_M1_v1',
    result_contract: 'backtesting:FuturesRollResultResponse.data',
    validator: 'validateEmbeddedBacktestResult',
  },
  {
    bundle_id: 'expiry_to_Q1_v1',
    path: 'expiry_to_Q1_v1.json',
    preset_id: 'expiry_to_Q1_v1',
    result_contract: 'backtesting:FuturesRollResultResponse.data',
    validator: 'validateEmbeddedBacktestResult',
  },
  {
    bundle_id: 'premium',
    path: 'premium.json',
    preset_id: 'premium',
    result_contract: 'mo_option_premium:PremiumPlaneResponse',
    validator: 'validatePremiumPlane',
  },
  {
    bundle_id: 'publications',
    path: 'publications.json',
    preset_id: 'publications',
    result_contract: 'research_publication:PublicationList+Manifest+Analysis+ChartView',
    validator: 'validateEmbeddedPublicationSet',
  },
] as const
export type RegistryEntry = typeof registry[number]
