import type { StaticData, ResultIdentity, ExampleKey } from './results'
import { validateOptionChain } from '../../src/features/mo_option_chain/presentation'
import { validatePremiumPlane } from '../../src/features/mo_option_premium/presentation'
import { validateEmbeddedReport } from '../../src/features/futures_basis_research/presentation'
import { validateEmbeddedBacktestResult } from '../../src/features/backtesting/presentation'
import { validateEmbeddedCatalog, type EmbeddedCatalogPayload } from '../../src/features/research_catalog/presentation'
import { validateEmbeddedPublicationSet, type EmbeddedPublicationSetPayload } from '../../src/features/research_explorer/presentation'
import { registry } from '../build/registry'

type Bundle = { bundle_id: ExampleKey; preset_id: string; result_contract: string;
  source: ResultIdentity['source']; request: unknown; result: unknown }
export function adaptBundles(input: unknown): StaticData {
  if (!Array.isArray(input) || input.length !== registry.length) throw new Error('Invalid Bundle dataset')
  const bundles = new Map<ExampleKey, Bundle>()
  for (const value of input) {
    const entry = registry.find(entry => entry.bundle_id === value?.bundle_id)
    if (!entry || bundles.has(value.bundle_id) || value.bundle_format !== 'demo_bundle_v1' ||
      value.preset_id !== entry.preset_id || value.result_contract !== entry.result_contract ||
      value.source?.kind !== 'formal_http' || typeof value.source.description !== 'string' || !value.source.description.trim()) throw new Error('Invalid Bundle identity')
    bundles.set(value.bundle_id, value)
  }
  const get = (id: ExampleKey) => {
    const bundle = bundles.get(id)
    if (!bundle) throw new Error('Missing Bundle')
    return bundle
  }
  const basis = get('basis'), m1 = get('expiry_to_M1_v1'), q1 = get('expiry_to_Q1_v1')
  const catalogPayload = get('catalog').result as EmbeddedCatalogPayload
  const publicationPayload = get('publications').result as EmbeddedPublicationSetPayload
  validateEmbeddedCatalog(catalogPayload)
  validateEmbeddedPublicationSet(publicationPayload)
  return {
    chain: validateOptionChain(get('chain').result), premium: validatePremiumPlane(get('premium').result),
    basis: validateEmbeddedReport({ request: basis.request, report: basis.result }),
    m1: validateEmbeddedBacktestResult({ request: m1.request, result: m1.result }),
    q1: validateEmbeddedBacktestResult({ request: q1.request, result: q1.result }),
    catalogPayload, publicationPayload,
    identities: Object.fromEntries([...bundles].map(([id, bundle]) => [id, {
      id, preset_id: bundle.preset_id, result_contract: bundle.result_contract, source: bundle.source,
    }])) as StaticData['identities'],
  }
}
export function disclose(identity: ResultIdentity): string {
  return `${identity.id} · ${identity.source.description} · 构建前已通过结构与完整性校验。静态只读，不进行实时金融计算。数据不保证准确，仅供项目功能展示，不构成投资建议。`
}
